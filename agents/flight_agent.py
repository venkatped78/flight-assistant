# ============================================================
# agents/flight_agent.py — Flight Search AI Agent
# Uses Claude Tool Use for structured flight operations
# ============================================================

import json
import re
import random
import string
from datetime import datetime
from typing import List, Optional, Dict, Any
import anthropic

from config.settings import (
    config, MODEL, AGENT_SYSTEM_PROMPT,
    FLIGHT_TOOLS, AIRPORTS, AIRLINES,
)
from models.flight import (
    Flight, Passenger, Booking, SearchQuery,
    CabinClass, TripType, PriceAlert,
    BookingStatus,
)
from services.flight_engine import get_engine, MockFlightEngine
from services.database import Database
from services.ticket_generator import TicketGenerator


def _make_id(prefix="", n=8):
    return prefix + "".join(random.choices(string.ascii_uppercase + string.digits, k=n))


class FlightAgent:
    """
    AI Flight Assistant powered by Claude with Tool Use.

    The agent:
    1. Understands natural language queries
    2. Calls flight search/booking tools
    3. Returns human-friendly responses
    4. Maintains conversation context
    """

    def __init__(self, api_key: str = None):
        self.client   = anthropic.Anthropic(api_key=api_key or config.anthropic_api_key)
        self.engine   = get_engine()
        self.db       = Database(config.db_path)
        self.ticketer = TicketGenerator()
        self.history  = []          # Conversation history
        self._flights_cache: List[Flight] = []   # Last search results
        self._last_booking: Optional[Booking]    = None

    # ─── Main Chat Interface ──────────────────────────────────

    def chat(self, user_message: str) -> str:
        """
        Process user message and return assistant response.
        Handles multi-turn conversation with tool use.
        """
        self.history.append({"role": "user", "content": user_message})

        while True:
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=4000,
                system=AGENT_SYSTEM_PROMPT,
                tools=FLIGHT_TOOLS,
                messages=self.history,
            )

            # If no tool use, return text response
            if response.stop_reason == "end_turn":
                assistant_text = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        assistant_text += block.text
                self.history.append({
                    "role":    "assistant",
                    "content": response.content,
                })
                return assistant_text

            # Process tool calls
            if response.stop_reason == "tool_use":
                self.history.append({
                    "role":    "assistant",
                    "content": response.content,
                })

                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = self._execute_tool(block.name, block.input)
                        tool_results.append({
                            "type":        "tool_result",
                            "tool_use_id": block.id,
                            "content":     json.dumps(result),
                        })

                self.history.append({
                    "role":    "user",
                    "content": tool_results,
                })
                # Continue loop for Claude to process tool results

    # ─── Tool Executor ───────────────────────────────────────

    def _execute_tool(self, tool_name: str, inputs: Dict[str, Any]) -> Dict:
        """Route tool calls to appropriate handlers."""
        handlers = {
            "search_flights":       self._tool_search_flights,
            "get_flight_details":   self._tool_get_flight_details,
            "book_flight":          self._tool_book_flight,
            "get_booking":          self._tool_get_booking,
            "cancel_booking":       self._tool_cancel_booking,
            "get_airport_info":     self._tool_get_airport_info,
            "check_visa_requirements": self._tool_check_visa,
            "get_price_calendar":   self._tool_price_calendar,
            "set_price_alert":      self._tool_set_price_alert,
        }
        handler = handlers.get(tool_name)
        if not handler:
            return {"error": f"Unknown tool: {tool_name}"}
        try:
            return handler(inputs)
        except Exception as e:
            return {"error": str(e), "tool": tool_name}

    # ─── Tool Implementations ─────────────────────────────────

    def _tool_search_flights(self, inputs: dict) -> dict:
        """Search flights based on query."""
        query = SearchQuery(
            origin      = inputs["origin"].upper(),
            destination = inputs["destination"].upper(),
            date        = inputs["date"],
            passengers  = inputs.get("passengers", 1),
            cabin_class = CabinClass(inputs.get("cabin_class", "economy")),
            return_date = inputs.get("return_date"),
            max_stops   = inputs.get("max_stops", 2),
            preferred_airline = inputs.get("preferred_airline"),
        )

        result = self.engine.search(query)
        self._flights_cache = result.flights
        self.db.log_search(query.origin, query.destination,
                           query.date, query.cabin_class.value,
                           result.total_found)

        # Format results
        flights_out = []
        for f in result.flights[:8]:  # Limit to top 8
            flights_out.append({
                "flight_id":      f.flight_id,
                "airline":        f.airline_name,
                "flight_number":  f.segments[0].flight_number,
                "origin":         f.origin,
                "destination":    f.destination,
                "departure":      f.departure_time.strftime("%H:%M on %d %b %Y"),
                "arrival":        f.arrival_time.strftime("%H:%M on %d %b %Y"),
                "duration":       f.duration_str(),
                "stops":          f.stops,
                "stop_description": "Direct" if f.stops == 0 else f"{f.stops} stop(s)",
                "price_inr":      f.price_inr,
                "taxes_inr":      f.taxes_inr,
                "total_inr":      f.total_inr,
                "cabin_class":    f.cabin_class.value,
                "seats_left":     f.seats_left,
                "refundable":     f.refundable,
                "baggage_cabin":  f.baggage_cabin,
                "baggage_checked":f.baggage_checked,
                "deal_badge":     f.deal_badge,
                "price_trend":    f.price_trend,
                "airline_rating": f.airline_rating,
                "amenities":      f.amenities,
            })

        return {
            "status":        "success",
            "total_found":   result.total_found,
            "flights":       flights_out,
            "cheapest_price":result.cheapest.total_inr if result.cheapest else None,
            "fastest_flight":result.fastest.flight_id if result.fastest else None,
            "best_value":    result.best_value.flight_id if result.best_value else None,
            "origin_city":   AIRPORTS.get(query.origin, {}).get("city", query.origin),
            "dest_city":     AIRPORTS.get(query.destination, {}).get("city", query.destination),
            "search_date":   query.date,
        }

    def _tool_get_flight_details(self, inputs: dict) -> dict:
        """Get detailed info for a specific flight."""
        flight_id = inputs["flight_id"]
        flight = next((f for f in self._flights_cache if f.flight_id == flight_id), None)

        if not flight:
            return {"error": f"Flight {flight_id} not found. Please search again."}

        segments = []
        for seg in flight.segments:
            segments.append({
                "flight_number": seg.flight_number,
                "airline":       seg.airline_name,
                "origin":        seg.origin,
                "destination":   seg.destination,
                "departure":     seg.departure_time.strftime("%H:%M, %d %b %Y"),
                "arrival":       seg.arrival_time.strftime("%H:%M, %d %b %Y"),
                "duration":      f"{seg.duration_mins // 60}h {seg.duration_mins % 60}m",
                "aircraft":      seg.aircraft_type,
                "meal":          seg.meal_included,
                "wifi":          seg.wifi_available,
                "seats_available": seg.seats_available,
            })

        return {
            "flight_id":       flight.flight_id,
            "airline":         flight.airline_name,
            "airline_rating":  flight.airline_rating,
            "segments":        segments,
            "total_duration":  flight.duration_str(),
            "stops":           flight.stops,
            "price_inr":       flight.price_inr,
            "taxes_inr":       flight.taxes_inr,
            "total_inr":       flight.total_inr,
            "refundable":      flight.refundable,
            "cancellation_fee":flight.cancellation_fee,
            "baggage_cabin":   flight.baggage_cabin,
            "baggage_checked": flight.baggage_checked,
            "seats_left":      flight.seats_left,
            "amenities":       flight.amenities,
            "available_meals": ["Standard", "Vegetarian", "Vegan", "Jain", "Halal", "Kosher"],
            "seat_map":        "Available at check-in",
        }

    def _tool_book_flight(self, inputs: dict) -> dict:
        """Book a flight."""
        flight_id = inputs["flight_id"]
        flight = next((f for f in self._flights_cache if f.flight_id == flight_id), None)

        if not flight:
            return {"error": "Flight not found. Please search again."}

        # Parse passengers
        passengers = []
        for pax_data in inputs.get("passengers", []):
            passengers.append(Passenger(
                first_name  = pax_data.get("first_name", ""),
                last_name   = pax_data.get("last_name", ""),
                email       = pax_data.get("email", ""),
                phone       = pax_data.get("phone", ""),
                dob         = pax_data.get("dob"),
                passport    = pax_data.get("passport"),
                nationality = pax_data.get("nationality", "Indian"),
            ))

        if not passengers:
            return {"error": "No passenger details provided."}

        booking = self.engine.book(
            flight       = flight,
            passengers   = passengers,
            seat_prefs   = inputs.get("seat_preferences", []),
            meal         = inputs.get("meal_preference", "Standard"),
            extra_baggage= inputs.get("add_baggage", False),
            coupon       = inputs.get("coupon_code", ""),
        )

        self._last_booking = booking
        self.db.save_booking(booking)

        # Generate ticket
        try:
            ticket_path = self.ticketer.generate_ticket(booking)
        except Exception:
            ticket_path = None

        return {
            "status":        "BOOKING_CONFIRMED",
            "pnr":           booking.pnr,
            "flight":        booking.flight.segments[0].flight_number,
            "airline":       booking.flight.airline_name,
            "route":         f"{booking.flight.origin} → {booking.flight.destination}",
            "departure":     booking.flight.departure_time.strftime("%H:%M, %d %b %Y"),
            "arrival":       booking.flight.arrival_time.strftime("%H:%M, %d %b %Y"),
            "passengers":    [f"{p.first_name} {p.last_name}" for p in passengers],
            "seats":         booking.seat_numbers,
            "meal":          booking.meal_preference,
            "total_paid":    booking.total_paid,
            "coupon_applied":booking.coupon_applied,
            "discount":      booking.discount_inr,
            "cancellation_deadline": booking.cancellation_deadline.strftime("%d %b %Y %H:%M") if booking.cancellation_deadline else "N/A",
            "check_in_opens":booking.check_in_open.strftime("%d %b %Y %H:%M") if booking.check_in_open else "N/A",
            "ticket_pdf":    ticket_path,
            "message":       f"Booking confirmed! Your PNR is {booking.pnr}. Ticket PDF generated.",
        }

    def _tool_get_booking(self, inputs: dict) -> dict:
        """Retrieve booking details."""
        pnr = inputs["pnr"].upper()
        booking = self.db.get_booking(pnr)
        if not booking:
            return {"error": f"No booking found for PNR: {pnr}"}

        fd = booking["flight_data"]
        return {
            "pnr":        pnr,
            "status":     booking["status"],
            "airline":    fd["airline"],
            "flight":     fd["flight_number"],
            "route":      f"{fd['origin']} → {fd['destination']}",
            "departure":  fd["departure"],
            "arrival":    fd["arrival"],
            "cabin":      fd["cabin"],
            "passengers": booking["passengers"],
            "seats":      booking["seats"],
            "meal":       booking["meal"],
            "total_paid": booking["total_paid"],
            "coupon":     booking["coupon"],
            "discount":   booking["discount"],
            "booked_at":  booking["created_at"],
        }

    def _tool_cancel_booking(self, inputs: dict) -> dict:
        """Cancel a booking."""
        pnr = inputs["pnr"].upper()
        booking_data = self.db.get_booking(pnr)
        if not booking_data:
            return {"error": f"No booking found for PNR: {pnr}"}

        if booking_data["status"] == "CANCELLED":
            return {"error": "Booking is already cancelled."}

        # Calculate refund
        dep_str  = booking_data["flight_data"]["departure"]
        try:
            dep_time = datetime.fromisoformat(dep_str)
            hrs_left = (dep_time - datetime.now()).total_seconds() / 3600
        except Exception:
            hrs_left = 0

        paid = booking_data["total_paid"]
        if hrs_left > 72:
            refund_pct, policy = 0.90, "Full refund (90%) - cancelled >72h before"
        elif hrs_left > 24:
            refund_pct, policy = 0.70, "Partial refund (70%) - cancelled 24-72h before"
        elif hrs_left > 4:
            refund_pct, policy = 0.50, "Partial refund (50%) - cancelled 4-24h before"
        else:
            refund_pct, policy = 0.0, "No refund - cancelled <4h before departure"

        refund = round(paid * refund_pct, 0)
        self.db.update_status(pnr, "CANCELLED")

        return {
            "status":        "CANCELLED",
            "pnr":           pnr,
            "total_paid":    paid,
            "refund_amount": refund,
            "refund_policy": policy,
            "refund_timeline": "5-7 business days to original payment method",
            "message":       f"Booking {pnr} cancelled. Refund of ₹{refund:,.0f} initiated.",
        }

    def _tool_get_airport_info(self, inputs: dict) -> dict:
        """Get airport information."""
        code = inputs["airport_code"].upper()
        airport = AIRPORTS.get(code)
        if not airport:
            return {"error": f"Unknown airport code: {code}"}

        return {
            "code":     code,
            "name":     airport["name"],
            "city":     airport["city"],
            "country":  airport["country"],
            "timezone": airport["timezone"],
            "terminals": ["Terminal 1", "Terminal 2", "Terminal 3"],
            "facilities": ["Free Wi-Fi", "Lounges", "Duty Free", "Restaurants",
                           "Currency Exchange", "ATMs", "Medical Center"],
            "transport": {
                "metro":  "Metro/subway available in most major airports",
                "taxi":   "Pre-paid taxis available outside arrivals",
                "bus":    "Airport bus service to city center",
                "rental": "Car rental counters in arrivals hall",
            },
            "tips": [
                f"Arrive 2 hours early for domestic, 3 hours for international flights",
                f"Check-in counters open 3 hours before departure",
                f"Security screening can take 20-45 minutes during peak hours",
            ],
        }

    def _tool_check_visa(self, inputs: dict) -> dict:
        """Check visa requirements."""
        nationality = inputs["nationality"]
        destination = inputs["destination"].upper()
        purpose     = inputs.get("travel_purpose", "tourism")

        dest_country = AIRPORTS.get(destination, {}).get("country", destination)

        # Simplified visa rules (in production, use a real visa API)
        visa_free_for_indians = ["Nepal", "Bhutan", "Indonesia (30 days)",
                                  "Maldives", "Jamaica", "Mauritius"]
        visa_on_arrival = ["Thailand", "Sri Lanka", "Cambodia", "Laos",
                           "Myanmar", "Seychelles"]
        e_visa = ["UAE", "USA (ESTA not required for tourists)", "UK",
                  "Singapore", "Malaysia", "Australia", "New Zealand"]

        result = {
            "nationality": nationality,
            "destination": dest_country,
            "purpose":     purpose,
            "documents_required": [
                "Valid passport (6 months validity)",
                "Return ticket",
                "Hotel booking / address proof",
                "Sufficient funds proof",
            ],
        }

        if dest_country in visa_free_for_indians:
            result.update({
                "visa_required": False,
                "visa_type":     "Visa-free",
                "message":       f"No visa required for {nationality} citizens to {dest_country}",
                "max_stay":      "30 days (tourist)",
            })
        elif dest_country in visa_on_arrival:
            result.update({
                "visa_required": True,
                "visa_type":     "Visa on Arrival",
                "fee":           "$25-50 USD approximately",
                "max_stay":      "15-30 days",
                "message":       f"Visa on Arrival available at {dest_country} airports",
            })
        elif dest_country in e_visa:
            result.update({
                "visa_required": True,
                "visa_type":     "e-Visa",
                "apply_at":      f"Official {dest_country} government immigration website",
                "processing":    "3-5 business days",
                "message":       f"Apply for e-Visa online before travel to {dest_country}",
            })
        else:
            result.update({
                "visa_required": True,
                "visa_type":     "Embassy Visa",
                "apply_at":      f"{dest_country} Embassy or consulate",
                "processing":    "2-4 weeks",
                "message":       f"Apply at {dest_country} Embassy well in advance",
            })

        result["disclaimer"] = "Visa rules change frequently. Always verify on official government website."
        return result

    def _tool_price_calendar(self, inputs: dict) -> dict:
        """Get price calendar for flexible dates."""
        origin = inputs["origin"].upper()
        dest   = inputs["destination"].upper()
        month  = inputs["month"]
        cabin  = inputs.get("cabin_class", "economy")

        calendar = self.engine.get_price_calendar(origin, dest, month, cabin)
        prices   = list(calendar.values())

        return {
            "origin":       origin,
            "destination":  dest,
            "month":        month,
            "cabin_class":  cabin,
            "price_calendar": calendar,
            "cheapest_date":  min(calendar, key=calendar.get),
            "cheapest_price": min(prices),
            "most_expensive_date": max(calendar, key=calendar.get),
            "average_price":  round(sum(prices) / len(prices), 0),
            "tip": "Book on the cheapest date for maximum savings!",
        }

    def _tool_set_price_alert(self, inputs: dict) -> dict:
        """Set a price alert."""
        alert = PriceAlert(
            alert_id     = _make_id("ALT", 8),
            origin       = inputs["origin"].upper(),
            destination  = inputs["destination"].upper(),
            date         = inputs["date"],
            target_price = inputs["target_price"],
            email        = inputs["email"],
        )
        self.db.save_alert(alert)
        return {
            "status":        "ALERT_SET",
            "alert_id":      alert.alert_id,
            "route":         f"{alert.origin} → {alert.destination}",
            "date":          alert.date,
            "target_price":  f"₹{alert.target_price:,.0f}",
            "notify_email":  alert.email,
            "message":       f"Price alert set! We'll email {alert.email} when price drops below ₹{alert.target_price:,.0f}",
        }

    # ─── Direct API methods (for CLI) ─────────────────────────

    def reset_conversation(self):
        """Clear conversation history."""
        self.history = []
        self._flights_cache = []

    def get_stats(self) -> Dict:
        return self.db.get_stats()

    def get_all_bookings(self) -> List[dict]:
        return self.db.get_all_bookings()

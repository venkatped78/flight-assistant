# ============================================================
# services/flight_engine.py — Flight Search Engine
# Supports: Mock data (demo) + Real Amadeus API
# ============================================================

import random
import string
import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from models.flight import (
    Flight, FlightSegment, CabinClass, SearchQuery,
    SearchResult, Booking, Passenger, BookingStatus,
    PriceAlert,
)
from config.settings import (
    AIRPORTS, AIRLINES, BASE_FARES_INR,
    CABIN_CLASSES, config,
)


def _make_id(prefix: str = "FL", n: int = 8) -> str:
    return prefix + "".join(random.choices(string.ascii_uppercase + string.digits, k=n))


def _get_base_fare(origin: str, destination: str) -> float:
    """Get base fare for a route (bidirectional)."""
    fare = BASE_FARES_INR.get((origin, destination))
    if not fare:
        fare = BASE_FARES_INR.get((destination, origin))
    if not fare:
        # Estimate based on distance heuristic
        fare = random.uniform(3000, 60000)
    return fare


def _apply_price_factors(base: float, airline: str, cabin: str,
                          days_ahead: int, seats_left: int) -> float:
    """Apply dynamic pricing factors."""
    price = base
    # Cabin multiplier
    price *= CABIN_CLASSES.get(cabin, {"multiplier": 1.0})["multiplier"]
    # Demand factor (closer to departure = more expensive)
    if days_ahead <= 2:
        price *= random.uniform(1.5, 2.5)
    elif days_ahead <= 7:
        price *= random.uniform(1.2, 1.6)
    elif days_ahead <= 14:
        price *= random.uniform(1.0, 1.3)
    elif days_ahead >= 60:
        price *= random.uniform(0.7, 0.9)
    # Seats factor
    if seats_left <= 3:
        price *= 1.3
    # Random variation ±10%
    price *= random.uniform(0.92, 1.12)
    return round(price, -1)  # Round to nearest 10


class MockFlightEngine:
    """
    Production-quality mock flight engine.
    Generates realistic flight data for demo/testing.
    Replace with real API calls (Amadeus, Skyscanner) for production.
    """

    def search(self, query: SearchQuery) -> SearchResult:
        """Search flights and return results."""
        origin = query.origin.upper()
        dest   = query.destination.upper()

        if origin not in AIRPORTS:
            raise ValueError(f"Unknown airport: {origin}")
        if dest not in AIRPORTS:
            raise ValueError(f"Unknown airport: {dest}")

        travel_date = datetime.strptime(query.date, "%Y-%m-%d")
        days_ahead  = (travel_date.date() - datetime.now().date()).days
        base_fare   = _get_base_fare(origin, dest)

        flights     = []
        airline_codes = list(AIRLINES.keys())

        # Determine which airlines fly this route
        is_domestic = (AIRPORTS[origin]["country"] == "India" and
                       AIRPORTS[dest]["country"] == "India")
        if is_domestic:
            route_airlines = ["6E", "AI", "SG", "UK", "QP", "IX"]
        else:
            route_airlines = ["AI", "EK", "QR", "UK", "SQ", "BA", "LH", "EY"]

        random.shuffle(route_airlines)

        for i, airline_code in enumerate(route_airlines[:6]):
            airline = AIRLINES.get(airline_code, {})
            stops   = 0 if i < 3 else random.choice([0, 1])

            if query.max_stops < stops:
                continue

            if query.preferred_airline and airline_code != query.preferred_airline:
                continue

            # Generate departure times
            dep_hour = random.choice([5, 6, 7, 8, 9, 10, 11, 12, 14, 16, 18, 20, 22])
            dep_time = travel_date.replace(hour=dep_hour, minute=random.choice([0, 15, 30, 45]))

            # Flight duration
            base_dur = _estimate_duration(origin, dest, is_domestic)
            if stops > 0:
                base_dur += random.randint(90, 240)  # Layover time

            arr_time = dep_time + timedelta(minutes=base_dur)

            seats_left  = random.randint(1, 50)
            fare        = _apply_price_factors(base_fare, airline_code,
                                               query.cabin_class.value,
                                               days_ahead, seats_left)
            taxes       = round(fare * 0.18, 0)
            total       = fare + taxes

            # Build segments
            segments = []
            if stops == 0:
                segments.append(FlightSegment(
                    flight_number  = f"{airline_code}{random.randint(100,999)}",
                    airline_code   = airline_code,
                    airline_name   = airline.get("name", ""),
                    origin         = origin,
                    destination    = dest,
                    departure_time = dep_time,
                    arrival_time   = arr_time,
                    duration_mins  = base_dur,
                    aircraft_type  = random.choice(["Boeing 737", "Airbus A320", "Boeing 777", "Airbus A380", "Boeing 787"]),
                    cabin_class    = CabinClass(query.cabin_class),
                    seats_available= seats_left,
                    meal_included  = query.cabin_class.value in ["business", "first"],
                    wifi_available = airline_code in ["EK", "QR", "SQ", "BA"],
                ))
            else:
                # With stopover
                via_airports = _get_via_airports(origin, dest, is_domestic)
                via  = random.choice(via_airports)
                dur1 = base_dur // 2 - 30
                dur2 = base_dur // 2 - 30
                mid  = dep_time + timedelta(minutes=dur1)
                lay  = random.randint(60, 180)
                dep2 = mid + timedelta(minutes=lay)
                arr2 = dep2 + timedelta(minutes=dur2)

                segments = [
                    FlightSegment(
                        flight_number  = f"{airline_code}{random.randint(100,999)}",
                        airline_code   = airline_code,
                        airline_name   = airline.get("name", ""),
                        origin         = origin,
                        destination    = via,
                        departure_time = dep_time,
                        arrival_time   = mid,
                        duration_mins  = dur1,
                        aircraft_type  = "Airbus A320",
                        cabin_class    = CabinClass(query.cabin_class),
                        seats_available= seats_left,
                    ),
                    FlightSegment(
                        flight_number  = f"{airline_code}{random.randint(100,999)}",
                        airline_code   = airline_code,
                        airline_name   = airline.get("name", ""),
                        origin         = via,
                        destination    = dest,
                        departure_time = dep2,
                        arrival_time   = arr2,
                        duration_mins  = dur2,
                        aircraft_type  = "Boeing 737",
                        cabin_class    = CabinClass(query.cabin_class),
                        seats_available= seats_left,
                    ),
                ]
                arr_time   = arr2
                base_dur   = int((arr_time - dep_time).total_seconds() / 60)

            # Deal badges
            badge = None
            if fare == min(f.price_inr for f in flights) if flights else True:
                badge = "💰 Cheapest"
            if days_ahead >= 30 and fare < base_fare * 0.85:
                badge = "🔥 Great Deal"
            if seats_left <= 3:
                badge = f"⚡ Only {seats_left} left!"

            # Amenities
            amenities = []
            if query.cabin_class.value in ["business", "first"]:
                amenities = ["Lie-flat seats", "Priority boarding", "Lounge access", "Fine dining"]
            elif airline_code in ["EK", "QR", "SQ"]:
                amenities = ["ICE Entertainment", "USB charging", "Extra legroom"]

            flights.append(Flight(
                flight_id      = _make_id("FL"),
                segments       = segments,
                stops          = stops,
                total_duration = base_dur,
                price_inr      = fare,
                taxes_inr      = taxes,
                total_inr      = total,
                cabin_class    = CabinClass(query.cabin_class),
                refundable     = random.choice([True, True, False]),
                cancellation_fee = round(fare * 0.15, 0) if random.random() > 0.3 else 0,
                baggage_cabin  = "7 kg" if is_domestic else "7 kg",
                baggage_checked= "15 kg" if query.cabin_class.value == "economy" else "32 kg",
                seats_left     = seats_left,
                deal_badge     = badge,
                price_trend    = random.choice(["rising", "falling", "stable"]),
                airline_rating = airline.get("rating", 4.0),
                amenities      = amenities,
            ))

        # Apply max price filter
        if query.max_price:
            flights = [f for f in flights if f.total_inr <= query.max_price]

        # Sort by price
        flights.sort(key=lambda x: x.total_inr)

        result = SearchResult(
            query=query,
            flights=flights,
            total_found=len(flights),
        )
        if flights:
            result.cheapest   = min(flights, key=lambda f: f.total_inr)
            result.fastest    = min(flights, key=lambda f: f.total_duration)
            result.best_value = max(flights, key=lambda f: f.airline_rating / (f.total_inr / 1000))

        return result

    def get_details(self, flight_id: str, all_flights: List[Flight]) -> Optional[Flight]:
        """Get detailed flight info by ID."""
        for f in all_flights:
            if f.flight_id == flight_id:
                return f
        return None

    def book(self, flight: Flight, passengers: List[Passenger],
             seat_prefs: List[str] = None, meal: str = "Standard",
             extra_baggage: bool = False, coupon: str = "") -> Booking:
        """Book a flight and return booking confirmation."""
        pnr = _make_id("PNR", 6)

        # Apply coupon
        discount = 0.0
        if coupon:
            coupon_discounts = {
                "FIRST10": 0.10, "SAVE15": 0.15,
                "SKYFLY": 0.08,  "NEW20": 0.20,
            }
            disc_pct = coupon_discounts.get(coupon.upper(), 0)
            discount = round(flight.total_inr * disc_pct, 0)

        total = (flight.total_inr * len(passengers)) - discount
        if extra_baggage:
            total += 500 * len(passengers)

        # Assign seats
        seat_map = ["A", "B", "C", "D", "E", "F"]
        seats = [f"{random.randint(1,30)}{random.choice(seat_map)}"
                 for _ in passengers]

        booking = Booking(
            pnr              = pnr,
            flight           = flight,
            passengers       = passengers,
            status           = BookingStatus.CONFIRMED,
            total_paid       = total,
            seat_numbers     = seats,
            meal_preference  = meal,
            extra_baggage    = extra_baggage,
            cancellation_deadline = flight.departure_time - timedelta(hours=24),
            check_in_open    = flight.departure_time - timedelta(hours=48),
            coupon_applied   = coupon if discount > 0 else None,
            discount_inr     = discount,
        )
        return booking

    def cancel(self, booking: Booking, reason: str = "") -> Booking:
        """Cancel booking and calculate refund."""
        now        = datetime.now()
        dep_time   = booking.flight.departure_time
        hours_left = (dep_time - now).total_seconds() / 3600

        if hours_left > 72:
            refund_pct = 0.90
        elif hours_left > 24:
            refund_pct = 0.70
        elif hours_left > 4:
            refund_pct = 0.50
        else:
            refund_pct = 0.0

        if not booking.flight.refundable:
            refund_pct = min(refund_pct, 0.10)

        booking.refund_amount = round(booking.total_paid * refund_pct, 0)
        booking.status        = BookingStatus.CANCELLED
        return booking

    def get_price_calendar(self, origin: str, dest: str, month: str,
                            cabin: str = "economy") -> Dict[str, float]:
        """Get cheapest fares for each day of a month."""
        base  = _get_base_fare(origin, dest)
        mult  = CABIN_CLASSES.get(cabin, {"multiplier": 1.0})["multiplier"]
        year, mon = map(int, month.split("-"))
        import calendar
        days = calendar.monthrange(year, mon)[1]
        result = {}
        for d in range(1, days + 1):
            date_str = f"{year}-{mon:02d}-{d:02d}"
            # Weekends slightly cheaper/expensive
            dow  = datetime(year, mon, d).weekday()
            mult2 = 1.1 if dow in [4, 5] else 0.95  # Fri/Sat more expensive
            price = round(base * mult * mult2 * random.uniform(0.85, 1.2), -2)
            result[date_str] = price
        return result


# ─── Amadeus Real API Integration ────────────────────────────

class AmadeusFlightEngine:
    """
    Real Amadeus API integration.
    Get free API keys at: https://developers.amadeus.com

    Setup:
    1. Register at developers.amadeus.com
    2. Create app → get API Key + Secret
    3. Add to .env: AMADEUS_API_KEY, AMADEUS_API_SECRET
    """

    BASE_URL = "https://test.api.amadeus.com"   # Use production URL for live

    def __init__(self):
        self.api_key    = config.amadeus_api_key
        self.api_secret = config.amadeus_secret
        self._token     = None
        self._token_exp = None

    def _get_token(self) -> str:
        """Get OAuth2 access token."""
        if self._token and self._token_exp and datetime.now() < self._token_exp:
            return self._token

        import requests
        resp = requests.post(
            f"{self.BASE_URL}/v1/security/oauth2/token",
            data={
                "grant_type":    "client_credentials",
                "client_id":     self.api_key,
                "client_secret": self.api_secret,
            }
        )
        data = resp.json()
        self._token     = data["access_token"]
        self._token_exp = datetime.now() + timedelta(seconds=data["expires_in"] - 60)
        return self._token

    def search(self, query: SearchQuery) -> SearchResult:
        """Search flights via Amadeus API."""
        import requests

        token   = self._get_token()
        headers = {"Authorization": f"Bearer {token}"}

        params = {
            "originLocationCode":      query.origin,
            "destinationLocationCode": query.destination,
            "departureDate":           query.date,
            "adults":                  query.passengers,
            "travelClass":             query.cabin_class.value.upper(),
            "nonStop":                 "true" if query.max_stops == 0 else "false",
            "currencyCode":            "INR",
            "max":                     20,
        }
        if query.return_date:
            params["returnDate"] = query.return_date

        resp = requests.get(
            f"{self.BASE_URL}/v2/shopping/flight-offers",
            headers=headers, params=params,
        )
        data = resp.json()

        flights = []
        for offer in data.get("data", []):
            try:
                flights.append(self._parse_offer(offer, query))
            except Exception:
                continue

        result = SearchResult(query=query, flights=flights, total_found=len(flights))
        if flights:
            result.cheapest = min(flights, key=lambda f: f.total_inr)
            result.fastest  = min(flights, key=lambda f: f.total_duration)
        return result

    def _parse_offer(self, offer: dict, query: SearchQuery) -> Flight:
        """Parse Amadeus offer into Flight model."""
        price = float(offer["price"]["grandTotal"])
        segs  = []

        for itin in offer["itineraries"]:
            for seg in itin["segments"]:
                dep = datetime.fromisoformat(seg["departure"]["at"])
                arr = datetime.fromisoformat(seg["arrival"]["at"])
                dur = int((arr - dep).total_seconds() / 60)
                al  = seg["carrierCode"]
                segs.append(FlightSegment(
                    flight_number  = f"{al}{seg['number']}",
                    airline_code   = al,
                    airline_name   = AIRLINES.get(al, {}).get("name", al),
                    origin         = seg["departure"]["iataCode"],
                    destination    = seg["arrival"]["iataCode"],
                    departure_time = dep,
                    arrival_time   = arr,
                    duration_mins  = dur,
                    cabin_class    = CabinClass(query.cabin_class),
                ))

        total_dur = sum(s.duration_mins for s in segs)
        return Flight(
            flight_id      = offer["id"],
            segments       = segs,
            stops          = len(segs) - 1,
            total_duration = total_dur,
            price_inr      = price * 0.85,
            taxes_inr      = price * 0.15,
            total_inr      = price,
            cabin_class    = CabinClass(query.cabin_class),
        )


def get_engine():
    """Factory: return real or mock engine based on config."""
    if config.amadeus_api_key and config.amadeus_secret:
        return AmadeusFlightEngine()
    return MockFlightEngine()


# ─── Helper functions ─────────────────────────────────────────

def _estimate_duration(origin: str, dest: str, is_domestic: bool) -> int:
    """Estimate flight duration in minutes."""
    # Known durations
    durations = {
        ("DEL","BOM"): 135, ("DEL","BLR"): 165, ("DEL","HYD"): 155,
        ("DEL","MAA"): 175, ("BOM","BLR"): 105, ("BOM","HYD"): 105,
        ("BLR","HYD"): 65,  ("DEL","DXB"): 195, ("DEL","LHR"): 510,
        ("DEL","JFK"): 870, ("DEL","SIN"): 360, ("BOM","DXB"): 185,
        ("DEL","NRT"): 510, ("DEL","SYD"): 660, ("DEL","BKK"): 270,
        ("DEL","CDG"): 480, ("DEL","DOH"): 195,
    }
    dur = durations.get((origin, dest)) or durations.get((dest, origin))
    if dur:
        return dur + random.randint(-15, 15)
    return random.randint(60, 240) if is_domestic else random.randint(180, 600)


def _get_via_airports(origin: str, dest: str, is_domestic: bool) -> List[str]:
    """Get possible stopover airports."""
    if is_domestic:
        candidates = ["DEL", "BOM", "BLR", "HYD", "MAA"]
    else:
        candidates = ["DXB", "DOH", "SIN", "AUH", "BKK", "KUL", "CDG"]
    return [a for a in candidates if a != origin and a != dest] or ["DXB"]

# ============================================================
# config/settings.py — Flight Assistant Configuration
# ============================================================

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-sonnet-4-20250514"

# ─── Major Airports Database ─────────────────────────────────
AIRPORTS = {
    # India
    "DEL": {"name": "Indira Gandhi International", "city": "New Delhi",     "country": "India",   "timezone": "Asia/Kolkata"},
    "BOM": {"name": "Chhatrapati Shivaji Maharaj", "city": "Mumbai",        "country": "India",   "timezone": "Asia/Kolkata"},
    "BLR": {"name": "Kempegowda International",    "city": "Bangalore",     "country": "India",   "timezone": "Asia/Kolkata"},
    "HYD": {"name": "Rajiv Gandhi International",  "city": "Hyderabad",     "country": "India",   "timezone": "Asia/Kolkata"},
    "MAA": {"name": "Chennai International",       "city": "Chennai",       "country": "India",   "timezone": "Asia/Kolkata"},
    "CCU": {"name": "Netaji Subhas Chandra Bose",  "city": "Kolkata",       "country": "India",   "timezone": "Asia/Kolkata"},
    "COK": {"name": "Cochin International",        "city": "Kochi",         "country": "India",   "timezone": "Asia/Kolkata"},
    "PNQ": {"name": "Pune International",          "city": "Pune",          "country": "India",   "timezone": "Asia/Kolkata"},
    "AMD": {"name": "Sardar Vallabhbhai Patel",    "city": "Ahmedabad",     "country": "India",   "timezone": "Asia/Kolkata"},
    "GOI": {"name": "Goa International (Dabolim)", "city": "Goa",           "country": "India",   "timezone": "Asia/Kolkata"},
    "JAI": {"name": "Jaipur International",        "city": "Jaipur",        "country": "India",   "timezone": "Asia/Kolkata"},
    "LKO": {"name": "Chaudhary Charan Singh",      "city": "Lucknow",       "country": "India",   "timezone": "Asia/Kolkata"},
    # International
    "DXB": {"name": "Dubai International",         "city": "Dubai",         "country": "UAE",     "timezone": "Asia/Dubai"},
    "SIN": {"name": "Singapore Changi",            "city": "Singapore",     "country": "Singapore","timezone": "Asia/Singapore"},
    "LHR": {"name": "London Heathrow",             "city": "London",        "country": "UK",      "timezone": "Europe/London"},
    "JFK": {"name": "John F. Kennedy International","city": "New York",     "country": "USA",     "timezone": "America/New_York"},
    "LAX": {"name": "Los Angeles International",   "city": "Los Angeles",   "country": "USA",     "timezone": "America/Los_Angeles"},
    "CDG": {"name": "Charles de Gaulle",           "city": "Paris",         "country": "France",  "timezone": "Europe/Paris"},
    "FRA": {"name": "Frankfurt Airport",           "city": "Frankfurt",     "country": "Germany", "timezone": "Europe/Berlin"},
    "NRT": {"name": "Narita International",        "city": "Tokyo",         "country": "Japan",   "timezone": "Asia/Tokyo"},
    "SYD": {"name": "Sydney Kingsford Smith",      "city": "Sydney",        "country": "Australia","timezone": "Australia/Sydney"},
    "HKG": {"name": "Hong Kong International",     "city": "Hong Kong",     "country": "China",   "timezone": "Asia/Hong_Kong"},
    "BKK": {"name": "Suvarnabhumi Airport",        "city": "Bangkok",       "country": "Thailand","timezone": "Asia/Bangkok"},
    "KUL": {"name": "Kuala Lumpur International",  "city": "Kuala Lumpur",  "country": "Malaysia","timezone": "Asia/Kuala_Lumpur"},
    "DOH": {"name": "Hamad International",         "city": "Doha",          "country": "Qatar",   "timezone": "Asia/Qatar"},
    "AUH": {"name": "Abu Dhabi International",     "city": "Abu Dhabi",     "country": "UAE",     "timezone": "Asia/Dubai"},
    "ICN": {"name": "Incheon International",       "city": "Seoul",         "country": "South Korea","timezone": "Asia/Seoul"},
    "ORD": {"name": "O'Hare International",        "city": "Chicago",       "country": "USA",     "timezone": "America/Chicago"},
    "AMS": {"name": "Amsterdam Schiphol",          "city": "Amsterdam",     "country": "Netherlands","timezone": "Europe/Amsterdam"},
    "ZRH": {"name": "Zurich Airport",              "city": "Zurich",        "country": "Switzerland","timezone": "Europe/Zurich"},
}

# ─── Airlines Database ───────────────────────────────────────
AIRLINES = {
    # Indian carriers
    "AI":  {"name": "Air India",       "country": "India",   "alliance": "Star Alliance", "rating": 3.8},
    "6E":  {"name": "IndiGo",          "country": "India",   "alliance": "None",           "rating": 4.1},
    "SG":  {"name": "SpiceJet",        "country": "India",   "alliance": "None",           "rating": 3.5},
    "UK":  {"name": "Vistara",         "country": "India",   "alliance": "Star Alliance",  "rating": 4.3},
    "QP":  {"name": "Akasa Air",       "country": "India",   "alliance": "None",           "rating": 4.0},
    "IX":  {"name": "Air India Express","country":"India",   "alliance": "None",           "rating": 3.6},
    # International
    "EK":  {"name": "Emirates",        "country": "UAE",     "alliance": "None",           "rating": 4.7},
    "QR":  {"name": "Qatar Airways",   "country": "Qatar",   "alliance": "Oneworld",       "rating": 4.8},
    "EY":  {"name": "Etihad Airways",  "country": "UAE",     "alliance": "None",           "rating": 4.5},
    "SQ":  {"name": "Singapore Airlines","country":"Singapore","alliance":"Star Alliance",  "rating": 4.9},
    "BA":  {"name": "British Airways", "country": "UK",      "alliance": "Oneworld",       "rating": 4.2},
    "LH":  {"name": "Lufthansa",       "country": "Germany", "alliance": "Star Alliance",  "rating": 4.3},
    "AF":  {"name": "Air France",      "country": "France",  "alliance": "SkyTeam",        "rating": 4.1},
    "UA":  {"name": "United Airlines", "country": "USA",     "alliance": "Star Alliance",  "rating": 3.9},
    "AA":  {"name": "American Airlines","country": "USA",    "alliance": "Oneworld",       "rating": 3.8},
    "NH":  {"name": "ANA",             "country": "Japan",   "alliance": "Star Alliance",  "rating": 4.8},
    "TK":  {"name": "Turkish Airlines","country": "Turkey",  "alliance": "Star Alliance",  "rating": 4.4},
    "MH":  {"name": "Malaysia Airlines","country":"Malaysia","alliance": "Oneworld",        "rating": 4.2},
    "CX":  {"name": "Cathay Pacific",  "country": "HK",      "alliance": "Oneworld",       "rating": 4.6},
    "KE":  {"name": "Korean Air",      "country": "Korea",   "alliance": "SkyTeam",        "rating": 4.5},
}

# ─── Cabin Classes ───────────────────────────────────────────
CABIN_CLASSES = {
    "economy":       {"label": "Economy",        "multiplier": 1.0},
    "premium_economy":{"label": "Premium Economy","multiplier": 1.8},
    "business":      {"label": "Business Class", "multiplier": 3.5},
    "first":         {"label": "First Class",    "multiplier": 6.0},
}

# ─── Baggage Policies ────────────────────────────────────────
BAGGAGE_POLICIES = {
    "economy": {
        "cabin":    "7 kg (1 piece)",
        "checked":  "15-23 kg (1 piece)",
        "extra_fee": "₹500-2000 per kg",
    },
    "business": {
        "cabin":    "14 kg (2 pieces)",
        "checked":  "32 kg (2 pieces)",
        "extra_fee": "Varies",
    },
}

# ─── Base Fares (INR) for route calculation ───────────────────
BASE_FARES_INR = {
    # Domestic India (one way)
    ("DEL", "BOM"): 3500,
    ("DEL", "BLR"): 4000,
    ("DEL", "HYD"): 3800,
    ("DEL", "MAA"): 4500,
    ("DEL", "GOI"): 5500,
    ("BOM", "BLR"): 2800,
    ("BOM", "HYD"): 3000,
    ("BOM", "MAA"): 3200,
    ("BLR", "HYD"): 1800,
    ("BLR", "MAA"): 2500,
    ("BLR", "COK"): 2200,
    ("HYD", "MAA"): 2600,
    # International (economy one way)
    ("DEL", "DXB"): 12000,
    ("BOM", "DXB"):  9000,
    ("DEL", "LHR"): 35000,
    ("BOM", "LHR"): 32000,
    ("DEL", "JFK"): 55000,
    ("BOM", "JFK"): 52000,
    ("DEL", "SIN"): 18000,
    ("BOM", "SIN"): 16000,
    ("DEL", "NRT"): 42000,
    ("DEL", "SYD"): 48000,
    ("DEL", "CDG"): 38000,
    ("DEL", "FRA"): 36000,
    ("DEL", "BKK"): 16000,
    ("DEL", "DOH"): 10000,
    ("DEL", "KUL"): 20000,
}

# ─── Agent System Prompt ─────────────────────────────────────
AGENT_SYSTEM_PROMPT = """You are SkyAssist, an expert AI Flight Search and Booking Assistant
with access to real-time flight data, pricing, and booking capabilities.

You help travelers:
1. Search flights (one-way, round-trip, multi-city)
2. Compare prices across airlines
3. Find best deals and alternatives
4. Book tickets and manage reservations
5. Provide travel advice and visa information
6. Handle cancellations and modifications

You are helpful, professional, and always:
- Suggest the best value options
- Warn about visa requirements
- Mention baggage policies
- Flag price alerts and deals
- Provide travel tips for destinations

When searching flights, consider: price, duration, stops, airline quality, departure time.
Always show prices in INR unless user specifies otherwise.

Return ONLY valid JSON when tool results are needed. Use plain conversational text otherwise."""

# ─── Tool Definitions for Claude ─────────────────────────────
FLIGHT_TOOLS = [
    {
        "name": "search_flights",
        "description": "Search for available flights between two cities. Returns list of flight options with prices, duration, stops, and airline details.",
        "input_schema": {
            "type": "object",
            "properties": {
                "origin":       {"type": "string", "description": "Origin airport IATA code (e.g., DEL, BOM)"},
                "destination":  {"type": "string", "description": "Destination airport IATA code"},
                "date":         {"type": "string", "description": "Travel date in YYYY-MM-DD format"},
                "return_date":  {"type": "string", "description": "Return date for round trip (YYYY-MM-DD), optional"},
                "passengers":   {"type": "integer","description": "Number of passengers (default: 1)"},
                "cabin_class":  {"type": "string", "description": "economy/premium_economy/business/first"},
                "max_stops":    {"type": "integer","description": "Maximum stops (0=direct, 1=one stop, 2=any)"},
                "preferred_airline": {"type": "string", "description": "Preferred airline code, optional"},
            },
            "required": ["origin", "destination", "date"],
        },
    },
    {
        "name": "get_flight_details",
        "description": "Get detailed information about a specific flight including seat map, meal options, and amenities.",
        "input_schema": {
            "type": "object",
            "properties": {
                "flight_id": {"type": "string", "description": "Flight ID from search results"},
            },
            "required": ["flight_id"],
        },
    },
    {
        "name": "book_flight",
        "description": "Book a flight ticket for passengers.",
        "input_schema": {
            "type": "object",
            "properties": {
                "flight_id":    {"type": "string",  "description": "Flight ID to book"},
                "passengers":   {"type": "array",   "description": "List of passenger details",
                    "items": {
                        "type": "object",
                        "properties": {
                            "first_name": {"type": "string"},
                            "last_name":  {"type": "string"},
                            "dob":        {"type": "string", "description": "Date of birth YYYY-MM-DD"},
                            "passport":   {"type": "string", "description": "Passport number"},
                            "nationality":{"type": "string"},
                            "email":      {"type": "string"},
                            "phone":      {"type": "string"},
                        },
                        "required": ["first_name", "last_name", "email", "phone"],
                    }
                },
                "seat_preferences": {"type": "array", "items": {"type": "string"}},
                "meal_preference":  {"type": "string"},
                "add_baggage":      {"type": "boolean"},
                "payment_method":   {"type": "string"},
                "coupon_code":      {"type": "string"},
            },
            "required": ["flight_id", "passengers"],
        },
    },
    {
        "name": "get_booking",
        "description": "Retrieve booking details using PNR or booking reference.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pnr":           {"type": "string", "description": "PNR / booking reference number"},
                "passenger_name":{"type": "string", "description": "Last name of passenger"},
            },
            "required": ["pnr"],
        },
    },
    {
        "name": "cancel_booking",
        "description": "Cancel a flight booking and process refund.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pnr":    {"type": "string"},
                "reason": {"type": "string"},
            },
            "required": ["pnr"],
        },
    },
    {
        "name": "get_airport_info",
        "description": "Get airport information including terminals, facilities, and transport options.",
        "input_schema": {
            "type": "object",
            "properties": {
                "airport_code": {"type": "string", "description": "IATA airport code"},
            },
            "required": ["airport_code"],
        },
    },
    {
        "name": "check_visa_requirements",
        "description": "Check visa requirements for traveling between countries.",
        "input_schema": {
            "type": "object",
            "properties": {
                "nationality":   {"type": "string", "description": "Passenger nationality/passport country"},
                "destination":   {"type": "string", "description": "Destination country or airport code"},
                "travel_purpose":{"type": "string", "description": "tourism/business/transit"},
            },
            "required": ["nationality", "destination"],
        },
    },
    {
        "name": "get_price_calendar",
        "description": "Get cheapest fares for a route across dates (flexible date search).",
        "input_schema": {
            "type": "object",
            "properties": {
                "origin":      {"type": "string"},
                "destination": {"type": "string"},
                "month":       {"type": "string", "description": "Month in YYYY-MM format"},
                "cabin_class": {"type": "string"},
            },
            "required": ["origin", "destination", "month"],
        },
    },
    {
        "name": "set_price_alert",
        "description": "Set a price alert for a route to notify when price drops.",
        "input_schema": {
            "type": "object",
            "properties": {
                "origin":       {"type": "string"},
                "destination":  {"type": "string"},
                "date":         {"type": "string"},
                "target_price": {"type": "number", "description": "Alert when price drops below this"},
                "email":        {"type": "string"},
            },
            "required": ["origin", "destination", "date", "target_price", "email"],
        },
    },
]


@dataclass
class Config:
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    amadeus_api_key:   str = field(default_factory=lambda: os.getenv("AMADEUS_API_KEY", ""))
    amadeus_secret:    str = field(default_factory=lambda: os.getenv("AMADEUS_API_SECRET", ""))
    db_path:           str = field(default_factory=lambda: os.getenv("DB_PATH", "flights.db"))
    currency:          str = field(default_factory=lambda: os.getenv("CURRENCY", "INR"))
    dry_run:           bool= field(default_factory=lambda: os.getenv("DRY_RUN", "true").lower() == "true")


config = Config()

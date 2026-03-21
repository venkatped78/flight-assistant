# ============================================================
# models/flight.py — Flight Data Models
# ============================================================

from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


class CabinClass(str, Enum):
    ECONOMY         = "economy"
    PREMIUM_ECONOMY = "premium_economy"
    BUSINESS        = "business"
    FIRST           = "first"


class BookingStatus(str, Enum):
    CONFIRMED  = "CONFIRMED"
    PENDING    = "PENDING"
    CANCELLED  = "CANCELLED"
    REFUNDED   = "REFUNDED"
    CHECKED_IN = "CHECKED_IN"
    COMPLETED  = "COMPLETED"


class TripType(str, Enum):
    ONE_WAY    = "one_way"
    ROUND_TRIP = "round_trip"
    MULTI_CITY = "multi_city"


@dataclass
class Airport:
    code:     str
    name:     str
    city:     str
    country:  str
    terminal: Optional[str] = None


@dataclass
class FlightSegment:
    flight_number:  str
    airline_code:   str
    airline_name:   str
    origin:         str
    destination:    str
    departure_time: datetime
    arrival_time:   datetime
    duration_mins:  int
    aircraft_type:  str          = "Boeing 737"
    cabin_class:    CabinClass   = CabinClass.ECONOMY
    seats_available:int          = 50
    terminal_dep:   str          = ""
    terminal_arr:   str          = ""
    meal_included:  bool         = False
    wifi_available: bool         = False


@dataclass
class Flight:
    flight_id:      str
    segments:       List[FlightSegment]
    stops:          int
    total_duration: int               # minutes
    price_inr:      float
    taxes_inr:      float
    total_inr:      float
    cabin_class:    CabinClass
    refundable:     bool              = True
    cancellation_fee: float           = 0
    baggage_cabin:  str               = "7 kg"
    baggage_checked:str               = "15 kg"
    seats_left:     int               = 10
    deal_badge:     Optional[str]     = None
    price_trend:    str               = "stable"  # rising/falling/stable
    airline_rating: float             = 4.0
    amenities:      List[str]         = field(default_factory=list)
    raw_data:       Dict              = field(default_factory=dict)

    @property
    def origin(self) -> str:
        return self.segments[0].origin

    @property
    def destination(self) -> str:
        return self.segments[-1].destination

    @property
    def departure_time(self) -> datetime:
        return self.segments[0].departure_time

    @property
    def arrival_time(self) -> datetime:
        return self.segments[-1].arrival_time

    @property
    def airline_code(self) -> str:
        return self.segments[0].airline_code

    @property
    def airline_name(self) -> str:
        return self.segments[0].airline_name

    @property
    def is_direct(self) -> bool:
        return self.stops == 0

    def duration_str(self) -> str:
        h, m = divmod(self.total_duration, 60)
        return f"{h}h {m}m"


@dataclass
class Passenger:
    first_name:  str
    last_name:   str
    email:       str
    phone:       str
    dob:         Optional[str] = None
    passport:    Optional[str] = None
    nationality: str           = "Indian"
    gender:      str           = "M"
    frequent_flyer: Optional[str] = None


@dataclass
class Booking:
    pnr:            str
    flight:         Flight
    passengers:     List[Passenger]
    status:         BookingStatus      = BookingStatus.CONFIRMED
    total_paid:     float              = 0
    booked_at:      datetime           = field(default_factory=datetime.now)
    seat_numbers:   List[str]          = field(default_factory=list)
    meal_preference:str                = "Standard"
    extra_baggage:  bool               = False
    insurance:      bool               = False
    refund_amount:  float              = 0
    cancellation_deadline: Optional[datetime] = None
    check_in_open:  Optional[datetime] = None
    boarding_pass_url: Optional[str]   = None
    coupon_applied: Optional[str]      = None
    discount_inr:   float              = 0


@dataclass
class PriceAlert:
    alert_id:     str
    origin:       str
    destination:  str
    date:         str
    target_price: float
    email:        str
    created_at:   datetime = field(default_factory=datetime.now)
    triggered:    bool     = False


@dataclass
class SearchQuery:
    origin:       str
    destination:  str
    date:         str
    passengers:   int          = 1
    cabin_class:  CabinClass   = CabinClass.ECONOMY
    return_date:  Optional[str]= None
    max_stops:    int          = 2
    preferred_airline: Optional[str] = None
    max_price:    Optional[float]    = None
    trip_type:    TripType     = TripType.ONE_WAY


@dataclass
class SearchResult:
    query:        SearchQuery
    flights:      List[Flight]
    searched_at:  datetime     = field(default_factory=datetime.now)
    total_found:  int          = 0
    cheapest:     Optional[Flight] = None
    fastest:      Optional[Flight] = None
    best_value:   Optional[Flight] = None

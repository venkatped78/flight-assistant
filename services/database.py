# ============================================================
# services/database.py — SQLite Database Service
# ============================================================

import sqlite3
import json
from datetime import datetime
from typing import List, Optional
from models.flight import Booking, PriceAlert, BookingStatus


class Database:
    def __init__(self, db_path: str = "flights.db"):
        self.db_path = db_path
        self._init()

    def _conn(self):
        c = sqlite3.connect(self.db_path)
        c.row_factory = sqlite3.Row
        return c

    def _init(self):
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS bookings (
                    pnr          TEXT PRIMARY KEY,
                    flight_data  TEXT,
                    passengers   TEXT,
                    status       TEXT DEFAULT 'CONFIRMED',
                    total_paid   REAL,
                    seats        TEXT,
                    meal         TEXT,
                    extra_baggage INTEGER DEFAULT 0,
                    coupon       TEXT,
                    discount     REAL DEFAULT 0,
                    created_at   TEXT,
                    updated_at   TEXT
                );

                CREATE TABLE IF NOT EXISTS price_alerts (
                    alert_id     TEXT PRIMARY KEY,
                    origin       TEXT,
                    destination  TEXT,
                    date         TEXT,
                    target_price REAL,
                    email        TEXT,
                    triggered    INTEGER DEFAULT 0,
                    created_at   TEXT
                );

                CREATE TABLE IF NOT EXISTS search_history (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    origin     TEXT,
                    destination TEXT,
                    date       TEXT,
                    cabin      TEXT,
                    results    INTEGER,
                    searched_at TEXT
                );
            """)

    def save_booking(self, booking: Booking):
        import dataclasses
        flight_data = {
            "flight_id":      booking.flight.flight_id,
            "airline":        booking.flight.airline_name,
            "flight_number":  booking.flight.segments[0].flight_number,
            "origin":         booking.flight.origin,
            "destination":    booking.flight.destination,
            "departure":      booking.flight.departure_time.isoformat(),
            "arrival":        booking.flight.arrival_time.isoformat(),
            "duration":       booking.flight.total_duration,
            "stops":          booking.flight.stops,
            "cabin":          booking.flight.cabin_class.value,
            "price":          booking.flight.price_inr,
            "total":          booking.flight.total_inr,
            "refundable":     booking.flight.refundable,
        }
        pax_data = [
            {"name": f"{p.first_name} {p.last_name}",
             "email": p.email, "phone": p.phone,
             "passport": p.passport}
            for p in booking.passengers
        ]
        with self._conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO bookings
                (pnr, flight_data, passengers, status, total_paid,
                 seats, meal, extra_baggage, coupon, discount, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                booking.pnr,
                json.dumps(flight_data),
                json.dumps(pax_data),
                booking.status.value,
                booking.total_paid,
                json.dumps(booking.seat_numbers),
                booking.meal_preference,
                1 if booking.extra_baggage else 0,
                booking.coupon_applied,
                booking.discount_inr,
                booking.booked_at.isoformat(),
                datetime.now().isoformat(),
            ))

    def get_booking(self, pnr: str) -> Optional[dict]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM bookings WHERE pnr=?", (pnr.upper(),)
            ).fetchone()
            if row:
                d = dict(row)
                d["flight_data"] = json.loads(d["flight_data"])
                d["passengers"]  = json.loads(d["passengers"])
                d["seats"]       = json.loads(d["seats"])
                return d
            return None

    def update_status(self, pnr: str, status: str):
        with self._conn() as conn:
            conn.execute(
                "UPDATE bookings SET status=?, updated_at=? WHERE pnr=?",
                (status, datetime.now().isoformat(), pnr.upper())
            )

    def get_all_bookings(self) -> List[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM bookings ORDER BY created_at DESC"
            ).fetchall()
            result = []
            for row in rows:
                d = dict(row)
                d["flight_data"] = json.loads(d["flight_data"])
                d["passengers"]  = json.loads(d["passengers"])
                result.append(d)
            return result

    def save_alert(self, alert: PriceAlert):
        with self._conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO price_alerts
                (alert_id, origin, destination, date, target_price, email, triggered, created_at)
                VALUES (?,?,?,?,?,?,?,?)
            """, (
                alert.alert_id, alert.origin, alert.destination,
                alert.date, alert.target_price, alert.email,
                1 if alert.triggered else 0,
                alert.created_at.isoformat(),
            ))

    def get_active_alerts(self) -> List[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM price_alerts WHERE triggered=0"
            ).fetchall()
            return [dict(r) for r in rows]

    def log_search(self, origin: str, dest: str, date: str,
                   cabin: str, results: int):
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO search_history
                (origin, destination, date, cabin, results, searched_at)
                VALUES (?,?,?,?,?,?)
            """, (origin, dest, date, cabin, results, datetime.now().isoformat()))

    def get_stats(self) -> dict:
        with self._conn() as conn:
            bookings   = conn.execute("SELECT COUNT(*) FROM bookings").fetchone()[0]
            revenue    = conn.execute("SELECT SUM(total_paid) FROM bookings WHERE status='CONFIRMED'").fetchone()[0] or 0
            cancelled  = conn.execute("SELECT COUNT(*) FROM bookings WHERE status='CANCELLED'").fetchone()[0]
            searches   = conn.execute("SELECT COUNT(*) FROM search_history").fetchone()[0]
            alerts     = conn.execute("SELECT COUNT(*) FROM price_alerts WHERE triggered=0").fetchone()[0]
            return {
                "total_bookings": bookings,
                "total_revenue":  revenue,
                "cancelled":      cancelled,
                "searches":       searches,
                "active_alerts":  alerts,
            }

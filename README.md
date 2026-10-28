# ✈ SkyAssist — AI Flight Search & Booking Assistant

> **Production-ready AI Flight Assistant** powered by Claude AI with Tool Use.
> Search flights, compare prices, book tickets, manage bookings — all through
> natural language conversation. Supports real Amadeus API + mock mode for testing.

![Python](https://img.shields.io/badge/Python-3.10+-3776ab)
![Claude](https://img.shields.io/badge/AI-Claude%20Sonnet-2dd4bf)
![Airports](https://img.shields.io/badge/Airports-30+-orange)
![Airlines](https://img.shields.io/badge/Airlines-20+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 🎯 What It Does

```
User: "Find me cheapest flights from Delhi to Dubai next Friday"
         ↓
SkyAssist AI (Claude + Tools)
  ├── search_flights() → 6 results, ranked by price
  ├── get_flight_details() → Baggage, meals, seat info
  └── Returns: Formatted comparison with deal badges

User: "Book the Emirates one for John Doe, john@email.com"
         ↓
  ├── book_flight() → PNR confirmed
  ├── generate_ticket() → PDF boarding pass created
  └── Returns: Booking confirmation + ticket path

User: "Cancel it"
         ↓
  ├── cancel_booking() → Refund calculated
  └── Returns: Cancellation + refund amount
```

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 **Smart Search** | Natural language flight search |
| ✈ **Multi-airline** | 20+ airlines, 30+ airports (India + International) |
| 💰 **Price Comparison** | Side-by-side with deal badges |
| 📅 **Flexible Dates** | Price calendar across full month |
| 🎫 **One-click Booking** | Complete booking in one message |
| 📄 **PDF Tickets** | Professional boarding pass generation |
| ❌ **Cancellation** | Smart refund calculation |
| 🔔 **Price Alerts** | Email alerts when price drops |
| 🌍 **Visa Info** | Visa requirements by nationality |
| 🏢 **Airport Info** | Terminal, transport, facilities |
| 💬 **Conversation** | Multi-turn context-aware chat |
| 🗄️ **SQLite DB** | Persistent bookings + search history |
| 🔌 **Real API** | Amadeus API support for live data |

---

## 🚀 Quick Start

### 1. Install
```bash
pip install -r requirements.txt
```

### 2. Configure
Edit `.env`:
```
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here

# Optional: Real flight data (free tier available)
# AMADEUS_API_KEY=your_amadeus_key
# AMADEUS_API_SECRET=your_amadeus_secret

DRY_RUN=true
```

### 3. Run
```bash
# Interactive chat
python main.py

# Demo mode (automated queries)
python main.py demo

# Ask single question
python main.py ask "flights from delhi to mumbai tomorrow"
```

---

## 🎮 Usage

### Interactive Mode
```bash
python main.py
```
Then type natural language:
```
You: Find me flights from Hyderabad to Singapore on 2025-05-10
You: Show business class options only
You: Book the Singapore Airlines one for Priya Sharma, priya@email.com, +91-9876543210
You: Check my booking
You: Cancel it and get refund
```

### CLI Commands
```bash
# Interactive chat
python main.py

# Demo
python main.py demo

# Quick ask
python main.py ask "cheapest flights Delhi to London in June"

# View all bookings
python main.py bookings

# Statistics
python main.py stats
```

---

## 🗣️ Natural Language Examples

```
# Search
"Flights from Delhi to Dubai tomorrow"
"Cheap tickets Mumbai to Goa this weekend"
"Business class Delhi to London 15 June"
"Direct flights only from Bangalore to Singapore"
"IndiGo flights from Hyderabad to Chennai"

# Booking
"Book the first option for Rahul Sharma, rahul@email.com, 9876543210"
"Add extra baggage for the booking"
"Apply coupon SAVE15"

# Management
"Check booking PNR123456"
"Cancel my booking"
"When is check-in for my flight?"

# Information
"Do Indians need visa for Dubai?"
"Visa requirements for USA tourism"
"What are the facilities at Delhi airport?"
"What's the baggage limit for economy?"

# Price Tools
"Show cheapest dates in June for Mumbai to Singapore"
"Alert me when Delhi to London drops below ₹35000 at my@email.com"
```

---

## 📁 Project Structure

```
flight-assistant/
│
├── main.py                      ← CLI entry point
│
├── agents/
│   └── flight_agent.py          ← AI Agent (Claude + Tool Use)
│       ├── chat()               → Main conversation handler
│       ├── _execute_tool()      → Routes tool calls
│       └── Tool handlers:
│           ├── search_flights
│           ├── book_flight
│           ├── cancel_booking
│           ├── get_booking
│           ├── check_visa
│           ├── get_price_calendar
│           └── set_price_alert
│
├── services/
│   ├── flight_engine.py         ← Search engine (Mock + Amadeus)
│   │   ├── MockFlightEngine     → Realistic demo data
│   │   └── AmadeusFlightEngine  → Real Amadeus API
│   ├── database.py              ← SQLite persistence
│   └── ticket_generator.py      ← PDF ticket generation
│
├── models/
│   └── flight.py                ← Data models
│       ├── Flight, FlightSegment
│       ├── Booking, Passenger
│       ├── SearchQuery, SearchResult
│       └── PriceAlert
│
├── config/
│   └── settings.py              ← Config, airports DB, airlines, prompts, tools
│
├── display.py                   ← Rich terminal UI
├── requirements.txt
├── .env
└── README.md
```

---

## 🔌 Real API Integration (Amadeus)

Replace mock data with real flights:

1. Register at [developers.amadeus.com](https://developers.amadeus.com) (free)
2. Create app → get API Key + Secret
3. Add to `.env`:
```
AMADEUS_API_KEY=your_key
AMADEUS_API_SECRET=your_secret
```
4. System auto-detects and uses Amadeus when credentials present

**Free tier:** 2000 API calls/month — enough for testing

---

## 💳 Supported Coupon Codes (Demo)

| Code | Discount |
|------|----------|
| FIRST10 | 10% off |
| SAVE15 | 15% off |
| SKYFLY | 8% off |
| NEW20 | 20% off |

---

## 🗄️ Database Schema

```sql
bookings       -- All flight bookings with PNR
price_alerts   -- User-set price drop notifications
search_history -- Analytics on searches
```

---

## 🎯 AI/ML Interview Talking Points

1. **Agentic AI with Tool Use** — Claude decides which tools to call based on context
2. **Multi-turn Conversation** — Full history maintained across messages
3. **Structured Tool Definitions** — JSON Schema for input validation
4. **Dynamic Pricing Engine** — Demand-based, days-ahead, seats-left pricing
5. **Real API Integration** — Amadeus OAuth2 + fallback to mock
6. **PDF Generation** — ReportLab professional ticket generation
7. **SQLite Persistence** — Bookings, alerts, search history
8. **Factory Pattern** — Engine selection (real vs mock)
9. **Error Handling** — Graceful failures with helpful messages
10. **Domain Modeling** — Rich dataclass hierarchy for aviation

---

## 🛠 Tech Stack

| Library | Purpose |
|---------|---------|
| `anthropic` | Claude AI with Tool Use |
| `rich` | Terminal UI |
| `click` | CLI framework |
| `reportlab` | PDF ticket generation |
| `sqlite3` | Booking database |
| `requests` | Amadeus API calls |
| `pydantic` | Data validation |

---

## 📈 Roadmap

- [ ] FastAPI REST backend
- [ ] React web frontend
- [ ] Real-time seat map
- [ ] Hotel + car rental bundling
- [ ] Loyalty points integration
- [ ] Multi-city trip planner
- [ ] WhatsApp bot integration
- [ ] Email/SMS notifications

---


---
**Built for AI/ML Engineers · Demonstrates production-grade Claude Tool Use application**

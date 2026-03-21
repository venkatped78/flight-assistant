# ============================================================
# display.py — Rich Terminal UI for Flight Assistant
# ============================================================

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich.rule import Rule
from rich.align import Align
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt
from rich import box
from rich.markdown import Markdown

console = Console()


def print_header():
    console.print()
    console.print(Align.center(
        "[bold white on #1a237e]  ✈  SKYASSIST — AI FLIGHT ASSISTANT  ✈  [/]"
    ))
    console.print(Align.center(
        "[dim]Search · Compare · Book · Manage · All powered by Claude AI[/dim]"
    ))
    console.print()


def print_welcome():
    console.print(Panel(
        "[bold]Hi! I'm SkyAssist, your AI flight booking assistant.[/bold]\n\n"
        "I can help you:\n"
        "  ✈  [cyan]Search flights[/] — 'Find flights from Delhi to Mumbai tomorrow'\n"
        "  💰  [cyan]Compare prices[/] — 'Show me cheapest options this month'\n"
        "  🎫  [cyan]Book tickets[/] — 'Book the IndiGo flight for Rahul Sharma'\n"
        "  📋  [cyan]Manage bookings[/] — 'Check my booking PNR123456'\n"
        "  ❌  [cyan]Cancel flights[/] — 'Cancel my booking and get refund'\n"
        "  🌍  [cyan]Visa info[/] — 'Do I need visa for Dubai from India?'\n"
        "  🔔  [cyan]Price alerts[/] — 'Alert me when Delhi-London drops below ₹30000'\n\n"
        "[dim]Type your query in plain English. I handle the rest![/dim]",
        title="[bold #1a237e]Welcome to SkyAssist ✈[/]",
        border_style="#1a237e",
        padding=(1, 2),
    ))
    console.print()


def print_thinking():
    return Progress(
        SpinnerColumn(style="#1a237e"),
        TextColumn("[bold #1a237e]{task.description}[/]"),
        console=console, transient=True,
    )


def print_response(text: str):
    """Print assistant response with formatting."""
    console.print()
    console.print(Panel(
        Markdown(text) if text.strip().startswith("#") else text,
        title="[bold #1a237e]✈ SkyAssist[/]",
        border_style="#1a237e",
        padding=(1, 2),
    ))
    console.print()


def print_stats(stats: dict):
    console.print()
    console.print(Rule("[bold #1a237e]📊 Statistics[/]"))
    panels = [
        Panel(f"[bold cyan]{stats['total_bookings']}[/]\n[dim]Total Bookings[/]",
              border_style="cyan", padding=(0,3)),
        Panel(f"[bold green]₹{stats['total_revenue']:,.0f}[/]\n[dim]Revenue[/]",
              border_style="green", padding=(0,3)),
        Panel(f"[bold red]{stats['cancelled']}[/]\n[dim]Cancelled[/]",
              border_style="red", padding=(0,3)),
        Panel(f"[bold yellow]{stats['searches']}[/]\n[dim]Searches[/]",
              border_style="yellow", padding=(0,3)),
        Panel(f"[bold #6c63ff]{stats['active_alerts']}[/]\n[dim]Price Alerts[/]",
              border_style="#6c63ff", padding=(0,3)),
    ]
    console.print(Columns(panels, equal=True, expand=True))
    console.print()


def print_bookings_table(bookings: list):
    if not bookings:
        console.print("[dim]No bookings found.[/]")
        return

    table = Table(title="All Bookings", box=box.ROUNDED,
                  border_style="#1a237e", header_style="bold #1a237e",
                  show_lines=True)
    table.add_column("PNR",       width=10)
    table.add_column("Route",     width=15)
    table.add_column("Flight",    width=10)
    table.add_column("Departure", width=20)
    table.add_column("Passengers",width=20)
    table.add_column("Total",     width=12, justify="right")
    table.add_column("Status",    width=12)

    status_styles = {
        "CONFIRMED":  "bold green",
        "CANCELLED":  "bold red",
        "PENDING":    "yellow",
        "COMPLETED":  "bright_green",
    }
    for b in bookings:
        fd  = b["flight_data"]
        pax = ", ".join(p["name"] for p in b["passengers"][:2])
        if len(b["passengers"]) > 2:
            pax += f" +{len(b['passengers'])-2}"

        sty = status_styles.get(b["status"], "white")
        table.add_row(
            b["pnr"],
            f"{fd['origin']}→{fd['destination']}",
            fd.get("flight_number",""),
            fd["departure"][:16] if fd.get("departure") else "",
            pax,
            f"₹{b['total_paid']:,.0f}",
            f"[{sty}]{b['status']}[/]",
        )
    console.print(table)


def print_example_queries():
    console.print("[bold]Example queries you can try:[/]")
    examples = [
        "Search flights from Delhi to Mumbai on 2025-04-15",
        "Find cheapest flights from Hyderabad to Dubai next month",
        "Show business class flights from Bangalore to London",
        "Book the first flight for John Doe, john@email.com, +91-9876543210",
        "Check my booking PNR123456",
        "Cancel booking ABC123",
        "Do Indians need visa to visit Singapore?",
        "Set price alert for Delhi to London below ₹35000 on my@email.com",
        "Show price calendar for Mumbai to Dubai in April 2025",
        "What are the baggage rules for IndiGo economy?",
    ]
    for i, q in enumerate(examples, 1):
        console.print(f"  [dim]{i}.[/] {q}")
    console.print()


def print_success(msg): console.print(f"[bold green]✅[/] {msg}")
def print_error(msg):   console.print(f"[bold red]❌[/] {msg}")
def print_info(msg):    console.print(f"[bold cyan]ℹ[/]  {msg}")
def print_warn(msg):    console.print(f"[bold yellow]⚠[/]  {msg}")

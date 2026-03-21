#!/usr/bin/env python3
# ============================================================
# main.py — SkyAssist Flight Assistant CLI
# ============================================================
# Usage:
#   python main.py              # Interactive chat mode
#   python main.py demo         # Run demo with sample queries
#   python main.py bookings     # View all bookings
#   python main.py stats        # View statistics
# ============================================================

import os
import sys
import click
from dotenv import load_dotenv
from rich.prompt import Prompt, Confirm

from agents.flight_agent import FlightAgent
from display import (
    console, print_header, print_welcome, print_thinking,
    print_response, print_stats, print_bookings_table,
    print_example_queries, print_success, print_error,
    print_info, print_warn,
)

load_dotenv()

# ─── Demo queries ─────────────────────────────────────────────
DEMO_QUERIES = [
    "Search flights from Delhi to Mumbai on 2025-06-15 for 2 passengers",
    "Show me the cheapest option and book it for Rahul Sharma, rahul@email.com, +91-9876543210",
    "Check my latest booking details",
    "Do Indian citizens need a visa to travel to Dubai?",
    "Set a price alert for Delhi to London below ₹40000 on test@email.com for 2025-07-01",
]


def run_interactive(agent: FlightAgent):
    """Run interactive chat session."""
    print_header()
    print_welcome()
    print_example_queries()

    console.print("[dim]Type 'quit' to exit · 'reset' to start new conversation · 'help' for examples[/dim]")
    console.print()

    while True:
        try:
            user_input = Prompt.ask("[bold #1a237e]You[/]").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye! Safe travels! ✈[/dim]")
            break

        if not user_input:
            continue

        if user_input.lower() in ["quit", "exit", "bye"]:
            console.print("[bold]Goodbye! Safe travels! ✈[/bold]")
            break

        if user_input.lower() == "reset":
            agent.reset_conversation()
            print_success("Conversation reset. Starting fresh!")
            continue

        if user_input.lower() in ["help", "examples"]:
            print_example_queries()
            continue

        if user_input.lower() == "stats":
            print_stats(agent.get_stats())
            continue

        if user_input.lower() == "bookings":
            print_bookings_table(agent.get_all_bookings())
            continue

        # Process with AI
        with print_thinking() as progress:
            task = progress.add_task("SkyAssist is searching...", total=None)
            try:
                response = agent.chat(user_input)
                progress.update(task, completed=True)
            except Exception as e:
                progress.update(task, completed=True)
                print_error(f"Error: {e}")
                continue

        print_response(response)


def run_demo(agent: FlightAgent):
    """Run automated demo with sample queries."""
    print_header()
    console.print("[bold #1a237e]🎭 Running Demo — SkyAssist AI Flight Assistant[/bold #1a237e]\n")
    console.print("[dim]Watch the AI search, recommend, and book flights automatically![/dim]\n")

    for i, query in enumerate(DEMO_QUERIES, 1):
        console.print(f"\n[bold cyan]Demo {i}/{len(DEMO_QUERIES)}:[/bold cyan] {query}")
        console.print()

        with print_thinking() as progress:
            task = progress.add_task(f"Processing query {i}...", total=None)
            try:
                response = agent.chat(query)
                progress.update(task, completed=True)
            except Exception as e:
                progress.update(task, completed=True)
                print_error(f"Error: {e}")
                continue

        print_response(response)

        if i < len(DEMO_QUERIES):
            import time
            time.sleep(1)

    console.print("\n[bold green]✅ Demo complete![/bold green]")
    print_stats(agent.get_stats())
    print_bookings_table(agent.get_all_bookings())


# ─── CLI ─────────────────────────────────────────────────────

@click.group(invoke_without_command=True)
@click.option("--api-key", default=None, help="Anthropic API key")
@click.pass_context
def cli(ctx, api_key):
    """
    \b
    ✈  SkyAssist — AI Flight Search & Booking Assistant
    Powered by Claude AI with Tool Use

    \b
    Examples:
      python main.py            # Interactive chat
      python main.py demo       # Auto demo
      python main.py bookings   # All bookings
      python main.py stats      # Statistics
    """
    key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        print_header()
        key = Prompt.ask("[bold cyan]Enter Anthropic API key[/]")

    ctx.ensure_object(dict)
    ctx.obj["agent"] = FlightAgent(api_key=key)

    if ctx.invoked_subcommand is None:
        run_interactive(ctx.obj["agent"])


@cli.command()
@click.pass_context
def demo(ctx):
    """Run automated demo with sample queries."""
    run_demo(ctx.obj["agent"])


@cli.command()
@click.pass_context
def bookings(ctx):
    """View all bookings."""
    print_header()
    print_bookings_table(ctx.obj["agent"].get_all_bookings())


@cli.command()
@click.pass_context
def stats(ctx):
    """View statistics."""
    print_header()
    print_stats(ctx.obj["agent"].get_stats())


@cli.command()
@click.argument("query", nargs=-1)
@click.pass_context
def ask(ctx, query):
    """Ask a single question and get response."""
    question = " ".join(query)
    if not question:
        print_error("Please provide a query.")
        return
    print_header()
    with print_thinking() as p:
        t = p.add_task("Searching...", total=None)
        response = ctx.obj["agent"].chat(question)
        p.update(t, completed=True)
    print_response(response)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        load_dotenv()
        key   = os.environ.get("ANTHROPIC_API_KEY", "")
        agent = FlightAgent(api_key=key)
        run_interactive(agent)
    else:
        cli(obj={})

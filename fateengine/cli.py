"""Typer CLI for Fate Engine."""

from __future__ import annotations

import asyncio
import sys
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.prompt import Prompt

from fateengine import __version__
from fateengine.models import Decision, LifeArea, LifeState, SimulationConfig
from fateengine.visualizer import render_banner, render_result

console = Console()
app = typer.Typer(
    name="fateengine",
    help="🔮 Fate Engine — AI-powered life path simulator",
    no_args_is_help=True,
    rich_markup_mode="rich",
)


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"[bold bright_cyan]Fate Engine[/bold bright_cyan] v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        Optional[bool],
        typer.Option("--version", "-V", callback=_version_callback, is_eager=True),
    ] = None,
) -> None:
    """🔮 Fate Engine — peer into your possible futures."""


@app.command()
def simulate(
    num_paths: Annotated[int, typer.Option("--paths", "-n", help="Paths per option")] = 20,
    years: Annotated[int, typer.Option("--years", "-y", help="Years to simulate")] = 5,
) -> None:
    """Interactive simulation — answer questions about your life, then explore futures."""
    render_banner()
    console.print("[bold]Let's map out your possible futures.[/bold]\n")

    career = Prompt.ask("💼  Current career situation")
    finances = Prompt.ask("💰  Financial picture")
    health = Prompt.ask("❤️   Health status", default="Good")
    relationships = Prompt.ask("👥  Key relationships")
    location = Prompt.ask("📍  Location", default="")
    age_str = Prompt.ask("🎂  Your age", default="30")
    skills_raw = Prompt.ask("🛠   Notable skills (comma-separated)", default="")
    goals_raw = Prompt.ask("🎯  Life goals (comma-separated)", default="")

    console.print()
    decision_desc = Prompt.ask("[bold bright_cyan]🤔  What decision are you facing?[/bold bright_cyan]")
    options_raw = Prompt.ask("    Options (comma-separated, at least 2)")
    options = [o.strip() for o in options_raw.split(",") if o.strip()]
    if len(options) < 2:
        console.print("[red]Need at least 2 options.[/red]")
        raise typer.Exit(code=1)

    state = LifeState(
        career=career,
        finances=finances,
        health=health,
        relationships=relationships,
        skills=[s.strip() for s in skills_raw.split(",") if s.strip()],
        location=location,
        age=int(age_str),
        goals=[g.strip() for g in goals_raw.split(",") if g.strip()],
    )
    decision = Decision(description=decision_desc, options=options)
    config = SimulationConfig(num_paths=num_paths, years_ahead=years)

    _run_simulation(state, decision, config)


@app.command()
def quick(
    decision: Annotated[str, typer.Argument(help="Decision in plain text")],
    situation: Annotated[str, typer.Option("--situation", "-s", help="Your current situation")] = "",
) -> None:
    """Quick simulation from a text argument — no interview."""
    render_banner()
    console.print(f"[bold]Quick simulation:[/bold] {decision}\n")

    from fateengine.simulator import FateSimulator

    sim = FateSimulator()

    with console.status("[bright_cyan]Simulating possible futures…[/bright_cyan]", spinner="dots"):
        result = asyncio.run(sim.quick_simulate(situation or "Not specified", decision))

    render_result(result)


@app.command()
def compare(
    option_a: Annotated[str, typer.Argument(help="First option")],
    option_b: Annotated[str, typer.Argument(help="Second option")],
    context: Annotated[str, typer.Option("--context", "-c", help="Life context")] = "",
    years: Annotated[int, typer.Option("--years", "-y")] = 5,
    paths: Annotated[int, typer.Option("--paths", "-n")] = 20,
) -> None:
    """Head-to-head comparison of two options."""
    render_banner()
    console.print(f"[bold]Comparing:[/bold] {option_a} vs {option_b}\n")

    decision = Decision(
        description=f"Should I choose '{option_a}' or '{option_b}'?",
        options=[option_a, option_b],
    )
    state = LifeState(career=context) if context else LifeState()
    config = SimulationConfig(num_paths=paths, years_ahead=years)

    _run_simulation(state, decision, config)


@app.command()
def serve(
    host: Annotated[str, typer.Option(help="Bind host")] = "0.0.0.0",
    port: Annotated[int, typer.Option(help="Bind port")] = 8420,
) -> None:
    """Start the Fate Engine API server."""
    import uvicorn

    from fateengine.api.app import create_app

    console.print(f"[bold bright_cyan]Starting Fate Engine API on {host}:{port}[/bold bright_cyan]")
    uvicorn.run(create_app(), host=host, port=port)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _run_simulation(state: LifeState, decision: Decision, config: SimulationConfig) -> None:
    from fateengine.simulator import FateSimulator

    sim = FateSimulator()

    with console.status("[bright_cyan]Running Monte Carlo simulation…[/bright_cyan]", spinner="dots"):
        result = asyncio.run(sim.simulate(state, decision, config))

    render_result(result)

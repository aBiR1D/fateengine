"""MCP (Model Context Protocol) server exposing Fate Engine tools."""

from __future__ import annotations

import asyncio
import json

from mcp.server.fastmcp import FastMCP

from fateengine.models import Decision, LifeState, SimulationConfig
from fateengine.simulator import FateSimulator

mcp = FastMCP(
    "fateengine",
    description="Fate Engine — AI-powered life path simulator. "
    "Runs Monte Carlo simulations of possible futures to help evaluate life decisions.",
)

_simulator = FateSimulator()


@mcp.tool()
async def simulate_life_path(
    career: str = "",
    finances: str = "",
    health: str = "Good",
    relationships: str = "",
    age: int = 30,
    location: str = "",
    skills: list[str] | None = None,
    goals: list[str] | None = None,
    decision_description: str = "",
    options: list[str] | None = None,
    num_paths: int = 20,
    years_ahead: int = 5,
) -> str:
    """Run a full Monte Carlo life-path simulation.

    Provide the person's current state and the decision they face.
    Returns probability-weighted life paths with scores and insights.
    """
    state = LifeState(
        career=career,
        finances=finances,
        health=health,
        relationships=relationships,
        age=age,
        location=location,
        skills=skills or [],
        goals=goals or [],
    )
    decision = Decision(
        description=decision_description,
        options=options or ["Option A", "Option B"],
    )
    config = SimulationConfig(num_paths=num_paths, years_ahead=years_ahead)

    result = await _simulator.simulate(state, decision, config)
    return result.model_dump_json(indent=2)


@mcp.tool()
async def quick_fate(
    situation: str = "",
    decision: str = "",
) -> str:
    """Quick life-path simulation from free-form text.

    Just describe your situation and the decision — the engine handles the rest.
    """
    result = await _simulator.quick_simulate(situation, decision)
    return result.model_dump_json(indent=2)


@mcp.tool()
async def explain_fate_engine() -> str:
    """Explain what the Fate Engine is and how it works."""
    return (
        "# Fate Engine\n\n"
        "The Fate Engine is an AI-powered life path simulator.\n\n"
        "## How it works\n"
        "1. You describe your current life situation (career, finances, health, etc.)\n"
        "2. You specify a decision you're facing with 2–5 options\n"
        "3. The engine runs Monte Carlo-style simulations using AI to generate "
        "realistic life events for each option\n"
        "4. Each path is scored across happiness, finances, career, relationships, and health\n"
        "5. You get probability-weighted outcomes, key insights, and actionable recommendations\n\n"
        "## Dimensions tracked\n"
        "- Career\n"
        "- Finances\n"
        "- Health\n"
        "- Relationships\n"
        "- Skills\n"
        "- Personal growth\n\n"
        "## Use cases\n"
        "- Should I quit my job to start a startup?\n"
        "- Should I relocate for a new opportunity?\n"
        "- Should I go back to school?\n"
        "- Any major life decision with multiple options\n"
    )


def main() -> None:
    """Entry point when run as `python -m fateengine.mcp.server`."""
    mcp.run()


if __name__ == "__main__":
    main()

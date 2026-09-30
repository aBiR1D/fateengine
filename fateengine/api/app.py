"""FastAPI application for the Fate Engine REST API."""

from __future__ import annotations

from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

from fateengine import __version__
from fateengine.models import (
    Decision,
    LifeState,
    SimulationConfig,
    SimulationResult,
)
from fateengine.simulator import FateSimulator


# ── Request / Response schemas ──────────────────────────────────────

class SimulateRequest(BaseModel):
    state: LifeState
    decision: Decision
    config: Optional[SimulationConfig] = None


class QuickRequest(BaseModel):
    situation: str = Field(default="", description="Current life situation (free text)")
    decision: str = Field(..., description="Decision or question in plain text")


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = __version__


# ── App factory ─────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title="Fate Engine API",
        description="AI-powered life path simulator — Monte Carlo futures for your biggest decisions",
        version=__version__,
    )

    simulator = FateSimulator()

    @app.get("/health", response_model=HealthResponse, tags=["system"])
    async def health() -> HealthResponse:
        return HealthResponse()

    @app.post("/api/v1/simulate", response_model=SimulationResult, tags=["simulation"])
    async def simulate(req: SimulateRequest) -> SimulationResult:
        """Run a full life-path simulation."""
        return await simulator.simulate(req.state, req.decision, req.config)

    @app.post("/api/v1/quick", response_model=SimulationResult, tags=["simulation"])
    async def quick(req: QuickRequest) -> SimulationResult:
        """Quick simulation from free-form text."""
        return await simulator.quick_simulate(req.situation, req.decision)

    return app

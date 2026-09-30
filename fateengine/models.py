"""Domain models for the Fate Engine life-path simulator."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class LifeArea(str, Enum):
    """Dimensions of life that the simulator tracks."""

    CAREER = "career"
    FINANCES = "finances"
    HEALTH = "health"
    RELATIONSHIPS = "relationships"
    SKILLS = "skills"
    PERSONAL_GROWTH = "personal_growth"


class LifeState(BaseModel):
    """Snapshot of a person's current life situation."""

    career: str = Field(
        default="",
        description="Current career situation — role, industry, satisfaction level",
    )
    finances: str = Field(
        default="",
        description="Financial picture — savings, income, debts, runway",
    )
    health: str = Field(
        default="",
        description="Physical and mental health status",
    )
    relationships: str = Field(
        default="",
        description="Key relationships — partner, family, social circle",
    )
    skills: list[str] = Field(
        default_factory=list,
        description="Notable skills and expertise",
    )
    location: str = Field(default="", description="Current city / country")
    age: int = Field(default=30, ge=16, le=100, description="Current age")
    goals: list[str] = Field(
        default_factory=list,
        description="Life goals and aspirations",
    )

    def summary(self) -> str:
        """Human-readable one-paragraph summary."""
        parts: list[str] = []
        if self.career:
            parts.append(f"Career: {self.career}")
        if self.finances:
            parts.append(f"Finances: {self.finances}")
        if self.health:
            parts.append(f"Health: {self.health}")
        if self.relationships:
            parts.append(f"Relationships: {self.relationships}")
        if self.skills:
            parts.append(f"Skills: {', '.join(self.skills)}")
        if self.location:
            parts.append(f"Location: {self.location}")
        parts.append(f"Age: {self.age}")
        if self.goals:
            parts.append(f"Goals: {', '.join(self.goals)}")
        return " | ".join(parts)


class Decision(BaseModel):
    """A life decision the user is contemplating."""

    description: str = Field(
        ..., description="Plain-language description of the decision"
    )
    options: list[str] = Field(
        min_length=2,
        max_length=5,
        description="The distinct options being considered (2–5)",
    )


class SimulationConfig(BaseModel):
    """Knobs for the simulation run."""

    num_paths: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Simulation paths per option",
    )
    years_ahead: int = Field(
        default=5,
        ge=1,
        le=30,
        description="How many years into the future to simulate",
    )
    focus_areas: list[LifeArea] = Field(
        default_factory=lambda: list(LifeArea),
        description="Which life dimensions to emphasise",
    )


class LifeEvent(BaseModel):
    """A single event on a simulated life path."""

    year: int = Field(..., description="Simulation year (1-based offset from now)")
    area: LifeArea = Field(..., description="Life area affected")
    description: str = Field(..., description="What happens")
    impact_score: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        description="Impact magnitude from -1 (catastrophic) to +1 (transformative)",
    )
    probability: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Estimated probability of this event occurring",
    )


class LifePath(BaseModel):
    """One simulated trajectory through the future."""

    option: str = Field(..., description="Which decision option this path follows")
    events: list[LifeEvent] = Field(default_factory=list)
    final_state: Optional[LifeState] = None
    happiness_score: float = Field(default=0.0, ge=0.0, le=10.0)
    financial_score: float = Field(default=0.0, ge=0.0, le=10.0)
    career_score: float = Field(default=0.0, ge=0.0, le=10.0)
    relationship_score: float = Field(default=0.0, ge=0.0, le=10.0)
    health_score: float = Field(default=0.0, ge=0.0, le=10.0)
    overall_score: float = Field(default=0.0, ge=0.0, le=10.0)

    @property
    def score_vector(self) -> dict[str, float]:
        return {
            "happiness": self.happiness_score,
            "financial": self.financial_score,
            "career": self.career_score,
            "relationships": self.relationship_score,
            "health": self.health_score,
            "overall": self.overall_score,
        }


class OptionStatistics(BaseModel):
    """Aggregate statistics for a single decision option."""

    option: str
    mean_overall: float = 0.0
    median_overall: float = 0.0
    best_case: float = 0.0
    worst_case: float = 0.0
    std_dev: float = 0.0
    mean_happiness: float = 0.0
    mean_financial: float = 0.0
    mean_career: float = 0.0
    mean_relationship: float = 0.0
    mean_health: float = 0.0
    upside_probability: float = Field(
        default=0.0, description="P(overall > 7.0)"
    )
    downside_probability: float = Field(
        default=0.0, description="P(overall < 4.0)"
    )


class SimulationResult(BaseModel):
    """Complete output of a Fate Engine simulation run."""

    decision: Decision
    config: SimulationConfig
    paths_by_option: dict[str, list[LifePath]] = Field(default_factory=dict)
    statistics: list[OptionStatistics] = Field(default_factory=list)
    optimal_path: Optional[LifePath] = None
    key_insights: list[str] = Field(default_factory=list)
    action_items: list[str] = Field(default_factory=list)

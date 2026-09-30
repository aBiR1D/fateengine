"""Tests for all Pydantic domain models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from fateengine.models import (
    Decision,
    LifeArea,
    LifeEvent,
    LifePath,
    LifeState,
    OptionStatistics,
    SimulationConfig,
    SimulationResult,
)


# ── LifeState ───────────────────────────────────────────────────────


class TestLifeState:
    def test_defaults(self):
        state = LifeState()
        assert state.age == 30
        assert state.skills == []
        assert state.goals == []
        assert state.career == ""

    def test_full_state(self):
        state = LifeState(
            career="Senior engineer at BigCo",
            finances="150k salary, 50k savings",
            health="Good, exercises 3x/week",
            relationships="Married, 1 kid",
            skills=["Python", "ML", "Leadership"],
            location="San Francisco",
            age=35,
            goals=["Start a company", "Write a book"],
        )
        assert state.age == 35
        assert len(state.skills) == 3
        assert "San Francisco" in state.location

    def test_age_bounds(self):
        with pytest.raises(ValidationError):
            LifeState(age=15)
        with pytest.raises(ValidationError):
            LifeState(age=101)
        LifeState(age=16)
        LifeState(age=100)

    def test_summary(self):
        state = LifeState(career="Engineer", age=28, location="NYC")
        summary = state.summary()
        assert "Engineer" in summary
        assert "28" in summary
        assert "NYC" in summary

    def test_summary_empty_state(self):
        state = LifeState()
        summary = state.summary()
        assert "Age: 30" in summary


# ── Decision ────────────────────────────────────────────────────────


class TestDecision:
    def test_valid_decision(self):
        d = Decision(
            description="Should I quit my job?",
            options=["Stay", "Quit and freelance"],
        )
        assert len(d.options) == 2

    def test_min_options(self):
        with pytest.raises(ValidationError):
            Decision(description="test", options=["Only one"])

    def test_max_options(self):
        with pytest.raises(ValidationError):
            Decision(description="test", options=[f"opt{i}" for i in range(6)])

    def test_five_options(self):
        d = Decision(description="test", options=[f"opt{i}" for i in range(5)])
        assert len(d.options) == 5


# ── SimulationConfig ────────────────────────────────────────────────


class TestSimulationConfig:
    def test_defaults(self):
        cfg = SimulationConfig()
        assert cfg.num_paths == 100
        assert cfg.years_ahead == 5
        assert len(cfg.focus_areas) == len(LifeArea)

    def test_custom(self):
        cfg = SimulationConfig(
            num_paths=50,
            years_ahead=10,
            focus_areas=[LifeArea.CAREER, LifeArea.FINANCES],
        )
        assert cfg.num_paths == 50
        assert cfg.years_ahead == 10
        assert len(cfg.focus_areas) == 2

    def test_bounds(self):
        with pytest.raises(ValidationError):
            SimulationConfig(num_paths=0)
        with pytest.raises(ValidationError):
            SimulationConfig(num_paths=1001)
        with pytest.raises(ValidationError):
            SimulationConfig(years_ahead=0)
        with pytest.raises(ValidationError):
            SimulationConfig(years_ahead=31)


# ── LifeEvent ───────────────────────────────────────────────────────


class TestLifeEvent:
    def test_valid_event(self):
        ev = LifeEvent(
            year=1,
            area=LifeArea.CAREER,
            description="Got promoted to Staff Engineer",
            impact_score=0.6,
            probability=0.3,
        )
        assert ev.year == 1
        assert ev.area == LifeArea.CAREER
        assert ev.impact_score == 0.6

    def test_impact_bounds(self):
        with pytest.raises(ValidationError):
            LifeEvent(year=1, area=LifeArea.HEALTH, description="x", impact_score=1.5)
        with pytest.raises(ValidationError):
            LifeEvent(year=1, area=LifeArea.HEALTH, description="x", impact_score=-1.5)

    def test_probability_bounds(self):
        with pytest.raises(ValidationError):
            LifeEvent(year=1, area=LifeArea.HEALTH, description="x", probability=-0.1)
        with pytest.raises(ValidationError):
            LifeEvent(year=1, area=LifeArea.HEALTH, description="x", probability=1.1)

    def test_defaults(self):
        ev = LifeEvent(year=2, area=LifeArea.FINANCES, description="Savings grow")
        assert ev.impact_score == 0.0
        assert ev.probability == 0.5


# ── LifePath ────────────────────────────────────────────────────────


class TestLifePath:
    def test_empty_path(self):
        path = LifePath(option="Stay")
        assert path.events == []
        assert path.overall_score == 0.0

    def test_path_with_events(self):
        events = [
            LifeEvent(year=1, area=LifeArea.CAREER, description="Promotion"),
            LifeEvent(year=2, area=LifeArea.FINANCES, description="Raise"),
        ]
        path = LifePath(
            option="Stay",
            events=events,
            happiness_score=7.5,
            financial_score=8.0,
            career_score=9.0,
            relationship_score=6.0,
            health_score=7.0,
            overall_score=7.5,
        )
        assert len(path.events) == 2
        assert path.overall_score == 7.5

    def test_score_bounds(self):
        with pytest.raises(ValidationError):
            LifePath(option="x", overall_score=-1)
        with pytest.raises(ValidationError):
            LifePath(option="x", overall_score=11)

    def test_score_vector(self):
        path = LifePath(
            option="Test",
            happiness_score=8.0,
            financial_score=6.0,
            career_score=7.0,
            relationship_score=5.0,
            health_score=9.0,
            overall_score=7.0,
        )
        vec = path.score_vector
        assert vec["happiness"] == 8.0
        assert vec["overall"] == 7.0
        assert len(vec) == 6


# ── OptionStatistics ────────────────────────────────────────────────


class TestOptionStatistics:
    def test_defaults(self):
        stat = OptionStatistics(option="Stay")
        assert stat.mean_overall == 0.0
        assert stat.upside_probability == 0.0

    def test_full(self):
        stat = OptionStatistics(
            option="Quit",
            mean_overall=6.5,
            median_overall=6.0,
            best_case=9.0,
            worst_case=2.0,
            std_dev=1.8,
            mean_happiness=7.0,
            mean_financial=5.0,
            mean_career=8.0,
            mean_relationship=6.0,
            mean_health=7.0,
            upside_probability=0.35,
            downside_probability=0.15,
        )
        assert stat.best_case == 9.0
        assert stat.downside_probability == 0.15


# ── SimulationResult ────────────────────────────────────────────────


class TestSimulationResult:
    def test_minimal(self):
        decision = Decision(description="test", options=["A", "B"])
        config = SimulationConfig()
        result = SimulationResult(decision=decision, config=config)
        assert result.paths_by_option == {}
        assert result.optimal_path is None
        assert result.key_insights == []

    def test_full_result(self):
        decision = Decision(description="test", options=["A", "B"])
        config = SimulationConfig()
        path_a = LifePath(option="A", overall_score=7.0)
        path_b = LifePath(option="B", overall_score=5.0)
        result = SimulationResult(
            decision=decision,
            config=config,
            paths_by_option={"A": [path_a], "B": [path_b]},
            statistics=[
                OptionStatistics(option="A", mean_overall=7.0),
                OptionStatistics(option="B", mean_overall=5.0),
            ],
            optimal_path=path_a,
            key_insights=["A is better on average"],
            action_items=["Choose A"],
        )
        assert len(result.paths_by_option) == 2
        assert result.optimal_path is not None
        assert result.optimal_path.option == "A"

    def test_serialization_roundtrip(self):
        decision = Decision(description="test", options=["A", "B"])
        config = SimulationConfig(num_paths=10, years_ahead=3)
        result = SimulationResult(decision=decision, config=config)
        json_str = result.model_dump_json()
        restored = SimulationResult.model_validate_json(json_str)
        assert restored.decision.description == "test"
        assert restored.config.num_paths == 10


# ── LifeArea enum ───────────────────────────────────────────────────


class TestLifeArea:
    def test_values(self):
        assert LifeArea.CAREER.value == "career"
        assert LifeArea.FINANCES.value == "finances"
        assert LifeArea.PERSONAL_GROWTH.value == "personal_growth"

    def test_all_areas(self):
        assert len(LifeArea) == 6

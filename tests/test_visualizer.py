"""Tests for the Rich terminal visualisation module."""

from __future__ import annotations

from io import StringIO

from rich.console import Console

from fateengine.models import (
    Decision,
    LifeArea,
    LifeEvent,
    LifePath,
    OptionStatistics,
    SimulationConfig,
    SimulationResult,
)
from fateengine.visualizer import (
    render_actions,
    render_banner,
    render_comparison,
    render_insights,
    render_life_paths,
    render_result,
    render_scores,
    render_timeline,
)


def _capture(fn, *args, **kwargs) -> str:
    """Capture Rich console output as plain text."""
    buf = StringIO()
    import fateengine.visualizer as viz

    original = viz.console
    viz.console = Console(file=buf, force_terminal=True, width=120)
    try:
        fn(*args, **kwargs)
    finally:
        viz.console = original
    return buf.getvalue()


def _sample_paths() -> list[LifePath]:
    return [
        LifePath(
            option="Quit",
            events=[
                LifeEvent(
                    year=1,
                    area=LifeArea.CAREER,
                    description="Founded startup",
                    impact_score=0.7,
                    probability=0.6,
                ),
                LifeEvent(
                    year=2,
                    area=LifeArea.FINANCES,
                    description="Burned through savings",
                    impact_score=-0.5,
                    probability=0.8,
                ),
                LifeEvent(
                    year=3,
                    area=LifeArea.CAREER,
                    description="Startup gets Series A",
                    impact_score=0.9,
                    probability=0.25,
                ),
            ],
            happiness_score=7.5,
            financial_score=5.0,
            career_score=8.5,
            relationship_score=6.0,
            health_score=6.5,
            overall_score=7.0,
        ),
        LifePath(
            option="Quit",
            events=[
                LifeEvent(
                    year=1,
                    area=LifeArea.CAREER,
                    description="Freelancing phase",
                    impact_score=0.3,
                    probability=0.7,
                ),
            ],
            happiness_score=6.0,
            financial_score=4.0,
            career_score=5.0,
            relationship_score=7.0,
            health_score=7.0,
            overall_score=5.5,
        ),
    ]


def _sample_stats() -> list[OptionStatistics]:
    return [
        OptionStatistics(
            option="Stay",
            mean_overall=6.5,
            median_overall=6.5,
            best_case=8.0,
            worst_case=5.0,
            std_dev=0.9,
            mean_happiness=6.0,
            mean_financial=7.5,
            mean_career=6.0,
            mean_relationship=7.0,
            mean_health=7.0,
            upside_probability=0.20,
            downside_probability=0.05,
        ),
        OptionStatistics(
            option="Quit",
            mean_overall=6.2,
            median_overall=6.0,
            best_case=9.0,
            worst_case=2.0,
            std_dev=2.1,
            mean_happiness=7.0,
            mean_financial=4.5,
            mean_career=7.5,
            mean_relationship=6.0,
            mean_health=6.5,
            upside_probability=0.35,
            downside_probability=0.20,
        ),
    ]


def _sample_result() -> SimulationResult:
    paths = _sample_paths()
    return SimulationResult(
        decision=Decision(
            description="Should I quit my job to start a startup?",
            options=["Stay", "Quit"],
        ),
        config=SimulationConfig(num_paths=20, years_ahead=5),
        paths_by_option={"Quit": paths, "Stay": [paths[1]]},
        statistics=_sample_stats(),
        optimal_path=paths[0],
        key_insights=["'Stay' is safer", "'Quit' has higher ceiling"],
        action_items=["Build savings buffer first"],
    )


# ── Tests ───────────────────────────────────────────────────────────


class TestRenderBanner:
    def test_contains_fate_art(self):
        output = _capture(render_banner)
        # "FATE" is rendered as block-character ASCII art; check for unique fragments
        assert "███████╗" in output  # block-art letters are present

    def test_contains_engine_text(self):
        output = _capture(render_banner)
        # "ENGINE" is rendered as spaced letters in the banner
        assert "E  N  G  I  N  E" in output or "Life Path Simulator" in output


class TestRenderLifePaths:
    def test_renders_option_name(self):
        output = _capture(render_life_paths, "Quit", _sample_paths())
        assert "Quit" in output

    def test_renders_events(self):
        output = _capture(render_life_paths, "Quit", _sample_paths())
        assert "Founded startup" in output
        assert "Series A" in output

    def test_renders_scores(self):
        output = _capture(render_life_paths, "Quit", _sample_paths())
        assert "7.0" in output

    def test_empty_paths(self):
        output = _capture(render_life_paths, "Empty", [])
        assert "Empty" in output


class TestRenderComparison:
    def test_renders_all_options(self):
        output = _capture(render_comparison, _sample_stats())
        assert "Stay" in output
        assert "Quit" in output

    def test_renders_metrics(self):
        output = _capture(render_comparison, _sample_stats())
        assert "Mean Overall" in output
        assert "Best Case" in output
        assert "Happiness" in output

    def test_renders_values(self):
        output = _capture(render_comparison, _sample_stats())
        assert "6.5" in output
        assert "9.0" in output


class TestRenderTimeline:
    def test_renders_years(self):
        path = _sample_paths()[0]
        output = _capture(render_timeline, path)
        assert "Year 1" in output
        assert "Year 2" in output
        assert "Year 3" in output

    def test_renders_events(self):
        path = _sample_paths()[0]
        output = _capture(render_timeline, path)
        assert "Founded startup" in output
        assert "Burned through savings" in output


class TestRenderScores:
    def test_renders_dimensions(self):
        output = _capture(render_scores, _sample_stats())
        assert "Happiness" in output
        assert "Financial" in output
        assert "Career" in output
        assert "Health" in output

    def test_renders_bars(self):
        output = _capture(render_scores, _sample_stats())
        assert "█" in output


class TestRenderInsights:
    def test_renders_insights(self):
        insights = ["Insight A", "Insight B"]
        output = _capture(render_insights, insights)
        assert "Insight A" in output
        assert "Insight B" in output


class TestRenderActions:
    def test_renders_actions(self):
        actions = ["Do X", "Do Y"]
        output = _capture(render_actions, actions)
        assert "Do X" in output
        assert "Do Y" in output


class TestRenderResult:
    def test_full_render(self):
        result = _sample_result()
        output = _capture(render_result, result)
        assert "quit my job" in output.lower() or "Quit" in output
        assert "Stay" in output
        assert "Build savings" in output

    def test_no_crash_minimal_result(self):
        result = SimulationResult(
            decision=Decision(description="Test?", options=["A", "B"]),
            config=SimulationConfig(),
        )
        output = _capture(render_result, result)
        assert "Test?" in output

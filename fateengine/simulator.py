"""Core Monte Carlo life-path simulation engine."""

from __future__ import annotations

import asyncio
import logging
import math
import statistics
from typing import Any

from fateengine.ai import AIEngine
from fateengine.config import Settings
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

logger = logging.getLogger(__name__)

# How many paths to request per LLM call (batching for efficiency)
_PATHS_PER_CALL = 5
_MAX_CONCURRENT = 4


class FateSimulator:
    """Runs probability-weighted life-path simulations powered by LLM generation."""

    def __init__(self, ai: AIEngine | None = None, settings: Settings | None = None) -> None:
        self._ai = ai or AIEngine(settings)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def simulate(
        self,
        state: LifeState,
        decision: Decision,
        config: SimulationConfig | None = None,
    ) -> SimulationResult:
        """Run a full simulation for *decision* given *state*."""
        config = config or SimulationConfig()
        paths_by_option: dict[str, list[LifePath]] = {}

        for option in decision.options:
            paths = await self._simulate_option(state, decision, option, config)
            paths_by_option[option] = paths

        stats = [
            self._compute_statistics(option, paths)
            for option, paths in paths_by_option.items()
        ]

        optimal = self._pick_optimal(paths_by_option)

        insights = self._derive_insights(stats)
        actions = self._derive_actions(stats, optimal)

        return SimulationResult(
            decision=decision,
            config=config,
            paths_by_option=paths_by_option,
            statistics=stats,
            optimal_path=optimal,
            key_insights=insights,
            action_items=actions,
        )

    async def quick_simulate(
        self,
        situation: str,
        decision_text: str,
    ) -> SimulationResult:
        """Convenience wrapper: parse free-text inputs then simulate."""
        parsed = await self._parse_inputs(situation, decision_text)
        state, decision = parsed
        config = SimulationConfig(num_paths=20, years_ahead=5)
        return await self.simulate(state, decision, config)

    # ------------------------------------------------------------------
    # Simulation internals
    # ------------------------------------------------------------------

    async def _simulate_option(
        self,
        state: LifeState,
        decision: Decision,
        option: str,
        config: SimulationConfig,
    ) -> list[LifePath]:
        """Generate *config.num_paths* life paths for a single option."""
        num_calls = max(1, math.ceil(config.num_paths / _PATHS_PER_CALL))
        sem = asyncio.Semaphore(_MAX_CONCURRENT)

        async def _batch(batch_size: int) -> list[LifePath]:
            async with sem:
                return await self._generate_paths(
                    state, decision, option, config, batch_size
                )

        remaining = config.num_paths
        tasks: list[asyncio.Task[list[LifePath]]] = []
        for _ in range(num_calls):
            batch_sz = min(_PATHS_PER_CALL, remaining)
            remaining -= batch_sz
            tasks.append(asyncio.create_task(_batch(batch_sz)))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        paths: list[LifePath] = []
        for r in results:
            if isinstance(r, list):
                paths.extend(r)
            else:
                logger.warning("Batch generation failed: %s", r)
        return paths

    async def _generate_paths(
        self,
        state: LifeState,
        decision: Decision,
        option: str,
        config: SimulationConfig,
        count: int,
    ) -> list[LifePath]:
        """Ask the LLM to produce *count* distinct paths."""
        focus = ", ".join(a.value for a in config.focus_areas)
        prompt = (
            f"CURRENT LIFE STATE:\n{state.summary()}\n\n"
            f"DECISION: {decision.description}\n"
            f"CHOSEN OPTION: {option}\n\n"
            f"Generate {count} distinct, realistic life paths spanning "
            f"{config.years_ahead} years if this person chooses \"{option}\".\n"
            f"Focus areas: {focus}.\n\n"
            f"For each path, include:\n"
            f"- A list of key life events (year, area, description, impact_score, probability)\n"
            f"- Scores (0–10) for: happiness, financial, career, relationship, health, overall\n\n"
            f"Return a JSON object with key \"paths\" containing a list of path objects.\n"
            f"Each path object has keys: events (list), happiness_score, financial_score, "
            f"career_score, relationship_score, health_score, overall_score.\n"
            f"Each event has keys: year (int), area (one of {[a.value for a in LifeArea]}), "
            f"description (str), impact_score (float -1 to 1), probability (float 0 to 1)."
        )

        from pydantic import BaseModel, Field

        class _PathBatch(BaseModel):
            paths: list[LifePath]

        # Temporarily override the LifePath to not require 'option' in the JSON
        # by post-processing
        class _RawPath(BaseModel):
            events: list[LifeEvent] = Field(default_factory=list)
            happiness_score: float = 0.0
            financial_score: float = 0.0
            career_score: float = 0.0
            relationship_score: float = 0.0
            health_score: float = 0.0
            overall_score: float = 0.0

        class _RawBatch(BaseModel):
            paths: list[_RawPath]

        batch = await self._ai.generate_json(prompt, _RawBatch)
        return [
            LifePath(
                option=option,
                events=p.events,
                happiness_score=max(0.0, min(10.0, p.happiness_score)),
                financial_score=max(0.0, min(10.0, p.financial_score)),
                career_score=max(0.0, min(10.0, p.career_score)),
                relationship_score=max(0.0, min(10.0, p.relationship_score)),
                health_score=max(0.0, min(10.0, p.health_score)),
                overall_score=max(0.0, min(10.0, p.overall_score)),
            )
            for p in batch.paths
        ]

    async def _parse_inputs(
        self,
        situation: str,
        decision_text: str,
    ) -> tuple[LifeState, Decision]:
        """Use the LLM to turn free-form text into structured models."""
        from pydantic import BaseModel

        class _Parsed(BaseModel):
            state: LifeState
            decision: Decision

        prompt = (
            f"Parse the following into a structured LifeState and Decision.\n\n"
            f"SITUATION: {situation}\n\n"
            f"DECISION: {decision_text}\n\n"
            f"If the decision text doesn't clearly list options, infer 2–3 reasonable options.\n"
            f"Return a JSON object with keys 'state' and 'decision'."
        )
        parsed = await self._ai.generate_json(prompt, _Parsed)
        return parsed.state, parsed.decision

    # ------------------------------------------------------------------
    # Statistics & analysis
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_statistics(option: str, paths: list[LifePath]) -> OptionStatistics:
        if not paths:
            return OptionStatistics(option=option)

        overalls = [p.overall_score for p in paths]
        return OptionStatistics(
            option=option,
            mean_overall=statistics.mean(overalls),
            median_overall=statistics.median(overalls),
            best_case=max(overalls),
            worst_case=min(overalls),
            std_dev=statistics.stdev(overalls) if len(overalls) > 1 else 0.0,
            mean_happiness=statistics.mean(p.happiness_score for p in paths),
            mean_financial=statistics.mean(p.financial_score for p in paths),
            mean_career=statistics.mean(p.career_score for p in paths),
            mean_relationship=statistics.mean(p.relationship_score for p in paths),
            mean_health=statistics.mean(p.health_score for p in paths),
            upside_probability=sum(1 for s in overalls if s > 7.0) / len(overalls),
            downside_probability=sum(1 for s in overalls if s < 4.0) / len(overalls),
        )

    @staticmethod
    def _pick_optimal(paths_by_option: dict[str, list[LifePath]]) -> LifePath | None:
        best: LifePath | None = None
        for paths in paths_by_option.values():
            for p in paths:
                if best is None or p.overall_score > best.overall_score:
                    best = p
        return best

    @staticmethod
    def _derive_insights(stats: list[OptionStatistics]) -> list[str]:
        insights: list[str] = []
        if not stats:
            return insights

        best = max(stats, key=lambda s: s.mean_overall)
        worst = min(stats, key=lambda s: s.mean_overall)
        insights.append(
            f"'{best.option}' has the highest average outcome ({best.mean_overall:.1f}/10), "
            f"while '{worst.option}' scores lowest ({worst.mean_overall:.1f}/10)."
        )

        riskiest = max(stats, key=lambda s: s.std_dev)
        safest = min(stats, key=lambda s: s.std_dev)
        if riskiest.option != safest.option:
            insights.append(
                f"'{riskiest.option}' is the highest-variance option (σ={riskiest.std_dev:.2f}) — "
                f"bigger potential swings. '{safest.option}' is more predictable (σ={safest.std_dev:.2f})."
            )

        for s in stats:
            if s.downside_probability > 0.25:
                insights.append(
                    f"⚠ '{s.option}' has a {s.downside_probability:.0%} chance of poor outcomes (score < 4)."
                )
            if s.upside_probability > 0.40:
                insights.append(
                    f"✦ '{s.option}' has a {s.upside_probability:.0%} shot at excellent outcomes (score > 7)."
                )

        return insights

    @staticmethod
    def _derive_actions(
        stats: list[OptionStatistics], optimal: LifePath | None
    ) -> list[str]:
        actions: list[str] = []
        if not stats:
            return actions

        best = max(stats, key=lambda s: s.mean_overall)
        actions.append(f"Lean towards '{best.option}' — it has the strongest expected outcome.")

        for s in stats:
            weak = min(
                [
                    ("happiness", s.mean_happiness),
                    ("finances", s.mean_financial),
                    ("career", s.mean_career),
                    ("relationships", s.mean_relationship),
                    ("health", s.mean_health),
                ],
                key=lambda x: x[1],
            )
            if weak[1] < 5.0:
                actions.append(
                    f"If you choose '{s.option}', proactively invest in {weak[0]} "
                    f"(projected score: {weak[1]:.1f}/10)."
                )

        if optimal and optimal.events:
            high_impact = sorted(optimal.events, key=lambda e: abs(e.impact_score), reverse=True)
            if high_impact:
                ev = high_impact[0]
                actions.append(
                    f"Key inflection point in year {ev.year}: {ev.description} "
                    f"(impact {ev.impact_score:+.2f}). Prepare for this."
                )

        return actions

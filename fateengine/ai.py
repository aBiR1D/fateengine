"""LLM abstraction layer — supports Anthropic Claude and OpenAI."""

from __future__ import annotations

import json
import logging
import re
from typing import Any, TypeVar

from pydantic import BaseModel

from fateengine.config import Settings, get_settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

SYSTEM_PROMPT = """\
You are the Fate Engine — an expert life-path simulation system.
Your role is to generate *realistic*, *nuanced*, probability-weighted life events
that could follow from a person's current situation and a specific decision.

Principles:
• Be honest, not optimistic.  Real life has setbacks, surprises, and compounding effects.
• Consider second- and third-order consequences.
• Assign calibrated probabilities — most events should NOT be 0.5.
• Impact scores should reflect magnitude: minor inconveniences ≈ ±0.1, life-changing events ≈ ±0.8–1.0.
• Cover ALL requested life areas, not just career/finances.
• When generating multiple paths, make them *genuinely different* — explore tail risks and lucky breaks.
• Ground events in the person's specific context (age, skills, location, relationships).

When returning JSON, return ONLY valid JSON with no markdown fences or commentary.\
"""


class AIEngine:
    """Unified interface to Anthropic and OpenAI language models."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._provider = self._settings.provider

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate(self, prompt: str, *, system: str | None = None) -> str:
        """Generate free-form text from the model."""
        sys = system or SYSTEM_PROMPT
        if self._provider == "openai":
            return await self._openai_generate(prompt, system=sys)
        return await self._anthropic_generate(prompt, system=sys)

    async def generate_json(
        self,
        prompt: str,
        response_model: type[T],
        *,
        system: str | None = None,
    ) -> T:
        """Generate structured JSON output parsed into *response_model*."""
        schema_hint = json.dumps(response_model.model_json_schema(), indent=2)
        augmented = (
            f"{prompt}\n\n"
            f"Respond with a single JSON object conforming to this schema:\n"
            f"```\n{schema_hint}\n```\n"
            f"Return ONLY the JSON object — no markdown fences, no extra text."
        )
        raw = await self.generate(augmented, system=system)
        cleaned = self._extract_json(raw)
        return response_model.model_validate_json(cleaned)

    # ------------------------------------------------------------------
    # Provider implementations
    # ------------------------------------------------------------------

    async def _anthropic_generate(self, prompt: str, *, system: str) -> str:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=self._settings.anthropic_api_key)
        response = await client.messages.create(
            model=self._settings.model,
            max_tokens=self._settings.max_tokens,
            temperature=self._settings.temperature,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    async def _openai_generate(self, prompt: str, *, system: str) -> str:
        import openai

        client = openai.AsyncOpenAI(api_key=self._settings.openai_api_key)
        response = await client.chat.completions.create(
            model=self._settings.model,
            max_tokens=self._settings.max_tokens,
            temperature=self._settings.temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )
        choice = response.choices[0]
        return choice.message.content or ""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_json(text: str) -> str:
        """Best-effort extraction of a JSON object from model output."""
        # Try to strip markdown code fences
        fenced = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
        if fenced:
            return fenced.group(1).strip()
        # Try to find a top-level { … }
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            return text[first_brace : last_brace + 1]
        return text.strip()

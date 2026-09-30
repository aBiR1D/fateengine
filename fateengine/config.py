"""Application configuration via environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Fate Engine configuration loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_prefix="FATEENGINE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    anthropic_api_key: str = ""
    openai_api_key: str = ""
    model: str = "claude-sonnet-4-20250514"
    provider: str = "anthropic"  # "anthropic" | "openai"
    temperature: float = 0.8
    max_tokens: int = 4096
    api_host: str = "0.0.0.0"
    api_port: int = 8420

    @property
    def active_api_key(self) -> str:
        if self.provider == "openai":
            return self.openai_api_key
        return self.anthropic_api_key


def get_settings() -> Settings:
    """Return a cached settings instance."""
    return Settings()

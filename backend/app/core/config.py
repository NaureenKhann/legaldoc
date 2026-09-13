"""
LegalDoc Intelligence Platform - Application Configuration
Uses Pydantic Settings v2 for type-safe, validated settings.
"""
from __future__ import annotations

import secrets
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    APP_NAME: str = "LegalDoc Intelligence Platform"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))

    # ── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://legaldoc:legaldoc_secret@localhost:5432/legaldoc"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # ── Redis ────────────────────────────────────────────────────────────────
    REDIS_URL: str | None = None

    # ── File Storage ─────────────────────────────────────────────────────────
    STORAGE_PATH: Path = Path("./storage")
    MAX_UPLOAD_SIZE_MB: int = 20
    ALLOWED_EXTENSIONS: str = "pdf,docx,txt"

    @property
    def allowed_extensions_set(self) -> set[str]:
        return {ext.lower().strip() for ext in self.ALLOWED_EXTENSIONS.split(",")}

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    # ── AI Provider ───────────────────────────────────────────────────────────
    LLM_PROVIDER: Literal["openai", "anthropic", "gemini"] = "openai"
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None
    LLM_MODEL: str | None = None  # uses provider default if None
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_RETRIES: int = 3
    LLM_TIMEOUT_SECONDS: int = 120

    # ── Demo Mode ────────────────────────────────────────────────────────────
    DEMO_MODE: bool = False
    DEMO_FIXTURES_PATH: Path = Path("./tests/fixtures")

    # ── Logging ──────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"

    # ── CORS ─────────────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    @field_validator("STORAGE_PATH", "DEMO_FIXTURES_PATH", mode="before")
    @classmethod
    def create_path(cls, v: str | Path) -> Path:
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_default_model(self) -> str:
        defaults = {
            "openai": "gpt-4o",
            "anthropic": "claude-3-5-sonnet-20241022",
            "gemini": "gemini-1.5-pro",
        }
        return self.LLM_MODEL or defaults[self.LLM_PROVIDER]

    def get_active_api_key(self) -> str | None:
        keys = {
            "openai": self.OPENAI_API_KEY,
            "anthropic": self.ANTHROPIC_API_KEY,
            "gemini": self.GEMINI_API_KEY,
        }
        return keys.get(self.LLM_PROVIDER)


@lru_cache
def get_settings() -> Settings:
    return Settings()

"""
StudyNexs Platform — Application Configuration
Uses Pydantic Settings for type-safe, validated configuration.
Production validators crash on boot if misconfigured.
"""
from __future__ import annotations

import enum
from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, enum.Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Central configuration — loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────
    APP_NAME: str = "StudyNexs API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # ── Database (PostgreSQL — async) ────────────────────────────
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "studynexs"
    POSTGRES_PASSWORD: str = "studynexs_dev"
    POSTGRES_DB: str = "studynexs"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def DATABASE_URL_SYNC(self) -> str:
        """Synchronous URL for Alembic migrations."""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # ── Redis ────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_TOKEN_BLACKLIST_PREFIX: str = "auth:blacklist:"
    REDIS_OTP_PREFIX: str = "auth:otp:"
    REDIS_USER_CACHE_PREFIX: str = "user:cache:"
    REDIS_USER_CACHE_TTL: int = 60  # seconds
    REDIS_RATE_LIMIT_PREFIX: str = "auth:ratelimit:"
    REDIS_REFRESH_JTI_PREFIX: str = "auth:refresh_jti:"
    REDIS_REFRESH_LOCK_PREFIX: str = "auth:refresh_lock:"

    # ── JWT / Auth ───────────────────────────────────────────────
    JWT_SECRET_KEY: str = "CHANGE-ME-IN-PRODUCTION-32-chars-minimum"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ── OTP ──────────────────────────────────────────────────────
    OTP_EXPIRE_MINUTES: int = 5
    OTP_MAX_ATTEMPTS: int = 3
    OTP_COOLDOWN_SECONDS: int = 300  # 5 minutes between sends
    OTP_LENGTH: int = 6

    # ── Rate Limiting ────────────────────────────────────────────
    RATE_LIMIT_ENABLED: bool = True
    AUTH_RATE_LIMIT_MAX_ATTEMPTS: int = 10
    AUTH_RATE_LIMIT_WINDOW_SECONDS: int = 900  # 15 minutes
    LOGIN_RATE_LIMIT_MAX_ATTEMPTS: int = 5
    LOGIN_RATE_LIMIT_WINDOW_SECONDS: int = 900
    API_RATE_LIMIT_READ_PER_MIN: int = 300
    API_RATE_LIMIT_WRITE_PER_MIN: int = 60
    API_RATE_LIMIT_UPLOAD_PER_MIN: int = 20
    API_RATE_LIMIT_WINDOW_SECONDS: int = 60

    # ── Outbox worker ────────────────────────────────────────────
    OUTBOX_WORKER_ENABLED: bool = True
    OUTBOX_POLL_INTERVAL_SECONDS: float = 2.0

    # ── Audit retention ──────────────────────────────────────────
    AUDIT_RETENTION_DAYS: int = 90

    # ── CORS ─────────────────────────────────────────────────────
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
        "http://127.0.0.1:3003",
    ]

    # ── Cookie Config ────────────────────────────────────────────
    COOKIE_DOMAIN: str | None = None  # None = current domain
    COOKIE_SECURE: bool = False  # True in production (HTTPS)
    COOKIE_SAMESITE: str = "lax"
    REFRESH_COOKIE_NAME: str = "studynexs_refresh"
    REFRESH_COOKIE_PATH: str = "/api/v1/auth/refresh"

    # ── Tenant ───────────────────────────────────────────────────
    TENANT_BASE_DOMAIN: str = "localhost"  # e.g., "studynexs.com" in production
    DEFAULT_TENANT_SLUG: str = "dev"  # fallback for local development

    # ── External Services (placeholders for Phase 2+) ────────────
    MSG91_AUTH_KEY: str = ""
    MSG91_TEMPLATE_ID: str = ""
    SENDGRID_API_KEY: str = ""
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    WEBHOOK_SECRET: str = "webhook-secret-change-me"

    # ── File Storage ─────────────────────────────────────────────
    AZURE_STORAGE_CONNECTION_STRING: str = ""
    AZURE_STORAGE_CONTAINER: str = "studynexs-files"

    # ── Qdrant (Vector DB) ───────────────────────────────────────
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: str = ""

    # ── AI / LLM Gateway (provider-agnostic; benchmark before committing) ──
    GEMINI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    AI_DEFAULT_PROVIDER: str = "gemini"  # default only; benchmark decides the real one
    AI_DEFAULT_MODEL: str = ""  # empty → factory picks the provider's default model
    AI_REQUEST_TIMEOUT_SECONDS: float = 120.0

    # ── Azure Speech (Neural TTS for the AI-tutor voice) ─────────
    # When unset, the tutor falls back to the browser's Web Speech voice.
    AZURE_SPEECH_KEY: str = ""
    AZURE_SPEECH_REGION: str = "centralindia"  # data residency: keep Indian region
    AZURE_SPEECH_VOICE: str = "en-IN-NeerjaNeural"  # soft, natural female Indian English

    # ── Derived Properties ───────────────────────────────────────
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == Environment.DEVELOPMENT

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == Environment.PRODUCTION

    # ── Production Guardrails ────────────────────────────────────
    @model_validator(mode="after")
    def _validate_production_config(self) -> "Settings":
        """Crash on boot if production config is unsafe."""
        if self.ENVIRONMENT != Environment.PRODUCTION:
            return self

        errors: list[str] = []

        if self.DEBUG:
            errors.append("DEBUG must be False in production")

        if "CHANGE-ME" in self.JWT_SECRET_KEY or len(self.JWT_SECRET_KEY) < 32:
            errors.append("JWT_SECRET_KEY must be changed and ≥32 characters")

        if "change-me" in self.WEBHOOK_SECRET.lower():
            errors.append("WEBHOOK_SECRET must be changed")

        unsafe_origins = {"*", "http://localhost:3000", "http://localhost:3001"}
        if unsafe_origins & set(self.ALLOWED_ORIGINS):
            errors.append("ALLOWED_ORIGINS must not contain localhost or wildcard")

        if not self.COOKIE_SECURE:
            errors.append("COOKIE_SECURE must be True in production (HTTPS)")

        if not self.REDIS_URL or "localhost" in self.REDIS_URL:
            errors.append("REDIS_URL must point to production Redis")

        provider_keys = {
            "openai": self.OPENAI_API_KEY,
            "anthropic": self.ANTHROPIC_API_KEY,
            "gemini": self.GEMINI_API_KEY,
        }
        default_provider_key = provider_keys.get(self.AI_DEFAULT_PROVIDER)
        if self.AI_DEFAULT_PROVIDER in provider_keys and not default_provider_key:
            errors.append(
                f"AI_DEFAULT_PROVIDER={self.AI_DEFAULT_PROVIDER!r} but its API key is not set"
            )

        if errors:
            raise ValueError(
                "FATAL: Production configuration errors:\n"
                + "\n".join(f"  • {e}" for e in errors)
            )

        return self


@lru_cache
def get_settings() -> Settings:
    """Cached singleton — call this everywhere."""
    return Settings()

"""
StudyNexs Platform — Application Configuration
Uses Pydantic Settings for type-safe, validated configuration.
Production validators crash on boot if misconfigured.
"""
from __future__ import annotations

import enum
from functools import lru_cache
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_API_ROOT = Path(__file__).resolve().parents[2]
_ENV_FILE = _API_ROOT / ".env"


class Environment(str, enum.Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Central configuration — loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE if _ENV_FILE.is_file() else ".env",
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

    # ── Prospect demo provisioning (Stage 2B) ─────────────────────
    DEMO_PROVISIONING_ENABLED: bool = False
    DEMO_SESSION_TTL_HOURS: int = 72
    DEMO_PROVISION_RATE_LIMIT_MAX: int = 5
    DEMO_PROVISION_RATE_LIMIT_WINDOW_SECONDS: int = 3600
    DEMO_MAX_ACTIVE_PROSPECTS: int = 200
    DEMO_PROTECTED_TENANT_SLUGS: list[str] = ["reference", "naagarjuna", "test"]
    DEMO_SWEEP_CRON_MINUTES: list[int] = [0, 15, 30, 45]

    # Cloudflare Turnstile — required in production when demo provisioning is enabled.
    TURNSTILE_SITE_KEY: str = ""
    TURNSTILE_SECRET_KEY: str = ""

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
        "http://localhost:3006",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
        "http://127.0.0.1:3003",
        "http://127.0.0.1:3006",
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
    # Platform hosts (api, app, demo, …) — not school tenants; see docs/URL_ARCHITECTURE.md
    TENANT_RESERVED_SUBDOMAINS: list[str] = [
        "api",
        "app",
        "demo",
        "dev",
        "test",
        "admin",
        "www",
    ]

    # ── External Services (placeholders for Phase 2+) ────────────
    MSG91_AUTH_KEY: str = ""
    MSG91_TEMPLATE_ID: str = ""
    SENDGRID_API_KEY: str = ""
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    WEBHOOK_SECRET: str = "webhook-secret-change-me"

    # ── Field encryption (regulated PII at rest, e.g. Aadhaar) ───
    # urlsafe-base64 Fernet keys. First encrypts; all decrypt (rotation-friendly). Empty in
    # dev = store plaintext (transparent). Production boot refuses to start without a key.
    # Generate a key with cryptography.fernet.Fernet.generate_key(); keep it in the secret store.
    AADHAAR_ENCRYPTION_KEYS: list[str] = []

    # ── File Storage ─────────────────────────────────────────────
    AZURE_STORAGE_CONNECTION_STRING: str = ""
    AZURE_STORAGE_CONTAINER: str = "studynexs-files"
    # Path to tesseract binary when not on PATH (Windows: ...\Tesseract-OCR\tesseract.exe)
    TESSERACT_CMD: str = ""

    # ── Qdrant (Vector DB) ───────────────────────────────────────
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: str = ""
    # Vector store backend for the RAG platform: qdrant | memory (memory = tests/dev only).
    VECTOR_STORE: str = "qdrant"

    # ── AI / LLM Gateway (provider-agnostic; benchmark before committing) ──
    GEMINI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    AI_DEFAULT_PROVIDER: str = "gemini"  # default only; benchmark decides the real one
    AI_DEFAULT_MODEL: str = ""  # empty → factory picks the provider's default model
    AI_FALLBACK_PROVIDER: str = ""  # e.g. ollama — used when primary provider fails
    # Answer-sheet OCR fallback; defaults to AI_FALLBACK_PROVIDER or ollama.
    AI_VISION_FALLBACK_PROVIDER: str = ""
    OLLAMA_BASE_URL: str = ""  # e.g. http://host.docker.internal:11434 (Docker → host Ollama)
    OLLAMA_MODEL: str = "gemma4:cloud"
    OLLAMA_VISION_MODEL: str = ""  # empty → OLLAMA_MODEL (gemma4 supports image input)
    OLLAMA_API_KEY: str = ""  # optional — Ollama cloud / authenticated endpoints
    AI_REQUEST_TIMEOUT_SECONDS: float = 120.0

    # ── Embeddings (RAG) — provider-agnostic; provider exposes >=1 model ─────────
    # EMBEDDING_PROVIDER selects the adapter (openai | ollama | stub | …); EMBEDDING_MODEL
    # names one of that provider's models. Default: OpenAI text-embedding-3-small (1536-dim).
    # No app code talks to a provider directly — everything goes through EmbeddingService.
    EMBEDDING_PROVIDER: str = "openai"
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    # ── Observability scrape (Prometheus) ─────────────────────────
    # When set, /metrics requires Authorization: Bearer <token> or X-Metrics-Token header.
    # In production, /metrics is disabled unless this is configured.
    METRICS_TOKEN: str = ""

    # ── OpenTelemetry (metrics + traces → OTLP collector) ───────
    OTEL_ENABLED: bool = False
    OTEL_SERVICE_NAME: str = "studynexs-api"
    OTEL_EXPORTER_OTLP_ENDPOINT: str = ""  # e.g. http://otel-collector:4317
    OTEL_EXPORTER_OTLP_PROTOCOL: str = "grpc"  # grpc | http
    OTEL_TRACES_SAMPLE_RATE: float = 1.0  # 0.0–1.0; lower in high-traffic prod
    OTEL_METRIC_EXPORT_INTERVAL_MS: int = 15000

    # ── Tutor TTS (Neural voice for AI tutor lessons) ─────────────
    # Provider: auto (Azure if key set, else Edge TTS), azure, edge, or off.
    # Edge TTS uses the same Microsoft Neural voices without an API key — good for pilot/demo.
    # Azure Speech is the production-grade path when you have a subscription + data residency needs.
    TUTOR_TTS_PROVIDER: str = "edge"  # edge | auto | azure | off — edge = Neerja without Azure key
    TUTOR_TTS_RATE: str = "-12%"  # base prosody — explain steps go slower in speech_prepare
    TUTOR_TTS_PITCH: str = "+0Hz"  # edge-tts pitch — keep Neerja natural
    # Expressive Neerja — warmer intonation for teaching (not flat read-aloud).
    TUTOR_TTS_VOICE: str = "en-IN-NeerjaExpressiveNeural"
    AZURE_SPEECH_KEY: str = ""
    AZURE_SPEECH_REGION: str = "centralindia"  # data residency: keep Indian region
    AZURE_SPEECH_VOICE: str = "en-IN-NeerjaExpressiveNeural"

    # Academic Evaluation Intelligence (AEI) controlled runtime integration.
    # Wave 1 is passive only: AEI observes evaluation requests without affecting marks,
    # gradebook, mastery, teacher-visible behavior, or persistence.
    AEI_PASSIVE_INTEGRATION_ENABLED: bool = False
    # Wave 2 compares AEI output against existing production suggestions for internal
    # validation only. It is also disabled by default and remains user-invisible.
    AEI_SHADOW_MODE_ENABLED: bool = False

    # ── Derived Properties ───────────────────────────────────────
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == Environment.DEVELOPMENT

    @property
    def demo_provisioning_allowed(self) -> bool:
        """Prospect tenant creation — explicit flag or non-production default."""
        if self.DEMO_PROVISIONING_ENABLED:
            return True
        return self.ENVIRONMENT in (Environment.DEVELOPMENT, Environment.TESTING)

    @property
    def demo_turnstile_required(self) -> bool:
        """Bot challenge on public provisioning — always in production when demo is on."""
        if not self.demo_provisioning_allowed:
            return False
        if self.ENVIRONMENT == Environment.PRODUCTION:
            return True
        return bool(self.TURNSTILE_SECRET_KEY.strip())

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
        if self.AI_DEFAULT_PROVIDER == "stub":
            errors.append("AI_DEFAULT_PROVIDER cannot be 'stub' in production")

        if not [k for k in self.AADHAAR_ENCRYPTION_KEYS if k.strip()]:
            errors.append(
                "AADHAAR_ENCRYPTION_KEYS must be set in production (regulated PII is "
                "encrypted at rest; generate with Fernet.generate_key())"
            )

        if self.DEMO_PROVISIONING_ENABLED and not self.TURNSTILE_SECRET_KEY.strip():
            errors.append(
                "TURNSTILE_SECRET_KEY is required when DEMO_PROVISIONING_ENABLED in production"
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

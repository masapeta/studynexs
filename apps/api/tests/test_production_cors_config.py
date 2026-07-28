"""Production CORS guardrails reject local, wildcard, and insecure origins."""

import pytest
from pydantic import ValidationError

from app.core.config import Environment, Settings


def _production_settings(origins: list[str]) -> Settings:
    return Settings(
        ENVIRONMENT=Environment.PRODUCTION,
        DEBUG=False,
        JWT_SECRET_KEY="production-jwt-secret-with-more-than-32-characters",
        WEBHOOK_SECRET="production-webhook-secret",
        ALLOWED_ORIGINS=origins,
        COOKIE_SECURE=True,
        REDIS_URL="rediss://redis.internal:6379/0",
        AI_DEFAULT_PROVIDER="ollama",
        AADHAAR_ENCRYPTION_KEYS=["configured-production-fernet-key"],
    )


@pytest.mark.parametrize(
    "origin",
    [
        "*",
        "https://*.studynexs.com",
        "http://app.studynexs.com",
        "https://localhost:3000",
        "https://school.localhost",
        "https://LOCALHOST.",
        "https://127.0.0.1:3000",
        "https://127.42.1.7",
        "https://[::1]",
        "https://0.0.0.0",
        "https://[::]",
        "https://app.studynexs.com/",
        " https://app.studynexs.com",
        "https://app.studynexs.com ",
        "https://user:password@app.studynexs.com",
        "https://app.studynexs.com/path",
        "https://app.studynexs.com?query=yes",
        "https://app.studynexs.com#fragment",
        "https://app.studynexs.com:not-a-port",
    ],
)
def test_production_rejects_unsafe_cors_origins(origin: str) -> None:
    with pytest.raises(ValidationError, match="ALLOWED_ORIGINS"):
        _production_settings([origin])


def test_production_accepts_exact_https_origins() -> None:
    settings = _production_settings(
        ["https://app.studynexs.com", "https://school.studynexs.com:8443"]
    )

    assert settings.ALLOWED_ORIGINS == [
        "https://app.studynexs.com",
        "https://school.studynexs.com:8443",
    ]


def test_development_keeps_local_http_origins() -> None:
    settings = Settings(ENVIRONMENT=Environment.DEVELOPMENT)

    assert "http://localhost:3000" in settings.ALLOWED_ORIGINS
    assert "http://127.0.0.1:3000" in settings.ALLOWED_ORIGINS

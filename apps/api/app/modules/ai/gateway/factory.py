"""Provider factory — selects an adapter by name/config. Adapters are imported
lazily so the app (and tests) import fine without the provider SDKs installed.
"""
from __future__ import annotations

from app.core.config import get_settings
from app.modules.ai.gateway.base import LLMProvider

settings = get_settings()

_DEFAULT_MODELS = {
    "gemini": "gemini-1.5-flash",
    "anthropic": "claude-haiku-4-5",
    "openai": "gpt-4o-mini",
    "ollama": "gemma4:cloud",
    "stub": "dev-stub",
}

_PROVIDER_KEYS = {
    "gemini": lambda: settings.GEMINI_API_KEY,
    "anthropic": lambda: settings.ANTHROPIC_API_KEY,
    "openai": lambda: settings.OPENAI_API_KEY,
}


def _provider_configured(name: str) -> bool:
    getter = _PROVIDER_KEYS.get(name)
    return bool(getter and getter())


def _ollama_configured() -> bool:
    return bool((settings.OLLAMA_BASE_URL or "").strip())


def ollama_configured() -> bool:
    return _ollama_configured()


def get_provider(name: str | None = None) -> LLMProvider:
    provider = (name or settings.AI_DEFAULT_PROVIDER).lower()
    if settings.is_production and provider == "stub":
        raise RuntimeError("Stub AI provider is disabled in production")
    if provider == "stub":
        from app.modules.ai.gateway.stub import StubProvider

        return StubProvider()
    if provider == "ollama" and _ollama_configured():
        from app.modules.ai.gateway.ollama import OllamaProvider

        return OllamaProvider()
    if provider == "gemini" and _provider_configured("gemini"):
        from app.modules.ai.gateway.gemini import GeminiProvider

        return GeminiProvider()
    if provider == "anthropic" and _provider_configured("anthropic"):
        from app.modules.ai.gateway.anthropic import AnthropicProvider

        return AnthropicProvider()
    if provider == "openai" and _provider_configured("openai"):
        from app.modules.ai.gateway.openai import OpenAIProvider

        return OpenAIProvider()
    if settings.is_development:
        from app.modules.ai.gateway.stub import StubProvider

        return StubProvider()
    if provider in _PROVIDER_KEYS:
        raise RuntimeError(f"{provider.upper()}_API_KEY is not configured")
    raise ValueError(f"Unknown AI provider: {provider!r}")


def default_model(provider: str | None = None) -> str:
    """Resolve the model to use: explicit config wins, else the provider's default."""
    provider = (provider or settings.AI_DEFAULT_PROVIDER).lower()
    if provider == "ollama":
        return settings.OLLAMA_MODEL or _DEFAULT_MODELS["ollama"]
    return settings.AI_DEFAULT_MODEL or _DEFAULT_MODELS.get(provider, "")

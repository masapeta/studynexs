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
}


def get_provider(name: str | None = None) -> LLMProvider:
    provider = (name or settings.AI_DEFAULT_PROVIDER).lower()
    if provider == "gemini":
        from app.modules.ai.gateway.gemini import GeminiProvider

        return GeminiProvider()
    if provider == "anthropic":
        from app.modules.ai.gateway.anthropic import AnthropicProvider

        return AnthropicProvider()
    if provider == "openai":
        from app.modules.ai.gateway.openai import OpenAIProvider

        return OpenAIProvider()
    raise ValueError(f"Unknown AI provider: {provider!r}")


def default_model(provider: str | None = None) -> str:
    """Resolve the model to use: explicit config wins, else the provider's default."""
    provider = (provider or settings.AI_DEFAULT_PROVIDER).lower()
    return settings.AI_DEFAULT_MODEL or _DEFAULT_MODELS.get(provider, "")

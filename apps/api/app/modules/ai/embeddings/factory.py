"""Config-driven embedding-provider selection.

``EMBEDDING_PROVIDER`` picks the adapter; providers are added here without touching call sites.
OpenAI is the default; when its key is absent outside production we fall back to the offline
stub so local dev/tests work without a key (production requires a real key).
"""
from __future__ import annotations

from app.core.config import get_settings
from app.modules.ai.embeddings.base import EmbeddingProvider
from app.modules.ai.embeddings.stub_provider import StubEmbeddingProvider

settings = get_settings()


def get_embedding_provider(name: str | None = None) -> EmbeddingProvider:
    name = (name or settings.EMBEDDING_PROVIDER).lower()

    if name == "stub":
        return StubEmbeddingProvider()

    if name == "openai":
        if settings.OPENAI_API_KEY:
            from app.modules.ai.embeddings.openai_provider import OpenAIEmbeddingProvider

            return OpenAIEmbeddingProvider()
        if not settings.is_production:
            return StubEmbeddingProvider()  # offline dev/test fallback
        raise RuntimeError("OPENAI_API_KEY is required for the 'openai' embedding provider")

    # ollama / azure / gemini / sentence-transformers slot in here as they're added.
    raise ValueError(f"Unknown embedding provider: {name!r}")

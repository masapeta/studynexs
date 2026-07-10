"""OpenAI embedding provider — the StudyNexs default.

Exposes text-embedding-3-small (default) and -3-large. The SDK is imported lazily so the app
imports fine without it installed, matching the LLM-gateway adapter convention.
"""
from __future__ import annotations

from app.core.config import get_settings
from app.modules.ai.embeddings.base import EmbeddingModel, EmbeddingProvider, EmbeddingResult

settings = get_settings()


class OpenAIEmbeddingProvider(EmbeddingProvider):
    name = "openai"
    models = {
        "text-embedding-3-small": EmbeddingModel("text-embedding-3-small", 1536),
        "text-embedding-3-large": EmbeddingModel("text-embedding-3-large", 3072),
    }
    default_model_name = "text-embedding-3-small"

    async def embed(self, texts: list[str], *, model: str | None = None) -> EmbeddingResult:
        spec = self.resolve_model(model)
        if not texts:
            return EmbeddingResult([], self.name, spec.name, spec.dimensions, 0)

        from openai import AsyncOpenAI  # lazy import

        client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY, timeout=settings.AI_REQUEST_TIMEOUT_SECONDS
        )
        resp = await client.embeddings.create(model=spec.name, input=texts)
        # Preserve input order (OpenAI returns index-tagged data).
        ordered = sorted(resp.data, key=lambda d: d.index)
        vectors = [d.embedding for d in ordered]
        tokens = getattr(getattr(resp, "usage", None), "total_tokens", 0) or 0
        return EmbeddingResult(
            vectors=vectors,
            provider=self.name,
            model=spec.name,
            dimensions=spec.dimensions,
            tokens=tokens,
        )

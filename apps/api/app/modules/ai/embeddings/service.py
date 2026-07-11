"""EmbeddingService — the single door the RAG/Document-Intelligence platform embeds through.

Application code depends only on this service, never on a provider SDK. The provider is chosen
by config (or injected for tests). Each call emits a structured telemetry event so embedding
volume/cost is observable alongside the rest of the AI platform.
"""
from __future__ import annotations

import structlog

from app.modules.ai.embeddings.base import EmbeddingProvider, EmbeddingResult
from app.modules.ai.embeddings.factory import get_embedding_provider

logger = structlog.get_logger()


class EmbeddingService:
    def __init__(self, provider: EmbeddingProvider | None = None) -> None:
        # Dependency injection: tests/other providers pass one; default resolves from config.
        self._provider = provider or get_embedding_provider()

    @property
    def provider_name(self) -> str:
        return self._provider.name

    def dimensions(self, model: str | None = None) -> int:
        return self._provider.resolve_model(model).dimensions

    async def embed(
        self,
        texts: list[str],
        *,
        feature: str,
        model: str | None = None,
        school_id: str | None = None,
    ) -> EmbeddingResult:
        """Embed texts for a named feature (e.g. 'curriculum_ingest', 'qp_retrieval')."""
        result = await self._provider.embed(texts, model=model)
        logger.info(
            "embeddings_generated",
            feature=feature,
            provider=result.provider,
            model=result.model,
            dimensions=result.dimensions,
            count=len(texts),
            tokens=result.tokens,
            school_id=school_id,
        )
        return result

    async def embed_one(
        self, text: str, *, feature: str, model: str | None = None, school_id: str | None = None
    ) -> list[float]:
        result = await self.embed([text], feature=feature, model=model, school_id=school_id)
        return result.vectors[0]


async def embed_texts(
    texts: list[str], *, feature: str, model: str | None = None, school_id: str | None = None
) -> EmbeddingResult:
    """Convenience wrapper using a config-resolved provider."""
    return await EmbeddingService().embed(
        texts, feature=feature, model=model, school_id=school_id
    )

"""Shared, provider-agnostic embedding platform.

All RAG / Document-Intelligence code embeds text through ``EmbeddingService`` — never by
calling a provider SDK directly. Providers are pluggable and each provider exposes one or more
models (provider→model separation), so a new provider or model is a config change, not an
architectural one. Default: OpenAI ``text-embedding-3-small``.
"""

from app.modules.ai.embeddings.base import (
    EmbeddingModel,
    EmbeddingProvider,
    EmbeddingResult,
)
from app.modules.ai.embeddings.service import EmbeddingService, embed_texts

__all__ = [
    "EmbeddingModel",
    "EmbeddingProvider",
    "EmbeddingResult",
    "EmbeddingService",
    "embed_texts",
]

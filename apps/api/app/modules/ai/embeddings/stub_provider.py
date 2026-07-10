"""Deterministic offline embedding provider for tests and key-less local dev.

Same text → same unit vector; different text → different vector. No network, no cost — so RAG
and ingestion tests are meaningful without spending on a real embedding API.
"""
from __future__ import annotations

import hashlib
import math

from app.modules.ai.embeddings.base import EmbeddingModel, EmbeddingProvider, EmbeddingResult

_DIM = 64


class StubEmbeddingProvider(EmbeddingProvider):
    name = "stub"
    models = {"stub-embed": EmbeddingModel("stub-embed", _DIM)}
    default_model_name = "stub-embed"

    async def embed(self, texts: list[str], *, model: str | None = None) -> EmbeddingResult:
        spec = self.resolve_model(model)
        vectors = [self._vector(t, spec.dimensions) for t in texts]
        return EmbeddingResult(
            vectors=vectors,
            provider=self.name,
            model=spec.name,
            dimensions=spec.dimensions,
            tokens=sum(len(t.split()) for t in texts),
        )

    @staticmethod
    def _vector(text: str, dim: int) -> list[float]:
        # Seed a small LCG from the text hash, emit `dim` values in [-1, 1], unit-normalize.
        x = int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:8], "big") or 1
        vals: list[float] = []
        for _ in range(dim):
            x = (1103515245 * x + 12345) & 0x7FFFFFFF
            vals.append((x / 0x7FFFFFFF) * 2.0 - 1.0)
        norm = math.sqrt(sum(v * v for v in vals)) or 1.0
        return [v / norm for v in vals]

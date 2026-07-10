"""In-memory vector store for tests / key-less dev. Cosine similarity + hard school_id filter."""
from __future__ import annotations

import math
from typing import Any

from app.modules.ai.vectorstore.base import (
    VectorMatch,
    VectorPoint,
    VectorStore,
    match_payload,
)


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


class InMemoryVectorStore(VectorStore):
    def __init__(self) -> None:
        self._collections: dict[str, dict[str, VectorPoint]] = {}

    async def ensure_collection(self, name: str, *, dimensions: int) -> None:
        self._collections.setdefault(name, {})

    async def upsert(self, collection: str, points: list[VectorPoint]) -> int:
        store = self._collections.setdefault(collection, {})
        for p in points:
            if "school_id" not in p.payload:
                raise ValueError("vector payload must include school_id (tenant scope)")
            store[p.id] = p
        return len(points)

    async def search(
        self,
        collection: str,
        vector: list[float],
        *,
        school_id: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[VectorMatch]:
        required = {"school_id": school_id, **(filters or {})}
        store = self._collections.get(collection, {})
        scored = [
            VectorMatch(id=p.id, score=_cosine(vector, p.vector), payload=p.payload)
            for p in store.values()
            if match_payload(p.payload, required)
        ]
        scored.sort(key=lambda m: m.score, reverse=True)
        return scored[:top_k]

    async def delete(
        self, collection: str, *, school_id: str, filters: dict[str, Any] | None = None
    ) -> None:
        required = {"school_id": school_id, **(filters or {})}
        store = self._collections.get(collection, {})
        for pid in [pid for pid, p in store.items() if match_payload(p.payload, required)]:
            del store[pid]

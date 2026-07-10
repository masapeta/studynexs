"""Vector-store interface. Retrieval is tenant-scoped by construction: ``search`` takes a
required ``school_id`` and implementations must apply it as a hard filter."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class VectorPoint:
    """A vector to store. ``payload`` must carry ``school_id`` (and usually ``pack_id`` etc.)
    so retrieval can be tenant- and curriculum-scoped."""

    id: str
    vector: list[float]
    payload: dict[str, Any]


@dataclass
class VectorMatch:
    id: str
    score: float
    payload: dict[str, Any]


class VectorStore(ABC):
    @abstractmethod
    async def ensure_collection(self, name: str, *, dimensions: int) -> None:
        """Create the collection (cosine distance) if absent. Idempotent."""

    @abstractmethod
    async def upsert(self, collection: str, points: list[VectorPoint]) -> int:
        """Insert/replace points. Each point's payload must include ``school_id``. Returns count."""

    @abstractmethod
    async def search(
        self,
        collection: str,
        vector: list[float],
        *,
        school_id: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[VectorMatch]:
        """Nearest neighbours, ALWAYS restricted to ``school_id`` (plus any extra filters)."""

    @abstractmethod
    async def delete(
        self, collection: str, *, school_id: str, filters: dict[str, Any] | None = None
    ) -> None:
        """Delete points within a school (never cross-tenant)."""


def match_payload(payload: dict[str, Any], required: dict[str, Any]) -> bool:
    """Shared helper: does payload satisfy every key==value in ``required``?"""
    return all(payload.get(k) == v for k, v in required.items())

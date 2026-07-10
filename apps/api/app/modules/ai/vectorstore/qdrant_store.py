"""Qdrant-backed vector store. Cosine distance; every search is hard-filtered by school_id."""
from __future__ import annotations

import uuid
from typing import Any

from app.core.config import get_settings
from app.modules.ai.vectorstore.base import VectorMatch, VectorPoint, VectorStore

settings = get_settings()


def _point_id(raw: str) -> str:
    """Qdrant point ids must be UUIDs or uints; map arbitrary string ids to a stable UUID5."""
    try:
        return str(uuid.UUID(str(raw)))
    except ValueError:
        return str(uuid.uuid5(uuid.NAMESPACE_URL, str(raw)))


class QdrantVectorStore(VectorStore):
    def __init__(self) -> None:
        self._client = None

    def _get_client(self):
        if self._client is None:
            from qdrant_client import AsyncQdrantClient

            self._client = AsyncQdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT,
                api_key=settings.QDRANT_API_KEY or None,
            )
        return self._client

    async def ensure_collection(self, name: str, *, dimensions: int) -> None:
        from qdrant_client.models import Distance, VectorParams

        client = self._get_client()
        if not await client.collection_exists(name):
            await client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=dimensions, distance=Distance.COSINE),
            )

    async def upsert(self, collection: str, points: list[VectorPoint]) -> int:
        from qdrant_client.models import PointStruct

        if not points:
            return 0
        structs = []
        for p in points:
            if "school_id" not in p.payload:
                raise ValueError("vector payload must include school_id (tenant scope)")
            payload = {**p.payload, "ref_id": p.id}
            structs.append(PointStruct(id=_point_id(p.id), vector=p.vector, payload=payload))
        client = self._get_client()
        # wait=True so a retrieval immediately after ingestion is consistent.
        await client.upsert(collection_name=collection, points=structs, wait=True)
        return len(structs)

    def _filter(self, school_id: str, filters: dict[str, Any] | None):
        from qdrant_client.models import FieldCondition, Filter, MatchValue

        must = [FieldCondition(key="school_id", match=MatchValue(value=school_id))]
        for key, value in (filters or {}).items():
            must.append(FieldCondition(key=key, match=MatchValue(value=value)))
        return Filter(must=must)

    async def search(
        self,
        collection: str,
        vector: list[float],
        *,
        school_id: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[VectorMatch]:
        client = self._get_client()
        # A collection that was never created has nothing to return — treat it as empty rather
        # than letting Qdrant raise a 404 (this is the first-ever retrieval for a namespace,
        # before anything has been indexed).
        if not await client.collection_exists(collection):
            return []
        resp = await client.query_points(
            collection_name=collection,
            query=vector,
            query_filter=self._filter(school_id, filters),
            limit=top_k,
            with_payload=True,
        )
        return [
            VectorMatch(
                id=(pt.payload or {}).get("ref_id", str(pt.id)),
                score=pt.score,
                payload=pt.payload or {},
            )
            for pt in resp.points
        ]

    async def delete(
        self, collection: str, *, school_id: str, filters: dict[str, Any] | None = None
    ) -> None:
        from qdrant_client.models import FilterSelector

        client = self._get_client()
        if not await client.collection_exists(collection):
            return
        await client.delete(
            collection_name=collection,
            points_selector=FilterSelector(filter=self._filter(school_id, filters)),
        )

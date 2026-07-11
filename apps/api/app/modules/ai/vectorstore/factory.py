"""Config-driven vector-store selection + collection naming.

``VECTOR_STORE`` picks the backend (qdrant | memory). Collection names encode the embedding
provider and dimension because a Qdrant collection is fixed-dimension — switching embedding
models writes to a different collection rather than corrupting an existing one.
"""
from __future__ import annotations

import re

from app.core.config import get_settings
from app.modules.ai.vectorstore.base import VectorStore

settings = get_settings()


def get_vector_store(name: str | None = None) -> VectorStore:
    name = (name or settings.VECTOR_STORE).lower()
    if name == "memory":
        from app.modules.ai.vectorstore.memory_store import InMemoryVectorStore

        return InMemoryVectorStore()
    if name == "qdrant":
        from app.modules.ai.vectorstore.qdrant_store import QdrantVectorStore

        return QdrantVectorStore()
    raise ValueError(f"Unknown vector store: {name!r}")


def collection_name(namespace: str, provider: str, dimensions: int) -> str:
    """e.g. ('curriculum', 'openai', 1536) -> 'curriculum__openai__1536'.

    Tenancy is enforced by the mandatory school_id payload filter, not by collection — a single
    collection per (namespace, provider, dim) holds all schools' vectors, filtered on read.
    """
    ns = re.sub(r"[^a-z0-9]+", "_", namespace.lower()).strip("_")
    prov = re.sub(r"[^a-z0-9]+", "_", provider.lower()).strip("_")
    return f"{ns}__{prov}__{dimensions}"

"""Shared vector-store platform for RAG.

Provider-agnostic over the vector database (Qdrant today). Retrieval is ALWAYS tenant-scoped:
``search`` requires a ``school_id`` and every backend enforces it as a hard filter, so one
school can never retrieve another's vectors (the sacred multi-tenant rule extends into RAG).
"""

from app.modules.ai.vectorstore.base import VectorMatch, VectorPoint, VectorStore
from app.modules.ai.vectorstore.factory import collection_name, get_vector_store

__all__ = [
    "VectorMatch",
    "VectorPoint",
    "VectorStore",
    "collection_name",
    "get_vector_store",
]

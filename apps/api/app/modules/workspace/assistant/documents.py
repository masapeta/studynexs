"""Document knowledge provider — the DOCUMENT route's authoritative seam (spec §9, §10).

School policy/handbook/rules retrieval is unstructured knowledge, distinct from live
ERP data. This defines the tenant-scoped interface and a concrete provider. There is
no school-policy document store yet, so the default provider is honest: it reports the
knowledge base is not configured rather than inventing policy (spec §9: "do not pretend").

When a policy store is added (ingested docs with metadata + embeddings), implement a
provider here that retrieves from it — no caller changes needed.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class DocumentCitation:
    document_id: str
    title: str
    document_type: str | None = None
    snippet: str | None = None
    effective_from: str | None = None
    version: str | None = None


@dataclass(frozen=True)
class DocumentAnswer:
    """Result of a document-knowledge lookup. ``configured`` distinguishes 'no store'
    from 'store exists but no match'."""

    query: str
    configured: bool
    citations: list[DocumentCitation] = field(default_factory=list)
    context_text: str = ""

    @property
    def has_matches(self) -> bool:
        return bool(self.citations)


class DocumentKnowledgeProvider(Protocol):
    async def search(
        self, *, school_id: uuid.UUID, query: str, top_k: int = 5
    ) -> DocumentAnswer: ...


class NullDocumentProvider:
    """Default: no policy knowledge base is configured for the tenant yet."""

    async def search(
        self, *, school_id: uuid.UUID, query: str, top_k: int = 5
    ) -> DocumentAnswer:
        return DocumentAnswer(query=query, configured=False)


def get_document_provider() -> DocumentKnowledgeProvider:
    """Factory — swap in a real (RAG-backed) provider once a policy store exists."""
    return NullDocumentProvider()

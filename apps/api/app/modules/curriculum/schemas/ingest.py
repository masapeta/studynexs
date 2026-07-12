"""Document Intelligence ingest schemas — pack-scoped document upload indexing."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.db.models.document_ingestion import DocumentType, IngestStatus

DocTypeLiteral = Literal["worksheet", "circular", "notes", "other"]


class IngestDocumentIn(BaseModel):
    file_id: uuid.UUID
    doc_type: DocTypeLiteral = "notes"


class IngestDocumentOut(BaseModel):
    id: uuid.UUID
    pack_id: uuid.UUID
    file_id: uuid.UUID
    doc_type: DocumentType
    status: IngestStatus
    version: int
    chunks_indexed: int
    source_name: str
    error_message: str | None = None

    model_config = {"from_attributes": True}


class IngestionSummaryOut(BaseModel):
    id: uuid.UUID
    file_id: uuid.UUID
    doc_type: DocumentType
    status: IngestStatus
    version: int
    chunks_indexed: int
    source_name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class IngestStatusOut(BaseModel):
    indexed_topic_count: int
    indexed_document_chunks: int
    last_ingested_at: datetime | None = None
    recent_ingestions: list[IngestionSummaryOut] = Field(default_factory=list)

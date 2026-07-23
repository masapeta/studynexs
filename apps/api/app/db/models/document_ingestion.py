"""Document ingestion audit — tracks OCR/chunk/embed/index runs per pack (Batch 16)."""
from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import BaseModel


class DocumentType(str, enum.Enum):
    WORKSHEET = "worksheet"
    CIRCULAR = "circular"
    NOTES = "notes"
    OTHER = "other"


class IngestStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentIngestion(BaseModel):
    __tablename__ = "document_ingestions"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    pack_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("curriculum_packs.id"), nullable=False
    )
    file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("uploaded_files.id"), nullable=False
    )
    doc_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    status: Mapped[IngestStatus] = mapped_column(
        Enum(IngestStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=IngestStatus.PENDING,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    chunks_indexed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_name: Mapped[str] = mapped_column(String(300), nullable=False)
    ingested_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    __table_args__ = (
        Index("ix_doc_ingest_school_pack", "school_id", "pack_id"),
        Index("ix_doc_ingest_pack_file", "pack_id", "file_id"),
    )

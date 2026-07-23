"""Content Review Queue — AI-drafted or gap content awaiting teacher approval (Batch 20)."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import BaseModel


class ContentReviewItemType(str, enum.Enum):
    CONCEPT_CARD_GAP = "concept_card_gap"
    DOCUMENT_INGEST = "document_ingest"


class ContentReviewStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ContentReviewSource(str, enum.Enum):
    TUTOR_GAP = "tutor_gap"
    DOCUMENT_INGEST = "document_ingest"
    TEACHER = "teacher"


class ContentReviewItem(BaseModel):
    __tablename__ = "content_review_items"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    pack_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("curriculum_packs.id", ondelete="CASCADE"), nullable=False
    )
    item_type: Mapped[ContentReviewItemType] = mapped_column(
        Enum(ContentReviewItemType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    status: Mapped[ContentReviewStatus] = mapped_column(
        Enum(ContentReviewStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ContentReviewStatus.PENDING,
    )
    source: Mapped[ContentReviewSource] = mapped_column(
        Enum(ContentReviewSource, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    concept_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("curriculum_concepts.id", ondelete="SET NULL"),
        nullable=True,
    )
    source_ref_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    draft_payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    result_card_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("concept_cards.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_content_review_school_pack_status", "school_id", "pack_id", "status"),
        Index("ix_content_review_concept", "school_id", "concept_id"),
    )

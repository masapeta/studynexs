"""ConceptCard — teacher-approved explanation unit for tutor grounding (Batch 18)."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import BaseModel


class ConceptCardStatus(str, enum.Enum):
    DRAFT = "draft"
    APPROVED = "approved"


class ConceptCard(BaseModel):
    __tablename__ = "concept_cards"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    pack_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("curriculum_packs.id", ondelete="CASCADE"), nullable=False
    )
    concept_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("curriculum_concepts.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    examples: Mapped[list | None] = mapped_column(JSONB)
    hints: Mapped[list | None] = mapped_column(JSONB)
    visual_kind: Mapped[str] = mapped_column(String(50), nullable=False, default="generic")
    status: Mapped[ConceptCardStatus] = mapped_column(
        Enum(ConceptCardStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ConceptCardStatus.DRAFT,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("school_id", "concept_id", name="uq_concept_card_per_concept"),
        Index("ix_concept_cards_school_pack", "school_id", "pack_id"),
        Index("ix_concept_cards_concept", "concept_id"),
    )

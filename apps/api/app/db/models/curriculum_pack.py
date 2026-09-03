"""Curriculum models — the school's structured, versioned syllabus (the moat).

A CurriculumPack is per school × class × subject × academic year × book edition.
It holds a Chapter → Topic tree (concepts as a lightweight JSONB list for now) and
an exam blueprint. Drafts are editable; once a class-incharge/HOD APPROVES a pack it
becomes immutable — changes require a new version (annual rollover). Question papers,
evaluation and mastery will reference packs instead of free-text topics.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import BaseModel


class PackStatus(str, enum.Enum):
    DRAFT = "draft"        # editable
    APPROVED = "approved"  # immutable; change = new version


class CurriculumPack(BaseModel):
    __tablename__ = "curriculum_packs"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False
    )
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=False
    )
    board: Mapped[str] = mapped_column(String(50), nullable=False)
    book_title: Mapped[str | None] = mapped_column(String(200))
    publisher: Mapped[str | None] = mapped_column(String(150))
    edition: Mapped[str | None] = mapped_column(String(50))
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[PackStatus] = mapped_column(
        SAEnum(PackStatus), nullable=False, default=PackStatus.DRAFT
    )
    # Exam blueprint as data: [{"title","marks_per_q","count","type","answer_any"?}]
    blueprint: Mapped[list | None] = mapped_column(JSONB)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # RAG publish status — set on approve via RagService.index_pack (Batch 1 reconciliation).
    rag_indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rag_index_topic_count: Mapped[int | None] = mapped_column(Integer)
    rag_index_error: Mapped[str | None] = mapped_column(String(500))

    __table_args__ = (
        UniqueConstraint(
            "school_id", "class_id", "subject_id", "academic_year_id", "version",
            name="uq_pack_scope_version",
        ),
        Index("ix_packs_school_scope", "school_id", "class_id", "subject_id", "academic_year_id"),
    )


class CurriculumChapter(BaseModel):
    __tablename__ = "curriculum_chapters"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    pack_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("curriculum_packs.id", ondelete="CASCADE"), nullable=False
    )
    number: Mapped[str | None] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (Index("ix_chapters_pack", "pack_id"),)


class CurriculumTopic(BaseModel):
    __tablename__ = "curriculum_topics"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    chapter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("curriculum_chapters.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Lightweight concept list; a first-class Concept/ConceptCard table is a later slice.
    concepts: Mapped[list | None] = mapped_column(JSONB)

    __table_args__ = (Index("ix_topics_chapter", "chapter_id"),)


class CurriculumLearningOutcome(BaseModel):
    """Structured learning outcome attached to a topic or chapter within a pack."""

    __tablename__ = "curriculum_learning_outcomes"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    topic_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("curriculum_topics.id", ondelete="CASCADE")
    )
    chapter_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("curriculum_chapters.id", ondelete="CASCADE")
    )
    code: Mapped[str | None] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(String(1000), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        Index("ix_learning_outcomes_topic", "topic_id"),
        Index("ix_learning_outcomes_chapter", "chapter_id"),
    )


class CurriculumPackAuditEvent(BaseModel):
    """Append-only audit trail for CurriculumPack lifecycle (Batch 1 reconciliation)."""

    __tablename__ = "curriculum_pack_audit_events"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    pack_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("curriculum_packs.id", ondelete="CASCADE"), nullable=False
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    event_metadata: Mapped[dict | None] = mapped_column(JSONB)

    __table_args__ = (
        Index("ix_pack_audit_school_pack", "school_id", "pack_id"),
        Index("ix_pack_audit_pack_created", "pack_id", "created_at"),
    )

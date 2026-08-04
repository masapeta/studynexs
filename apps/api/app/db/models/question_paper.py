"""AI-generated question paper — drafted by the LLM, then edited & approved by a teacher.

Board / grade / subject / blueprint are stored as DATA (not hardcoded), so the same
engine serves any board or grade — only the inputs change.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import BaseModel
from app.db.models.examination import ExamType


class PaperStatus(str, enum.Enum):
    """Approval workflow — AI credits are charged at generation, not approval."""

    DRAFT = "draft"                      # AI-generated
    EDITED = "edited"                    # teacher saved edits
    PENDING_APPROVAL = "pending_approval"  # submitted to incharge/HOD
    APPROVED = "approved"                # incharge signed off
    REJECTED = "rejected"                # reusable after edit/clone; banked on re-approve
    PUBLISHED = "published"              # used in exam / handed out
    ARCHIVED = "archived"                # retired copy


# Statuses where the paper body must not change.
_LOCKED_STATUSES = frozenset(
    {
        PaperStatus.PENDING_APPROVAL,
        PaperStatus.APPROVED,
        PaperStatus.PUBLISHED,
        PaperStatus.ARCHIVED,
    }
)

# Awaiting teacher submit or incharge decision.
_OPEN_REVIEW_STATUSES = frozenset(
    {PaperStatus.DRAFT, PaperStatus.EDITED, PaperStatus.PENDING_APPROVAL, PaperStatus.REJECTED}
)

# Teacher-owned papers not yet submitted for approval.
_TEACHER_SUBMIT_STATUSES = frozenset({PaperStatus.DRAFT, PaperStatus.EDITED, PaperStatus.REJECTED})

# Papers incharge should review (includes legacy drafts not yet submitted).
_INCHARGE_REVIEW_STATUSES = frozenset(
    {PaperStatus.DRAFT, PaperStatus.EDITED, PaperStatus.PENDING_APPROVAL}
)


class QuestionPaper(BaseModel):
    __tablename__ = "question_papers"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    # Curriculum grounding (Assessment Intelligence): when set, the paper was generated from a
    # school's APPROVED CurriculumPack via RAG retrieval — every question is grounded and cited.
    # Nullable so legacy / free-text papers (grounded=False) remain valid.
    pack_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("curriculum_packs.id"), nullable=True
    )
    grounded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Ordered citation sources aligned with per-question `citations` indices:
    # [{"index": 1, "chapter": "...", "topic": "...", "ref_id": "..."}]
    grounding_sources: Mapped[list | None] = mapped_column(JSONB)
    # Populated only for the feature-flagged, authorized ungrounded Studio exception. The
    # creator is the authorizing actor; the reason makes the exception reviewable/auditable.
    ungrounded_reason: Mapped[str | None] = mapped_column(Text)

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    board: Mapped[str] = mapped_column(String(50), nullable=False)          # e.g. "SSC"
    grade: Mapped[str] = mapped_column(String(20), nullable=False)          # e.g. "Class 10"
    subject_name: Mapped[str] = mapped_column(String(100), nullable=False)  # snapshot for display
    # Shared with Exam so the authored paper and its eventual assessment use one canonical type.
    exam_type: Mapped[ExamType] = mapped_column(
        Enum(ExamType), nullable=False, default=ExamType.UNIT_TEST
    )
    total_marks: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    duration_minutes: Mapped[int | None] = mapped_column(Integer)
    topics: Mapped[list | None] = mapped_column(JSONB)            # list[str]
    difficulty_mix: Mapped[dict | None] = mapped_column(JSONB)   # {"easy":40,"medium":40,"hard":20}
    general_instructions: Mapped[str | None] = mapped_column(Text)
    # sections = paper body: list of {title, instructions, questions:[{number,text,marks,type,...}]}
    sections: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    status: Mapped[PaperStatus] = mapped_column(
        Enum(PaperStatus, values_callable=lambda x: [e.value for e in x]),
        default=PaperStatus.DRAFT,
        nullable=False,
    )
    ai_model: Mapped[str | None] = mapped_column(String(100))    # which model drafted it
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejected_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejection_reason: Mapped[str | None] = mapped_column(Text)

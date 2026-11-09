"""Answer sheet evaluation — AI-suggested marks with teacher HITL approval."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import BaseModel

# P-R4: server-side answer-sheet page limits.
MAX_ANSWER_SHEET_PAGES = 12
MAX_ANSWER_SHEET_TOTAL_BYTES = 60 * 1024 * 1024

REVISION_KIND_APPROVED = "approved"
REVISION_KIND_REOPENED = "reopened"

# String statuses — extend without PG enum migration.
EVAL_STATUS_PENDING = "pending"
EVAL_STATUS_PROCESSING = "processing"
EVAL_STATUS_SUGGESTED = "suggested"
EVAL_STATUS_APPROVED = "approved"
EVAL_STATUS_FAILED = "failed"


class AnswerSheetEvaluation(BaseModel):
    """One student's answer sheet evaluated against an exam linked to an AI paper."""

    __tablename__ = "answer_sheet_evaluations"
    __table_args__ = (
        UniqueConstraint("exam_id", "student_id", name="uq_eval_exam_student"),
        UniqueConstraint("school_id", "id", name="uq_answer_sheet_evaluations_school_id_id"),
        Index("ix_eval_school_exam", "school_id", "exam_id"),
        Index("ix_eval_school_status", "school_id", "status"),
    )

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    exam_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exams.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), nullable=False
    )
    file_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("uploaded_files.id"), nullable=True
    )
    job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=True
    )
    # Answers supplied by teacher or merged from vision OCR before grading.
    input_answers: Mapped[dict | None] = mapped_column(JSONB)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=EVAL_STATUS_PENDING)
    # {qno: {marks_suggested, max_marks, feedback, confidence, student_answer}}
    ai_suggestions: Mapped[dict | None] = mapped_column(JSONB)
    correction_summary: Mapped[str | None] = mapped_column(Text)
    # {qno: {marks, feedback, reason}}
    teacher_overrides: Mapped[dict | None] = mapped_column(JSONB)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)


class AnswerSheetEvaluationRevision(BaseModel):
    """Append-only history of an evaluation: every approval and every reopen (plan §5.1 M2).

    Result versions created from an AI evaluation point at the ``approved`` revision that
    produced them, which is how learner-facing misconceptions prove their provenance.
    """

    __tablename__ = "answer_sheet_evaluation_revisions"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    evaluation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    revision_no: Mapped[int] = mapped_column(Integer, nullable=False)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    ai_suggestions: Mapped[dict | None] = mapped_column(JSONB)
    teacher_overrides: Mapped[dict | None] = mapped_column(JSONB)
    input_answers: Mapped[dict | None] = mapped_column(JSONB)
    page_file_ids: Mapped[list | None] = mapped_column(JSONB)
    question_marks: Mapped[dict | None] = mapped_column(JSONB)
    marks_obtained: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    correction_summary: Mapped[str | None] = mapped_column(Text)
    actor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    # {provider, model, prompt_version} when recorded in ai_suggestions metadata.
    model_info: Mapped[dict | None] = mapped_column(JSONB)

    __table_args__ = (
        UniqueConstraint("evaluation_id", "revision_no", name="uq_eval_revision_no"),
        UniqueConstraint("school_id", "id", name="uq_eval_revisions_school_id_id"),
        ForeignKeyConstraint(
            ["school_id", "evaluation_id"],
            ["answer_sheet_evaluations.school_id", "answer_sheet_evaluations.id"],
            name="fk_eval_revision_evaluation",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["school_id", "actor_id"],
            ["users.school_id", "users.id"],
            name="fk_eval_revision_actor",
        ),
        CheckConstraint(
            f"kind IN ('{REVISION_KIND_APPROVED}', '{REVISION_KIND_REOPENED}')",
            name="ck_eval_revision_kind",
        ),
        CheckConstraint(
            "kind <> 'reopened' OR reason IS NOT NULL", name="ck_eval_revision_reopen_reason"
        ),
        Index("ix_eval_revisions_school_eval", "school_id", "evaluation_id"),
    )


class AnswerSheetPage(BaseModel):
    """Ordered pages of a multi-page answer sheet (plan §15, P-R4 limits enforced in service)."""

    __tablename__ = "answer_sheet_pages"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    evaluation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    file_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    page_no: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint("evaluation_id", "page_no", name="uq_answer_sheet_page_no"),
        UniqueConstraint("evaluation_id", "file_id", name="uq_answer_sheet_page_file"),
        ForeignKeyConstraint(
            ["school_id", "evaluation_id"],
            ["answer_sheet_evaluations.school_id", "answer_sheet_evaluations.id"],
            name="fk_answer_sheet_page_evaluation",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["school_id", "file_id"],
            ["uploaded_files.school_id", "uploaded_files.id"],
            name="fk_answer_sheet_page_file",
        ),
        CheckConstraint(
            f"page_no BETWEEN 1 AND {MAX_ANSWER_SHEET_PAGES}", name="ck_answer_sheet_page_no"
        ),
    )

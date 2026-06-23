"""Answer sheet evaluation — AI-suggested marks with teacher HITL approval."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import BaseModel

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

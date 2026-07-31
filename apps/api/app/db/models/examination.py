"""Examination models — Exam definitions and student marks."""
from __future__ import annotations

import enum
import uuid
from datetime import date

from sqlalchemy import (
    Boolean,
    Date,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import BaseModel


class ExamType(str, enum.Enum):
    UNIT_TEST = "unit_test"
    FORMATIVE_ASSESSMENT = "formative_assessment"
    SUMMATIVE_ASSESSMENT = "summative_assessment"
    MID_TERM = "mid_term"
    FINAL = "final"
    ASSIGNMENT = "assignment"
    QUIZ = "quiz"
    # SSC-style assessments — added for topic-mastery tracking
    SLIP_TEST = "slip_test"
    QUARTERLY = "quarterly"
    HALF_YEARLY = "half_yearly"


class Exam(BaseModel):
    __tablename__ = "exams"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False
    )
    exam_type: Mapped[ExamType] = mapped_column(Enum(ExamType), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    total_marks: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    date: Mapped[date | None] = mapped_column(Date)
    # Whole-exam chapter/topic tag — slip/unit tests map 1:1 to a chapter.
    topic: Mapped[str | None] = mapped_column(String(120))
    # [{"no": "1", "max_marks": 4, "topic": "Algebra"}] — single source of truth for
    # per-question max marks + topic mapping; re-tagging here retroactively fixes
    # topic attribution without touching mark rows. Takes precedence over `topic`.
    question_schema: Mapped[list | None] = mapped_column(JSONB)
    # Set when question schema is imported from an approved AI question paper.
    source_paper_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("question_papers.id"), nullable=True
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )


class ExamMark(BaseModel):
    __tablename__ = "exam_marks"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    exam_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exams.id"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), nullable=False
    )
    marks_obtained: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    # {"1": 3.5, "2": 4} question-no -> marks; absent key = unattempted (internal
    # choice). When present, marks_obtained is server-derived as the sum.
    question_marks: Mapped[dict | None] = mapped_column(JSONB)
    grade_letter: Mapped[str | None] = mapped_column(String(5))
    remarks: Mapped[str | None] = mapped_column(Text)
    ai_feedback: Mapped[str | None] = mapped_column(Text)
    ai_graded: Mapped[bool] = mapped_column(Boolean, default=False)
    # Provenance: the approved answer-sheet evaluation this mark was finalized from.
    # Nullable — manually entered marks have no evaluation. Links the authoritative
    # mark back to its full HITL trail (AI suggestions, teacher overrides, approver).
    source_evaluation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("answer_sheet_evaluations.id", ondelete="SET NULL"),
        nullable=True,
    )

    __table_args__ = (
        UniqueConstraint("exam_id", "student_id", name="uq_exam_student"),
        Index("ix_exam_marks_school_student", "school_id", "student_id"),
    )

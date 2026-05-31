"""AI-generated question paper — drafted by the LLM, then edited & approved by a teacher.

Board / grade / subject / blueprint are stored as DATA (not hardcoded), so the same
engine serves any board or grade — only the inputs change.
"""
from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import BaseModel


class PaperStatus(str, enum.Enum):
    DRAFT = "draft"        # AI-generated, awaiting teacher review
    APPROVED = "approved"  # teacher reviewed/edited and signed off (human-in-the-loop gate)


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

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    board: Mapped[str] = mapped_column(String(50), nullable=False)          # e.g. "SSC"
    grade: Mapped[str] = mapped_column(String(20), nullable=False)          # e.g. "Class 10"
    subject_name: Mapped[str] = mapped_column(String(100), nullable=False)  # snapshot for display
    total_marks: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    duration_minutes: Mapped[int | None] = mapped_column(Integer)
    topics: Mapped[list | None] = mapped_column(JSONB)            # list[str]
    difficulty_mix: Mapped[dict | None] = mapped_column(JSONB)   # {"easy":40,"medium":40,"hard":20}
    general_instructions: Mapped[str | None] = mapped_column(Text)
    # sections = paper body: list of {title, instructions, questions:[{number,text,marks,type,...}]}
    sections: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    status: Mapped[PaperStatus] = mapped_column(
        Enum(PaperStatus), default=PaperStatus.DRAFT, nullable=False
    )
    ai_model: Mapped[str | None] = mapped_column(String(100))    # which model drafted it

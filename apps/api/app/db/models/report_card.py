"""Report card — consolidated marks + attendance + an AI-drafted remark, teacher-approved."""
from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import BaseModel


class ReportStatus(str, enum.Enum):
    DRAFT = "draft"        # consolidated + AI remark drafted, awaiting teacher review
    APPROVED = "approved"  # teacher reviewed/edited the remark and signed off


class ReportCard(BaseModel):
    __tablename__ = "report_cards"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), nullable=False
    )
    class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    title: Mapped[str] = mapped_column(String(150), nullable=False)
    student_name: Mapped[str] = mapped_column(String(200), nullable=False)  # snapshot
    class_name: Mapped[str] = mapped_column(String(50), nullable=False)     # snapshot
    # subjects = [{subject, marks_obtained, total_marks}] consolidated across the term's exams
    subjects: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    total_obtained: Mapped[float] = mapped_column(Numeric(8, 2), default=0)
    total_max: Mapped[float] = mapped_column(Numeric(8, 2), default=0)
    percentage: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    overall_grade: Mapped[str | None] = mapped_column(String(5))
    attendance_percentage: Mapped[float | None] = mapped_column(Numeric(5, 2))
    ai_remark: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ReportStatus] = mapped_column(
        Enum(ReportStatus), default=ReportStatus.DRAFT, nullable=False
    )
    ai_model: Mapped[str | None] = mapped_column(String(100))

    __table_args__ = (
        Index("ix_report_cards_school_class", "school_id", "class_id"),
    )

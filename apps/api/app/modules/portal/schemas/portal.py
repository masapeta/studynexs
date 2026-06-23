"""Portal home schemas — parent, student, teacher-facing summaries."""
from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, Field


class ChildSummaryOut(BaseModel):
    student_id: uuid.UUID
    name: str
    class_label: str
    roll_no: Optional[str] = None
    attendance_pct: Optional[float] = None
    fee_pending: float = 0
    weak_topic_count: int = 0


class PortalContextOut(BaseModel):
    portal: str  # staff | teacher | parent | student
    role: str
    children: list[ChildSummaryOut] = Field(default_factory=list)
    student_id: Optional[uuid.UUID] = None
    student_name: Optional[str] = None
    class_label: Optional[str] = None


class FeatureTeaserOut(BaseModel):
    id: str
    title: str
    description: str
    status: str  # live | preview | coming_soon
    href: Optional[str] = None

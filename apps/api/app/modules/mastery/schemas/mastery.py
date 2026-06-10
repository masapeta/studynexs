"""Mastery schemas."""

import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.mastery import FlagSeverity, FlagStatus, MasteryTrend


class TopicMasteryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    topic: str
    topic_display: str
    mastery_pct: float
    class_avg_pct: Optional[float] = None
    assessments_count: int
    last_assessed_on: Optional[date] = None
    trend: MasteryTrend
    history: list[dict] = []


class SubjectMasteryOut(BaseModel):
    subject_id: uuid.UUID
    subject_name: str
    class_id: uuid.UUID
    topics: list[TopicMasteryOut]


class MasteryProfileOut(BaseModel):
    student_id: uuid.UUID
    subjects: list[SubjectMasteryOut]


class HeatmapCellOut(BaseModel):
    student_id: uuid.UUID
    student_name: str
    roll_no: Optional[str] = None
    topics: dict[str, float]  # topic_display -> mastery_pct


class ClassHeatmapOut(BaseModel):
    class_id: uuid.UUID
    subject_id: uuid.UUID
    topic_columns: list[str]  # topic_display, ordered
    students: list[HeatmapCellOut]


class RecomputeRequest(BaseModel):
    class_id: uuid.UUID
    subject_id: uuid.UUID


class RecomputeResponse(BaseModel):
    rows_upserted: int = Field(..., ge=0)


class FlagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    student_id: uuid.UUID
    class_id: uuid.UUID
    subject_id: uuid.UUID
    topic: str
    topic_display: str
    severity: FlagSeverity
    status: FlagStatus
    reasons: list[str]
    evidence: dict
    narrative: Optional[str] = None
    ai_model: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    dismissed_reason: Optional[str] = None
    notified_at: Optional[datetime] = None
    created_at: datetime
    # Joined display fields (not on the model)
    student_name: Optional[str] = None
    class_name: Optional[str] = None
    subject_name: Optional[str] = None


class NarrativeUpdate(BaseModel):
    narrative: str = Field(..., min_length=1, max_length=2000)


class DismissRequest(BaseModel):
    reason: Optional[str] = Field(None, max_length=300)


class NotifyResponse(BaseModel):
    flag: FlagOut
    parents_notified: int


class DigestEntryOut(BaseModel):
    student_id: uuid.UUID
    student_name: str
    flags: list[FlagOut]


class DigestOut(BaseModel):
    class_id: Optional[uuid.UUID] = None
    generated_on: date
    students: list[DigestEntryOut]

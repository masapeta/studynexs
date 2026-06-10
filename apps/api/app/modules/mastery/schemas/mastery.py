"""Mastery schemas."""

import uuid
from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.mastery import MasteryTrend


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

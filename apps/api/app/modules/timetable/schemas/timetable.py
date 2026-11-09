"""Timetable schemas."""

import uuid
from datetime import time as time_type

from pydantic import BaseModel, ConfigDict, field_validator

from app.db.models.timetable import DayOfWeek


class TimetableSlotCreate(BaseModel):
    class_id: uuid.UUID
    subject_id: uuid.UUID
    teacher_id: uuid.UUID
    day_of_week: DayOfWeek
    period_number: int
    start_time: str  # "08:30"
    end_time: str    # "09:15"


class ClassSubjectTeacherOut(BaseModel):
    """A teacher mapped to teach a subject in a class — minimal fields for slot editing."""

    teacher_id: uuid.UUID
    full_name: str
    subject_id: uuid.UUID


class TimetableSlotOut(BaseModel):
    id: uuid.UUID
    class_id: uuid.UUID
    subject_id: uuid.UUID
    teacher_id: uuid.UUID
    day_of_week: DayOfWeek
    period_number: int
    start_time: str
    end_time: str

    teacher_name: str | None = None
    subject_name: str | None = None

    @field_validator("start_time", "end_time", mode="before")
    @classmethod
    def _coerce_time(cls, v):
        # DB stores these as datetime.time; serialize to "HH:MM" for the API.
        return v.strftime("%H:%M") if isinstance(v, time_type) else v

    model_config = ConfigDict(from_attributes=True)

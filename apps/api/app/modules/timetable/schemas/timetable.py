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


class TimetableSlotOut(BaseModel):
    id: uuid.UUID
    class_id: uuid.UUID
    subject_id: uuid.UUID
    teacher_id: uuid.UUID
    day_of_week: DayOfWeek
    period_number: int
    start_time: str
    end_time: str

    @field_validator("start_time", "end_time", mode="before")
    @classmethod
    def _coerce_time(cls, v):
        # DB stores these as datetime.time; serialize to "HH:MM" for the API.
        return v.strftime("%H:%M") if isinstance(v, time_type) else v

    model_config = ConfigDict(from_attributes=True)

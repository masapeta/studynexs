"""Attendance schemas."""

import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.attendance import AttendanceStatus


class AttendanceEntry(BaseModel):
    student_id: uuid.UUID
    status: AttendanceStatus
    remarks: str | None = None


class BulkMarkRequest(BaseModel):
    class_id: uuid.UUID
    date: date
    entries: list[AttendanceEntry]


class AttendanceOut(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    class_id: uuid.UUID
    date: date
    status: AttendanceStatus
    marked_by: uuid.UUID
    remarks: str | None = None
    model_config = ConfigDict(from_attributes=True)


class AttendanceSummary(BaseModel):
    total: int
    present: int
    absent: int
    late: int
    half_day: int

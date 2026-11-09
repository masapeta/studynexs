"""Exam-result release + submissions + learner results contracts (plan Rev 2 §5.2–§5.4)."""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

ReleaseStatus = Literal["not_released", "released", "withdrawn", "blocked"]
ReleaseAction = Literal["release", "withdraw", "block", "unblock"]


class ReleaseEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_no: int
    generation_no: Optional[int] = None
    action: ReleaseAction
    actor_id: uuid.UUID
    actor_role: str
    reason: Optional[str] = None
    published_count: int
    pending_counts: dict[str, int] | None = None
    partial: bool
    prior_status: ReleaseStatus
    resulting_status: ReleaseStatus
    created_at: datetime


class ReleaseStateOut(BaseModel):
    status: ReleaseStatus
    current_generation_no: int
    published_count: int
    unpublished_changes_count: int
    pending: dict[str, int]
    blocked_reason: Optional[str] = None
    can_release: bool
    can_withdraw: bool
    can_override: bool
    history: list[ReleaseEventOut]


class ReleasePreviewOut(BaseModel):
    preview_token: str
    action_token: uuid.UUID
    preview_fingerprint: str
    expected_generation_no: int
    status: ReleaseStatus
    eligible_count: int
    changes_count: int
    pending: dict[str, int]
    pending_total: int
    expires_in_seconds: int


class ReleaseConfirmIn(BaseModel):
    preview_token: str = Field(min_length=20, max_length=2000)
    confirm_partial: bool = False
    acknowledged_pending_count: Optional[int] = Field(default=None, ge=0)


class ReleaseConfirmOut(BaseModel):
    no_changes: bool = False
    replayed: bool = False
    release: Optional[ReleaseEventOut] = None


class GovernedReleaseActionIn(BaseModel):
    reason: str = Field(min_length=3, max_length=500)
    # Client-generated idempotency key (double-click / retry safe).
    action_token: uuid.UUID


class SubmissionRow(BaseModel):
    student_id: uuid.UUID
    student_name: str
    roll_no: Optional[str] = None
    status: str
    evaluation_id: Optional[uuid.UUID] = None
    page_count: int = 0
    latest_version_no: Optional[int] = None
    published_version_no: Optional[int] = None
    changed_since_release: bool = False


class LearnerResultSummary(BaseModel):
    exam_id: uuid.UUID
    exam_title: str
    subject_name: Optional[str] = None
    exam_date: Optional[date] = None
    status: Literal["released", "pending"]
    marks_obtained: Optional[float] = None
    total_marks: Optional[float] = None
    percentage: Optional[float] = None
    grade_letter: Optional[str] = None
    published_at: Optional[datetime] = None


class LearnerResultDetail(LearnerResultSummary):
    question_marks: dict[str, Any] | None = None
    question_max_marks: dict[str, float] | None = None
    feedback: Optional[str] = None

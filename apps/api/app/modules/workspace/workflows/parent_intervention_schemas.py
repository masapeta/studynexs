"""IO contract for the Parent Intervention workflow (referenced by its WorkflowDefinition)."""
from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class ParentInterventionRequest(BaseModel):
    """Workflow input: which at-risk signal + threshold to intervene on."""

    reason: str = Field(default="low_attendance")
    attendance_threshold: float = Field(default=75.0, ge=1, le=100)


class InterventionDraftOut(BaseModel):
    draft_id: uuid.UUID
    student: str
    parent: str
    reason: str
    message: str
    status: str


class ParentInterventionOut(BaseModel):
    """Workflow output: the cohort of 1:1 drafts awaiting approval."""

    batch_id: uuid.UUID
    total_students: int
    total_recipients: int
    drafts: list[InterventionDraftOut] = Field(default_factory=list)

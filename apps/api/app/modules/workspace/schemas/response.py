"""Workspace response envelope for the Phase 0 teacher copilot."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.workspace.schemas.blocks import WorkspaceAction, WorkspaceBlock, WorkspaceCitation


class WorkspaceSchemaModel(BaseModel):
    """Shared strict base for workspace contracts."""

    model_config = ConfigDict(extra="forbid")


class WorkspaceMessage(WorkspaceSchemaModel):
    title: str = Field(..., max_length=120)
    summary: str = Field(..., max_length=400)
    tone: Literal["informative", "cautious", "blocked"]


class WorkspaceVerification(WorkspaceSchemaModel):
    status: Literal["verified", "stale", "missing", "conflicting", "requires_approval"]
    checked_at: datetime | None = None
    source_systems: list[str] = Field(default_factory=list)


class WorkspaceApproval(WorkspaceSchemaModel):
    required: bool = False
    reason: str | None = None


class WorkspaceRetention(WorkspaceSchemaModel):
    retention_class: Literal["ephemeral", "audit", "support_case"] = "ephemeral"


class WorkspaceSpeech(WorkspaceSchemaModel):
    speakable_summary: str
    language: str


class WorkspaceTelemetry(WorkspaceSchemaModel):
    used_model: str | None = None
    used_fallback: bool = False
    tool_calls: int = Field(default=0, ge=0)
    tool_failures: int = Field(default=0, ge=0)


class WorkspaceWarning(WorkspaceSchemaModel):
    code: str
    detail: str


class WorkspaceError(WorkspaceSchemaModel):
    code: str
    detail: str


class WorkspaceResponse(WorkspaceSchemaModel):
    schema_version: Literal["workspace.response.v1"] = "workspace.response.v1"
    request_id: uuid.UUID
    correlation_id: str
    mode: Literal["read"] = "read"
    message: WorkspaceMessage
    blocks: list[WorkspaceBlock] = Field(default_factory=list)
    citations: list[WorkspaceCitation] = Field(default_factory=list)
    actions: list[WorkspaceAction] = Field(default_factory=list)
    verification: WorkspaceVerification
    warnings: list[WorkspaceWarning] = Field(default_factory=list)
    errors: list[WorkspaceError] = Field(default_factory=list)
    approval: WorkspaceApproval = Field(default_factory=WorkspaceApproval)
    data_retention: WorkspaceRetention = Field(default_factory=WorkspaceRetention)
    speech: WorkspaceSpeech | None = None
    telemetry: WorkspaceTelemetry = Field(default_factory=WorkspaceTelemetry)

    @model_validator(mode="after")
    def _validate_first_slice_invariants(self) -> "WorkspaceResponse":
        if self.approval.required:
            raise ValueError("approval.required must be false in the first slice")
        if self.approval.reason is not None:
            raise ValueError("approval.reason must be null in the first slice")
        if self.speech is not None:
            raise ValueError("speech must be null in the first slice")
        return self

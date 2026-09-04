"""Tool metadata contracts for the Phase 0 teacher workspace."""

from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

ToolRole = Literal["teacher", "class_incharge"]
ToolSideEffectLevel = Literal["none", "workflow_request", "approval_required"]
ToolCachePolicy = Literal["no_cache", "per_turn", "short_ttl"]
ToolPiiLevel = Literal["none", "low", "medium", "high"]


class WorkspaceToolContext(BaseModel):
    """Backend-injected execution context for bounded read tools."""

    model_config = ConfigDict(extra="forbid")

    teacher_user_id: uuid.UUID
    school_id: uuid.UUID
    role: ToolRole
    tenant_slug: str
    correlation_id: str | None = None


class WorkspaceToolMetadata(BaseModel):
    """Static registry contract for first-slice read tools."""

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    name: str
    input_schema: type[BaseModel]
    output_schema: type[BaseModel]
    read_only: Literal[True] = True
    side_effect_level: Literal["none"] = "none"
    requires_human_confirmation: Literal[False] = False
    idempotency_key_required: Literal[False] = False
    allowed_roles: list[ToolRole] = Field(default_factory=list, min_length=1)
    scope_rule: str
    audit_event_type: str
    pii_level: ToolPiiLevel
    max_payload_size: int = Field(..., gt=0)
    tool_result_cache_policy: ToolCachePolicy
    timeout_ms: int = Field(..., gt=0)
    retry_count: int = Field(..., ge=0, le=1)
    circuit_breaker_threshold: int = Field(..., ge=1)
    circuit_breaker_cooldown_seconds: int = Field(..., ge=1)

    @field_validator("allowed_roles")
    @classmethod
    def _dedupe_allowed_roles(cls, value: list[ToolRole]) -> list[ToolRole]:
        seen: set[str] = set()
        deduped: list[ToolRole] = []
        for role in value:
            if role in seen:
                continue
            seen.add(role)
            deduped.append(role)
        if not deduped:
            raise ValueError("allowed_roles must contain at least one role")
        return deduped

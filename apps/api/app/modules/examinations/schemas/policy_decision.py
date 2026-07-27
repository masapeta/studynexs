"""Canonical PolicyDecision model for AEI v1.

Batch 4 introduces workflow policy decisions without marks, scoring, teacher-review
UI changes, database schema changes, or Evaluation Service integration.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

PolicyDecisionStatus = Literal["supported", "manual_review", "unsupported"]
PolicyCapabilityMode = Literal[
    "supported",
    "partial",
    "assist",
    "checklist",
    "manual_review",
    "unsupported",
]


class PolicyTraceEntry(BaseModel):
    """Structured trace entry for one Evaluation Policy decision."""

    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)

    policy: str
    status: Literal["executed", "skipped"]
    supported: bool
    decision: PolicyDecisionStatus | None = None
    metadata: Mapping[str, Any] = Field(default_factory=dict)

    @field_validator("metadata", mode="after")
    @classmethod
    def _freeze_metadata(cls, value: Mapping[str, Any]) -> Mapping[str, Any]:
        return _freeze_mapping(value)

    @field_serializer("metadata")
    def _serialize_metadata(self, value: Mapping[str, Any]) -> dict[str, Any]:
        return dict(value)


class PolicyDecision(BaseModel):
    """Immutable AEI workflow decision produced by Batch 4 policies."""

    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)

    decision: PolicyDecisionStatus
    manual_review_required: bool
    supported_capability: bool
    capability_mode: PolicyCapabilityMode | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    reason: str
    explanations: tuple[str, ...] = ()
    subject: str | None = None
    capability: str | None = None
    reasoning_type: str | None = None
    metadata: Mapping[str, Any] = Field(default_factory=dict)
    policy_trace: tuple[PolicyTraceEntry, ...] = ()

    @field_validator("metadata", mode="after")
    @classmethod
    def _freeze_metadata(cls, value: Mapping[str, Any]) -> Mapping[str, Any]:
        return _freeze_mapping(value)

    @field_serializer("metadata")
    def _serialize_metadata(self, value: Mapping[str, Any]) -> dict[str, Any]:
        return dict(value)


def _freeze_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(value))

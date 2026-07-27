"""Canonical TeacherReviewDecision model for AEI v1.

Batch 5 introduces the human governance contract on top of PolicyDecision. It
does not persist review decisions, integrate with Evaluation Service, change UI,
assign marks, or perform scoring.
"""

from __future__ import annotations

from datetime import datetime
from types import MappingProxyType
from typing import Any, Literal, Mapping

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)

from app.modules.examinations.schemas.policy_decision import PolicyDecision

ReviewStatus = Literal["PENDING", "UNDER_REVIEW", "APPROVED", "OVERRIDDEN", "REJECTED"]
REVIEW_STATUSES: tuple[ReviewStatus, ...] = (
    "PENDING",
    "UNDER_REVIEW",
    "APPROVED",
    "OVERRIDDEN",
    "REJECTED",
)
TERMINAL_REVIEW_STATUSES: set[ReviewStatus] = {"APPROVED", "OVERRIDDEN", "REJECTED"}
TEACHER_REVIEW_VERSION = "aei-teacher-review-v1"


class TeacherReviewDecision(BaseModel):
    """Immutable AEI teacher-review contract produced from a PolicyDecision."""

    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)

    review_status: ReviewStatus
    review_required: bool
    policy_decision: PolicyDecision
    approved_policy: PolicyDecision | None = None
    override_applied: bool = False
    override_reason: str | None = None
    reviewer_identifier: str | None = None
    review_timestamp: datetime | None = None
    audit_metadata: Mapping[str, Any] = Field(default_factory=dict)
    review_version: str = TEACHER_REVIEW_VERSION

    @field_validator("audit_metadata", mode="after")
    @classmethod
    def _freeze_audit_metadata(cls, value: Mapping[str, Any]) -> Mapping[str, Any]:
        return _freeze_mapping(value)

    @field_serializer("audit_metadata")
    def _serialize_audit_metadata(self, value: Mapping[str, Any]) -> dict[str, Any]:
        return dict(value)

    @model_validator(mode="after")
    def _validate_review_contract(self) -> "TeacherReviewDecision":
        if self.review_required != self.policy_decision.manual_review_required:
            raise ValueError("review_required must match the source PolicyDecision")

        if self.review_status in {"UNDER_REVIEW", *TERMINAL_REVIEW_STATUSES}:
            if not self.reviewer_identifier:
                raise ValueError("active or terminal teacher review requires reviewer_identifier")
            if self.review_timestamp is None:
                raise ValueError("active or terminal teacher review requires review_timestamp")

        if self.review_status == "APPROVED":
            if self.approved_policy != self.policy_decision:
                raise ValueError("approved reviews must approve the source PolicyDecision")
            if self.override_applied or self.override_reason:
                raise ValueError("approved reviews cannot contain override data")

        if self.review_status == "OVERRIDDEN":
            if self.approved_policy is not None:
                raise ValueError("overridden reviews cannot approve the source PolicyDecision")
            if not self.override_applied:
                raise ValueError("overridden reviews must set override_applied")
            if not self.override_reason or not self.override_reason.strip():
                raise ValueError("overridden reviews require a non-empty override_reason")

        if self.review_status == "REJECTED":
            if self.approved_policy is not None:
                raise ValueError("rejected reviews cannot approve the source PolicyDecision")
            if self.override_applied or self.override_reason:
                raise ValueError("rejected reviews cannot contain override data")

        return self

    @property
    def terminal(self) -> bool:
        """Return whether the review status represents a completed review."""

        return self.review_status in TERMINAL_REVIEW_STATUSES


def _freeze_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(value))

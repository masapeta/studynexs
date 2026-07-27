"""Teacher Review layer for AEI v1.

Batch 5 converts a PolicyDecision into a human review contract. It does not
inspect AcademicAnswer or AcademicReasoningResult, persist reviews, integrate
with Evaluation Service, change UI, assign marks, or perform scoring.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Mapping

from app.modules.examinations.schemas.policy_decision import PolicyDecision
from app.modules.examinations.schemas.teacher_review_decision import (
    TERMINAL_REVIEW_STATUSES,
    ReviewStatus,
    TeacherReviewDecision,
)


class TeacherReviewStateError(ValueError):
    """Raised when a teacher-review state transition is invalid."""


def create_teacher_review_decision(
    policy_decision: PolicyDecision,
    *,
    audit_metadata: dict[str, Any] | None = None,
) -> TeacherReviewDecision:
    """Create the initial teacher-review contract for a PolicyDecision."""

    return TeacherReviewDecision(
        review_status="PENDING",
        review_required=policy_decision.manual_review_required,
        policy_decision=policy_decision,
        audit_metadata=_merge_audit_metadata(
            None,
            {
                "review_source": "policy_decision",
                "policy_decision": policy_decision.decision,
                **(audit_metadata or {}),
            },
        ),
    )


def start_teacher_review(
    decision: TeacherReviewDecision,
    *,
    reviewer_identifier: str,
    review_timestamp: datetime | None = None,
    audit_metadata: dict[str, Any] | None = None,
) -> TeacherReviewDecision:
    """Move a pending review into active teacher review."""

    _ensure_transition(decision, allowed_from={"PENDING"}, target="UNDER_REVIEW")
    return _copy_review_decision(
        decision,
        {
            "review_status": "UNDER_REVIEW",
            "reviewer_identifier": reviewer_identifier,
            "review_timestamp": _timestamp(review_timestamp),
            "audit_metadata": _merge_audit_metadata(
                decision.audit_metadata,
                {"transition": "start_review", **(audit_metadata or {})},
            ),
        },
    )


def approve_teacher_review(
    decision: TeacherReviewDecision,
    *,
    reviewer_identifier: str,
    review_timestamp: datetime | None = None,
    audit_metadata: dict[str, Any] | None = None,
) -> TeacherReviewDecision:
    """Record teacher approval of the policy decision."""

    _ensure_transition(
        decision,
        allowed_from={"PENDING", "UNDER_REVIEW"},
        target="APPROVED",
    )
    return _copy_review_decision(
        decision,
        {
            "review_status": "APPROVED",
            "approved_policy": decision.policy_decision,
            "override_applied": False,
            "override_reason": None,
            "reviewer_identifier": reviewer_identifier,
            "review_timestamp": _timestamp(review_timestamp),
            "audit_metadata": _merge_audit_metadata(
                decision.audit_metadata,
                {"transition": "approve", **(audit_metadata or {})},
            ),
        },
    )


def override_teacher_review(
    decision: TeacherReviewDecision,
    *,
    override_reason: str,
    reviewer_identifier: str,
    review_timestamp: datetime | None = None,
    audit_metadata: dict[str, Any] | None = None,
) -> TeacherReviewDecision:
    """Record teacher override of the policy decision."""

    if not override_reason.strip():
        raise TeacherReviewStateError("Teacher override requires a non-empty reason")
    _ensure_transition(
        decision,
        allowed_from={"PENDING", "UNDER_REVIEW"},
        target="OVERRIDDEN",
    )
    return _copy_review_decision(
        decision,
        {
            "review_status": "OVERRIDDEN",
            "approved_policy": None,
            "override_applied": True,
            "override_reason": override_reason,
            "reviewer_identifier": reviewer_identifier,
            "review_timestamp": _timestamp(review_timestamp),
            "audit_metadata": _merge_audit_metadata(
                decision.audit_metadata,
                {"transition": "override", **(audit_metadata or {})},
            ),
        },
    )


def reject_teacher_review(
    decision: TeacherReviewDecision,
    *,
    reviewer_identifier: str,
    rejection_reason: str | None = None,
    review_timestamp: datetime | None = None,
    audit_metadata: dict[str, Any] | None = None,
) -> TeacherReviewDecision:
    """Record teacher rejection of the policy decision without applying an override."""

    _ensure_transition(
        decision,
        allowed_from={"PENDING", "UNDER_REVIEW"},
        target="REJECTED",
    )
    metadata = {"transition": "reject", **(audit_metadata or {})}
    if rejection_reason:
        metadata["rejection_reason"] = rejection_reason
    return _copy_review_decision(
        decision,
        {
            "review_status": "REJECTED",
            "approved_policy": None,
            "override_applied": False,
            "override_reason": None,
            "reviewer_identifier": reviewer_identifier,
            "review_timestamp": _timestamp(review_timestamp),
            "audit_metadata": _merge_audit_metadata(decision.audit_metadata, metadata),
        },
    )


def _ensure_transition(
    decision: TeacherReviewDecision,
    *,
    allowed_from: set[ReviewStatus],
    target: ReviewStatus,
) -> None:
    if decision.review_status in TERMINAL_REVIEW_STATUSES:
        raise TeacherReviewStateError(
            f"Cannot transition terminal review {decision.review_status} to {target}"
        )
    if decision.review_status not in allowed_from:
        raise TeacherReviewStateError(
            f"Cannot transition review {decision.review_status} to {target}"
        )


def _merge_audit_metadata(
    existing: Mapping[str, Any] | None,
    updates: dict[str, Any],
) -> dict[str, Any]:
    merged = dict(existing or {})
    merged.update(updates)
    return merged


def _timestamp(value: datetime | None) -> datetime:
    return value if value is not None else datetime.now(UTC)


def _copy_review_decision(
    decision: TeacherReviewDecision,
    update: dict[str, Any],
) -> TeacherReviewDecision:
    data = decision.model_dump()
    data.update(update)
    return TeacherReviewDecision.model_validate(data)

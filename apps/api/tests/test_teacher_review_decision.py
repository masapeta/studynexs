from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.modules.examinations.schemas.policy_decision import PolicyDecision
from app.modules.examinations.schemas.teacher_review_decision import (
    TEACHER_REVIEW_VERSION,
    TeacherReviewDecision,
)


def _policy_decision(
    *,
    decision: str = "manual_review",
    manual_review_required: bool = True,
) -> PolicyDecision:
    return PolicyDecision(
        decision=decision,
        manual_review_required=manual_review_required,
        supported_capability=True,
        reason="Policy requires teacher review.",
    )


def test_teacher_review_decision_is_assignment_protected():
    review = TeacherReviewDecision(
        review_status="PENDING",
        review_required=True,
        policy_decision=_policy_decision(),
    )

    with pytest.raises(ValidationError):
        review.review_status = "APPROVED"

    assert review.review_status == "PENDING"


def test_teacher_review_decision_audit_metadata_is_read_only():
    review = TeacherReviewDecision(
        review_status="PENDING",
        review_required=True,
        policy_decision=_policy_decision(),
        audit_metadata={"review_source": "policy_decision"},
    )

    with pytest.raises(TypeError):
        review.audit_metadata["review_source"] = "mutated"

    assert review.audit_metadata["review_source"] == "policy_decision"


def test_teacher_review_decision_rejects_unknown_top_level_fields():
    with pytest.raises(ValidationError):
        TeacherReviewDecision(
            review_status="PENDING",
            review_required=True,
            policy_decision=_policy_decision(),
            marks=1,
        )


def test_teacher_review_decision_requires_review_flag_to_match_policy():
    with pytest.raises(ValidationError):
        TeacherReviewDecision(
            review_status="PENDING",
            review_required=False,
            policy_decision=_policy_decision(manual_review_required=True),
        )


def test_teacher_review_decision_validates_approved_contract():
    policy = _policy_decision(decision="supported", manual_review_required=False)
    timestamp = datetime(2026, 7, 27, 9, 0, tzinfo=UTC)

    review = TeacherReviewDecision(
        review_status="APPROVED",
        review_required=False,
        policy_decision=policy,
        approved_policy=policy,
        reviewer_identifier="teacher:math-1",
        review_timestamp=timestamp,
    )

    assert review.terminal is True
    assert review.approved_policy == policy
    assert review.review_version == TEACHER_REVIEW_VERSION


def test_teacher_review_decision_rejects_impossible_override_contract():
    policy = _policy_decision()
    timestamp = datetime(2026, 7, 27, 9, 0, tzinfo=UTC)

    with pytest.raises(ValidationError):
        TeacherReviewDecision(
            review_status="OVERRIDDEN",
            review_required=True,
            policy_decision=policy,
            override_applied=True,
            override_reason="",
            reviewer_identifier="teacher:math-1",
            review_timestamp=timestamp,
        )


def test_teacher_review_decision_serializes_stably():
    policy = _policy_decision()
    timestamp = datetime(2026, 7, 27, 9, 0, tzinfo=UTC)
    original = TeacherReviewDecision(
        review_status="APPROVED",
        review_required=True,
        policy_decision=policy,
        approved_policy=policy,
        reviewer_identifier="teacher:math-1",
        review_timestamp=timestamp,
        audit_metadata={"transition": "approve"},
    )

    restored = TeacherReviewDecision.model_validate_json(original.model_dump_json())

    assert restored == original
    assert restored.policy_decision == policy
    assert restored.audit_metadata["transition"] == "approve"

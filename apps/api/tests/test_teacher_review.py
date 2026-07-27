from datetime import UTC, datetime

import pytest

from app.modules.examinations.schemas.policy_decision import PolicyDecision
from app.modules.examinations.services.teacher_review import (
    TeacherReviewStateError,
    approve_teacher_review,
    create_teacher_review_decision,
    override_teacher_review,
    reject_teacher_review,
    start_teacher_review,
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


def test_create_teacher_review_decision_from_policy_decision():
    policy = _policy_decision()

    review = create_teacher_review_decision(policy, audit_metadata={"source": "test"})

    assert review.review_status == "PENDING"
    assert review.review_required is True
    assert review.policy_decision == policy
    assert review.approved_policy is None
    assert review.audit_metadata["review_source"] == "policy_decision"
    assert review.audit_metadata["source"] == "test"
    assert "marks" not in review.model_dump()


def test_create_teacher_review_decision_preserves_non_required_policy_review_flag():
    policy = _policy_decision(decision="supported", manual_review_required=False)

    review = create_teacher_review_decision(policy)

    assert review.review_status == "PENDING"
    assert review.review_required is False


def test_start_teacher_review_moves_pending_to_under_review_without_mutating_original():
    timestamp = datetime(2026, 7, 27, 9, 0, tzinfo=UTC)
    review = create_teacher_review_decision(_policy_decision())

    active = start_teacher_review(
        review,
        reviewer_identifier="teacher:math-1",
        review_timestamp=timestamp,
        audit_metadata={"station": "answer_sheet_review"},
    )

    assert review.review_status == "PENDING"
    assert active.review_status == "UNDER_REVIEW"
    assert active.reviewer_identifier == "teacher:math-1"
    assert active.review_timestamp == timestamp
    assert active.audit_metadata["transition"] == "start_review"
    assert active.audit_metadata["station"] == "answer_sheet_review"


def test_approve_teacher_review_records_approved_policy():
    timestamp = datetime(2026, 7, 27, 9, 5, tzinfo=UTC)
    active = start_teacher_review(
        create_teacher_review_decision(_policy_decision()),
        reviewer_identifier="teacher:math-1",
        review_timestamp=datetime(2026, 7, 27, 9, 0, tzinfo=UTC),
    )

    approved = approve_teacher_review(
        active,
        reviewer_identifier="teacher:math-1",
        review_timestamp=timestamp,
        audit_metadata={"decision_rationale": "Matches rubric policy."},
    )

    assert approved.review_status == "APPROVED"
    assert approved.terminal is True
    assert approved.approved_policy == active.policy_decision
    assert approved.override_applied is False
    assert approved.override_reason is None
    assert approved.review_timestamp == timestamp
    assert approved.audit_metadata["transition"] == "approve"
    assert approved.audit_metadata["decision_rationale"] == "Matches rubric policy."


def test_override_teacher_review_records_override_reason():
    timestamp = datetime(2026, 7, 27, 9, 10, tzinfo=UTC)
    review = create_teacher_review_decision(_policy_decision())

    overridden = override_teacher_review(
        review,
        override_reason="Teacher accepted alternate valid working.",
        reviewer_identifier="teacher:math-1",
        review_timestamp=timestamp,
    )

    assert overridden.review_status == "OVERRIDDEN"
    assert overridden.terminal is True
    assert overridden.approved_policy is None
    assert overridden.override_applied is True
    assert overridden.override_reason == "Teacher accepted alternate valid working."
    assert overridden.audit_metadata["transition"] == "override"


def test_override_teacher_review_requires_non_empty_reason():
    review = create_teacher_review_decision(_policy_decision())

    with pytest.raises(TeacherReviewStateError):
        override_teacher_review(
            review,
            override_reason=" ",
            reviewer_identifier="teacher:math-1",
        )


def test_reject_teacher_review_records_rejection_metadata():
    timestamp = datetime(2026, 7, 27, 9, 15, tzinfo=UTC)
    review = create_teacher_review_decision(_policy_decision())

    rejected = reject_teacher_review(
        review,
        reviewer_identifier="teacher:math-1",
        rejection_reason="Image is unreadable.",
        review_timestamp=timestamp,
    )

    assert rejected.review_status == "REJECTED"
    assert rejected.terminal is True
    assert rejected.approved_policy is None
    assert rejected.override_applied is False
    assert rejected.audit_metadata["transition"] == "reject"
    assert rejected.audit_metadata["rejection_reason"] == "Image is unreadable."


def test_terminal_teacher_review_cannot_transition_again():
    approved = approve_teacher_review(
        create_teacher_review_decision(_policy_decision()),
        reviewer_identifier="teacher:math-1",
        review_timestamp=datetime(2026, 7, 27, 9, 0, tzinfo=UTC),
    )

    with pytest.raises(TeacherReviewStateError):
        override_teacher_review(
            approved,
            override_reason="Changed my mind.",
            reviewer_identifier="teacher:math-1",
        )

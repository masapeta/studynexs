from datetime import UTC, datetime

import pytest

from app.modules.examinations.services.aei_v1_review_policy import (
    apply_review_policy_metadata,
    normalize_teacher_overrides_for_review_policy,
)


def test_review_policy_marks_low_confidence_for_manual_review():
    suggestions = {
        "1": {
            "marks_suggested": 1,
            "max_marks": 2,
            "feedback": "Partial match.",
            "confidence": 0.55,
            "method": "heuristic_fallback",
        }
    }

    enriched = apply_review_policy_metadata(suggestions)

    q1 = enriched["1"]
    assert q1["manual_review_required"] is True
    assert "below the review threshold" in q1["manual_review_reason"]
    assert q1["confidence_reason"] == "Confidence is below the teacher-review threshold."
    assert q1["capability_mode"] == "manual_review"
    assert q1["aei_v1_review_policy"]["batch"] == "B"


def test_review_policy_does_not_mark_high_confidence_supported_suggestion():
    suggestions = {
        "1": {
            "marks_suggested": 2,
            "max_marks": 2,
            "feedback": "Correct.",
            "confidence": 0.98,
            "method": "objective",
        }
    }

    enriched = apply_review_policy_metadata(suggestions)

    q1 = enriched["1"]
    assert q1["manual_review_required"] is False
    assert q1["manual_review_reason"] is None
    assert q1["capability_mode"] == "supported"


def test_review_policy_preserves_existing_manual_review_reason():
    suggestions = {
        "1": {
            "marks_suggested": 0,
            "max_marks": 1,
            "feedback": "Teacher review required.",
            "confidence": 0.35,
            "manual_review_required": True,
            "manual_review_reason": "Unit parse failed.",
        }
    }

    enriched = apply_review_policy_metadata(suggestions)

    assert enriched["1"]["manual_review_required"] is True
    assert enriched["1"]["manual_review_reason"] == "Unit parse failed."


def test_review_policy_does_not_mislabel_high_confidence_manual_review():
    suggestions = {
        "1": {
            "marks_suggested": 0,
            "max_marks": 1,
            "feedback": "Teacher review required.",
            "confidence": 0.9,
            "manual_review_required": True,
            "manual_review_reason": "Capability requires teacher confirmation.",
        }
    }

    enriched = apply_review_policy_metadata(suggestions)

    assert enriched["1"]["manual_review_required"] is True
    assert (
        enriched["1"]["confidence_reason"]
        == "Confidence meets the threshold; teacher review is required by policy."
    )


def test_review_policy_routes_missing_confidence_to_manual_review():
    suggestions = {
        "1": {
            "marks_suggested": 0,
            "max_marks": 1,
            "feedback": "Review manually.",
            "method": "unknown",
        }
    }

    enriched = apply_review_policy_metadata(suggestions)

    assert enriched["1"]["manual_review_required"] is True
    assert "unavailable" in enriched["1"]["manual_review_reason"]


def test_override_audit_requires_reason_when_teacher_changes_marks():
    with pytest.raises(ValueError, match="requires a non-empty reason"):
        normalize_teacher_overrides_for_review_policy(
            suggestions={"1": {"marks_suggested": 1, "manual_review_required": True}},
            teacher_overrides={"1": {"marks": 2}},
            reviewer_identifier="teacher-1",
            review_timestamp=datetime(2026, 7, 28, tzinfo=UTC),
        )


def test_override_audit_records_changed_marks_and_reason():
    normalized = normalize_teacher_overrides_for_review_policy(
        suggestions={
            "1": {
                "marks_suggested": 1,
                "manual_review_required": True,
                "manual_review_reason": "Low confidence.",
            }
        },
        teacher_overrides={"1": {"marks": 2, "reason": "Valid alternate method."}},
        reviewer_identifier="teacher-1",
        review_timestamp=datetime(2026, 7, 28, tzinfo=UTC),
    )

    audit = normalized["1"]["aei_v1_override_audit"]
    assert normalized["1"]["reason"] == "Valid alternate method."
    assert audit["batch"] == "B"
    assert audit["override_applied"] is True
    assert audit["original_marks_suggested"] == 1
    assert audit["final_marks"] == 2
    assert audit["manual_review_required"] is True


def test_override_audit_allows_same_mark_without_reason():
    normalized = normalize_teacher_overrides_for_review_policy(
        suggestions={"1": {"marks_suggested": 1, "manual_review_required": False}},
        teacher_overrides={"1": {"marks": 1}},
        reviewer_identifier="teacher-1",
        review_timestamp=datetime(2026, 7, 28, tzinfo=UTC),
    )

    assert normalized["1"]["aei_v1_override_audit"]["override_applied"] is False


def test_override_audit_sanitizes_reason_even_when_marks_do_not_change():
    normalized = normalize_teacher_overrides_for_review_policy(
        suggestions={"1": {"marks_suggested": 1, "manual_review_required": False}},
        teacher_overrides={"1": {"marks": 1, "reason": "  Reviewed and accepted.  "}},
        reviewer_identifier="teacher-1",
        review_timestamp=datetime(2026, 7, 28, tzinfo=UTC),
    )

    assert normalized["1"]["reason"] == "Reviewed and accepted."
    assert normalized["1"]["aei_v1_override_audit"]["override_applied"] is False

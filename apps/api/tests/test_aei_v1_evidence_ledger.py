from datetime import UTC, datetime

from app.modules.examinations.services.aei_v1_evidence_ledger import (
    AEI_EVIDENCE_LEDGER_METHOD,
    build_approved_evidence_metadata,
    contains_unsafe_evidence_key,
    is_teacher_approved_evidence,
)


def test_approved_evidence_requires_teacher_approval_metadata():
    assert (
        is_teacher_approved_evidence(
            evaluation_status="approved",
            approved_by="teacher-1",
            approved_at=datetime(2026, 7, 28, tzinfo=UTC),
        )
        is True
    )
    assert (
        is_teacher_approved_evidence(
            evaluation_status="suggested",
            approved_by="teacher-1",
            approved_at=datetime(2026, 7, 28, tzinfo=UTC),
        )
        is False
    )
    assert (
        is_teacher_approved_evidence(
            evaluation_status="approved",
            approved_by=None,
            approved_at=datetime(2026, 7, 28, tzinfo=UTC),
        )
        is False
    )


def test_unapproved_evaluation_does_not_emit_question_evidence():
    metadata = build_approved_evidence_metadata(
        evaluation_status="suggested",
        suggestions={
            "1": {
                "marks_suggested": 2,
                "max_marks": 2,
                "student_answer": "4",
                "confidence": 0.98,
            }
        },
        teacher_overrides={},
        approved_by=None,
        approved_at=None,
    )

    assert metadata["method"] == AEI_EVIDENCE_LEDGER_METHOD
    assert metadata["approved_evidence"] is False
    assert metadata["approved_for_downstream"] is False
    assert metadata["questions"] == {}
    assert metadata["raw_student_answer_excluded"] is True
    assert contains_unsafe_evidence_key(metadata) is False


def test_approved_evidence_keeps_original_suggestion_and_teacher_decision_separate():
    approved_at = datetime(2026, 7, 28, 10, 15, tzinfo=UTC)
    metadata = build_approved_evidence_metadata(
        evaluation_status="approved",
        suggestions={
            "3": {
                "marks_suggested": 1,
                "max_marks": 3,
                "student_answer": "plants use sunlight",
                "confidence": 0.61,
                "method": "heuristic_fallback",
                "manual_review_required": True,
                "manual_review_reason": "Low confidence.",
                "capability_mode": "manual_review",
                "grounding_sources": [{"ref_id": "trace-topic-1", "text": "Long source"}],
            }
        },
        teacher_overrides={
            "3": {
                "marks": 2,
                "reason": "Teacher accepted partial conceptual explanation.",
                "aei_v1_override_audit": {
                    "batch": "B",
                    "method": "aei_v1_review_policy",
                    "override_applied": True,
                    "original_marks_suggested": 1,
                    "final_marks": 2,
                    "manual_review_required": True,
                    "manual_review_reason": "Low confidence.",
                    "reviewer_identifier": "teacher-1",
                    "review_timestamp": approved_at,
                },
            }
        },
        approved_by="teacher-1",
        approved_at=approved_at,
    )

    q3 = metadata["questions"]["3"]
    assert metadata["approved_evidence"] is True
    assert metadata["override_count"] == 1
    assert metadata["manual_review_required_count"] == 1
    assert q3["source_of_truth"] == "teacher_decision"
    assert q3["original_suggestion"]["marks_suggested"] == 1
    assert q3["original_suggestion"]["citation_ids"] == ["trace-topic-1"]
    assert q3["final_teacher_decision"]["final_marks"] == 2
    assert q3["final_teacher_decision"]["override_applied"] is True
    assert q3["final_teacher_decision"]["override_audit"]["batch"] == "B"
    assert contains_unsafe_evidence_key(metadata) is False


def test_approved_evidence_same_marks_is_not_an_override():
    metadata = build_approved_evidence_metadata(
        evaluation_status="approved",
        suggestions={
            "1": {
                "marks_suggested": 2,
                "max_marks": 2,
                "student_answer": "4",
                "manual_review_required": False,
            }
        },
        teacher_overrides={"1": {"marks": 2}},
        approved_by="teacher-1",
        approved_at=datetime(2026, 7, 28, tzinfo=UTC),
    )

    q1 = metadata["questions"]["1"]
    assert metadata["override_count"] == 0
    assert q1["final_teacher_decision"]["final_marks"] == 2
    assert q1["final_teacher_decision"]["override_applied"] is False
    assert contains_unsafe_evidence_key(metadata) is False

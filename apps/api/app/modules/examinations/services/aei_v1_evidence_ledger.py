"""AEI v1.0 Batch C approved-evidence ledger helpers.

Batch C hardens evidence metadata for downstream intelligence by making the
teacher-approved source of truth explicit. It does not persist evidence, migrate
schemas, assign marks, or expose raw student answers in the approved-evidence
contract.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Mapping

AEI_EVIDENCE_LEDGER_METHOD = "aei_v1_approved_evidence_ledger"
AEI_EVIDENCE_LEDGER_BATCH = "C"

_UNSAFE_EVIDENCE_KEYS = frozenset({
    "student_answer",
    "raw_answer",
    "raw_input",
    "ocr_text",
    "transcript",
    "answer_text",
})

_SAFE_SUGGESTION_KEYS = frozenset({
    "marks_suggested",
    "max_marks",
    "confidence",
    "method",
    "evaluation_method",
    "capability_mode",
    "confidence_reason",
    "manual_review_required",
    "manual_review_reason",
    "normalized_answer",
    "matched_acceptable_answer",
    "grounded",
})

_SAFE_REVIEW_POLICY_KEYS = frozenset({
    "batch",
    "method",
    "confidence",
    "confidence_threshold",
    "manual_review_required",
    "manual_review_reason",
    "source_method",
    "existing_manual_review_required",
    "missing_confidence",
    "low_confidence",
})

_SAFE_OVERRIDE_AUDIT_KEYS = frozenset({
    "batch",
    "method",
    "override_applied",
    "original_marks_suggested",
    "final_marks",
    "manual_review_required",
    "manual_review_reason",
    "reviewer_identifier",
    "review_timestamp",
})


def build_approved_evidence_metadata(
    *,
    evaluation_status: str | None,
    suggestions: Mapping[str, Mapping[str, Any]] | None,
    teacher_overrides: Mapping[str, Mapping[str, Any]] | None,
    approved_by: Any | None,
    approved_at: Any | None,
) -> dict[str, Any]:
    """Build sanitized Batch C metadata for an evaluation evidence ledger."""

    approved = is_teacher_approved_evidence(
        evaluation_status=evaluation_status,
        approved_by=approved_by,
        approved_at=approved_at,
    )
    if not approved:
        return {
            "batch": AEI_EVIDENCE_LEDGER_BATCH,
            "method": AEI_EVIDENCE_LEDGER_METHOD,
            "approved_evidence": False,
            "approved_evidence_reason": "Evaluation has not been approved by a teacher.",
            "approved_for_downstream": False,
            "questions": {},
            "question_count": 0,
            "override_count": 0,
            "manual_review_required_count": 0,
            "parent_student_safe": True,
            "raw_student_answer_excluded": True,
            "downstream_contract": _downstream_contract(),
        }

    normalized_suggestions = _normalize_mapping(suggestions)
    normalized_overrides = _normalize_mapping(teacher_overrides)
    questions: dict[str, dict[str, Any]] = {}
    override_count = 0
    manual_review_required_count = 0

    for qno in sorted(normalized_suggestions, key=_question_sort_key):
        suggestion = normalized_suggestions[qno]
        override = normalized_overrides.get(qno, {})
        final_decision = _teacher_decision(
            suggestion=suggestion,
            override=override,
            approved_by=approved_by,
            approved_at=approved_at,
        )
        if final_decision["override_applied"]:
            override_count += 1
        if bool(suggestion.get("manual_review_required")):
            manual_review_required_count += 1

        questions[qno] = {
            "question_no": qno,
            "approved_for_downstream": True,
            "source_of_truth": "teacher_decision",
            "original_suggestion": _safe_original_suggestion(suggestion),
            "final_teacher_decision": final_decision,
        }

    return {
        "batch": AEI_EVIDENCE_LEDGER_BATCH,
        "method": AEI_EVIDENCE_LEDGER_METHOD,
        "approved_evidence": True,
        "approved_evidence_reason": "Teacher-approved evaluation evidence.",
        "approved_for_downstream": True,
        "teacher_approved_by": str(approved_by),
        "teacher_approved_at": _isoformat(approved_at),
        "question_count": len(questions),
        "override_count": override_count,
        "manual_review_required_count": manual_review_required_count,
        "parent_student_safe": True,
        "raw_student_answer_excluded": True,
        "downstream_contract": _downstream_contract(),
        "questions": questions,
    }


def is_teacher_approved_evidence(
    *,
    evaluation_status: str | None,
    approved_by: Any | None,
    approved_at: Any | None,
) -> bool:
    """Return whether an evaluation is approved evidence for downstream use."""

    return evaluation_status == "approved" and approved_by is not None and approved_at is not None


def contains_unsafe_evidence_key(value: Any) -> bool:
    """Detect raw-answer keys in nested evidence metadata."""

    if isinstance(value, Mapping):
        return any(
            str(key) in _UNSAFE_EVIDENCE_KEYS or contains_unsafe_evidence_key(item)
            for key, item in value.items()
        )
    if isinstance(value, (list, tuple, set)):
        return any(contains_unsafe_evidence_key(item) for item in value)
    return False


def _safe_original_suggestion(suggestion: Mapping[str, Any]) -> dict[str, Any]:
    safe = {
        key: _json_safe(value)
        for key, value in suggestion.items()
        if key in _SAFE_SUGGESTION_KEYS and key not in _UNSAFE_EVIDENCE_KEYS
    }

    review_policy = suggestion.get("aei_v1_review_policy")
    if isinstance(review_policy, Mapping):
        safe["review_policy"] = {
            key: _json_safe(value)
            for key, value in review_policy.items()
            if key in _SAFE_REVIEW_POLICY_KEYS
        }

    citation_ids = _citation_ids(suggestion)
    if citation_ids:
        safe["citation_ids"] = citation_ids

    return safe


def _teacher_decision(
    *,
    suggestion: Mapping[str, Any],
    override: Mapping[str, Any],
    approved_by: Any,
    approved_at: Any,
) -> dict[str, Any]:
    suggested_marks = _optional_float(suggestion.get("marks_suggested"))
    override_marks = _optional_float(override.get("marks"))
    final_marks = suggested_marks if override_marks is None else override_marks
    override_applied = (
        suggested_marks is not None
        and final_marks is not None
        and round(suggested_marks, 2) != round(final_marks, 2)
    )

    audit = override.get("aei_v1_override_audit")
    if isinstance(audit, Mapping):
        audit_override = audit.get("override_applied")
        if isinstance(audit_override, bool):
            override_applied = audit_override

    decision: dict[str, Any] = {
        "final_marks": final_marks,
        "max_marks": _optional_float(suggestion.get("max_marks")),
        "override_applied": override_applied,
        "override_reason": override.get("reason"),
        "approved_by": str(approved_by),
        "approved_at": _isoformat(approved_at),
        "manual_review_was_required": bool(suggestion.get("manual_review_required")),
    }
    if isinstance(audit, Mapping):
        decision["override_audit"] = {
            key: _json_safe(value)
            for key, value in audit.items()
            if key in _SAFE_OVERRIDE_AUDIT_KEYS
        }
    return decision


def _downstream_contract() -> dict[str, Any]:
    return {
        "source_of_truth": "teacher_decision",
        "student_parent_visibility": "teacher_approved_only",
        "learning_intelligence_visibility": "teacher_approved_only",
        "raw_student_answer_excluded": True,
        "autonomous_grading": False,
    }


def _normalize_mapping(
    value: Mapping[str, Mapping[str, Any]] | None,
) -> dict[str, dict[str, Any]]:
    normalized: dict[str, dict[str, Any]] = {}
    for key, item in (value or {}).items():
        if isinstance(item, Mapping):
            normalized[str(key)] = dict(item)
    return normalized


def _citation_ids(suggestion: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    for source in suggestion.get("grounding_sources") or []:
        if isinstance(source, Mapping) and source.get("ref_id"):
            refs.append(str(source["ref_id"]))
    for citation in suggestion.get("citations") or []:
        refs.append(str(citation))
    return sorted(set(refs))


def _question_sort_key(value: str) -> tuple[int, Any]:
    return (0, int(value)) if value.isdigit() else (1, value)


def _optional_float(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _isoformat(value: Any) -> str | None:
    if isinstance(value, datetime | date):
        return value.isoformat()
    if value is None:
        return None
    return str(value)


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _json_safe(item)
            for key, item in value.items()
            if str(key) not in _UNSAFE_EVIDENCE_KEYS
        }
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if isinstance(value, datetime | date):
        return value.isoformat()
    return value

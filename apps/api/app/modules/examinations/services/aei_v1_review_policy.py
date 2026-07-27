"""AEI v1.0 Batch B review-policy metadata helpers.

Batch B makes uncertainty and teacher authority explicit in production
suggestions. It does not grade answers, change marks, alter teacher-review
routing, update the evidence ledger, or expose new UI/API contracts.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.modules.ai.gateway.input_guard import sanitize_prompt_text

AEI_REVIEW_POLICY_METHOD = "aei_v1_review_policy"
DEFAULT_REVIEW_CONFIDENCE_THRESHOLD = 0.75


def apply_review_policy_metadata(
    suggestions: dict[str, dict[str, Any]],
    *,
    confidence_threshold: float = DEFAULT_REVIEW_CONFIDENCE_THRESHOLD,
) -> dict[str, dict[str, Any]]:
    """Return suggestions enriched with Batch B review-policy metadata."""

    enriched: dict[str, dict[str, Any]] = {}
    for qno, suggestion in suggestions.items():
        enriched[qno] = _enrich_suggestion(
            suggestion,
            confidence_threshold=confidence_threshold,
        )
    return enriched


def normalize_teacher_overrides_for_review_policy(
    *,
    suggestions: dict[str, dict[str, Any]],
    teacher_overrides: dict[str, dict[str, Any]],
    reviewer_identifier: str,
    review_timestamp: datetime,
) -> dict[str, dict[str, Any]]:
    """Validate and enrich teacher overrides with Batch B audit metadata."""

    normalized: dict[str, dict[str, Any]] = {}
    for qno, override in (teacher_overrides or {}).items():
        suggestion = suggestions.get(str(qno), {})
        normalized[str(qno)] = _normalize_override(
            qno=str(qno),
            override=override,
            suggestion=suggestion,
            reviewer_identifier=reviewer_identifier,
            review_timestamp=review_timestamp,
        )
    return normalized


def _enrich_suggestion(
    suggestion: dict[str, Any],
    *,
    confidence_threshold: float,
) -> dict[str, Any]:
    updated = dict(suggestion)
    confidence = _optional_float(updated.get("confidence"))
    existing_manual_review = bool(updated.get("manual_review_required"))
    missing_confidence = confidence is None
    low_confidence = confidence is not None and confidence < confidence_threshold
    manual_review_required = existing_manual_review or missing_confidence or low_confidence

    manual_review_reason = updated.get("manual_review_reason")
    if manual_review_required and not manual_review_reason:
        manual_review_reason = _manual_review_reason(
            confidence=confidence,
            confidence_threshold=confidence_threshold,
            existing_manual_review=existing_manual_review,
        )

    confidence_reason = updated.get("confidence_reason")
    if not confidence_reason:
        confidence_reason = _confidence_reason(
            confidence=confidence,
            confidence_threshold=confidence_threshold,
            manual_review_required=manual_review_required,
            existing_manual_review=existing_manual_review,
        )

    updated["manual_review_required"] = manual_review_required
    updated["manual_review_reason"] = manual_review_reason
    updated["capability_mode"] = updated.get("capability_mode") or _capability_mode(updated)
    updated["confidence_reason"] = confidence_reason
    updated["aei_v1_review_policy"] = {
        "batch": "B",
        "method": AEI_REVIEW_POLICY_METHOD,
        "confidence": confidence,
        "confidence_threshold": confidence_threshold,
        "manual_review_required": manual_review_required,
        "manual_review_reason": manual_review_reason,
        "source_method": updated.get("method"),
        "existing_manual_review_required": existing_manual_review,
        "missing_confidence": missing_confidence,
        "low_confidence": low_confidence,
    }
    return updated


def _normalize_override(
    *,
    qno: str,
    override: dict[str, Any],
    suggestion: dict[str, Any],
    reviewer_identifier: str,
    review_timestamp: datetime,
) -> dict[str, Any]:
    normalized = dict(override or {})
    suggested_marks = _optional_float(suggestion.get("marks_suggested"))
    override_marks = _optional_float(normalized.get("marks"))
    override_applied = (
        suggested_marks is not None
        and override_marks is not None
        and round(suggested_marks, 2) != round(override_marks, 2)
    )

    reason = normalized.get("reason")
    if reason is not None and str(reason).strip():
        normalized["reason"] = sanitize_prompt_text(
            str(reason),
            max_length=500,
            field_name=f"teacher_overrides.{qno}.reason",
            reject_injection=True,
        )
        reason = normalized["reason"]
    if override_applied:
        if reason is None or not str(reason).strip():
            raise ValueError(f"Override for Q{qno} requires a non-empty reason")

    normalized["aei_v1_override_audit"] = {
        "batch": "B",
        "method": AEI_REVIEW_POLICY_METHOD,
        "override_applied": override_applied,
        "original_marks_suggested": suggested_marks,
        "final_marks": override_marks,
        "manual_review_required": bool(suggestion.get("manual_review_required")),
        "manual_review_reason": suggestion.get("manual_review_reason"),
        "reviewer_identifier": reviewer_identifier,
        "review_timestamp": review_timestamp.isoformat(),
    }
    return normalized


def _manual_review_reason(
    *,
    confidence: float | None,
    confidence_threshold: float,
    existing_manual_review: bool,
) -> str:
    if existing_manual_review:
        return "Existing AEI suggestion requires teacher review."
    if confidence is None:
        return "Suggestion confidence is unavailable and should be reviewed by a teacher."
    return (
        f"Suggestion confidence {confidence:.2f} is below the review threshold "
        f"{confidence_threshold:.2f}."
    )


def _confidence_reason(
    *,
    confidence: float | None,
    confidence_threshold: float,
    manual_review_required: bool,
    existing_manual_review: bool,
) -> str:
    if confidence is None:
        return "Confidence was not provided by the suggestion source."
    if confidence < confidence_threshold:
        return "Confidence is below the teacher-review threshold."
    if manual_review_required or existing_manual_review:
        return "Confidence meets the threshold; teacher review is required by policy."
    return "Confidence meets the teacher-review threshold."


def _capability_mode(suggestion: dict[str, Any]) -> str:
    aei_v1 = suggestion.get("aei_v1")
    if isinstance(aei_v1, dict) and aei_v1.get("capability_mode"):
        return str(aei_v1["capability_mode"])
    if suggestion.get("manual_review_required"):
        return "manual_review"
    return "supported"


def _optional_float(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

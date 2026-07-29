"""AEI Activation / Trust helpers.

This module is the controlled-runtime trust layer for certified AEI v1.0
capabilities. It does not grade answers, call AI providers, migrate schemas, or
switch any source of truth. It only:

- summarizes activation/trust posture;
- detects manual-review-required suggestions;
- validates teacher acknowledgement when the default-off gate is enabled;
- emits low-cardinality operational evidence.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Mapping

import structlog

from app.core.platform_metrics import platform_metrics
from app.modules.ai.gateway.input_guard import sanitize_prompt_text

AEI_ACTIVATION_TRUST_METHOD = "aei_activation_trust"
AEI_MANUAL_REVIEW_ACK_METHOD = "aei_v1_manual_review_acknowledgement"
AEI_ACTIVATION_TRUST_METRIC_TASK = "aei_activation_trust"

_ALLOWED_ACK_ACTIONS = frozenset({"accepted", "adjusted", "rejected"})
_AEI_METADATA_KEYS = frozenset({
    "aei_v1",
    "aei_v1_review_policy",
    "aei_v1_language_ocr_assist",
    "aei_v1_visual_science_assist",
    "normalized_answer",
    "matched_acceptable_answer",
    "manual_review_required",
    "capability_mode",
    "language_ocr_capability_mode",
    "visual_science_capability_mode",
})

logger = structlog.get_logger()


def activation_trust_profile_enabled(settings: Any) -> bool:
    """Return whether any controlled AEI v1.0 trust capability is enabled."""

    return bool(
        getattr(settings, "AEI_V1_MATH_NORMALIZATION_ENABLED", False)
        or getattr(settings, "AEI_V1_REVIEW_POLICY_ENABLED", False)
        or getattr(settings, "AEI_V1_EVIDENCE_LEDGER_METADATA_ENABLED", False)
        or getattr(settings, "AEI_V1_LANGUAGE_OCR_ASSIST_ENABLED", False)
        or getattr(settings, "AEI_V1_VISUAL_SCIENCE_ASSIST_ENABLED", False)
        or getattr(settings, "AEI_V1_MANUAL_REVIEW_ACK_REQUIRED", False)
    )


def manual_review_required_questions(
    suggestions: Mapping[str, Mapping[str, Any]] | None,
) -> tuple[str, ...]:
    """Return sorted question numbers that carry a manual-review signal."""

    required: list[str] = []
    for qno, suggestion in (suggestions or {}).items():
        if _suggestion_requires_manual_review(suggestion):
            required.append(str(qno))
    return tuple(sorted(required, key=_question_sort_key))


def validate_and_merge_manual_review_acknowledgements(
    *,
    suggestions: Mapping[str, Mapping[str, Any]] | None,
    teacher_overrides: Mapping[str, Mapping[str, Any]] | None,
    manual_review_acknowledgements: Mapping[str, Mapping[str, Any]] | None,
    reviewer_identifier: str,
    review_timestamp: datetime,
) -> dict[str, dict[str, Any]]:
    """Validate required acknowledgements and merge them into overrides metadata."""

    started = time.perf_counter()
    platform_metrics.record_job_event(
        task=AEI_ACTIVATION_TRUST_METRIC_TASK,
        status="manual_review_ack_invoked",
    )
    normalized_overrides = _normalize_nested_mapping(teacher_overrides)
    acknowledgements = _normalize_nested_mapping(manual_review_acknowledgements)
    required_questions = manual_review_required_questions(suggestions)
    if not required_questions:
        platform_metrics.record_job_event(
            task=AEI_ACTIVATION_TRUST_METRIC_TASK,
            status="manual_review_ack_not_required",
            duration_ms=_elapsed_ms(started),
        )
        return normalized_overrides

    missing = [
        qno
        for qno in required_questions
        if not _acknowledged(acknowledgements.get(qno))
    ]
    if missing:
        platform_metrics.record_job_event(
            task=AEI_ACTIVATION_TRUST_METRIC_TASK,
            status="manual_review_ack_missing",
            duration_ms=_elapsed_ms(started),
        )
        raise ValueError(
            "Teacher review acknowledgement required for "
            + ", ".join(f"Q{qno}" for qno in missing)
        )

    for qno in required_questions:
        suggestion = dict((suggestions or {}).get(qno, {}))
        override = dict(normalized_overrides.get(qno, {}))
        acknowledgement = acknowledgements[qno]
        override[AEI_MANUAL_REVIEW_ACK_METHOD] = _acknowledgement_metadata(
            qno=qno,
            acknowledgement=acknowledgement,
            suggestion=suggestion,
            override=override,
            reviewer_identifier=reviewer_identifier,
            review_timestamp=review_timestamp,
        )
        normalized_overrides[qno] = override

    platform_metrics.record_job_event(
        task=AEI_ACTIVATION_TRUST_METRIC_TASK,
        status="manual_review_acknowledged",
        duration_ms=_elapsed_ms(started),
    )
    logger.info(
        "aei_activation_trust_manual_review_acknowledged",
        question_count=len(required_questions),
    )
    return normalized_overrides


def build_activation_trust_evidence(
    *,
    suggestions: Mapping[str, Mapping[str, Any]] | None,
    teacher_overrides: Mapping[str, Mapping[str, Any]] | None = None,
    manual_review_acknowledgement_required: bool,
) -> dict[str, Any]:
    """Build additive evidence-ledger metadata for activation/trust proof."""

    normalized_suggestions = _normalize_nested_mapping(suggestions)
    normalized_overrides = _normalize_nested_mapping(teacher_overrides)
    manual_review_questions = manual_review_required_questions(normalized_suggestions)
    acknowledged_questions = tuple(
        qno
        for qno in manual_review_questions
        if _override_acknowledged(normalized_overrides.get(qno))
    )
    capability_counts = _capability_counts(normalized_suggestions)
    return {
        "method": AEI_ACTIVATION_TRUST_METHOD,
        "manual_review_acknowledgement_required": manual_review_acknowledgement_required,
        "manual_review_required_count": len(manual_review_questions),
        "manual_review_acknowledged_count": len(acknowledged_questions),
        "manual_review_required_questions": list(manual_review_questions),
        "manual_review_acknowledged_questions": list(acknowledged_questions),
        "teacher_authority": "required",
        "approved_evidence_source": "teacher_decision",
        "autonomous_grading": False,
        "source_switching": False,
        "capability_counts": capability_counts,
    }


def observe_activation_trust_suggestions(
    *,
    enabled: bool,
    suggestions: Mapping[str, Mapping[str, Any]] | None,
) -> dict[str, Any] | None:
    """Record low-cardinality activation/trust runtime evidence."""

    if not enabled:
        return None

    started = time.perf_counter()
    platform_metrics.record_job_event(task=AEI_ACTIVATION_TRUST_METRIC_TASK, status="invoked")
    try:
        evidence = build_activation_trust_evidence(
            suggestions=suggestions,
            teacher_overrides=None,
            manual_review_acknowledgement_required=False,
        )
        counts = evidence["capability_counts"]
        if counts.get("math_normalization", 0):
            platform_metrics.record_job_event(
                task=AEI_ACTIVATION_TRUST_METRIC_TASK,
                status="math_normalization_applied",
            )
        if counts.get("language_ocr_assist", 0):
            platform_metrics.record_job_event(
                task=AEI_ACTIVATION_TRUST_METRIC_TASK,
                status="language_ocr_assist_applied",
            )
        if counts.get("visual_science_assist", 0):
            platform_metrics.record_job_event(
                task=AEI_ACTIVATION_TRUST_METRIC_TASK,
                status="visual_science_assist_applied",
            )
        if evidence["manual_review_required_count"]:
            platform_metrics.record_job_event(
                task=AEI_ACTIVATION_TRUST_METRIC_TASK,
                status="manual_review_required",
            )
        platform_metrics.record_job_event(
            task=AEI_ACTIVATION_TRUST_METRIC_TASK,
            status="completed",
            duration_ms=_elapsed_ms(started),
        )
        logger.info(
            "aei_activation_trust_completed",
            question_count=len(suggestions or {}),
            manual_review_required_count=evidence["manual_review_required_count"],
            capability_counts=counts,
        )
        return evidence
    except Exception:
        platform_metrics.record_job_event(
            task=AEI_ACTIVATION_TRUST_METRIC_TASK,
            status="failed",
            duration_ms=_elapsed_ms(started),
        )
        logger.exception("aei_activation_trust_failed")
        return None


def _suggestion_requires_manual_review(suggestion: Mapping[str, Any]) -> bool:
    return bool(
        suggestion.get("manual_review_required")
        or suggestion.get("teacher_correction_required")
        or suggestion.get("requires_language_teacher_review")
        or suggestion.get("visual_science_review_required")
        or suggestion.get("assist_only")
        or suggestion.get("checklist_only")
        or str(suggestion.get("capability_mode") or "").lower()
        in {"assist", "checklist", "manual_review", "unsupported", "expansion"}
    )


def _acknowledged(value: Mapping[str, Any] | None) -> bool:
    if not isinstance(value, Mapping):
        return False
    return value.get("acknowledged") is True


def _acknowledgement_metadata(
    *,
    qno: str,
    acknowledgement: Mapping[str, Any],
    suggestion: Mapping[str, Any],
    override: Mapping[str, Any],
    reviewer_identifier: str,
    review_timestamp: datetime,
) -> dict[str, Any]:
    suggested_marks = _optional_float(suggestion.get("marks_suggested"))
    override_marks = _optional_float(override.get("marks"))
    override_applied = (
        suggested_marks is not None
        and override_marks is not None
        and round(suggested_marks, 2) != round(override_marks, 2)
    )
    action = _action(acknowledgement, override_applied=override_applied)
    note = _optional_note(acknowledgement.get("note"), qno=qno)
    metadata: dict[str, Any] = {
        "method": AEI_MANUAL_REVIEW_ACK_METHOD,
        "acknowledged": True,
        "action": action,
        "manual_review_required": True,
        "manual_review_reason": suggestion.get("manual_review_reason"),
        "override_applied": override_applied,
        "reviewer_identifier": reviewer_identifier,
        "review_timestamp": review_timestamp.isoformat(),
    }
    if note:
        metadata["note"] = note
    return metadata


def _action(acknowledgement: Mapping[str, Any], *, override_applied: bool) -> str:
    raw_action = str(acknowledgement.get("action") or "").strip().lower()
    if raw_action in _ALLOWED_ACK_ACTIONS:
        return raw_action
    return "adjusted" if override_applied else "accepted"


def _optional_note(value: Any, *, qno: str) -> str | None:
    if value is None or value == "":
        return None
    return sanitize_prompt_text(
        str(value),
        max_length=500,
        field_name=f"manual_review_acknowledgements.{qno}.note",
        reject_injection=True,
    )


def _override_acknowledged(override: Mapping[str, Any] | None) -> bool:
    if not isinstance(override, Mapping):
        return False
    ack = override.get(AEI_MANUAL_REVIEW_ACK_METHOD)
    return isinstance(ack, Mapping) and ack.get("acknowledged") is True


def _normalize_nested_mapping(
    value: Mapping[str, Mapping[str, Any]] | None,
) -> dict[str, dict[str, Any]]:
    normalized: dict[str, dict[str, Any]] = {}
    for key, item in (value or {}).items():
        if isinstance(item, Mapping):
            normalized[str(key)] = dict(item)
    return normalized


def _capability_counts(suggestions: Mapping[str, Mapping[str, Any]]) -> dict[str, int]:
    counts = {
        "questions": 0,
        "aei_metadata": 0,
        "math_normalization": 0,
        "review_policy": 0,
        "evidence_ledger_ready": 0,
        "language_ocr_assist": 0,
        "visual_science_assist": 0,
        "assist_or_checklist": 0,
    }
    for suggestion in suggestions.values():
        counts["questions"] += 1
        if any(key in suggestion for key in _AEI_METADATA_KEYS):
            counts["aei_metadata"] += 1
        if suggestion.get("method") == "aei_v1_math_normalization":
            counts["math_normalization"] += 1
        if isinstance(suggestion.get("aei_v1_review_policy"), Mapping):
            counts["review_policy"] += 1
        if isinstance(suggestion.get("aei_v1_language_ocr_assist"), Mapping):
            counts["language_ocr_assist"] += 1
        if isinstance(suggestion.get("aei_v1_visual_science_assist"), Mapping):
            counts["visual_science_assist"] += 1
        if suggestion.get("assist_only") is True or suggestion.get("checklist_only") is True:
            counts["assist_or_checklist"] += 1
        if suggestion.get("manual_review_required") is not None:
            counts["evidence_ledger_ready"] += 1
    return counts


def _optional_float(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _question_sort_key(value: str) -> tuple[int, Any]:
    return (0, int(value)) if value.isdigit() else (1, value)


def _elapsed_ms(started: float) -> float:
    return (time.perf_counter() - started) * 1000

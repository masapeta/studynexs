"""Passive AEI consumer migration dual-read observer for EUI Phase 7A.

This module compares sanitized legacy AEI/evaluation signals with available
EUI passive signals. It is default-off, deterministic, non-authoritative, and
exception-isolated. It must never influence production evaluation behavior.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
import uuid
from collections import deque
from threading import Lock
from typing import Any

from app.core.platform_metrics import platform_metrics
from app.modules.eui.schemas.aei_consumer_migration import (
    AEIConsumerMigrationCapture,
    AEIConsumerMigrationComparison,
    AEIConsumerMigrationDifference,
    AEIConsumerMigrationSubjectType,
)
from app.modules.eui.schemas.educational_context import EducationalContext
from app.modules.eui.schemas.platform_capability import PlatformCapabilityLookupResult
from app.modules.eui.schemas.trust_report import TrustReport

logger = logging.getLogger(__name__)

EUI_AEI_CONSUMER_MIGRATION_METRIC_TASK = "eui_consumer_migration"
DEFAULT_CAPTURE_LIMIT = 100
PRODUCT_IMPACTING_KEYS = frozenset(
    {
        "result_hash",
        "marks_hash",
        "gradebook_hash",
        "policy_hash",
        "teacher_review_hash",
        "evidence_hash",
    }
)


class AEIConsumerMigrationCaptureRegistry:
    """Bounded in-memory capture store for passive certification only."""

    def __init__(self, *, max_entries: int = DEFAULT_CAPTURE_LIMIT) -> None:
        self._items: deque[AEIConsumerMigrationCapture] = deque(maxlen=max_entries)
        self._lock = Lock()

    def record(self, capture: AEIConsumerMigrationCapture) -> None:
        with self._lock:
            self._items.append(capture)

    def snapshot(self) -> list[AEIConsumerMigrationCapture]:
        with self._lock:
            return list(self._items)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()


eui_aei_consumer_migration_captures = AEIConsumerMigrationCaptureRegistry()


class AEIConsumerMigrationAdapter:
    """Map AEI/evaluation and EUI passive signals into comparison evidence."""

    def build_comparison(
        self,
        *,
        tenant_id: uuid.UUID,
        subject_type: AEIConsumerMigrationSubjectType,
        subject_ref: str,
        legacy_summary: dict[str, Any],
        eui_summary: dict[str, Any] | None = None,
        educational_context: EducationalContext | None = None,
        capability_lookup: PlatformCapabilityLookupResult | None = None,
        trust_report: TrustReport | None = None,
        source_flag_enabled: bool = False,
    ) -> AEIConsumerMigrationComparison:
        """Build a non-authoritative dual-read comparison.

        The source flag is intentionally recorded but behaviorally inert in
        Phase 7A. ``source_switch_active`` remains false by model contract.
        """

        safe_eui_summary = _merge_eui_summary(
            eui_summary=eui_summary,
            educational_context=educational_context,
            capability_lookup=capability_lookup,
            trust_report=trust_report,
        )
        differences = classify_migration_differences(
            legacy_summary=legacy_summary,
            eui_summary=safe_eui_summary,
            educational_context=educational_context,
            capability_lookup=capability_lookup,
            trust_report=trust_report,
        )
        comparison_id = stable_aei_consumer_migration_id(
            subject_type=subject_type,
            subject_ref=subject_ref,
            payload={
                "legacy": _redacted_summary(legacy_summary),
                "eui": _redacted_summary(safe_eui_summary),
                "differences": [difference.difference_type for difference in differences],
            },
        )
        return AEIConsumerMigrationComparison(
            id=comparison_id,
            tenant_id=tenant_id,
            subject_type=subject_type,
            subject_ref=subject_ref,
            legacy_summary=_redacted_summary(legacy_summary),
            eui_summary=_redacted_summary(safe_eui_summary),
            differences=tuple(differences),
            trust_report_ref=trust_report.id if trust_report is not None else None,
            trust_posture=trust_report.overall_posture if trust_report is not None else None,
            trust_consumer_visibility=(
                trust_report.consumer_visibility if trust_report is not None else None
            ),
            eui_identity_present=bool(
                safe_eui_summary.get("educational_identity_id")
                or (educational_context and educational_context.educational_identity_id)
            ),
            eui_context_present=educational_context is not None
            or bool(safe_eui_summary.get("context_available")),
            capability_mode=(
                capability_lookup.mode
                if capability_lookup is not None
                else safe_eui_summary.get("capability_mode")
            ),
            source_flag_enabled=source_flag_enabled,
            metadata={
                "phase": "7A",
                "source_flag_inert": True,
                "source_of_truth": "legacy_aei_evaluation",
            },
        )


def observe_aei_consumer_migration(
    *,
    enabled: bool,
    tenant_id: uuid.UUID,
    subject_type: AEIConsumerMigrationSubjectType,
    subject_ref: str,
    legacy_summary: dict[str, Any],
    eui_summary: dict[str, Any] | None = None,
    educational_context: EducationalContext | None = None,
    capability_lookup: PlatformCapabilityLookupResult | None = None,
    trust_report: TrustReport | None = None,
    source_enabled: bool = False,
    adapter: AEIConsumerMigrationAdapter | None = None,
) -> AEIConsumerMigrationCapture | None:
    """Run passive AEI consumer migration comparison behind a feature flag."""

    if not enabled:
        return None

    started = time.perf_counter()
    platform_metrics.record_job_event(
        task=EUI_AEI_CONSUMER_MIGRATION_METRIC_TASK,
        status="invoked",
    )
    try:
        active_adapter = adapter or AEIConsumerMigrationAdapter()
        comparison = active_adapter.build_comparison(
            tenant_id=tenant_id,
            subject_type=subject_type,
            subject_ref=subject_ref,
            legacy_summary=legacy_summary,
            eui_summary=eui_summary,
            educational_context=educational_context,
            capability_lookup=capability_lookup,
            trust_report=trust_report,
            source_flag_enabled=source_enabled,
        )
    except Exception as exc:
        duration_ms = _duration_ms(started)
        platform_metrics.record_job_event(
            task=EUI_AEI_CONSUMER_MIGRATION_METRIC_TASK,
            status="failed",
            duration_ms=duration_ms,
        )
        logger.exception(
            "EUI AEI consumer migration passive comparison failed",
            extra={
                "eui_consumer": "aei",
                "eui_subject_type": subject_type,
                "eui_duration_ms": round(duration_ms, 2),
            },
        )
        capture = AEIConsumerMigrationCapture(
            subject_type=subject_type,
            subject_ref=subject_ref,
            status="failed",
            duration_ms=duration_ms,
            error=str(exc),
        )
        eui_aei_consumer_migration_captures.record(capture)
        return None

    duration_ms = _duration_ms(started)
    status = _capture_status(comparison)
    platform_metrics.record_job_event(
        task=EUI_AEI_CONSUMER_MIGRATION_METRIC_TASK,
        status=status,
        duration_ms=duration_ms,
    )
    if status == "diverged":
        platform_metrics.record_job_event(
            task=EUI_AEI_CONSUMER_MIGRATION_METRIC_TASK,
            status="diverged",
        )
    if status == "unsafe_difference":
        platform_metrics.record_job_event(
            task=EUI_AEI_CONSUMER_MIGRATION_METRIC_TASK,
            status="unsafe_difference",
        )

    capture = AEIConsumerMigrationCapture(
        subject_type=subject_type,
        subject_ref=subject_ref,
        status=status,
        duration_ms=duration_ms,
        comparison=comparison,
    )
    eui_aei_consumer_migration_captures.record(capture)
    logger.info(
        "EUI AEI consumer migration passive comparison completed",
        extra={
            "eui_consumer": "aei",
            "eui_subject_type": subject_type,
            "eui_status": status,
            "eui_difference_types": comparison.difference_types,
            "eui_has_blockers": comparison.has_blockers,
            "eui_source_flag_enabled": comparison.source_flag_enabled,
            "eui_source_switch_active": comparison.source_switch_active,
            "eui_duration_ms": round(duration_ms, 2),
        },
    )
    return capture


def classify_migration_differences(
    *,
    legacy_summary: dict[str, Any],
    eui_summary: dict[str, Any] | None = None,
    educational_context: EducationalContext | None = None,
    capability_lookup: PlatformCapabilityLookupResult | None = None,
    trust_report: TrustReport | None = None,
) -> tuple[AEIConsumerMigrationDifference, ...]:
    """Classify passive dual-read differences deterministically."""

    safe_eui_summary = _merge_eui_summary(
        eui_summary=eui_summary,
        educational_context=educational_context,
        capability_lookup=capability_lookup,
        trust_report=trust_report,
    )
    differences: list[AEIConsumerMigrationDifference] = []

    if trust_report is not None and trust_report.consumer_visibility != "internal_only":
        differences.append(
            AEIConsumerMigrationDifference(
                difference_type="unsafe",
                reason="trust_report_not_internal_only",
                blocker=True,
                eui_signal=trust_report.consumer_visibility,
            )
        )

    tenant_difference = _tenant_difference(legacy_summary, safe_eui_summary)
    if tenant_difference is not None:
        differences.append(
            AEIConsumerMigrationDifference(
                difference_type="unsafe",
                reason="tenant_signal_mismatch",
                blocker=True,
                metadata=tenant_difference,
            )
        )

    for key in sorted(PRODUCT_IMPACTING_KEYS):
        if (
            key in legacy_summary
            and key in safe_eui_summary
            and legacy_summary[key] != safe_eui_summary[key]
        ):
            differences.append(
                AEIConsumerMigrationDifference(
                    difference_type="product_impacting",
                    reason=f"{key}_mismatch",
                    blocker=True,
                    legacy_signal=str(legacy_summary[key]),
                    eui_signal=str(safe_eui_summary[key]),
                )
            )

    if not _has_eui_evidence(
        safe_eui_summary,
        educational_context,
        capability_lookup,
        trust_report,
    ):
        differences.append(
            AEIConsumerMigrationDifference(
                difference_type="eui_missing",
                reason="no_eui_passive_evidence_available",
                blocker=False,
                legacy_signal="available",
                eui_signal="missing",
            )
        )

    if _truthy(legacy_summary.get("ambiguous")) and _has_eui_evidence(
        safe_eui_summary,
        educational_context,
        capability_lookup,
        trust_report,
    ):
        differences.append(
            AEIConsumerMigrationDifference(
                difference_type="legacy_ambiguous",
                reason="legacy_signal_ambiguous_eui_evidence_available",
                blocker=False,
                legacy_signal="ambiguous",
                eui_signal="available",
            )
        )

    if _eui_richer(legacy_summary, safe_eui_summary, educational_context, trust_report):
        differences.append(
            AEIConsumerMigrationDifference(
                difference_type="eui_richer",
                reason="eui_has_additional_context_or_trust_evidence",
                blocker=False,
                legacy_signal="limited",
                eui_signal="richer",
            )
        )

    if not differences:
        differences.append(
            AEIConsumerMigrationDifference(
                difference_type="equivalent",
                reason="sanitized_dual_read_summaries_are_equivalent",
                blocker=False,
            )
        )

    return tuple(differences)


def summarize_legacy_evaluation(suggestions: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Produce a sanitized legacy evaluation summary without raw answers or marks."""

    methods: set[str] = set()
    low_confidence_count = 0
    manual_review_signal_count = 0
    grounded_count = 0
    for suggestion in suggestions.values():
        method = str(suggestion.get("method") or "unknown")
        methods.add(method)
        confidence = _optional_float(suggestion.get("confidence"))
        if confidence is not None and confidence < 0.75:
            low_confidence_count += 1
            manual_review_signal_count += 1
        if method == "heuristic_fallback":
            manual_review_signal_count += 1
        if suggestion.get("grounded"):
            grounded_count += 1

    return {
        "available": True,
        "question_count": len(suggestions),
        "methods": tuple(sorted(methods)),
        "low_confidence_count": low_confidence_count,
        "manual_review_signal_count": manual_review_signal_count,
        "grounded_count": grounded_count,
    }


def summarize_aei_passive_capture(capture: Any | None) -> dict[str, Any]:
    """Produce a sanitized EUI-side summary from an AEI passive capture."""

    if capture is None:
        return {"available": False}

    questions = tuple(getattr(capture, "questions", ()) or ())
    policy_decisions: set[str] = set()
    manual_review_count = 0
    unsupported_count = 0
    for question in questions:
        policy = dict(getattr(question, "policy_decision", {}) or {})
        decision = str(policy.get("decision") or "unknown")
        policy_decisions.add(decision)
        if policy.get("manual_review_required"):
            manual_review_count += 1
        if policy.get("supported_capability") is False or decision == "unsupported":
            unsupported_count += 1

    shadow_comparison = getattr(capture, "shadow_comparison", None)
    return {
        "available": True,
        "question_count": int(getattr(capture, "question_count", len(questions)) or 0),
        "policy_decisions": tuple(sorted(policy_decisions)),
        "manual_review_count": manual_review_count,
        "unsupported_count": unsupported_count,
        "shadow_difference_count": (
            int(getattr(shadow_comparison, "difference_count", 0))
            if shadow_comparison is not None
            else 0
        ),
    }


def stable_aei_consumer_migration_id(
    *,
    subject_type: str,
    subject_ref: str,
    payload: dict[str, Any],
) -> str:
    """Build a deterministic comparison ID without embedding raw subject text."""

    digest_payload = {
        "subject_ref_hash": _digest(subject_ref),
        "payload": _json_safe(payload),
    }
    digest = _digest(digest_payload)
    return f"eui-aei-migration://{_slug(subject_type)}/{digest[:24]}"


def _merge_eui_summary(
    *,
    eui_summary: dict[str, Any] | None,
    educational_context: EducationalContext | None,
    capability_lookup: PlatformCapabilityLookupResult | None,
    trust_report: TrustReport | None,
) -> dict[str, Any]:
    merged = dict(eui_summary or {})
    if educational_context is not None:
        merged.update(
            {
                "context_available": True,
                "educational_identity_id": educational_context.educational_identity_id,
                "resolution_status": educational_context.resolution_status,
                "conflict_count": len(educational_context.conflicts),
                "ambiguity_count": len(educational_context.ambiguities),
            }
        )
    if capability_lookup is not None:
        merged.update(
            {
                "capability_mode": capability_lookup.mode,
                "capability_matched": capability_lookup.matched,
                "capability_conflict": capability_lookup.conflict,
            }
        )
    if trust_report is not None:
        merged.update(
            {
                "trust_report_id": trust_report.id,
                "trust_posture": trust_report.overall_posture,
                "trust_consumer_visibility": trust_report.consumer_visibility,
                "trust_review_required": trust_report.review_required,
            }
        )
    return merged


def _capture_status(comparison: AEIConsumerMigrationComparison) -> str:
    if any(difference.difference_type == "unsafe" for difference in comparison.differences):
        return "unsafe_difference"
    if comparison.difference_types != ("equivalent",):
        return "diverged"
    return "completed"


def _has_eui_evidence(
    eui_summary: dict[str, Any],
    educational_context: EducationalContext | None,
    capability_lookup: PlatformCapabilityLookupResult | None,
    trust_report: TrustReport | None,
) -> bool:
    if educational_context is not None or capability_lookup is not None or trust_report is not None:
        return True
    if eui_summary.get("available") is True:
        return True
    return any(
        key in eui_summary
        for key in (
            "educational_identity_id",
            "context_available",
            "capability_mode",
            "trust_report_id",
        )
    )


def _eui_richer(
    legacy_summary: dict[str, Any],
    eui_summary: dict[str, Any],
    educational_context: EducationalContext | None,
    trust_report: TrustReport | None,
) -> bool:
    if not _has_eui_evidence(eui_summary, educational_context, None, trust_report):
        return False
    if educational_context is not None and not legacy_summary.get("educational_context_id"):
        return True
    if trust_report is not None and not legacy_summary.get("trust_report_id"):
        return True
    return bool(
        eui_summary.get("educational_identity_id")
        and not legacy_summary.get("educational_identity_id")
    )


def _tenant_difference(
    legacy_summary: dict[str, Any],
    eui_summary: dict[str, Any],
) -> dict[str, Any] | None:
    legacy_tenant = legacy_summary.get("tenant_id")
    eui_tenant = eui_summary.get("tenant_id")
    if legacy_tenant is None or eui_tenant is None or str(legacy_tenant) == str(eui_tenant):
        return None
    return {
        "legacy_tenant_hash": _digest(str(legacy_tenant))[:12],
        "eui_tenant_hash": _digest(str(eui_tenant))[:12],
    }


def _redacted_summary(summary: dict[str, Any]) -> dict[str, Any]:
    """Keep only deterministic, bounded metadata approved for passive evidence."""

    redacted: dict[str, Any] = {}
    for key, value in summary.items():
        if key.lower() in {"student_answer", "raw_input", "ocr_text", "teacher_text", "name"}:
            continue
        redacted[key] = _json_safe(value)
    return redacted


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(val) for key, val in sorted(value.items())}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _digest(value: Any) -> str:
    payload = json.dumps(
        _json_safe(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _slug(value: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in value.lower()).strip("-") or "unknown"


def _duration_ms(started: float) -> float:
    return (time.perf_counter() - started) * 1000


def _optional_float(value: Any) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return None


def _truthy(value: Any) -> bool:
    return bool(value) is True

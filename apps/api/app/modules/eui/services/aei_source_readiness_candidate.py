"""Narrow AEI source-readiness candidate foundation for EUI Phase 7D.

This service consumes Phase 7C readiness scorecards and produces internal,
non-authoritative source-readiness candidates for the narrow
``context_metadata_only`` scope. It never switches AEI to EUI as source of
truth, never assigns marks, and never exposes user-facing evidence.
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from typing import Any

from app.core.platform_metrics import platform_metrics
from app.modules.eui.schemas.aei_source_readiness import (
    AEISourceReadinessCandidate,
    AEISourceReadinessCandidateScope,
    AEISourceReadinessCandidateState,
    AEISourceReadinessEvidenceClass,
    AEISourceReadinessScorecard,
)

EUI_AEI_SOURCE_READINESS_CANDIDATE_METRIC_TASK = (
    "eui_consumer_migration.source_readiness_candidate"
)
NARROW_AEI_CANDIDATE_SCOPE: AEISourceReadinessCandidateScope = "context_metadata_only"
READY_EVIDENCE_CLASSES: tuple[AEISourceReadinessEvidenceClass, ...] = (
    "educational_identity",
    "educational_context",
    "platform_capability",
    "trust_report",
    "readiness_scorecard",
    "safe_evidence_flags",
    "evidence_window",
    "behavior_equivalence",
    "performance",
    "rollback",
    "regression_coverage",
)


class AEISourceReadinessCandidateService:
    """Build internal source-readiness candidates from Phase 7C scorecards."""

    def build(
        self,
        *,
        scorecard: AEISourceReadinessScorecard,
        candidate_scope: AEISourceReadinessCandidateScope = NARROW_AEI_CANDIDATE_SCOPE,
        source_switch_requested: bool = False,
    ) -> AEISourceReadinessCandidate:
        """Produce a deterministic, non-authoritative source-readiness candidate."""

        started = time.perf_counter()
        platform_metrics.record_job_event(
            task=EUI_AEI_SOURCE_READINESS_CANDIDATE_METRIC_TASK,
            status="invoked",
        )
        state = _candidate_state(
            scorecard=scorecard,
            candidate_scope=candidate_scope,
            source_switch_requested=source_switch_requested,
        )
        blocked_classes = _blocked_evidence_classes(
            scorecard=scorecard,
            candidate_scope=candidate_scope,
            source_switch_requested=source_switch_requested,
        )
        candidate = AEISourceReadinessCandidate(
            id=stable_aei_source_readiness_candidate_id(
                tenant_id=scorecard.tenant_id,
                subject_type=scorecard.subject_type,
                scope_ref=scorecard.scope_ref,
                candidate_scope=candidate_scope,
                readiness_scorecard_ref=scorecard.id,
            ),
            tenant_id=scorecard.tenant_id,
            subject_type=scorecard.subject_type,
            scope_ref=scorecard.scope_ref,
            candidate_scope=candidate_scope,
            readiness_scorecard_ref=scorecard.id,
            readiness_review_posture=scorecard.review_posture,
            candidate_state=state,
            eligible_evidence_classes=READY_EVIDENCE_CLASSES
            if state == "ready_for_internal_trial"
            else (),
            blocked_evidence_classes=blocked_classes,
            source_flag_enabled=scorecard.source_flag_enabled,
            source_flag_status="enabled_inert"
            if scorecard.source_flag_enabled
            else "disabled_or_inert",
            source_switch_active=False,
            metadata={
                "authorization": "EUI-PH7D-NARROW-AEI-SOURCE-READINESS-AUTH-001",
                "passive": True,
                "internal_only": True,
                "source_of_truth": "legacy_aei_evaluation",
                "source_flag_inert": True,
                "source_switch_requested": source_switch_requested,
                "raw_content_captured": False,
                "ready_scope": NARROW_AEI_CANDIDATE_SCOPE,
            },
        )
        duration_ms = (time.perf_counter() - started) * 1000
        platform_metrics.record_job_event(
            task=EUI_AEI_SOURCE_READINESS_CANDIDATE_METRIC_TASK,
            status=candidate.candidate_state,
            duration_ms=duration_ms,
        )
        if candidate.candidate_state.startswith("blocked"):
            platform_metrics.record_job_event(
                task=EUI_AEI_SOURCE_READINESS_CANDIDATE_METRIC_TASK,
                status="blocked",
            )
        if candidate.candidate_state.startswith("not_ready"):
            platform_metrics.record_job_event(
                task=EUI_AEI_SOURCE_READINESS_CANDIDATE_METRIC_TASK,
                status="not_ready",
            )
        return candidate


def stable_aei_source_readiness_candidate_id(
    *,
    tenant_id: uuid.UUID,
    subject_type: str,
    scope_ref: str,
    candidate_scope: str,
    readiness_scorecard_ref: str,
) -> str:
    """Build a deterministic candidate ID without embedding raw scope text."""

    payload = {
        "tenant_id_hash": _digest(str(tenant_id)),
        "scope_ref_hash": _digest(scope_ref),
        "candidate_scope": candidate_scope,
        "readiness_scorecard_ref": readiness_scorecard_ref,
    }
    return (
        f"eui-aei-source-candidate://{_slug(subject_type)}/"
        f"{_slug(candidate_scope)}/{_digest(payload)[:24]}"
    )


def _candidate_state(
    *,
    scorecard: AEISourceReadinessScorecard,
    candidate_scope: str,
    source_switch_requested: bool,
) -> AEISourceReadinessCandidateState:
    if source_switch_requested:
        return "blocked_unsafe"
    if scorecard.review_posture == "blocked_unsafe":
        return "blocked_unsafe"
    if candidate_scope != NARROW_AEI_CANDIDATE_SCOPE:
        return "blocked_product_impacting"
    if scorecard.review_posture == "blocked_product_impacting":
        return "blocked_product_impacting"
    if scorecard.review_posture == "needs_capability_work":
        return "not_ready_capability_work"
    if scorecard.review_posture == "needs_more_evidence":
        return "not_ready_more_evidence"
    if scorecard.review_posture == "eligible" and scorecard.eligible:
        return "ready_for_internal_trial"
    return "not_ready_more_evidence"


def _blocked_evidence_classes(
    *,
    scorecard: AEISourceReadinessScorecard,
    candidate_scope: str,
    source_switch_requested: bool,
) -> tuple[AEISourceReadinessEvidenceClass, ...]:
    blocked: set[AEISourceReadinessEvidenceClass] = set()
    if source_switch_requested:
        blocked.add("safety")
        blocked.add("rollback")
    if candidate_scope != NARROW_AEI_CANDIDATE_SCOPE:
        blocked.add("product_behavior")
    for dimension in scorecard.dimensions:
        if dimension.status == "passed":
            continue
        blocked.update(_dimension_evidence_classes(dimension.dimension))
    return tuple(sorted(blocked))


def _dimension_evidence_classes(dimension: str) -> tuple[AEISourceReadinessEvidenceClass, ...]:
    mapping: dict[str, tuple[AEISourceReadinessEvidenceClass, ...]] = {
        "behavior_equivalence": ("behavior_equivalence",),
        "evidence_completeness": (
            "educational_identity",
            "educational_context",
            "platform_capability",
            "trust_report",
            "safe_evidence_flags",
        ),
        "capability_posture": ("platform_capability",),
        "trust_posture": ("trust_report",),
        "tenant_safety": ("tenant_safety",),
        "product_impacting_divergence": ("product_behavior",),
        "unsafe_divergence": ("safety",),
        "performance": ("performance",),
        "rollback": ("rollback",),
        "regression_coverage": ("regression_coverage",),
        "evidence_window": ("evidence_window",),
    }
    return mapping.get(dimension, ("safe_evidence_flags",))


def _digest(value: Any) -> str:
    payload = json.dumps(
        _json_safe(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


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


def _slug(value: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in value.lower()).strip("-") or "unknown"

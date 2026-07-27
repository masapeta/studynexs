"""Narrow AEI source-readiness trial foundation for EUI Phase 7E.

This service consumes Phase 7D source-readiness candidates and produces
internal, non-authoritative trial results for the narrow
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
    AEISourceReadinessEvidenceClass,
    AEISourceReadinessTrialMode,
    AEISourceReadinessTrialResult,
    AEISourceReadinessTrialState,
)
from app.modules.eui.services.aei_source_readiness_candidate import (
    NARROW_AEI_CANDIDATE_SCOPE,
)

EUI_AEI_SOURCE_READINESS_TRIAL_METRIC_TASK = (
    "eui_consumer_migration.source_readiness_trial"
)
INTERNAL_METADATA_TRIAL_MODE: AEISourceReadinessTrialMode = "internal_metadata_trial"


class AEISourceReadinessTrialService:
    """Build internal source-readiness trial results from Phase 7D candidates."""

    def build(
        self,
        *,
        candidate: AEISourceReadinessCandidate | None,
        tenant_id: uuid.UUID | None = None,
        subject_type: str | None = None,
        scope_ref: str | None = None,
        source_switch_requested: bool = False,
        legacy_source_of_truth_confirmed: bool = True,
        trial_enabled: bool = True,
    ) -> AEISourceReadinessTrialResult:
        """Produce a deterministic, non-authoritative source-readiness trial."""

        started = time.perf_counter()
        platform_metrics.record_job_event(
            task=EUI_AEI_SOURCE_READINESS_TRIAL_METRIC_TASK,
            status="invoked",
        )
        if candidate is None and (
            tenant_id is None or subject_type is None or scope_ref is None
        ):
            raise ValueError(
                "tenant_id, subject_type, and scope_ref are required when "
                "building a trial result without a candidate"
            )

        state = _trial_state(
            candidate=candidate,
            source_switch_requested=source_switch_requested,
            legacy_source_of_truth_confirmed=legacy_source_of_truth_confirmed,
            trial_enabled=trial_enabled,
        )
        selected_classes = _selected_evidence_classes(candidate, state)
        blocked_classes = _blocked_evidence_classes(
            candidate=candidate,
            source_switch_requested=source_switch_requested,
            legacy_source_of_truth_confirmed=legacy_source_of_truth_confirmed,
            trial_enabled=trial_enabled,
        )
        if candidate is not None:
            resolved_tenant_id = tenant_id or candidate.tenant_id
            resolved_subject_type = subject_type or candidate.subject_type
            resolved_scope_ref = scope_ref or candidate.scope_ref
        else:
            assert tenant_id is not None
            assert subject_type is not None
            assert scope_ref is not None
            resolved_tenant_id = tenant_id
            resolved_subject_type = subject_type
            resolved_scope_ref = scope_ref
        candidate_ref = candidate.id if candidate is not None else None
        candidate_scope = (
            candidate.candidate_scope if candidate is not None else NARROW_AEI_CANDIDATE_SCOPE
        )
        source_flag_enabled = candidate.source_flag_enabled if candidate else False
        result = AEISourceReadinessTrialResult(
            id=stable_aei_source_readiness_trial_id(
                tenant_id=resolved_tenant_id,
                subject_type=str(resolved_subject_type),
                scope_ref=resolved_scope_ref,
                candidate_ref=candidate_ref,
                candidate_scope=candidate_scope,
                trial_mode=INTERNAL_METADATA_TRIAL_MODE,
            ),
            tenant_id=resolved_tenant_id,
            subject_type=resolved_subject_type,  # type: ignore[arg-type]
            scope_ref=resolved_scope_ref,
            candidate_ref=candidate_ref,
            candidate_scope=candidate_scope,
            trial_mode=INTERNAL_METADATA_TRIAL_MODE,
            trial_state=state,
            selected_evidence_classes=selected_classes,
            blocked_evidence_classes=blocked_classes,
            legacy_source_of_truth_confirmed=legacy_source_of_truth_confirmed,
            source_flag_enabled=source_flag_enabled,
            source_flag_status="enabled_inert"
            if source_flag_enabled
            else "disabled_or_inert",
            source_switch_active=False,
            metadata={
                "authorization": "EUI-PH7E-NARROW-AEI-SOURCE-READINESS-TRIAL-AUTH-001",
                "passive": True,
                "internal_only": True,
                "source_of_truth": "legacy_aei_evaluation",
                "source_flag_inert": True,
                "source_switch_requested": source_switch_requested,
                "raw_content_captured": False,
                "trial_enabled": trial_enabled,
                "trial_scope": NARROW_AEI_CANDIDATE_SCOPE,
            },
        )
        duration_ms = (time.perf_counter() - started) * 1000
        platform_metrics.record_job_event(
            task=EUI_AEI_SOURCE_READINESS_TRIAL_METRIC_TASK,
            status=result.trial_state,
            duration_ms=duration_ms,
        )
        if result.trial_state.startswith("trial_blocked"):
            platform_metrics.record_job_event(
                task=EUI_AEI_SOURCE_READINESS_TRIAL_METRIC_TASK,
                status="blocked",
            )
        if result.trial_state == "trial_not_ready":
            platform_metrics.record_job_event(
                task=EUI_AEI_SOURCE_READINESS_TRIAL_METRIC_TASK,
                status="not_ready",
            )
        if result.trial_state == "trial_skipped":
            platform_metrics.record_job_event(
                task=EUI_AEI_SOURCE_READINESS_TRIAL_METRIC_TASK,
                status="skipped",
            )
        return result


def stable_aei_source_readiness_trial_id(
    *,
    tenant_id: uuid.UUID,
    subject_type: str,
    scope_ref: str,
    candidate_ref: str | None,
    candidate_scope: str,
    trial_mode: str,
) -> str:
    """Build a deterministic trial ID without embedding raw scope text."""

    payload = {
        "tenant_id_hash": _digest(str(tenant_id)),
        "scope_ref_hash": _digest(scope_ref),
        "candidate_ref": candidate_ref,
        "candidate_scope": candidate_scope,
        "trial_mode": trial_mode,
    }
    return (
        f"eui-aei-source-trial://{_slug(subject_type)}/"
        f"{_slug(trial_mode)}/{_digest(payload)[:24]}"
    )


def _trial_state(
    *,
    candidate: AEISourceReadinessCandidate | None,
    source_switch_requested: bool,
    legacy_source_of_truth_confirmed: bool,
    trial_enabled: bool,
) -> AEISourceReadinessTrialState:
    if not trial_enabled or candidate is None:
        return "trial_skipped"
    if source_switch_requested or not legacy_source_of_truth_confirmed:
        return "trial_blocked_unsafe"
    if candidate.source_switch_active:
        return "trial_blocked_unsafe"
    if candidate.candidate_state == "blocked_unsafe":
        return "trial_blocked_unsafe"
    if candidate.candidate_scope != NARROW_AEI_CANDIDATE_SCOPE:
        return "trial_blocked_product_impacting"
    if candidate.candidate_state == "blocked_product_impacting":
        return "trial_blocked_product_impacting"
    if candidate.candidate_state in {
        "not_ready_more_evidence",
        "not_ready_capability_work",
    }:
        return "trial_not_ready"
    if candidate.candidate_state == "ready_for_internal_trial":
        return "trial_ready"
    return "trial_not_ready"


def _selected_evidence_classes(
    candidate: AEISourceReadinessCandidate | None,
    state: str,
) -> tuple[AEISourceReadinessEvidenceClass, ...]:
    if candidate is None or state != "trial_ready":
        return ()
    return tuple(sorted(candidate.eligible_evidence_classes))


def _blocked_evidence_classes(
    *,
    candidate: AEISourceReadinessCandidate | None,
    source_switch_requested: bool,
    legacy_source_of_truth_confirmed: bool,
    trial_enabled: bool,
) -> tuple[AEISourceReadinessEvidenceClass, ...]:
    blocked: set[AEISourceReadinessEvidenceClass] = set()
    if not trial_enabled:
        blocked.add("safe_evidence_flags")
    if candidate is None:
        blocked.add("readiness_scorecard")
    else:
        blocked.update(candidate.blocked_evidence_classes)
        if candidate.candidate_scope != NARROW_AEI_CANDIDATE_SCOPE:
            blocked.add("product_behavior")
        if candidate.source_switch_active:
            blocked.add("safety")
            blocked.add("rollback")
    if source_switch_requested:
        blocked.add("safety")
        blocked.add("rollback")
    if not legacy_source_of_truth_confirmed:
        blocked.add("safety")
        blocked.add("rollback")
    return tuple(sorted(blocked))


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
    slug = "".join(ch if ch.isalnum() else "-" for ch in value.lower()).strip("-")
    return slug or "unknown"

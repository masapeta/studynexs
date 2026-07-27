"""EUI Phase 7E - narrow AEI source-readiness trial foundation."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from app.core.platform_metrics import PlatformMetricsRegistry
from app.modules.eui.schemas.aei_source_readiness import (
    AEISourceReadinessCandidate,
    AEISourceReadinessTrialResult,
)
from app.modules.eui.services import aei_source_readiness_trial as trials
from app.modules.eui.services.aei_source_readiness_trial import (
    AEISourceReadinessTrialService,
    stable_aei_source_readiness_trial_id,
)

TENANT_ID = uuid.UUID("11111111-1111-4111-8111-111111111111")


def test_source_readiness_trial_result_is_strict_internal_and_non_authoritative():
    result = AEISourceReadinessTrialResult(
        id="eui-aei-source-trial://answer-sheet-evaluation/internal-metadata-trial/abc123",
        tenant_id=TENANT_ID,
        subject_type="answer_sheet_evaluation",
        scope_ref="answer_sheet_evaluation:test",
        candidate_ref="eui-aei-source-candidate://answer-sheet-evaluation/context-metadata-only/abc123",
        trial_state="trial_ready",
        selected_evidence_classes=("educational_identity", "trust_report"),
    )

    dumped = result.model_dump(mode="json")
    assert dumped["tenant_id"] == str(TENANT_ID)
    assert result.authoritative is False
    assert result.trial_ready is True
    assert result.internal_only is True
    assert result.source_switch_active is False

    with pytest.raises(ValidationError):
        result.scope_ref = "changed"  # type: ignore[misc]

    with pytest.raises(ValidationError):
        AEISourceReadinessTrialResult(
            id="eui-aei-source-trial://answer-sheet-evaluation/internal-metadata-trial/abc123",
            tenant_id=TENANT_ID,
            subject_type="answer_sheet_evaluation",
            scope_ref="answer_sheet_evaluation:test",
            candidate_ref="eui-aei-source-candidate://answer-sheet-evaluation/context-metadata-only/abc123",
            trial_state="trial_ready",
            student_answer="raw answer",  # type: ignore[call-arg]
        )

    with pytest.raises(ValidationError):
        AEISourceReadinessTrialResult(
            id="eui-aei-source-trial://answer-sheet-evaluation/internal-metadata-trial/abc123",
            tenant_id=TENANT_ID,
            subject_type="answer_sheet_evaluation",
            scope_ref="answer_sheet_evaluation:test",
            candidate_ref="eui-aei-source-candidate://answer-sheet-evaluation/context-metadata-only/abc123",
            trial_state="trial_ready",
            source_switch_active=True,  # type: ignore[arg-type]
        )

    with pytest.raises(ValidationError):
        AEISourceReadinessTrialResult(
            id="eui-aei-source-trial://answer-sheet-evaluation/internal-metadata-trial/abc123",
            tenant_id=TENANT_ID,
            subject_type="answer_sheet_evaluation",
            scope_ref="answer_sheet_evaluation:test",
            candidate_ref="eui-aei-source-candidate://answer-sheet-evaluation/marks-source/abc123",
            candidate_scope="marks_source",
            trial_state="trial_ready",
        )

    with pytest.raises(ValidationError):
        AEISourceReadinessTrialResult(
            id="eui-aei-source-trial://answer-sheet-evaluation/internal-metadata-trial/abc123",
            tenant_id=TENANT_ID,
            subject_type="answer_sheet_evaluation",
            scope_ref="answer_sheet_evaluation:test",
            candidate_ref="eui-aei-source-candidate://answer-sheet-evaluation/context-metadata-only/abc123",
            trial_state="trial_ready",
            legacy_source_of_truth_confirmed=False,
        )


def test_source_readiness_trial_id_is_deterministic_and_avoids_scope_text():
    first = stable_aei_source_readiness_trial_id(
        tenant_id=TENANT_ID,
        subject_type="answer_sheet_evaluation",
        scope_ref="answer_sheet_evaluation:secret-school-context",
        candidate_ref="eui-aei-source-candidate://answer-sheet-evaluation/context-metadata-only/candidate-a",
        candidate_scope="context_metadata_only",
        trial_mode="internal_metadata_trial",
    )
    second = stable_aei_source_readiness_trial_id(
        tenant_id=TENANT_ID,
        subject_type="answer_sheet_evaluation",
        scope_ref="answer_sheet_evaluation:secret-school-context",
        candidate_ref="eui-aei-source-candidate://answer-sheet-evaluation/context-metadata-only/candidate-a",
        candidate_scope="context_metadata_only",
        trial_mode="internal_metadata_trial",
    )

    assert first == second
    assert first.startswith(
        "eui-aei-source-trial://answer-sheet-evaluation/internal-metadata-trial/"
    )
    assert "secret" not in first
    assert str(TENANT_ID) not in first


def test_trial_service_creates_ready_internal_trial_for_ready_candidate(monkeypatch):
    metrics = PlatformMetricsRegistry()
    monkeypatch.setattr(trials, "platform_metrics", metrics)

    result = AEISourceReadinessTrialService().build(
        candidate=_candidate("ready_for_internal_trial"),
    )

    assert result.trial_state == "trial_ready"
    assert result.trial_ready is True
    assert result.authoritative is False
    assert result.candidate_scope == "context_metadata_only"
    assert result.source_switch_active is False
    assert result.legacy_source_of_truth_confirmed is True
    assert result.metadata["source_of_truth"] == "legacy_aei_evaluation"
    assert result.metadata["raw_content_captured"] is False
    assert "readiness_scorecard" in result.selected_evidence_classes
    assert result.blocked_evidence_classes == ()
    assert metrics.snapshot()["jobs_by_status"]["invoked"] == 1
    assert metrics.snapshot()["jobs_by_status"]["trial_ready"] == 1


def test_trial_service_maps_not_ready_candidate_to_trial_not_ready():
    result = AEISourceReadinessTrialService().build(
        candidate=_candidate(
            "not_ready_more_evidence",
            blocked_evidence_classes=("evidence_window",),
        ),
    )

    assert result.trial_state == "trial_not_ready"
    assert result.trial_ready is False
    assert "evidence_window" in result.blocked_evidence_classes


def test_trial_service_blocks_product_impacting_candidate():
    result = AEISourceReadinessTrialService().build(
        candidate=_candidate(
            "blocked_product_impacting",
            blocked_evidence_classes=("product_behavior",),
        ),
    )

    assert result.trial_state == "trial_blocked_product_impacting"
    assert "product_behavior" in result.blocked_evidence_classes


def test_trial_service_blocks_unsafe_before_product_impacting():
    result = AEISourceReadinessTrialService().build(
        candidate=_candidate(
            "blocked_unsafe",
            blocked_evidence_classes=("product_behavior", "safety"),
        ),
    )

    assert result.trial_state == "trial_blocked_unsafe"
    assert "safety" in result.blocked_evidence_classes
    assert "product_behavior" in result.blocked_evidence_classes


def test_trial_service_blocks_scope_broader_than_context_metadata_only():
    result = AEISourceReadinessTrialService().build(
        candidate=_candidate("blocked_product_impacting", candidate_scope="marks_source"),
    )

    assert result.trial_state == "trial_blocked_product_impacting"
    assert result.candidate_scope == "marks_source"
    assert "product_behavior" in result.blocked_evidence_classes
    assert result.source_switch_active is False


def test_trial_service_blocks_source_switch_attempt_but_keeps_switch_inactive():
    result = AEISourceReadinessTrialService().build(
        candidate=_candidate("ready_for_internal_trial", source_flag_enabled=True),
        source_switch_requested=True,
    )

    assert result.trial_state == "trial_blocked_unsafe"
    assert result.source_flag_enabled is True
    assert result.source_flag_status == "enabled_inert"
    assert result.source_switch_active is False
    assert result.metadata["source_switch_requested"] is True
    assert "rollback" in result.blocked_evidence_classes
    assert "safety" in result.blocked_evidence_classes


def test_trial_service_skips_missing_or_disabled_trial():
    missing = AEISourceReadinessTrialService().build(
        candidate=None,
        tenant_id=TENANT_ID,
        subject_type="answer_sheet_evaluation",
        scope_ref="answer_sheet_evaluation:missing",
    )
    disabled = AEISourceReadinessTrialService().build(
        candidate=_candidate("ready_for_internal_trial"),
        trial_enabled=False,
    )

    assert missing.trial_state == "trial_skipped"
    assert "readiness_scorecard" in missing.blocked_evidence_classes
    assert disabled.trial_state == "trial_skipped"
    assert "safe_evidence_flags" in disabled.blocked_evidence_classes


def test_trial_service_blocks_missing_legacy_source_confirmation():
    result = AEISourceReadinessTrialService().build(
        candidate=_candidate("ready_for_internal_trial"),
        legacy_source_of_truth_confirmed=False,
    )

    assert result.trial_state == "trial_blocked_unsafe"
    assert result.legacy_source_of_truth_confirmed is False
    assert "rollback" in result.blocked_evidence_classes
    assert "safety" in result.blocked_evidence_classes


def _candidate(
    candidate_state: str,
    *,
    candidate_scope: str = "context_metadata_only",
    blocked_evidence_classes: tuple[str, ...] = (),
    source_flag_enabled: bool = False,
) -> AEISourceReadinessCandidate:
    posture_by_state = {
        "ready_for_internal_trial": "eligible",
        "not_ready_more_evidence": "needs_more_evidence",
        "not_ready_capability_work": "needs_capability_work",
        "blocked_product_impacting": "blocked_product_impacting",
        "blocked_unsafe": "blocked_unsafe",
    }
    return AEISourceReadinessCandidate(
        id=f"eui-aei-source-candidate://answer-sheet-evaluation/{candidate_scope}/{candidate_state}",
        tenant_id=TENANT_ID,
        subject_type="answer_sheet_evaluation",
        scope_ref=f"answer_sheet_evaluation:{candidate_state}",
        candidate_scope=candidate_scope,  # type: ignore[arg-type]
        readiness_scorecard_ref=f"eui-aei-readiness://answer-sheet-evaluation/{candidate_state}",
        readiness_review_posture=posture_by_state[candidate_state],  # type: ignore[arg-type]
        candidate_state=candidate_state,  # type: ignore[arg-type]
        eligible_evidence_classes=(
            (
                "educational_identity",
                "educational_context",
                "platform_capability",
                "trust_report",
                "readiness_scorecard",
            )
            if candidate_state == "ready_for_internal_trial"
            else ()
        ),
        blocked_evidence_classes=blocked_evidence_classes,  # type: ignore[arg-type]
        source_flag_enabled=source_flag_enabled,
        source_switch_active=False,
    )

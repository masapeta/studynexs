"""EUI Phase 7D - narrow AEI source-readiness candidate foundation."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from app.core.platform_metrics import PlatformMetricsRegistry
from app.modules.eui.schemas.aei_source_readiness import (
    AEISourceReadinessCandidate,
    AEISourceReadinessDimensionResult,
    AEISourceReadinessScorecard,
)
from app.modules.eui.services import aei_source_readiness_candidate as candidates
from app.modules.eui.services.aei_source_readiness_candidate import (
    AEISourceReadinessCandidateService,
    stable_aei_source_readiness_candidate_id,
)

TENANT_ID = uuid.UUID("11111111-1111-4111-8111-111111111111")


def test_source_readiness_candidate_is_strict_internal_and_non_authoritative():
    candidate = AEISourceReadinessCandidate(
        id="eui-aei-source-candidate://answer-sheet-evaluation/context-metadata-only/abc123",
        tenant_id=TENANT_ID,
        subject_type="answer_sheet_evaluation",
        scope_ref="answer_sheet_evaluation:test",
        readiness_scorecard_ref="eui-aei-readiness://answer-sheet-evaluation/abc123",
        readiness_review_posture="eligible",
        candidate_state="ready_for_internal_trial",
        eligible_evidence_classes=("educational_identity", "trust_report"),
    )

    dumped = candidate.model_dump(mode="json")
    assert dumped["tenant_id"] == str(TENANT_ID)
    assert candidate.authoritative is False
    assert candidate.ready_for_internal_trial is True
    assert candidate.internal_only is True
    assert candidate.source_switch_active is False

    with pytest.raises(ValidationError):
        candidate.scope_ref = "changed"  # type: ignore[misc]

    with pytest.raises(ValidationError):
        AEISourceReadinessCandidate(
            id="eui-aei-source-candidate://answer-sheet-evaluation/context-metadata-only/abc123",
            tenant_id=TENANT_ID,
            subject_type="answer_sheet_evaluation",
            scope_ref="answer_sheet_evaluation:test",
            readiness_scorecard_ref="eui-aei-readiness://answer-sheet-evaluation/abc123",
            readiness_review_posture="eligible",
            candidate_state="ready_for_internal_trial",
            student_answer="raw answer",  # type: ignore[call-arg]
        )

    with pytest.raises(ValidationError):
        AEISourceReadinessCandidate(
            id="eui-aei-source-candidate://answer-sheet-evaluation/context-metadata-only/abc123",
            tenant_id=TENANT_ID,
            subject_type="answer_sheet_evaluation",
            scope_ref="answer_sheet_evaluation:test",
            readiness_scorecard_ref="eui-aei-readiness://answer-sheet-evaluation/abc123",
            readiness_review_posture="eligible",
            candidate_state="ready_for_internal_trial",
            source_switch_active=True,  # type: ignore[arg-type]
        )

    with pytest.raises(ValidationError):
        AEISourceReadinessCandidate(
            id="eui-aei-source-candidate://answer-sheet-evaluation/marks-source/abc123",
            tenant_id=TENANT_ID,
            subject_type="answer_sheet_evaluation",
            scope_ref="answer_sheet_evaluation:test",
            candidate_scope="marks_source",
            readiness_scorecard_ref="eui-aei-readiness://answer-sheet-evaluation/abc123",
            readiness_review_posture="eligible",
            candidate_state="ready_for_internal_trial",
        )


def test_source_readiness_candidate_id_is_deterministic_and_avoids_scope_text():
    first = stable_aei_source_readiness_candidate_id(
        tenant_id=TENANT_ID,
        subject_type="answer_sheet_evaluation",
        scope_ref="answer_sheet_evaluation:secret-school-context",
        candidate_scope="context_metadata_only",
        readiness_scorecard_ref="eui-aei-readiness://answer-sheet-evaluation/readiness-a",
    )
    second = stable_aei_source_readiness_candidate_id(
        tenant_id=TENANT_ID,
        subject_type="answer_sheet_evaluation",
        scope_ref="answer_sheet_evaluation:secret-school-context",
        candidate_scope="context_metadata_only",
        readiness_scorecard_ref="eui-aei-readiness://answer-sheet-evaluation/readiness-a",
    )

    assert first == second
    assert first.startswith(
        "eui-aei-source-candidate://answer-sheet-evaluation/context-metadata-only/"
    )
    assert "secret" not in first
    assert str(TENANT_ID) not in first


def test_candidate_service_creates_ready_internal_trial_for_eligible_scorecard(
    monkeypatch,
):
    metrics = PlatformMetricsRegistry()
    monkeypatch.setattr(candidates, "platform_metrics", metrics)

    candidate = AEISourceReadinessCandidateService().build(
        scorecard=_scorecard("eligible", eligible=True),
    )

    assert candidate.candidate_state == "ready_for_internal_trial"
    assert candidate.ready_for_internal_trial is True
    assert candidate.authoritative is False
    assert candidate.candidate_scope == "context_metadata_only"
    assert candidate.source_switch_active is False
    assert candidate.metadata["source_of_truth"] == "legacy_aei_evaluation"
    assert candidate.metadata["raw_content_captured"] is False
    assert "readiness_scorecard" in candidate.eligible_evidence_classes
    assert candidate.blocked_evidence_classes == ()
    assert metrics.snapshot()["jobs_by_status"]["invoked"] == 1
    assert metrics.snapshot()["jobs_by_status"]["ready_for_internal_trial"] == 1


def test_candidate_service_maps_insufficient_evidence_to_not_ready():
    candidate = AEISourceReadinessCandidateService().build(
        scorecard=_scorecard(
            "needs_more_evidence",
            dimensions=(
                _dimension("evidence_window", "needs_more_evidence"),
            ),
        ),
    )

    assert candidate.candidate_state == "not_ready_more_evidence"
    assert candidate.ready_for_internal_trial is False
    assert "evidence_window" in candidate.blocked_evidence_classes


def test_candidate_service_maps_capability_work_to_not_ready():
    candidate = AEISourceReadinessCandidateService().build(
        scorecard=_scorecard(
            "needs_capability_work",
            dimensions=(
                _dimension("capability_posture", "needs_capability_work"),
            ),
        ),
    )

    assert candidate.candidate_state == "not_ready_capability_work"
    assert "platform_capability" in candidate.blocked_evidence_classes


def test_candidate_service_blocks_product_impacting_scorecard():
    candidate = AEISourceReadinessCandidateService().build(
        scorecard=_scorecard(
            "blocked_product_impacting",
            dimensions=(
                _dimension("product_impacting_divergence", "blocked_product_impacting"),
            ),
            blocker_categories=("blocked_product_impacting",),
        ),
    )

    assert candidate.candidate_state == "blocked_product_impacting"
    assert "product_behavior" in candidate.blocked_evidence_classes


def test_candidate_service_blocks_unsafe_before_product_impacting():
    candidate = AEISourceReadinessCandidateService().build(
        scorecard=_scorecard(
            "blocked_unsafe",
            dimensions=(
                _dimension("unsafe_divergence", "blocked_unsafe"),
                _dimension("product_impacting_divergence", "blocked_product_impacting"),
            ),
            blocker_categories=("blocked_product_impacting", "blocked_unsafe"),
        ),
    )

    assert candidate.candidate_state == "blocked_unsafe"
    assert "safety" in candidate.blocked_evidence_classes
    assert "product_behavior" in candidate.blocked_evidence_classes


def test_candidate_service_blocks_scope_broader_than_context_metadata_only():
    candidate = AEISourceReadinessCandidateService().build(
        scorecard=_scorecard("eligible", eligible=True),
        candidate_scope="marks_source",
    )

    assert candidate.candidate_state == "blocked_product_impacting"
    assert candidate.candidate_scope == "marks_source"
    assert "product_behavior" in candidate.blocked_evidence_classes
    assert candidate.source_switch_active is False


def test_candidate_service_blocks_source_switch_attempt_but_keeps_switch_inactive():
    candidate = AEISourceReadinessCandidateService().build(
        scorecard=_scorecard("eligible", eligible=True, source_flag_enabled=True),
        source_switch_requested=True,
    )

    assert candidate.candidate_state == "blocked_unsafe"
    assert candidate.source_flag_enabled is True
    assert candidate.source_flag_status == "enabled_inert"
    assert candidate.source_switch_active is False
    assert candidate.metadata["source_switch_requested"] is True
    assert "rollback" in candidate.blocked_evidence_classes
    assert "safety" in candidate.blocked_evidence_classes


def _scorecard(
    review_posture: str,
    *,
    eligible: bool = False,
    dimensions: tuple[AEISourceReadinessDimensionResult, ...] = (),
    blocker_categories: tuple[str, ...] = (),
    source_flag_enabled: bool = False,
) -> AEISourceReadinessScorecard:
    return AEISourceReadinessScorecard(
        id=f"eui-aei-readiness://answer-sheet-evaluation/{review_posture}",
        tenant_id=TENANT_ID,
        subject_type="answer_sheet_evaluation",
        scope_ref=f"answer_sheet_evaluation:{review_posture}",
        review_posture=review_posture,  # type: ignore[arg-type]
        eligible=eligible,
        evidence_window_required=2,
        evidence_window_count=2 if eligible else 1,
        reviewed_comparison_ids=("comparison-a", "comparison-b") if eligible else (),
        dimensions=dimensions,
        blocker_categories=blocker_categories,
        source_flag_enabled=source_flag_enabled,
    )


def _dimension(
    dimension: str,
    status: str,
) -> AEISourceReadinessDimensionResult:
    return AEISourceReadinessDimensionResult(
        dimension=dimension,  # type: ignore[arg-type]
        status=status,  # type: ignore[arg-type]
        reason=f"{dimension}_{status}",
        blocker=status.startswith("blocked"),
    )

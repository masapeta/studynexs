"""EUI Phase 7C - AEI divergence readiness review foundation."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from app.core.platform_metrics import PlatformMetricsRegistry
from app.modules.eui.schemas.aei_consumer_migration import (
    AEIConsumerMigrationComparison,
    AEIConsumerMigrationDifference,
)
from app.modules.eui.schemas.aei_source_readiness import (
    AEISourceReadinessDimensionResult,
    AEISourceReadinessScorecard,
)
from app.modules.eui.services import aei_divergence_readiness as readiness
from app.modules.eui.services.aei_divergence_readiness import (
    AEIDivergenceReadinessReviewService,
    stable_aei_source_readiness_id,
)

TENANT_ID = uuid.UUID("11111111-1111-4111-8111-111111111111")


def test_source_readiness_scorecard_is_strict_internal_and_non_authoritative():
    dimension = AEISourceReadinessDimensionResult(
        dimension="rollback",
        status="passed",
        reason="source_flag_inert",
    )
    scorecard = AEISourceReadinessScorecard(
        id="eui-aei-readiness://answer-sheet-evaluation/abc123",
        tenant_id=TENANT_ID,
        subject_type="answer_sheet_evaluation",
        scope_ref="answer_sheet_evaluation:test",
        review_posture="eligible",
        eligible=True,
        dimensions=(dimension,),
    )

    dumped = scorecard.model_dump(mode="json")
    assert dumped["tenant_id"] == str(TENANT_ID)
    assert scorecard.authoritative is False
    assert scorecard.internal_only is True
    assert scorecard.source_switch_active is False

    with pytest.raises(ValidationError):
        scorecard.scope_ref = "changed"  # type: ignore[misc]

    with pytest.raises(ValidationError):
        AEISourceReadinessScorecard(
            id="eui-aei-readiness://answer-sheet-evaluation/abc123",
            tenant_id=TENANT_ID,
            subject_type="answer_sheet_evaluation",
            scope_ref="answer_sheet_evaluation:test",
            review_posture="eligible",
            eligible=True,
            student_answer="raw answer",  # type: ignore[call-arg]
        )

    with pytest.raises(ValidationError):
        AEISourceReadinessScorecard(
            id="eui-aei-readiness://answer-sheet-evaluation/abc123",
            tenant_id=TENANT_ID,
            subject_type="answer_sheet_evaluation",
            scope_ref="answer_sheet_evaluation:test",
            review_posture="eligible",
            eligible=True,
            source_switch_active=True,  # type: ignore[arg-type]
        )


def test_source_readiness_id_is_deterministic_and_avoids_scope_text():
    first = stable_aei_source_readiness_id(
        subject_type="answer_sheet_evaluation",
        scope_ref="answer_sheet_evaluation:secret-school-context",
        comparison_ids=("b", "a"),
        review_posture="eligible",
    )
    second = stable_aei_source_readiness_id(
        subject_type="answer_sheet_evaluation",
        scope_ref="answer_sheet_evaluation:secret-school-context",
        comparison_ids=("a", "b"),
        review_posture="eligible",
    )

    assert first == second
    assert first.startswith("eui-aei-readiness://answer-sheet-evaluation/")
    assert "secret" not in first


def test_readiness_review_marks_clean_repeated_evidence_eligible(monkeypatch):
    metrics = PlatformMetricsRegistry()
    monkeypatch.setattr(readiness, "platform_metrics", metrics)

    scorecard = AEIDivergenceReadinessReviewService().review(
        tenant_id=TENANT_ID,
        subject_type="answer_sheet_evaluation",
        scope_ref="answer_sheet_evaluation:eligible",
        comparisons=(
            _comparison("eligible-a", "equivalent"),
            _comparison("eligible-b", "eui_richer"),
        ),
    )

    assert scorecard.review_posture == "eligible"
    assert scorecard.eligible is True
    assert scorecard.authoritative is False
    assert scorecard.source_switch_active is False
    assert scorecard.source_flag_enabled is False
    assert scorecard.blocker_categories == ()
    assert _dimension_status(scorecard, "evidence_window") == "passed"
    assert metrics.snapshot()["jobs_by_status"]["invoked"] == 1
    assert metrics.snapshot()["jobs_by_status"]["eligible"] == 1


def test_readiness_review_requires_minimum_evidence_window():
    scorecard = AEIDivergenceReadinessReviewService().review(
        tenant_id=TENANT_ID,
        subject_type="answer_sheet_evaluation",
        scope_ref="answer_sheet_evaluation:needs-more",
        comparisons=(_comparison("single-cycle", "equivalent"),),
    )

    assert scorecard.review_posture == "needs_more_evidence"
    assert scorecard.eligible is False
    assert _dimension_status(scorecard, "evidence_window") == "needs_more_evidence"


def test_readiness_review_blocks_unsafe_before_other_postures():
    scorecard = AEIDivergenceReadinessReviewService().review(
        tenant_id=TENANT_ID,
        subject_type="answer_sheet_evaluation",
        scope_ref="answer_sheet_evaluation:unsafe",
        comparisons=(
            _comparison("unsafe-a", "unsafe"),
            _comparison("missing-b", "eui_missing", complete_evidence=False),
        ),
    )

    assert scorecard.review_posture == "blocked_unsafe"
    assert scorecard.eligible is False
    assert "blocked_unsafe" in scorecard.blocker_categories


def test_readiness_review_blocks_product_impacting_differences():
    scorecard = AEIDivergenceReadinessReviewService().review(
        tenant_id=TENANT_ID,
        subject_type="answer_sheet_evaluation",
        scope_ref="answer_sheet_evaluation:product-impacting",
        comparisons=(
            _comparison("product-a", "product_impacting"),
            _comparison("product-b", "equivalent"),
        ),
    )

    assert scorecard.review_posture == "blocked_product_impacting"
    assert scorecard.eligible is False
    assert "blocked_product_impacting" in scorecard.blocker_categories


def test_readiness_review_needs_capability_work_for_missing_eui_evidence():
    scorecard = AEIDivergenceReadinessReviewService().review(
        tenant_id=TENANT_ID,
        subject_type="answer_sheet_evaluation",
        scope_ref="answer_sheet_evaluation:missing-eui",
        comparisons=(
            _comparison("missing-a", "eui_missing", complete_evidence=False),
            _comparison("missing-b", "eui_missing", complete_evidence=False),
        ),
    )

    assert scorecard.review_posture == "needs_capability_work"
    assert scorecard.eligible is False
    assert _dimension_status(scorecard, "evidence_completeness") == "needs_capability_work"


def test_readiness_review_needs_more_evidence_for_legacy_ambiguity():
    scorecard = AEIDivergenceReadinessReviewService().review(
        tenant_id=TENANT_ID,
        subject_type="answer_sheet_evaluation",
        scope_ref="answer_sheet_evaluation:legacy-ambiguous",
        comparisons=(
            _comparison("ambiguous-a", "legacy_ambiguous"),
            _comparison("ambiguous-b", "eui_richer"),
        ),
    )

    assert scorecard.review_posture == "needs_more_evidence"
    assert scorecard.eligible is False
    assert _dimension_status(scorecard, "behavior_equivalence") == "needs_more_evidence"


def test_readiness_review_requires_supported_capability_posture():
    scorecard = AEIDivergenceReadinessReviewService().review(
        tenant_id=TENANT_ID,
        subject_type="answer_sheet_evaluation",
        scope_ref="answer_sheet_evaluation:manual-review-capability",
        comparisons=(
            _comparison("manual-a", "equivalent", capability_mode="manual_review"),
            _comparison("manual-b", "equivalent", capability_mode="manual_review"),
        ),
    )

    assert scorecard.review_posture == "needs_capability_work"
    assert scorecard.eligible is False
    assert _dimension_status(scorecard, "capability_posture") == "needs_capability_work"


def test_readiness_review_treats_non_internal_trust_visibility_as_unsafe():
    scorecard = AEIDivergenceReadinessReviewService().review(
        tenant_id=TENANT_ID,
        subject_type="answer_sheet_evaluation",
        scope_ref="answer_sheet_evaluation:unsafe-trust",
        comparisons=(
            _comparison("trust-a", "equivalent", trust_visibility="teacher_safe"),
            _comparison("trust-b", "equivalent"),
        ),
    )

    assert scorecard.review_posture == "blocked_unsafe"
    assert scorecard.eligible is False
    assert _dimension_status(scorecard, "trust_posture") == "blocked_unsafe"


def test_readiness_review_records_source_flag_as_inert_not_authoritative():
    scorecard = AEIDivergenceReadinessReviewService().review(
        tenant_id=TENANT_ID,
        subject_type="answer_sheet_evaluation",
        scope_ref="answer_sheet_evaluation:source-flag-inert",
        comparisons=(
            _comparison("source-a", "equivalent", source_flag_enabled=True),
            _comparison("source-b", "eui_richer", source_flag_enabled=True),
        ),
    )

    assert scorecard.review_posture == "eligible"
    assert scorecard.source_flag_enabled is True
    assert scorecard.source_switch_active is False
    assert scorecard.metadata["source_flag_inert"] is True


def _comparison(
    name: str,
    difference_type: str,
    *,
    complete_evidence: bool = True,
    capability_mode: str = "supported",
    trust_visibility: str = "internal_only",
    source_flag_enabled: bool = False,
) -> AEIConsumerMigrationComparison:
    return AEIConsumerMigrationComparison(
        id=f"eui-aei-migration://answer-sheet-evaluation/{name}",
        tenant_id=TENANT_ID,
        subject_type="answer_sheet_evaluation",
        subject_ref=f"answer_sheet_evaluation:{name}",
        eui_summary={
            "available": complete_evidence,
            "rich_evidence_available": complete_evidence,
            "query_budget": {"per_question_db_traversal": False},
        },
        differences=(
            AEIConsumerMigrationDifference(
                difference_type=difference_type,  # type: ignore[arg-type]
                reason=f"{difference_type}_case",
                blocker=difference_type in {"product_impacting", "unsafe"},
            ),
        ),
        eui_identity_present=complete_evidence,
        eui_context_present=complete_evidence,
        capability_mode=capability_mode if complete_evidence else None,  # type: ignore[arg-type]
        trust_posture="trusted" if complete_evidence else None,
        trust_consumer_visibility=trust_visibility if complete_evidence else None,
        source_flag_enabled=source_flag_enabled,
    )


def _dimension_status(
    scorecard: AEISourceReadinessScorecard,
    dimension: str,
) -> str:
    for result in scorecard.dimensions:
        if result.dimension == dimension:
            return result.status
    raise AssertionError(f"Missing dimension {dimension}")

"""Deterministic AEI/EUI divergence readiness review for EUI Phase 7C.

This service reviews already-collected Phase 7A/7B passive comparison evidence.
It is internal-only, non-authoritative, read-only, and never switches AEI to EUI
as source of truth.
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from typing import Any, Iterable

from app.core.platform_metrics import platform_metrics
from app.modules.eui.schemas.aei_consumer_migration import (
    AEIConsumerMigrationComparison,
    AEIConsumerMigrationDifferenceType,
    AEIConsumerMigrationSubjectType,
)
from app.modules.eui.schemas.aei_source_readiness import (
    AEISourceReadinessDimensionResult,
    AEISourceReadinessPosture,
    AEISourceReadinessScorecard,
)

EUI_AEI_READINESS_REVIEW_METRIC_TASK = "eui_consumer_migration.readiness_review"
DEFAULT_EVIDENCE_WINDOW_REQUIRED = 2
ELIGIBLE_DIFFERENCE_TYPES = frozenset({"equivalent", "eui_richer"})
SOURCE_READY_CAPABILITY_MODES = frozenset({"supported"})


class AEIDivergenceReadinessReviewService:
    """Review passive AEI/EUI evidence for future source-readiness eligibility."""

    def __init__(
        self,
        *,
        evidence_window_required: int = DEFAULT_EVIDENCE_WINDOW_REQUIRED,
    ) -> None:
        if evidence_window_required < 1:
            raise ValueError("evidence_window_required must be >= 1")
        self.evidence_window_required = evidence_window_required

    def review(
        self,
        *,
        tenant_id: uuid.UUID,
        subject_type: AEIConsumerMigrationSubjectType,
        scope_ref: str,
        comparisons: Iterable[AEIConsumerMigrationComparison],
    ) -> AEISourceReadinessScorecard:
        """Produce a deterministic internal source-readiness scorecard."""

        started = time.perf_counter()
        platform_metrics.record_job_event(
            task=EUI_AEI_READINESS_REVIEW_METRIC_TASK,
            status="invoked",
        )
        comparison_tuple = tuple(comparisons)
        dimensions = _dimension_results(
            tenant_id=tenant_id,
            comparisons=comparison_tuple,
            evidence_window_required=self.evidence_window_required,
        )
        posture = _review_posture(
            dimensions=dimensions,
            evidence_window_count=len(comparison_tuple),
            evidence_window_required=self.evidence_window_required,
        )
        blocker_categories = tuple(
            sorted(
                {
                    result.status
                    for result in dimensions
                    if result.status in {"blocked_product_impacting", "blocked_unsafe"}
                }
            )
        )
        scorecard = AEISourceReadinessScorecard(
            id=stable_aei_source_readiness_id(
                subject_type=subject_type,
                scope_ref=scope_ref,
                comparison_ids=tuple(comparison.id for comparison in comparison_tuple),
                review_posture=posture,
            ),
            tenant_id=tenant_id,
            subject_type=subject_type,
            scope_ref=scope_ref,
            review_posture=posture,
            eligible=posture == "eligible",
            evidence_window_required=self.evidence_window_required,
            evidence_window_count=len(comparison_tuple),
            reviewed_comparison_ids=tuple(comparison.id for comparison in comparison_tuple),
            dimensions=dimensions,
            blocker_categories=blocker_categories,
            source_flag_enabled=any(
                comparison.source_flag_enabled for comparison in comparison_tuple
            ),
            source_switch_active=False,
            metadata={
                "authorization": "EUI-PH7C-AEI-DIVERGENCE-READINESS-AUTH-001",
                "passive": True,
                "internal_only": True,
                "source_of_truth": "legacy_aei_evaluation",
                "source_flag_inert": True,
                "raw_content_captured": False,
            },
        )
        duration_ms = (time.perf_counter() - started) * 1000
        platform_metrics.record_job_event(
            task=EUI_AEI_READINESS_REVIEW_METRIC_TASK,
            status=scorecard.review_posture,
            duration_ms=duration_ms,
        )
        if scorecard.review_posture.startswith("blocked"):
            platform_metrics.record_job_event(
                task=EUI_AEI_READINESS_REVIEW_METRIC_TASK,
                status="blocked",
            )
        if scorecard.review_posture == "needs_more_evidence":
            platform_metrics.record_job_event(
                task=EUI_AEI_READINESS_REVIEW_METRIC_TASK,
                status="needs_more_evidence",
            )
        return scorecard


def stable_aei_source_readiness_id(
    *,
    subject_type: str,
    scope_ref: str,
    comparison_ids: tuple[str, ...],
    review_posture: str,
) -> str:
    """Build a deterministic readiness ID without embedding raw scope text."""

    payload = {
        "scope_ref_hash": _digest(scope_ref),
        "comparison_ids": tuple(sorted(comparison_ids)),
        "review_posture": review_posture,
    }
    return f"eui-aei-readiness://{_slug(subject_type)}/{_digest(payload)[:24]}"


def _dimension_results(
    *,
    tenant_id: uuid.UUID,
    comparisons: tuple[AEIConsumerMigrationComparison, ...],
    evidence_window_required: int,
) -> tuple[AEISourceReadinessDimensionResult, ...]:
    difference_types = _difference_types(comparisons)
    return (
        _unsafe_divergence_dimension(comparisons),
        _product_impacting_dimension(difference_types),
        _tenant_safety_dimension(tenant_id=tenant_id, comparisons=comparisons),
        _behavior_equivalence_dimension(difference_types),
        _evidence_window_dimension(
            evidence_window_count=len(comparisons),
            evidence_window_required=evidence_window_required,
        ),
        _evidence_completeness_dimension(comparisons),
        _capability_posture_dimension(comparisons),
        _trust_posture_dimension(comparisons),
        _performance_dimension(comparisons),
        _rollback_dimension(comparisons),
        _regression_coverage_dimension(
            evidence_window_count=len(comparisons),
            evidence_window_required=evidence_window_required,
        ),
    )


def _review_posture(
    *,
    dimensions: tuple[AEISourceReadinessDimensionResult, ...],
    evidence_window_count: int,
    evidence_window_required: int,
) -> AEISourceReadinessPosture:
    statuses = tuple(result.status for result in dimensions)
    if "blocked_unsafe" in statuses:
        return "blocked_unsafe"
    if "blocked_product_impacting" in statuses:
        return "blocked_product_impacting"
    if evidence_window_count < evidence_window_required:
        return "needs_more_evidence"
    if "needs_capability_work" in statuses:
        return "needs_capability_work"
    if "needs_more_evidence" in statuses:
        return "needs_more_evidence"
    return "eligible"


def _unsafe_divergence_dimension(
    comparisons: tuple[AEIConsumerMigrationComparison, ...],
) -> AEISourceReadinessDimensionResult:
    unsafe_count = _count_difference(comparisons, "unsafe")
    if unsafe_count:
        return _dimension(
            "unsafe_divergence",
            "blocked_unsafe",
            "unsafe_divergence_present",
            blocker=True,
            metadata={"unsafe_count": unsafe_count},
        )
    return _dimension("unsafe_divergence", "passed", "unsafe_divergence_absent")


def _product_impacting_dimension(
    difference_types: tuple[str, ...],
) -> AEISourceReadinessDimensionResult:
    product_count = difference_types.count("product_impacting")
    if product_count:
        return _dimension(
            "product_impacting_divergence",
            "blocked_product_impacting",
            "product_impacting_divergence_present",
            blocker=True,
            metadata={"product_impacting_count": product_count},
        )
    return _dimension(
        "product_impacting_divergence",
        "passed",
        "product_impacting_divergence_absent",
    )


def _tenant_safety_dimension(
    *,
    tenant_id: uuid.UUID,
    comparisons: tuple[AEIConsumerMigrationComparison, ...],
) -> AEISourceReadinessDimensionResult:
    mismatches = sum(1 for comparison in comparisons if comparison.tenant_id != tenant_id)
    if mismatches:
        return _dimension(
            "tenant_safety",
            "blocked_unsafe",
            "comparison_tenant_mismatch",
            blocker=True,
            metadata={"mismatch_count": mismatches},
        )
    return _dimension("tenant_safety", "passed", "tenant_scope_consistent")


def _behavior_equivalence_dimension(
    difference_types: tuple[str, ...],
) -> AEISourceReadinessDimensionResult:
    if not difference_types:
        return _dimension(
            "behavior_equivalence",
            "needs_more_evidence",
            "no_comparison_evidence",
        )
    unsupported = tuple(
        sorted(set(difference_types).difference(ELIGIBLE_DIFFERENCE_TYPES))
    )
    if "legacy_ambiguous" in unsupported:
        return _dimension(
            "behavior_equivalence",
            "needs_more_evidence",
            "legacy_ambiguity_requires_more_evidence",
            metadata={"difference_types": tuple(sorted(set(difference_types)))},
        )
    if "eui_missing" in unsupported:
        return _dimension(
            "behavior_equivalence",
            "needs_capability_work",
            "eui_missing_required_behavior_evidence",
            metadata={"difference_types": tuple(sorted(set(difference_types)))},
        )
    if unsupported:
        return _dimension(
            "behavior_equivalence",
            "needs_capability_work",
            "non_equivalent_difference_requires_review",
            metadata={"difference_types": unsupported},
        )
    return _dimension(
        "behavior_equivalence",
        "passed",
        "equivalent_or_non_behavioral_richness_only",
    )


def _evidence_window_dimension(
    *,
    evidence_window_count: int,
    evidence_window_required: int,
) -> AEISourceReadinessDimensionResult:
    if evidence_window_count < evidence_window_required:
        return _dimension(
            "evidence_window",
            "needs_more_evidence",
            "minimum_evidence_window_not_met",
            metadata={
                "evidence_window_count": evidence_window_count,
                "evidence_window_required": evidence_window_required,
            },
        )
    return _dimension(
        "evidence_window",
        "passed",
        "minimum_evidence_window_met",
        metadata={
            "evidence_window_count": evidence_window_count,
            "evidence_window_required": evidence_window_required,
        },
    )


def _evidence_completeness_dimension(
    comparisons: tuple[AEIConsumerMigrationComparison, ...],
) -> AEISourceReadinessDimensionResult:
    missing = _missing_evidence_classes(comparisons)
    if missing:
        return _dimension(
            "evidence_completeness",
            "needs_capability_work",
            "required_eui_evidence_missing",
            metadata={"missing": missing},
        )
    return _dimension(
        "evidence_completeness",
        "passed",
        "required_eui_evidence_present",
    )


def _capability_posture_dimension(
    comparisons: tuple[AEIConsumerMigrationComparison, ...],
) -> AEISourceReadinessDimensionResult:
    modes = tuple(
        sorted(
            {
                str(comparison.capability_mode)
                for comparison in comparisons
                if comparison.capability_mode is not None
            }
        )
    )
    if not modes:
        return _dimension(
            "capability_posture",
            "needs_more_evidence",
            "capability_posture_missing",
        )
    non_ready = tuple(
        mode for mode in modes if mode not in SOURCE_READY_CAPABILITY_MODES
    )
    if non_ready:
        return _dimension(
            "capability_posture",
            "needs_capability_work",
            "capability_not_source_ready",
            metadata={"capability_modes": modes},
        )
    return _dimension(
        "capability_posture",
        "passed",
        "capability_supported_for_declared_scope",
        metadata={"capability_modes": modes},
    )


def _trust_posture_dimension(
    comparisons: tuple[AEIConsumerMigrationComparison, ...],
) -> AEISourceReadinessDimensionResult:
    visibility_values = tuple(
        sorted(
            {
                str(comparison.trust_consumer_visibility)
                for comparison in comparisons
                if comparison.trust_consumer_visibility is not None
            }
        )
    )
    if any(value != "internal_only" for value in visibility_values):
        return _dimension(
            "trust_posture",
            "blocked_unsafe",
            "trust_report_visibility_not_internal_only",
            blocker=True,
            metadata={"visibility_values": visibility_values},
        )
    if not visibility_values:
        return _dimension(
            "trust_posture",
            "needs_more_evidence",
            "trust_posture_missing",
        )
    return _dimension(
        "trust_posture",
        "passed",
        "trust_report_internal_only",
        metadata={"visibility_values": visibility_values},
    )


def _performance_dimension(
    comparisons: tuple[AEIConsumerMigrationComparison, ...],
) -> AEISourceReadinessDimensionResult:
    budgets = tuple(_query_budget(comparison) for comparison in comparisons)
    if not budgets:
        return _dimension("performance", "needs_more_evidence", "query_budget_missing")
    if any(budget.get("per_question_db_traversal") is not False for budget in budgets):
        return _dimension(
            "performance",
            "needs_capability_work",
            "query_budget_not_source_ready",
        )
    return _dimension("performance", "passed", "query_budget_source_ready")


def _rollback_dimension(
    comparisons: tuple[AEIConsumerMigrationComparison, ...],
) -> AEISourceReadinessDimensionResult:
    if any(comparison.source_switch_active for comparison in comparisons):
        return _dimension(
            "rollback",
            "blocked_unsafe",
            "source_switch_active",
            blocker=True,
        )
    return _dimension("rollback", "passed", "source_flag_inert_and_rollbackable")


def _regression_coverage_dimension(
    *,
    evidence_window_count: int,
    evidence_window_required: int,
) -> AEISourceReadinessDimensionResult:
    if evidence_window_count < evidence_window_required:
        return _dimension(
            "regression_coverage",
            "needs_more_evidence",
            "certification_window_not_met",
        )
    return _dimension(
        "regression_coverage",
        "passed",
        "certification_window_available_for_review",
    )


def _missing_evidence_classes(
    comparisons: tuple[AEIConsumerMigrationComparison, ...],
) -> tuple[str, ...]:
    if not comparisons:
        return ("comparison", "identity", "context", "capability", "trust")
    missing: set[str] = set()
    for comparison in comparisons:
        if comparison.eui_summary.get("rich_evidence_available") is not True:
            missing.add("rich_evidence")
        if not comparison.eui_identity_present:
            missing.add("identity")
        if not comparison.eui_context_present:
            missing.add("context")
        if comparison.capability_mode is None:
            missing.add("capability")
        if (
            comparison.trust_posture is None
            or comparison.trust_consumer_visibility is None
        ):
            missing.add("trust")
    return tuple(sorted(missing))


def _query_budget(comparison: AEIConsumerMigrationComparison) -> dict[str, Any]:
    value = comparison.eui_summary.get("query_budget")
    if isinstance(value, dict):
        return value
    return {}


def _difference_types(
    comparisons: tuple[AEIConsumerMigrationComparison, ...],
) -> tuple[str, ...]:
    return tuple(
        difference.difference_type
        for comparison in comparisons
        for difference in comparison.differences
    )


def _count_difference(
    comparisons: tuple[AEIConsumerMigrationComparison, ...],
    difference_type: AEIConsumerMigrationDifferenceType,
) -> int:
    return sum(
        1
        for comparison in comparisons
        for difference in comparison.differences
        if difference.difference_type == difference_type
    )


def _dimension(
    dimension: str,
    status: str,
    reason: str,
    *,
    blocker: bool = False,
    metadata: dict[str, Any] | None = None,
) -> AEISourceReadinessDimensionResult:
    return AEISourceReadinessDimensionResult(
        dimension=dimension,  # type: ignore[arg-type]
        status=status,  # type: ignore[arg-type]
        reason=reason,
        blocker=blocker,
        metadata=metadata or {},
    )


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

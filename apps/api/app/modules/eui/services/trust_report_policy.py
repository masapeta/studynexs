"""Deterministic Trust Report posture policy."""

from __future__ import annotations

from app.modules.eui.schemas.trust_report import (
    TrustDimension,
    TrustOverallPosture,
    TrustWarning,
)


def derive_overall_posture(
    dimensions: dict[str, TrustDimension],
    *,
    review_required: bool = False,
) -> TrustOverallPosture:
    """Derive overall posture using conservative precedence.

    This intentionally does not average dimension scores.
    """

    active_statuses = [
        dimension.status
        for dimension in dimensions.values()
        if dimension.status != "not_applicable"
    ]
    if "unsupported" in active_statuses:
        return "unsupported"
    if review_required or _has_blocker(dimensions):
        return "manual_review_required"
    if "missing" in active_statuses:
        return "insufficient_evidence"
    if any(status in {"weak", "partial"} for status in active_statuses):
        return "review_recommended"
    return "trusted"


def collect_dimension_warnings(
    dimensions: dict[str, TrustDimension],
) -> tuple[TrustWarning, ...]:
    warnings: list[TrustWarning] = []
    for dimension in dimensions.values():
        warnings.extend(dimension.warnings)
    return tuple(warnings)


def _has_blocker(dimensions: dict[str, TrustDimension]) -> bool:
    return any(
        warning.severity == "blocker"
        for dimension in dimensions.values()
        for warning in dimension.warnings
    )

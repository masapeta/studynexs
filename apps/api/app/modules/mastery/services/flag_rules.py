"""Weakness-flag rules — pure threshold functions over ledger rows.

A flag is a deterministic claim about a child that a teacher will review and a
parent may read. Rules err conservative: never flag on a single assessment, and
severity reflects how actionable the gap is, not drama.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.db.models.mastery import FlagSeverity, MasteryTrend

# R1 — below class average by this many percentage points.
GAP_MEDIUM = 15.0
GAP_HIGH = 25.0
# R3 — absolute floor, just above the SSC 35% pass line.
ABSOLUTE_FLOOR = 40.0
# Guard — one bad slip test must not alarm a parent.
MIN_ASSESSMENTS = 2
# Cool-off after a dismissal/notification before the same topic can re-flag.
COOLOFF_DAYS = 21


@dataclass(frozen=True)
class FlagCandidate:
    severity: FlagSeverity
    reasons: list[str]


def evaluate(
    *,
    mastery_pct: float,
    class_avg_pct: float | None,
    trend: MasteryTrend,
    assessments_count: int,
) -> FlagCandidate | None:
    """Evaluate one (student, topic) ledger row. None = nothing to flag."""
    if assessments_count < MIN_ASSESSMENTS:
        return None

    reasons: list[str] = []
    severity: FlagSeverity | None = None

    if class_avg_pct is not None:
        gap = class_avg_pct - mastery_pct
        if gap >= GAP_HIGH:
            reasons.append("below_class_avg")
            severity = FlagSeverity.HIGH
        elif gap >= GAP_MEDIUM:
            reasons.append("below_class_avg")
            severity = FlagSeverity.MEDIUM

    if trend == MasteryTrend.DECLINING:
        reasons.append("declining_trend")
        if severity is None:
            severity = FlagSeverity.MEDIUM
        elif "below_class_avg" in reasons:
            severity = FlagSeverity.HIGH  # behind AND falling

    if mastery_pct < ABSOLUTE_FLOOR:
        reasons.append("absolute_floor")
        severity = FlagSeverity.HIGH

    return FlagCandidate(severity=severity, reasons=reasons) if severity else None

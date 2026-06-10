"""Deterministic mastery computation — pure functions, no DB, no LLM.

The numbers a parent eventually reads are produced here and only here.
The LLM never computes; it only verbalizes pre-computed facts.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.db.models.mastery import MasteryTrend
from app.modules.mastery.services.topic_norm import display_topic, normalize_topic

# Heavier exams count more toward mastery.
TYPE_WEIGHTS: dict[str, float] = {
    "slip_test": 0.5,
    "quiz": 0.5,
    "assignment": 0.5,
    "unit_test": 1.0,
    "mid_term": 1.5,
    "quarterly": 1.5,
    "half_yearly": 2.0,
    "final": 2.5,
}
DEFAULT_TYPE_WEIGHT = 1.0

# Recency decay: an assessment from 90 days ago counts half as much as today's.
HALF_LIFE_DAYS = 90.0

# Trend over the last N chronological datapoints.
TREND_WINDOW = 3
TREND_MIN_DELTA = 10.0  # total drop/climb (pct points) required to call a trend

HISTORY_LIMIT = 8  # datapoints kept on the ledger row for UI/LLM grounding


@dataclass(frozen=True)
class Datapoint:
    """One student's score on one topic in one exam."""
    exam_id: str
    exam_type: str  # enum value, e.g. "slip_test"
    exam_title: str
    assessed_on: date
    pct: float  # 0..100, computed over ATTEMPTED questions of this topic


def topic_pcts_for_mark(
    *,
    question_schema: list[dict] | None,
    question_marks: dict[str, float] | None,
    exam_topic: str | None,
    marks_obtained: float,
    total_marks: float,
) -> dict[str, float]:
    """Per-topic pct for one student's one exam → {normalized_topic: pct}.

    Per-question exams: group attempted questions by topic (question topic, falling
    back to the exam topic). Unattempted questions are excluded from the denominator —
    with internal choice we cannot distinguish skip-by-choice from skip-by-inability.
    Total-only exams: the exam topic gets marks_obtained/total_marks.
    """
    if question_schema and question_marks:
        obtained: dict[str, float] = {}
        max_marks: dict[str, float] = {}
        for q in question_schema:
            qno = q["no"]
            if qno not in question_marks:
                continue  # unattempted
            raw_topic = q.get("topic") or exam_topic
            if not raw_topic:
                continue  # untagged question — no topic signal
            key = normalize_topic(raw_topic)
            obtained[key] = obtained.get(key, 0.0) + float(question_marks[qno])
            max_marks[key] = max_marks.get(key, 0.0) + float(q["max_marks"])
        return {
            key: round(obtained[key] / max_marks[key] * 100, 2)
            for key in obtained
            if max_marks[key] > 0
        }

    if exam_topic and total_marks > 0:
        pct = round(float(marks_obtained) / float(total_marks) * 100, 2)
        return {normalize_topic(exam_topic): pct}

    return {}


def weighted_mastery(datapoints: list[Datapoint], as_of: date) -> float:
    """Σ(w·pct)/Σ(w) where w = type weight × 0.5^(age/half-life)."""
    num = 0.0
    den = 0.0
    for dp in datapoints:
        age_days = max((as_of - dp.assessed_on).days, 0)
        decay = 0.5 ** (age_days / HALF_LIFE_DAYS)
        w = TYPE_WEIGHTS.get(dp.exam_type, DEFAULT_TYPE_WEIGHT) * decay
        num += w * dp.pct
        den += w
    return round(num / den, 2) if den > 0 else 0.0


def trend_of(datapoints: list[Datapoint]) -> MasteryTrend:
    """Trend over the last TREND_WINDOW chronological points (undecayed pcts)."""
    if len(datapoints) < 2:
        return MasteryTrend.INSUFFICIENT
    pts = [dp.pct for dp in sorted(datapoints, key=lambda d: d.assessed_on)[-TREND_WINDOW:]]
    declining = all(pts[i] >= pts[i + 1] for i in range(len(pts) - 1))
    improving = all(pts[i] <= pts[i + 1] for i in range(len(pts) - 1))
    if declining and pts[0] - pts[-1] >= TREND_MIN_DELTA:
        return MasteryTrend.DECLINING
    if improving and pts[-1] - pts[0] >= TREND_MIN_DELTA:
        return MasteryTrend.IMPROVING
    return MasteryTrend.STABLE


def history_of(datapoints: list[Datapoint]) -> list[dict]:
    """Last HISTORY_LIMIT datapoints, chronological — UI sparkline + LLM grounding."""
    recent = sorted(datapoints, key=lambda d: d.assessed_on)[-HISTORY_LIMIT:]
    return [
        {
            "exam_id": dp.exam_id,
            "exam_type": dp.exam_type,
            "title": dp.exam_title,
            "date": dp.assessed_on.isoformat(),
            "pct": dp.pct,
        }
        for dp in recent
    ]


__all__ = [
    "Datapoint",
    "topic_pcts_for_mark",
    "weighted_mastery",
    "trend_of",
    "history_of",
    "normalize_topic",
    "display_topic",
    "TYPE_WEIGHTS",
    "HALF_LIFE_DAYS",
    "TREND_MIN_DELTA",
    "HISTORY_LIMIT",
]

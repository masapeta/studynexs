"""Tests — deterministic mastery math (pure functions, no DB)."""

from datetime import date, timedelta

from app.db.models.mastery import MasteryTrend
from app.modules.mastery.services.compute import (
    Datapoint,
    history_of,
    topic_pcts_for_mark,
    trend_of,
    weighted_mastery,
)
from app.modules.mastery.services.topic_norm import display_topic, normalize_topic

TODAY = date(2026, 6, 10)


def dp(
    pct: float, days_ago: int = 0, exam_type: str = "unit_test", exam_id: str = "e1"
) -> Datapoint:
    return Datapoint(
        exam_id=exam_id,
        exam_type=exam_type,
        exam_title="T",
        assessed_on=TODAY - timedelta(days=days_ago),
        pct=pct,
    )


# ── topic normalization ──────────────────────────────────────────────────────

def test_normalize_topic_collapses_whitespace_and_case():
    assert normalize_topic(" Linear  Equations ") == "linear equations"
    assert normalize_topic("ALGEBRA") == normalize_topic("algebra")
    assert display_topic("  Linear  Equations ") == "Linear Equations"


# ── per-exam topic pcts ──────────────────────────────────────────────────────

SCHEMA = [
    {"no": "1", "max_marks": 10, "topic": "Algebra"},
    {"no": "2", "max_marks": 10, "topic": "Geometry"},
    {"no": "3", "max_marks": 10, "topic": "Algebra"},
]


def test_question_marks_grouped_by_topic():
    pcts = topic_pcts_for_mark(
        question_schema=SCHEMA,
        question_marks={"1": 5, "2": 8, "3": 10},
        exam_topic=None,
        marks_obtained=23,
        total_marks=30,
    )
    assert pcts == {"algebra": 75.0, "geometry": 80.0}


def test_unattempted_question_excluded_from_denominator():
    # Q3 (Algebra) unattempted — internal choice. Algebra = 5/10, not 5/20.
    pcts = topic_pcts_for_mark(
        question_schema=SCHEMA,
        question_marks={"1": 5, "2": 8},
        exam_topic=None,
        marks_obtained=13,
        total_marks=30,
    )
    assert pcts["algebra"] == 50.0


def test_untagged_question_falls_back_to_exam_topic():
    schema = [
        {"no": "1", "max_marks": 10, "topic": None},
        {"no": "2", "max_marks": 10, "topic": "Geometry"},
    ]
    pcts = topic_pcts_for_mark(
        question_schema=schema,
        question_marks={"1": 6, "2": 9},
        exam_topic="Algebra",
        marks_obtained=15,
        total_marks=20,
    )
    assert pcts == {"algebra": 60.0, "geometry": 90.0}


def test_exam_level_topic_fallback_for_total_only_marks():
    pcts = topic_pcts_for_mark(
        question_schema=None,
        question_marks=None,
        exam_topic="Trigonometry",
        marks_obtained=9,
        total_marks=25,
    )
    assert pcts == {"trigonometry": 36.0}


def test_no_topic_signal_yields_nothing():
    assert topic_pcts_for_mark(
        question_schema=None, question_marks=None, exam_topic=None,
        marks_obtained=20, total_marks=25,
    ) == {}


def test_retagging_schema_changes_attribution():
    retagged = [dict(q, topic="Linear Equations") for q in SCHEMA]
    pcts = topic_pcts_for_mark(
        question_schema=retagged,
        question_marks={"1": 5, "2": 8, "3": 10},
        exam_topic=None,
        marks_obtained=23,
        total_marks=30,
    )
    assert pcts == {"linear equations": round(23 / 30 * 100, 2)}


# ── weighted mastery ─────────────────────────────────────────────────────────

def test_weighted_mastery_single_point_is_its_pct():
    assert weighted_mastery([dp(64.0)], TODAY) == 64.0


def test_exam_type_weights_applied():
    # Same day (no decay): final (2.5) vs slip test (0.5) → 80*2.5 + 40*0.5 / 3.0
    pts = [dp(80.0, exam_type="final"), dp(40.0, exam_type="slip_test")]
    expected = round((80 * 2.5 + 40 * 0.5) / 3.0, 2)
    assert weighted_mastery(pts, TODAY) == expected


def test_recency_decay_half_life():
    # Same type; one today at 100, one exactly 90 days old at 0 → weight 1 vs 0.5.
    pts = [dp(100.0, days_ago=0), dp(0.0, days_ago=90)]
    assert weighted_mastery(pts, TODAY) == round(100 / 1.5, 2)


def test_weighted_mastery_empty_is_zero():
    assert weighted_mastery([], TODAY) == 0.0


# ── trend ────────────────────────────────────────────────────────────────────

def test_trend_insufficient_below_two_points():
    assert trend_of([dp(50.0)]) == MasteryTrend.INSUFFICIENT
    assert trend_of([]) == MasteryTrend.INSUFFICIENT


def test_trend_declining_requires_monotone_and_min_delta():
    falling = [dp(70.0, days_ago=30), dp(65.0, days_ago=15), dp(58.0, days_ago=1)]
    assert trend_of(falling) == MasteryTrend.DECLINING

    # Exactly 10-point total drop → DECLINING (boundary inclusive).
    boundary = [dp(70.0, days_ago=30), dp(65.0, days_ago=15), dp(60.0, days_ago=1)]
    assert trend_of(boundary) == MasteryTrend.DECLINING

    # 9-point drop → STABLE.
    shallow = [dp(70.0, days_ago=30), dp(65.0, days_ago=15), dp(61.0, days_ago=1)]
    assert trend_of(shallow) == MasteryTrend.STABLE

    # Non-monotone (dip then recovery) → STABLE even with a big swing.
    bumpy = [dp(70.0, days_ago=30), dp(40.0, days_ago=15), dp(69.0, days_ago=1)]
    assert trend_of(bumpy) == MasteryTrend.STABLE


def test_trend_improving():
    rising = [dp(40.0, days_ago=30), dp(52.0, days_ago=15), dp(60.0, days_ago=1)]
    assert trend_of(rising) == MasteryTrend.IMPROVING


def test_trend_uses_last_three_chronological():
    # Old catastrophic scores are outside the window; last 3 are flat → STABLE.
    pts = [
        dp(95.0, days_ago=120), dp(20.0, days_ago=90),
        dp(60.0, days_ago=30), dp(61.0, days_ago=15), dp(59.0, days_ago=1),
    ]
    assert trend_of(pts) == MasteryTrend.STABLE


# ── history ──────────────────────────────────────────────────────────────────

def test_history_keeps_last_eight_chronological():
    pts = [dp(float(i), days_ago=100 - i, exam_id=f"e{i}") for i in range(12)]
    hist = history_of(pts)
    assert len(hist) == 8
    assert [h["pct"] for h in hist] == [4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0]
    assert all(set(h) == {"exam_id", "exam_type", "title", "date", "pct"} for h in hist)

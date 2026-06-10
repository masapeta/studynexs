"""Tests — weakness-flag rules (pure) and flag persistence semantics (DB)."""

import pytest
from sqlalchemy import select

from app.db.models.mastery import FlagSeverity, FlagStatus, MasteryFlag, MasteryTrend
from app.modules.mastery.services.flag_rules import evaluate

# ── Pure rule tests (no DB) ──────────────────────────────────────────────────


def test_no_flag_below_min_assessments():
    assert evaluate(
        mastery_pct=10.0, class_avg_pct=80.0,
        trend=MasteryTrend.DECLINING, assessments_count=1,
    ) is None


def test_gap_boundaries():
    # 14.9-pt gap → no flag from R1 alone.
    assert evaluate(
        mastery_pct=60.1, class_avg_pct=75.0,
        trend=MasteryTrend.STABLE, assessments_count=3,
    ) is None
    # Exactly 15 → MEDIUM.
    medium = evaluate(
        mastery_pct=60.0, class_avg_pct=75.0,
        trend=MasteryTrend.STABLE, assessments_count=3,
    )
    assert medium and medium.severity == FlagSeverity.MEDIUM
    assert medium.reasons == ["below_class_avg"]
    # Exactly 25 → HIGH.
    high = evaluate(
        mastery_pct=50.0, class_avg_pct=75.0,
        trend=MasteryTrend.STABLE, assessments_count=3,
    )
    assert high and high.severity == FlagSeverity.HIGH


def test_declining_trend_alone_is_medium():
    flag = evaluate(
        mastery_pct=70.0, class_avg_pct=72.0,
        trend=MasteryTrend.DECLINING, assessments_count=3,
    )
    assert flag and flag.severity == FlagSeverity.MEDIUM
    assert flag.reasons == ["declining_trend"]


def test_behind_and_falling_is_high():
    flag = evaluate(
        mastery_pct=58.0, class_avg_pct=75.0,  # 17-pt gap (MEDIUM) ...
        trend=MasteryTrend.DECLINING,          # ... plus declining → HIGH
        assessments_count=3,
    )
    assert flag and flag.severity == FlagSeverity.HIGH
    assert set(flag.reasons) == {"below_class_avg", "declining_trend"}


def test_absolute_floor_boundary():
    # 40.0 is NOT below the floor.
    assert evaluate(
        mastery_pct=40.0, class_avg_pct=42.0,
        trend=MasteryTrend.STABLE, assessments_count=2,
    ) is None
    # 39.99 is → HIGH even with no gap and stable trend.
    flag = evaluate(
        mastery_pct=39.99, class_avg_pct=42.0,
        trend=MasteryTrend.STABLE, assessments_count=2,
    )
    assert flag and flag.severity == FlagSeverity.HIGH
    assert flag.reasons == ["absolute_floor"]


def test_no_class_average_still_floors():
    flag = evaluate(
        mastery_pct=30.0, class_avg_pct=None,
        trend=MasteryTrend.STABLE, assessments_count=2,
    )
    assert flag and flag.severity == FlagSeverity.HIGH


def test_strong_student_never_flagged():
    assert evaluate(
        mastery_pct=85.0, class_avg_pct=70.0,
        trend=MasteryTrend.IMPROVING, assessments_count=5,
    ) is None


# ── DB semantics (need Postgres) ─────────────────────────────────────────────


async def _seed_flagging_scenario(client, db_session, test_school, test_class, student_user):
    """Two slip tests where the student tanks Algebra → recompute raises a flag.

    A second strong student anchors the class average above the gap threshold.
    """
    from datetime import date, timedelta

    from sqlalchemy import select as sa_select

    from app.core.security import hash_password
    from app.db.models.academic import Subject
    from app.db.models.student import Student
    from app.db.models.user import User, UserRole
    from app.modules.mastery.services.mastery_service import recompute_class_subject
    from tests.conftest import auth_headers, get_auth_token

    subject = Subject(school_id=test_school.id, class_id=test_class.id, name="Maths", code="MTH")
    db_session.add(subject)
    await db_session.flush()

    strong_user = User(
        school_id=test_school.id, username="strong_student", mobile="+919000000801",
        full_name="Strong Student", role=UserRole.STUDENT,
        password_hash=hash_password("Strong@123"), is_active=True,
    )
    db_session.add(strong_user)
    await db_session.flush()
    strong = Student(
        school_id=test_school.id, user_id=strong_user.id, class_id=test_class.id,
        admission_no="ADM801", roll_no="2",
    )
    db_session.add(strong)
    await db_session.flush()

    weak = (
        await db_session.execute(sa_select(Student).where(Student.user_id == student_user.id))
    ).scalar_one()

    token = await get_auth_token(client, "test_admin", "Admin@123")
    for i, (weak_marks, strong_marks) in enumerate([(10, 23), (6, 24)]):
        resp = await client.post("/api/v1/exams", headers=auth_headers(token), json={
            "class_id": str(test_class.id),
            "subject_id": str(subject.id),
            "exam_type": "slip_test",
            "title": f"Algebra Slip {i + 1}",
            "total_marks": 25,
            "topic": "Algebra",
            "exam_date": (date.today() - timedelta(days=20 - i * 10)).isoformat(),
        })
        exam = resp.json()["data"]
        await client.post("/api/v1/exams/marks", headers=auth_headers(token), json={
            "exam_id": exam["id"],
            "entries": [
                {"student_id": str(weak.id), "marks_obtained": weak_marks},
                {"student_id": str(strong.id), "marks_obtained": strong_marks},
            ],
        })

    await recompute_class_subject(db_session, test_school.id, test_class.id, subject.id)
    return weak, subject, token


@pytest.mark.asyncio
async def test_recompute_raises_flag_once(
    client, admin_user, student_user, test_school, test_class, db_session,
):
    from app.db.models.student import Student  # noqa: F401 (fixture typing)
    from app.modules.mastery.services.mastery_service import recompute_class_subject

    weak, subject, _ = await _seed_flagging_scenario(
        client, db_session, test_school, test_class, student_user
    )

    flags = (
        await db_session.execute(
            select(MasteryFlag).where(MasteryFlag.student_id == weak.id)
        )
    ).scalars().all()
    assert len(flags) == 1
    flag = flags[0]
    assert flag.status == FlagStatus.PENDING_REVIEW
    assert flag.topic == "algebra"
    assert flag.evidence["student_name"]
    assert flag.evidence["history"]

    # Recompute again — open-flag dedupe keeps it at one.
    await recompute_class_subject(db_session, test_school.id, test_class.id, subject.id)
    flags = (
        await db_session.execute(
            select(MasteryFlag).where(MasteryFlag.student_id == weak.id)
        )
    ).scalars().all()
    assert len(flags) == 1


@pytest.mark.asyncio
async def test_dismissed_flag_cooloff_suppresses_reraise(
    client, admin_user, student_user, test_school, test_class, db_session,
):
    from app.modules.mastery.services.mastery_service import recompute_class_subject
    from tests.conftest import auth_headers

    weak, subject, token = await _seed_flagging_scenario(
        client, db_session, test_school, test_class, student_user
    )
    flag = (
        await db_session.execute(
            select(MasteryFlag).where(MasteryFlag.student_id == weak.id)
        )
    ).scalar_one()

    resp = await client.post(
        f"/api/v1/mastery/flags/{flag.id}/dismiss",
        headers=auth_headers(token),
        json={"reason": "already working with the student"},
    )
    assert resp.status_code == 200, resp.text

    # Recompute — the dismissal is recent (< 21 days) so no new flag is raised.
    await recompute_class_subject(db_session, test_school.id, test_class.id, subject.id)
    flags = (
        await db_session.execute(
            select(MasteryFlag).where(MasteryFlag.student_id == weak.id)
        )
    ).scalars().all()
    assert len(flags) == 1
    assert flags[0].status == FlagStatus.DISMISSED

"""Tests — marks-entry → outbox event → mastery ledger recompute pipeline."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import Class, Subject
from app.db.models.mastery import StudentTopicMastery
from app.db.models.outbox import OutboxEvent, OutboxStatus
from app.db.models.school import School
from app.db.models.student import Student
from app.db.models.user import User
from app.workers.outbox_worker import handle_exam_marks
from tests.conftest import auth_headers, get_auth_token


async def _setup_exam_with_marks(
    client: AsyncClient, db: AsyncSession, school: School, test_class: Class, student_user: User,
    *, topic: str | None = "Algebra",
) -> dict:
    subject = Subject(school_id=school.id, class_id=test_class.id, name="Maths", code="MTH")
    db.add(subject)
    await db.flush()
    student = (
        await db.execute(select(Student).where(Student.user_id == student_user.id))
    ).scalar_one()

    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.post("/api/v1/exams", headers=auth_headers(token), json={
        "class_id": str(test_class.id),
        "subject_id": str(subject.id),
        "exam_type": "slip_test",
        "title": "Algebra Slip Test",
        "total_marks": 25,
        "topic": topic,
        "exam_date": "2026-06-01",
    })
    assert resp.status_code == 201, resp.text
    exam = resp.json()["data"]

    resp = await client.post("/api/v1/exams/marks", headers=auth_headers(token), json={
        "exam_id": exam["id"],
        "entries": [{"student_id": str(student.id), "marks_obtained": 9}],
    })
    assert resp.status_code == 200, resp.text
    return {"exam": exam, "student": student, "subject": subject, "token": token}


@pytest.mark.asyncio
async def test_marks_entry_emits_outbox_event_in_same_txn(
    client: AsyncClient, admin_user: User, student_user: User,
    test_school: School, test_class: Class, db_session: AsyncSession,
):
    ctx = await _setup_exam_with_marks(client, db_session, test_school, test_class, student_user)

    events = (
        await db_session.execute(
            select(OutboxEvent).where(OutboxEvent.event_type == "exam_marks_entered")
        )
    ).scalars().all()
    assert len(events) == 1
    event = events[0]
    assert event.status == OutboxStatus.PENDING
    assert event.payload["exam_id"] == ctx["exam"]["id"]
    assert event.payload["class_id"] == str(test_class.id)
    assert event.target_module == "mastery"


@pytest.mark.asyncio
async def test_handler_builds_ledger_and_is_idempotent(
    client: AsyncClient, admin_user: User, student_user: User,
    test_school: School, test_class: Class, db_session: AsyncSession,
):
    ctx = await _setup_exam_with_marks(client, db_session, test_school, test_class, student_user)
    payload = {
        "school_id": str(test_school.id),
        "exam_id": ctx["exam"]["id"],
        "class_id": str(test_class.id),
        "subject_id": str(ctx["subject"].id),
    }

    await handle_exam_marks(payload, db_session)
    rows = (
        await db_session.execute(
            select(StudentTopicMastery).where(
                StudentTopicMastery.student_id == ctx["student"].id
            )
        )
    ).scalars().all()
    assert len(rows) == 1
    row = rows[0]
    assert row.topic == "algebra"
    assert row.topic_display == "Algebra"
    assert float(row.mastery_pct) == 36.0  # 9/25
    assert float(row.class_avg_pct) == 36.0  # single-student class
    assert row.assessments_count == 1
    assert len(row.history) == 1

    # Re-running the handler (worker retry) upserts the same row, no duplicates.
    await handle_exam_marks(payload, db_session)
    rows = (
        await db_session.execute(
            select(StudentTopicMastery).where(
                StudentTopicMastery.student_id == ctx["student"].id
            )
        )
    ).scalars().all()
    assert len(rows) == 1


@pytest.mark.asyncio
async def test_handler_noops_for_untagged_exam(
    client: AsyncClient, admin_user: User, student_user: User,
    test_school: School, test_class: Class, db_session: AsyncSession,
):
    ctx = await _setup_exam_with_marks(
        client, db_session, test_school, test_class, student_user, topic=None
    )
    await handle_exam_marks(
        {
            "school_id": str(test_school.id),
            "exam_id": ctx["exam"]["id"],
            "class_id": str(test_class.id),
            "subject_id": str(ctx["subject"].id),
        },
        db_session,
    )
    rows = (
        await db_session.execute(select(StudentTopicMastery))
    ).scalars().all()
    assert rows == []


@pytest.mark.asyncio
async def test_profile_endpoint_object_gating(
    client: AsyncClient, admin_user: User, student_user: User, parent_user: User,
    test_school: School, test_class: Class, db_session: AsyncSession,
):
    ctx = await _setup_exam_with_marks(client, db_session, test_school, test_class, student_user)
    await handle_exam_marks(
        {
            "school_id": str(test_school.id),
            "exam_id": ctx["exam"]["id"],
            "class_id": str(test_class.id),
            "subject_id": str(ctx["subject"].id),
        },
        db_session,
    )
    student_id = ctx["student"].id

    # Parent of the child and staff can read; the student can read self.
    for username, password in (
        ("test_parent", "Parent@123"),
        ("test_student", "Student@123"),
        ("test_admin", "Admin@123"),
    ):
        token = await get_auth_token(client, username, password)
        resp = await client.get(
            f"/api/v1/mastery/students/{student_id}", headers=auth_headers(token)
        )
        assert resp.status_code == 200, f"{username}: {resp.text}"

    data = resp.json()["data"]
    assert data["subjects"][0]["topics"][0]["topic_display"] == "Algebra"
    assert data["subjects"][0]["topics"][0]["mastery_pct"] == 36.0

    # Heatmap and recompute are staff-gated.
    student_token = await get_auth_token(client, "test_student", "Student@123")
    resp = await client.get(
        f"/api/v1/mastery/classes/{test_class.id}/heatmap?subject_id={ctx['subject'].id}",
        headers=auth_headers(student_token),
    )
    assert resp.status_code == 403
    resp = await client.post(
        "/api/v1/mastery/recompute",
        headers=auth_headers(student_token),
        json={"class_id": str(test_class.id), "subject_id": str(ctx["subject"].id)},
    )
    assert resp.status_code == 403

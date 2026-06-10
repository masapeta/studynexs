"""Tests — exam question schemas and per-question marks entry (mastery foundations)."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import Class, Subject
from app.db.models.examination import ExamMark
from app.db.models.school import School
from app.db.models.student import Student
from app.db.models.user import User
from tests.conftest import auth_headers, get_auth_token


async def _subject(db: AsyncSession, school: School, test_class: Class) -> Subject:
    subject = Subject(
        school_id=school.id, class_id=test_class.id, name="Mathematics", code="MTH"
    )
    db.add(subject)
    await db.flush()
    return subject


async def _create_exam(
    client: AsyncClient, token: str, test_class: Class, subject: Subject, **overrides
) -> dict:
    payload = {
        "class_id": str(test_class.id),
        "subject_id": str(subject.id),
        "exam_type": "slip_test",
        "title": "Algebra Slip Test",
        "total_marks": 25,
        "topic": "Algebra",
    }
    payload.update(overrides)
    resp = await client.post("/api/v1/exams", headers=auth_headers(token), json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]


QUESTIONS = [
    {"no": "1", "max_marks": 10, "topic": "Algebra"},
    {"no": "2", "max_marks": 10, "topic": "Geometry"},
    {"no": "3", "max_marks": 10, "topic": "Algebra"},
]


@pytest.mark.asyncio
async def test_exam_create_carries_topic_and_ssc_type(
    client: AsyncClient, admin_user: User, test_school: School, test_class: Class,
    db_session: AsyncSession,
):
    subject = await _subject(db_session, test_school, test_class)
    token = await get_auth_token(client, "test_admin", "Admin@123")
    exam = await _create_exam(client, token, test_class, subject)
    assert exam["topic"] == "Algebra"
    assert exam["exam_type"] == "slip_test"
    assert exam["has_question_schema"] is False


@pytest.mark.asyncio
async def test_question_schema_validation(
    client: AsyncClient, admin_user: User, test_school: School, test_class: Class,
    db_session: AsyncSession,
):
    subject = await _subject(db_session, test_school, test_class)
    token = await get_auth_token(client, "test_admin", "Admin@123")
    exam = await _create_exam(client, token, test_class, subject)
    url = f"/api/v1/exams/{exam['id']}/questions"

    # Duplicate question numbers rejected.
    resp = await client.put(url, headers=auth_headers(token), json={
        "questions": [{"no": "1", "max_marks": 15}, {"no": "1", "max_marks": 15}],
    })
    assert resp.status_code == 400
    assert "duplicate" in resp.json()["detail"]

    # Σ max below total_marks rejected (questions missing).
    resp = await client.put(url, headers=auth_headers(token), json={
        "questions": [{"no": "1", "max_marks": 10}],
    })
    assert resp.status_code == 400

    # Σ max above total_marks allowed (internal choice).
    resp = await client.put(url, headers=auth_headers(token), json={
        "questions": QUESTIONS + [{"no": "4", "max_marks": 10, "topic": "Geometry"}],
    })
    assert resp.status_code == 200
    assert resp.json()["data"]["has_question_schema"] is True

    # Read back.
    resp = await client.get(url, headers=auth_headers(token))
    assert resp.status_code == 200
    assert [q["no"] for q in resp.json()["data"]] == ["1", "2", "3", "4"]


@pytest.mark.asyncio
async def test_per_question_marks_derive_total(
    client: AsyncClient, admin_user: User, student_user: User,
    test_school: School, test_class: Class, db_session: AsyncSession,
):
    subject = await _subject(db_session, test_school, test_class)
    student = (
        await db_session.execute(select(Student).where(Student.user_id == student_user.id))
    ).scalar_one()

    token = await get_auth_token(client, "test_admin", "Admin@123")
    exam = await _create_exam(client, token, test_class, subject, total_marks=30)
    await client.put(
        f"/api/v1/exams/{exam['id']}/questions",
        headers=auth_headers(token),
        json={"questions": QUESTIONS},
    )

    # Client-sent marks_obtained is ignored; total derived from question marks.
    # Q3 unattempted (internal choice) — absent key, simply not counted.
    resp = await client.post("/api/v1/exams/marks", headers=auth_headers(token), json={
        "exam_id": exam["id"],
        "entries": [{
            "student_id": str(student.id),
            "marks_obtained": 999,
            "question_marks": {"1": 7.5, "2": 9},
        }],
    })
    assert resp.status_code == 200, resp.text

    mark = (
        await db_session.execute(select(ExamMark).where(ExamMark.exam_id == uuid.UUID(exam["id"])))
    ).scalar_one()
    assert float(mark.marks_obtained) == 16.5
    assert mark.question_marks == {"1": 7.5, "2": 9}


@pytest.mark.asyncio
async def test_per_question_marks_validation(
    client: AsyncClient, admin_user: User, student_user: User,
    test_school: School, test_class: Class, db_session: AsyncSession,
):
    subject = await _subject(db_session, test_school, test_class)
    student = (
        await db_session.execute(select(Student).where(Student.user_id == student_user.id))
    ).scalar_one()
    token = await get_auth_token(client, "test_admin", "Admin@123")
    exam = await _create_exam(client, token, test_class, subject, total_marks=30)

    # question_marks without a schema → 400.
    resp = await client.post("/api/v1/exams/marks", headers=auth_headers(token), json={
        "exam_id": exam["id"],
        "entries": [{"student_id": str(student.id), "question_marks": {"1": 5}}],
    })
    assert resp.status_code == 400

    await client.put(
        f"/api/v1/exams/{exam['id']}/questions",
        headers=auth_headers(token),
        json={"questions": QUESTIONS},
    )

    # Unknown question number → 400.
    resp = await client.post("/api/v1/exams/marks", headers=auth_headers(token), json={
        "exam_id": exam["id"],
        "entries": [{"student_id": str(student.id), "question_marks": {"9": 5}}],
    })
    assert resp.status_code == 400

    # Mark above the question max → 400.
    resp = await client.post("/api/v1/exams/marks", headers=auth_headers(token), json={
        "exam_id": exam["id"],
        "entries": [{"student_id": str(student.id), "question_marks": {"1": 11}}],
    })
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_legacy_total_only_marks_unchanged(
    client: AsyncClient, admin_user: User, student_user: User,
    test_school: School, test_class: Class, db_session: AsyncSession,
):
    """Regression guard: exams without schemas keep the original total-only flow."""
    subject = await _subject(db_session, test_school, test_class)
    student = (
        await db_session.execute(select(Student).where(Student.user_id == student_user.id))
    ).scalar_one()
    token = await get_auth_token(client, "test_admin", "Admin@123")
    exam = await _create_exam(client, token, test_class, subject, exam_type="unit_test", topic=None)

    resp = await client.post("/api/v1/exams/marks", headers=auth_headers(token), json={
        "exam_id": exam["id"],
        "entries": [{"student_id": str(student.id), "marks_obtained": 21, "grade_letter": "A"}],
    })
    assert resp.status_code == 200, resp.text

    mark = (
        await db_session.execute(select(ExamMark).where(ExamMark.exam_id == uuid.UUID(exam["id"])))
    ).scalar_one()
    assert float(mark.marks_obtained) == 21
    assert mark.question_marks is None


@pytest.mark.asyncio
async def test_schema_replace_cannot_orphan_recorded_marks(
    client: AsyncClient, admin_user: User, student_user: User,
    test_school: School, test_class: Class, db_session: AsyncSession,
):
    subject = await _subject(db_session, test_school, test_class)
    student = (
        await db_session.execute(select(Student).where(Student.user_id == student_user.id))
    ).scalar_one()
    token = await get_auth_token(client, "test_admin", "Admin@123")
    exam = await _create_exam(client, token, test_class, subject, total_marks=30)
    url = f"/api/v1/exams/{exam['id']}/questions"

    await client.put(url, headers=auth_headers(token), json={"questions": QUESTIONS})
    await client.post("/api/v1/exams/marks", headers=auth_headers(token), json={
        "exam_id": exam["id"],
        "entries": [{"student_id": str(student.id), "question_marks": {"3": 8}}],
    })

    # New schema drops Q3, which has recorded marks → 400.
    resp = await client.put(url, headers=auth_headers(token), json={
        "questions": [
            {"no": "1", "max_marks": 15, "topic": "Algebra"},
            {"no": "2", "max_marks": 15, "topic": "Geometry"},
        ],
    })
    assert resp.status_code == 400
    assert "Q" not in resp.json()["detail"] or "3" in resp.json()["detail"]

    # Re-tagging topics while keeping the same numbers is fine.
    resp = await client.put(url, headers=auth_headers(token), json={
        "questions": [
            {"no": "1", "max_marks": 10, "topic": "Linear Equations"},
            {"no": "2", "max_marks": 10, "topic": "Geometry"},
            {"no": "3", "max_marks": 10, "topic": "Linear Equations"},
        ],
    })
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_import_from_cross_school_paper_rejected(
    client: AsyncClient, admin_user: User, test_school: School, test_class: Class,
    db_session: AsyncSession,
):
    from app.db.models.question_paper import PaperStatus, QuestionPaper

    other_school = School(
        name="Other School", code="OTH2", tenant_slug="other2", board="SSC",
        contact_email="o2@test.com", contact_phone="+911111111112", is_active=True,
    )
    db_session.add(other_school)
    await db_session.flush()

    subject = await _subject(db_session, test_school, test_class)
    foreign_paper = QuestionPaper(
        school_id=other_school.id, class_id=test_class.id, subject_id=subject.id,
        created_by=admin_user.id, title="Foreign Paper", board="SSC", grade="Grade 10",
        subject_name="Maths", total_marks=25, duration_minutes=60,
        topics=["Algebra"], difficulty_mix={}, sections=[
            {"title": "A", "questions": [{"number": "1", "marks": 25, "text": "Q"}]}
        ],
        status=PaperStatus.APPROVED, ai_model="test",
    )
    db_session.add(foreign_paper)
    await db_session.flush()

    token = await get_auth_token(client, "test_admin", "Admin@123")
    exam = await _create_exam(client, token, test_class, subject)

    resp = await client.put(
        f"/api/v1/exams/{exam['id']}/questions",
        headers=auth_headers(token),
        json={"source_paper_id": str(foreign_paper.id)},
    )
    assert resp.status_code == 400
    assert "not found" in resp.json()["detail"]

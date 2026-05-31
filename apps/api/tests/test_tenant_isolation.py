"""Cross-tenant IDOR tests — foreign school IDs must not be accepted on writes."""

from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import AcademicYear, Class, Subject
from app.db.models.school import School
from app.db.models.user import User
from tests.conftest import auth_headers, get_auth_token


@pytest.mark.asyncio
async def test_create_subject_rejects_foreign_class(
    client: AsyncClient,
    admin_user: User,
    test_class: Class,
    db_session: AsyncSession,
):
    other_school = School(
        name="Foreign",
        code="FRN",
        tenant_slug="foreign",
        board="CBSE",
        contact_email="f@test.com",
        contact_phone="+919999999999",
        is_active=True,
    )
    db_session.add(other_school)
    await db_session.flush()

    other_year = AcademicYear(
        school_id=other_school.id,
        year_label="2026-2027",
        start_date=date(2026, 6, 1),
        end_date=date(2027, 5, 31),
        is_active=True,
    )
    db_session.add(other_year)
    await db_session.flush()

    foreign_class = Class(
        school_id=other_school.id,
        grade="Grade 9",
        section="Z",
        academic_year_id=other_year.id,
    )
    db_session.add(foreign_class)
    await db_session.flush()

    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.post(
        "/api/v1/academic/subjects",
        headers=auth_headers(token),
        json={"name": "Math", "class_id": str(foreign_class.id)},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_exam_marks_not_visible_across_schools(
    client: AsyncClient,
    admin_user: User,
    test_class: Class,
    db_session: AsyncSession,
):
    from app.db.models.examination import Exam, ExamType

    other_school = School(
        name="Other",
        code="OTH2",
        tenant_slug="other2",
        board="CBSE",
        contact_email="o2@test.com",
        contact_phone="+918888888888",
        is_active=True,
    )
    db_session.add(other_school)
    await db_session.flush()

    other_year = AcademicYear(
        school_id=other_school.id,
        year_label="2026-2027",
        start_date=date(2026, 6, 1),
        end_date=date(2027, 5, 31),
        is_active=True,
    )
    db_session.add(other_year)
    await db_session.flush()

    foreign_class = Class(
        school_id=other_school.id,
        grade="Grade 2",
        section="B",
        academic_year_id=other_year.id,
    )
    db_session.add(foreign_class)
    await db_session.flush()

    subject = Subject(
        school_id=other_school.id,
        name="Science",
        class_id=foreign_class.id,
    )
    db_session.add(subject)
    await db_session.flush()

    foreign_exam = Exam(
        school_id=other_school.id,
        class_id=foreign_class.id,
        subject_id=subject.id,
        exam_type=ExamType.QUIZ,
        title="Foreign Quiz",
        total_marks=100,
        created_by=admin_user.id,
    )
    db_session.add(foreign_exam)
    await db_session.flush()

    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.get(
        f"/api/v1/exams/{foreign_exam.id}/marks",
        headers=auth_headers(token),
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_exam_uses_exam_date_field(
    client: AsyncClient,
    admin_user: User,
    test_class: Class,
    db_session: AsyncSession,
):
    subject = Subject(
        school_id=admin_user.school_id,
        name="English",
        class_id=test_class.id,
    )
    db_session.add(subject)
    await db_session.flush()

    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.post(
        "/api/v1/exams",
        headers=auth_headers(token),
        json={
            "class_id": str(test_class.id),
            "subject_id": str(subject.id),
            "exam_type": "unit_test",
            "title": "Unit 1",
            "total_marks": 50,
            "exam_date": "2026-06-15",
        },
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["data"]["exam_date"] == "2026-06-15"

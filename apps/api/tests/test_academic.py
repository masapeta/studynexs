"""Tests — Academic module."""

from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import AcademicYear, Class, Subject, TeacherSubjectMapping
from app.db.models.user import User
from tests.conftest import auth_headers, get_auth_token


@pytest.mark.asyncio
async def test_list_classes(client: AsyncClient, admin_user: User):
    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.get("/api/v1/academic/classes", headers=auth_headers(token))
    assert resp.status_code == 200
    assert "items" in resp.json()


@pytest.mark.asyncio
async def test_teacher_class_scope_is_applied_before_pagination(
    client: AsyncClient,
    teacher_user: User,
    test_school,
    test_class: Class,
    academic_year: AcademicYear,
    db_session: AsyncSession,
):
    """A scoped class beyond the unfiltered first page must still be page one for its teacher."""
    allowed_class = Class(
        school_id=test_school.id,
        grade="Grade 9",
        section="A",
        academic_year_id=academic_year.id,
    )
    db_session.add(allowed_class)
    await db_session.flush()
    subject = Subject(
        school_id=test_school.id,
        class_id=allowed_class.id,
        name="Science",
        code="SCI",
    )
    db_session.add(subject)
    await db_session.flush()
    db_session.add(
        TeacherSubjectMapping(
            school_id=test_school.id,
            teacher_id=teacher_user.id,
            subject_id=subject.id,
            class_id=allowed_class.id,
            is_primary=True,
        )
    )
    await db_session.flush()

    token = await get_auth_token(client, "test_teacher", "Teacher@123")
    response = await client.get(
        "/api/v1/academic/classes?page=1&page_size=1",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert [row["id"] for row in payload["items"]] == [str(allowed_class.id)]
    assert payload["total"] == 1
    assert payload["total_pages"] == 1


@pytest.mark.asyncio
async def test_create_class(
    client: AsyncClient,
    admin_user: User,
    db_session: AsyncSession,
    test_school,
):
    # Need an academic year first
    ay = AcademicYear(
        school_id=test_school.id,
        year_label="2026-2028",
        start_date=date(2026, 4, 1),
        end_date=date(2028, 3, 31),
        is_active=True,
    )
    db_session.add(ay)
    await db_session.flush()

    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.post("/api/v1/academic/classes", headers=auth_headers(token), json={
        "grade": "Grade 1",
        "section": "A",
        "academic_year_id": str(ay.id),
    })
    assert resp.status_code == 201
    assert resp.json()["data"]["grade"] == "Grade 1"


@pytest.mark.asyncio
async def test_create_class_rejects_duplicate_incharge(
    client: AsyncClient,
    admin_user: User,
    teacher_user: User,
    db_session: AsyncSession,
    test_school,
    academic_year: AcademicYear,
):
    """A teacher cannot be homeroom incharge for more than one class in the same year."""
    first = Class(
        school_id=test_school.id,
        grade="Grade 2",
        section="A",
        academic_year_id=academic_year.id,
        class_incharge_id=teacher_user.id,
    )
    db_session.add(first)
    await db_session.flush()

    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.post(
        "/api/v1/academic/classes",
        headers=auth_headers(token),
        json={
            "grade": "Grade 3",
            "section": "A",
            "academic_year_id": str(academic_year.id),
            "class_incharge_id": str(teacher_user.id),
        },
    )
    assert resp.status_code == 409
    assert "homeroom teacher" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_list_subjects(client: AsyncClient, admin_user: User):
    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.get("/api/v1/academic/subjects", headers=auth_headers(token))
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_list_students(client: AsyncClient, admin_user: User):
    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.get("/api/v1/academic/students", headers=auth_headers(token))
    assert resp.status_code == 200
    assert "items" in resp.json()


@pytest.mark.asyncio
async def test_list_students_includes_dob_and_parent_phone(
    client: AsyncClient,
    admin_user: User,
    student_user: User,
    parent_user: User,
):
    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.get("/api/v1/academic/students", headers=auth_headers(token))
    assert resp.status_code == 200
    row = next(i for i in resp.json()["items"] if i["admission_no"] == "ADM001")
    assert "date_of_birth" in row
    assert row.get("parent_phone") == parent_user.mobile


@pytest.mark.asyncio
async def test_class_roster(
    client: AsyncClient, admin_user: User, test_class: Class, student_user: User
):
    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.get(
        f"/api/v1/academic/classes/{test_class.id}/roster",
        headers=auth_headers(token),
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert isinstance(data, list)
    assert len(data) >= 1
    row = next(r for r in data if r["student_name"])
    assert "attendance_pct" in row
    assert row["admission_no"]

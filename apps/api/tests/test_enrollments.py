"""Tests — Enrollments & student lifecycle (DM-3 expand phase)."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.models.academic import AcademicYear, Class
from app.db.models.school import School
from app.db.models.student import Enrollment, EnrollmentStatus, Student, StudentStatus
from app.db.models.user import User, UserRole
from tests.conftest import auth_headers, get_auth_token


@pytest.mark.asyncio
async def test_enroll_student_creates_enrollment_row(
    client: AsyncClient,
    admin_user: User,
    test_school: School,
    test_class: Class,
    academic_year: AcademicYear,
    db_session: AsyncSession,
):
    """Enrolling a student writes both students.class_id and an enrollments row."""
    user = User(
        school_id=test_school.id,
        username="enrl_student",
        mobile="+919876500001",
        full_name="Enrollment Test Student",
        role=UserRole.STUDENT,
        password_hash=hash_password("Student@123"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.post(
        "/api/v1/academic/students/enroll",
        json={
            "user_id": str(user.id),
            "class_id": str(test_class.id),
            "admission_no": "ENR001",
            "roll_no": "42",
        },
        headers=auth_headers(token),
    )
    assert resp.status_code == 201
    student_id = resp.json()["data"]["id"]

    rows = (
        await db_session.execute(
            select(Enrollment).where(Enrollment.student_id == uuid.UUID(student_id))
        )
    ).scalars().all()
    assert len(rows) == 1
    enrollment = rows[0]
    assert enrollment.school_id == test_school.id
    assert enrollment.class_id == test_class.id
    assert enrollment.academic_year_id == academic_year.id
    assert enrollment.status == EnrollmentStatus.ACTIVE
    assert enrollment.roll_no == "42"

    student = (
        await db_session.execute(
            select(Student).where(Student.id == uuid.UUID(student_id))
        )
    ).scalar_one()
    assert student.status == StudentStatus.ACTIVE


@pytest.mark.asyncio
async def test_one_enrollment_per_student_per_year(
    student_user: User,
    test_school: School,
    test_class: Class,
    academic_year: AcademicYear,
    db_session: AsyncSession,
):
    """uq_enrollment_student_year rejects a second enrollment in the same year."""
    student = (
        await db_session.execute(
            select(Student).where(Student.user_id == student_user.id)
        )
    ).scalar_one()

    db_session.add(
        Enrollment(
            school_id=test_school.id,
            student_id=student.id,
            class_id=test_class.id,
            academic_year_id=academic_year.id,
        )
    )
    await db_session.flush()

    db_session.add(
        Enrollment(
            school_id=test_school.id,
            student_id=student.id,
            class_id=test_class.id,
            academic_year_id=academic_year.id,
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_enrollments_are_tenant_scoped(
    student_user: User,
    test_school: School,
    test_class: Class,
    academic_year: AcademicYear,
    db_session: AsyncSession,
):
    """An enrollment carries its school_id; scoped reads exclude other tenants."""
    student = (
        await db_session.execute(
            select(Student).where(Student.user_id == student_user.id)
        )
    ).scalar_one()
    db_session.add(
        Enrollment(
            school_id=test_school.id,
            student_id=student.id,
            class_id=test_class.id,
            academic_year_id=academic_year.id,
        )
    )
    await db_session.flush()

    other_school_id = uuid.uuid4()
    rows = (
        await db_session.execute(
            select(Enrollment).where(Enrollment.school_id == other_school_id)
        )
    ).scalars().all()
    assert rows == []

    rows = (
        await db_session.execute(
            select(Enrollment).where(
                Enrollment.school_id == test_school.id,
                Enrollment.student_id == student.id,
            )
        )
    ).scalars().all()
    assert len(rows) == 1

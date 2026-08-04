"""Tests — Enrollments & student lifecycle (DM-3 expand phase)."""

import uuid
from datetime import date

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
from app.modules.academic.services.academic_service import AcademicService
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

    # The fixture already created this student's enrollment for the active year,
    # so a second one for the same year must violate the constraint.
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
async def test_one_active_enrollment_across_years(
    student_user: User,
    test_school: School,
    test_class: Class,
    db_session: AsyncSession,
):
    """A second ACTIVE enrollment in a DIFFERENT year is rejected.

    uq_enrollment_student_year only guards within one year; without the partial
    unique index a student could be simultaneously "current" in two years and
    the lifecycle service's scalar_one_or_none() lookups would 500.
    """
    student = (
        await db_session.execute(
            select(Student).where(Student.user_id == student_user.id)
        )
    ).scalar_one()

    next_year = AcademicYear(
        school_id=test_school.id,
        year_label="2027-2028",
        start_date=date(2027, 6, 1),
        end_date=date(2028, 5, 31),
        is_active=False,
    )
    db_session.add(next_year)
    await db_session.flush()
    next_class = Class(
        school_id=test_school.id,
        grade="Grade 2",
        section="A",
        academic_year_id=next_year.id,
    )
    db_session.add(next_class)
    await db_session.flush()

    # The fixture's enrollment for the current year is ACTIVE; opening a second
    # ACTIVE row in the next year must hit uq_one_active_enrollment_per_student.
    # SAVEPOINT so the failure doesn't roll back next_year/next_class.
    with pytest.raises(IntegrityError):
        async with db_session.begin_nested():
            db_session.add(
                Enrollment(
                    school_id=test_school.id,
                    student_id=student.id,
                    class_id=next_class.id,
                    academic_year_id=next_year.id,
                    status=EnrollmentStatus.ACTIVE,
                )
            )
            await db_session.flush()

    # But a CLOSED row in another year is fine — that is exactly what
    # promotion writes (close old year, open new year).
    db_session.add(
        Enrollment(
            school_id=test_school.id,
            student_id=student.id,
            class_id=next_class.id,
            academic_year_id=next_year.id,
            status=EnrollmentStatus.PROMOTED,
            ended_on=date(2028, 4, 30),
        )
    )
    await db_session.flush()


@pytest.mark.asyncio
async def test_read_helpers_return_current_and_full_history(
    student_user: User,
    test_school: School,
    test_class: Class,
    academic_year: AcademicYear,
    db_session: AsyncSession,
):
    """current_enrollment returns the open row; history is newest year first."""
    student = (
        await db_session.execute(
            select(Student).where(Student.user_id == student_user.id)
        )
    ).scalar_one()

    # The fixture already created this year's ACTIVE enrollment. Add a closed
    # prior year so ordering and history depth are both exercised.
    prior_year = AcademicYear(
        school_id=test_school.id,
        year_label="2025-2026",
        start_date=date(2025, 6, 1),
        end_date=date(2026, 5, 31),
        is_active=False,
    )
    db_session.add(prior_year)
    await db_session.flush()
    prior_class = Class(
        school_id=test_school.id,
        grade="Grade 0",
        section="A",
        academic_year_id=prior_year.id,
    )
    db_session.add(prior_class)
    await db_session.flush()
    db_session.add(
        Enrollment(
            school_id=test_school.id,
            student_id=student.id,
            class_id=prior_class.id,
            academic_year_id=prior_year.id,
            status=EnrollmentStatus.PROMOTED,
            ended_on=date(2026, 5, 31),
        )
    )
    await db_session.flush()

    service = AcademicService(db_session)

    current = await service.current_enrollment(test_school.id, student.id)
    assert current is not None
    assert current.academic_year_id == academic_year.id
    assert current.status == EnrollmentStatus.ACTIVE

    history = await service.enrollments_for_student(test_school.id, student.id)
    assert [e.academic_year_id for e in history] == [academic_year.id, prior_year.id]
    # History must stay history: the closed row keeps its own class and outcome.
    assert history[1].class_id == prior_class.id
    assert history[1].status == EnrollmentStatus.PROMOTED


@pytest.mark.asyncio
async def test_read_helpers_do_not_leak_across_tenants(
    student_user: User,
    test_school: School,
    db_session: AsyncSession,
):
    """Helpers are school-scoped: another tenant's id sees nothing."""
    student = (
        await db_session.execute(
            select(Student).where(Student.user_id == student_user.id)
        )
    ).scalar_one()
    service = AcademicService(db_session)

    other_school_id = uuid.uuid4()
    assert await service.current_enrollment(other_school_id, student.id) is None
    assert await service.enrollments_for_student(other_school_id, student.id) == []


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
    # Enrollment comes from the fixture — one per student per year.

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

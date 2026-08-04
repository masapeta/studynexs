"""Tests — Student lifecycle (DM-3b): class change, exits, re-admission."""

import uuid
from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import AcademicYear, Class
from app.db.models.attendance import Attendance, AttendanceStatus
from app.db.models.audit import AuditLog
from app.db.models.school import School
from app.db.models.student import Enrollment, EnrollmentStatus, Student, StudentStatus
from app.db.models.user import User
from tests.conftest import auth_headers, get_auth_token


async def _student_of(db_session: AsyncSession, student_user: User) -> Student:
    return (
        await db_session.execute(
            select(Student).where(Student.user_id == student_user.id)
        )
    ).scalar_one()


async def _sibling_class(
    db_session: AsyncSession, test_school: School, academic_year: AcademicYear
) -> Class:
    """Another section in the same academic year — a valid class-change target."""
    cls = Class(
        school_id=test_school.id,
        grade="Grade 1",
        section="B",
        academic_year_id=academic_year.id,
    )
    db_session.add(cls)
    await db_session.flush()
    return cls


# ── Class change ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_change_class_updates_current_enrollment_only(
    client: AsyncClient,
    admin_user: User,
    student_user: User,
    test_school: School,
    test_class: Class,
    academic_year: AcademicYear,
    db_session: AsyncSession,
):
    """Class change moves student + current enrollment; history stays untouched."""
    student = await _student_of(db_session, student_user)
    target = await _sibling_class(db_session, test_school, academic_year)

    # Historical attendance recorded against the ORIGINAL class.
    db_session.add(
        Attendance(
            school_id=test_school.id,
            student_id=student.id,
            class_id=test_class.id,
            date=date(2026, 7, 1),
            status=AttendanceStatus.PRESENT,
            marked_by=admin_user.id,
        )
    )
    await db_session.flush()

    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.post(
        f"/api/v1/academic/students/{student.id}/change-class",
        json={"class_id": str(target.id), "reason": "Section rebalancing"},
        headers=auth_headers(token),
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["class_id"] == str(target.id)
    assert data["student_status"] == "active"

    await db_session.refresh(student)
    assert student.class_id == target.id

    # Exactly one enrollment for the year, now pointing at the new class.
    enrollments = (
        await db_session.execute(
            select(Enrollment).where(Enrollment.student_id == student.id)
        )
    ).scalars().all()
    assert len(enrollments) == 1
    assert enrollments[0].class_id == target.id
    assert enrollments[0].academic_year_id == academic_year.id

    # History stays history: past attendance still points at the old class.
    attendance = (
        await db_session.execute(
            select(Attendance).where(Attendance.student_id == student.id)
        )
    ).scalars().all()
    assert [a.class_id for a in attendance] == [test_class.id]


@pytest.mark.asyncio
async def test_change_class_rejects_other_academic_year(
    client: AsyncClient,
    admin_user: User,
    student_user: User,
    test_school: School,
    db_session: AsyncSession,
):
    """Cross-year moves are promotion, not a class change."""
    student = await _student_of(db_session, student_user)
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

    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.post(
        f"/api/v1/academic/students/{student.id}/change-class",
        json={"class_id": str(next_class.id), "reason": "Wrong year on purpose"},
        headers=auth_headers(token),
    )
    assert resp.status_code == 400
    assert "academic year" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_change_class_writes_audit_entry(
    client: AsyncClient,
    admin_user: User,
    student_user: User,
    test_school: School,
    test_class: Class,
    academic_year: AcademicYear,
    db_session: AsyncSession,
):
    """Every lifecycle transition is attributable: who, what, why."""
    student = await _student_of(db_session, student_user)
    target = await _sibling_class(db_session, test_school, academic_year)

    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.post(
        f"/api/v1/academic/students/{student.id}/change-class",
        json={"class_id": str(target.id), "reason": "Parent request"},
        headers=auth_headers(token),
    )
    assert resp.status_code == 200

    entry = (
        await db_session.execute(
            select(AuditLog).where(
                AuditLog.action == "student.class_changed",
                AuditLog.resource_id == str(student.id),
            )
        )
    ).scalars().first()
    assert entry is not None
    assert entry.school_id == test_school.id
    assert entry.details["from_class_id"] == str(test_class.id)
    assert entry.details["to_class_id"] == str(target.id)
    assert entry.details["reason"] == "Parent request"


# ── Authorization ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_teacher_cannot_change_student_class(
    client: AsyncClient,
    teacher_user: User,
    student_user: User,
    test_school: School,
    academic_year: AcademicYear,
    db_session: AsyncSession,
):
    """Lifecycle actions are admin/super_admin only."""
    student = await _student_of(db_session, student_user)
    target = await _sibling_class(db_session, test_school, academic_year)

    token = await get_auth_token(client, "test_teacher", "Teacher@123")
    resp = await client.post(
        f"/api/v1/academic/students/{student.id}/change-class",
        json={"class_id": str(target.id), "reason": "Should be denied"},
        headers=auth_headers(token),
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_teacher_cannot_withdraw_student(
    client: AsyncClient,
    teacher_user: User,
    student_user: User,
    db_session: AsyncSession,
):
    student = await _student_of(db_session, student_user)
    token = await get_auth_token(client, "test_teacher", "Teacher@123")
    resp = await client.post(
        f"/api/v1/academic/students/{student.id}/withdraw",
        json={"reason": "Should be denied"},
        headers=auth_headers(token),
    )
    assert resp.status_code == 403


# ── Exits ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_transfer_out_closes_enrollment(
    client: AsyncClient,
    admin_user: User,
    student_user: User,
    test_class: Class,
    db_session: AsyncSession,
):
    """Transfer sets lifecycle status and closes the enrollment with a date."""
    student = await _student_of(db_session, student_user)

    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.post(
        f"/api/v1/academic/students/{student.id}/transfer-out",
        json={"reason": "Family relocating", "effective_date": "2026-08-31"},
        headers=auth_headers(token),
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["student_status"] == "transferred"

    await db_session.refresh(student)
    assert student.status == StudentStatus.TRANSFERRED

    enrollment = (
        await db_session.execute(
            select(Enrollment).where(Enrollment.student_id == student.id)
        )
    ).scalar_one()
    assert enrollment.status == EnrollmentStatus.TRANSFERRED
    assert enrollment.ended_on == date(2026, 8, 31)
    # The class link is preserved — the record of where they studied.
    assert enrollment.class_id == test_class.id


@pytest.mark.asyncio
async def test_withdraw_then_change_class_is_rejected(
    client: AsyncClient,
    admin_user: User,
    student_user: User,
    test_school: School,
    academic_year: AcademicYear,
    db_session: AsyncSession,
):
    """An exited student cannot be moved between classes."""
    student = await _student_of(db_session, student_user)
    target = await _sibling_class(db_session, test_school, academic_year)
    token = await get_auth_token(client, "test_admin", "Admin@123")

    withdraw = await client.post(
        f"/api/v1/academic/students/{student.id}/withdraw",
        json={"reason": "Left the school"},
        headers=auth_headers(token),
    )
    assert withdraw.status_code == 200

    resp = await client.post(
        f"/api/v1/academic/students/{student.id}/change-class",
        json={"class_id": str(target.id), "reason": "Should fail"},
        headers=auth_headers(token),
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_double_exit_is_rejected(
    client: AsyncClient,
    admin_user: User,
    student_user: User,
    db_session: AsyncSession,
):
    student = await _student_of(db_session, student_user)
    token = await get_auth_token(client, "test_admin", "Admin@123")

    first = await client.post(
        f"/api/v1/academic/students/{student.id}/withdraw",
        json={"reason": "First exit"},
        headers=auth_headers(token),
    )
    assert first.status_code == 200

    second = await client.post(
        f"/api/v1/academic/students/{student.id}/transfer-out",
        json={"reason": "Second exit"},
        headers=auth_headers(token),
    )
    assert second.status_code == 409


# ── Re-admission ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_readmit_reopens_same_year_enrollment(
    client: AsyncClient,
    admin_user: User,
    student_user: User,
    test_class: Class,
    db_session: AsyncSession,
):
    """
    Returning within the same academic year reopens the existing row rather
    than violating one-enrollment-per-student-per-year.
    """
    student = await _student_of(db_session, student_user)
    token = await get_auth_token(client, "test_admin", "Admin@123")

    await client.post(
        f"/api/v1/academic/students/{student.id}/withdraw",
        json={"reason": "Left temporarily"},
        headers=auth_headers(token),
    )
    resp = await client.post(
        f"/api/v1/academic/students/{student.id}/readmit",
        json={"class_id": str(test_class.id), "reason": "Returned"},
        headers=auth_headers(token),
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["student_status"] == "active"

    enrollments = (
        await db_session.execute(
            select(Enrollment).where(Enrollment.student_id == student.id)
        )
    ).scalars().all()
    assert len(enrollments) == 1
    assert enrollments[0].status == EnrollmentStatus.ACTIVE
    assert enrollments[0].ended_on is None


@pytest.mark.asyncio
async def test_readmit_active_student_is_rejected(
    client: AsyncClient,
    admin_user: User,
    student_user: User,
    test_class: Class,
    db_session: AsyncSession,
):
    student = await _student_of(db_session, student_user)
    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.post(
        f"/api/v1/academic/students/{student.id}/readmit",
        json={"class_id": str(test_class.id), "reason": "Already active"},
        headers=auth_headers(token),
    )
    assert resp.status_code == 409


# ── History & tenancy ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_enrollment_history_endpoint(
    client: AsyncClient,
    admin_user: User,
    student_user: User,
    test_class: Class,
    db_session: AsyncSession,
):
    student = await _student_of(db_session, student_user)
    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.get(
        f"/api/v1/academic/students/{student.id}/enrollments",
        headers=auth_headers(token),
    )
    assert resp.status_code == 200
    items = resp.json()["data"]
    assert len(items) == 1
    assert items[0]["status"] == "active"
    assert items[0]["class_name"] == f"{test_class.grade}-{test_class.section}"


@pytest.mark.asyncio
async def test_lifecycle_rejects_unknown_student(
    client: AsyncClient,
    admin_user: User,
    test_class: Class,
):
    """A student id from outside this tenant is simply not found."""
    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.post(
        f"/api/v1/academic/students/{uuid.uuid4()}/change-class",
        json={"class_id": str(test_class.id), "reason": "No such student"},
        headers=auth_headers(token),
    )
    assert resp.status_code == 404

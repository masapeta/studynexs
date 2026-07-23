"""Dashboard attendance state — truthful KPIs when rolls are missing or partial."""

from __future__ import annotations

from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.models.attendance import Attendance, AttendanceStatus
from app.db.models.school import School
from app.db.models.student import Student
from app.db.models.user import User, UserRole
from tests.conftest import access_token_for, auth_headers


async def _add_student(
    db: AsyncSession,
    school: School,
    class_id,
    *,
    admission_no: str,
    roll_no: str,
) -> Student:
    user = User(
        school_id=school.id,
        username=f"stu_{admission_no.lower()}",
        mobile=f"+91990000{roll_no.zfill(4)}",
        full_name=f"Student {roll_no}",
        role=UserRole.STUDENT,
        password_hash=hash_password("Student@123"),
        is_active=True,
    )
    db.add(user)
    await db.flush()
    student = Student(
        school_id=school.id,
        user_id=user.id,
        class_id=class_id,
        admission_no=admission_no,
        roll_no=roll_no,
    )
    db.add(student)
    await db.flush()
    return student


async def _mark_attendance(
    db: AsyncSession,
    *,
    school_id,
    student: Student,
    class_id,
    marked_by,
    on_date: date,
    status: AttendanceStatus,
) -> None:
    db.add(
        Attendance(
            school_id=school_id,
            student_id=student.id,
            class_id=class_id,
            date=on_date,
            status=status,
            marked_by=marked_by,
        )
    )
    await db.flush()


@pytest.mark.asyncio
async def test_dashboard_not_recorded_when_no_today_rolls(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    student_user: User,
    test_class,
):
    """Zero attendance rows today must not surface as 0% failure."""
    token = access_token_for(admin_user)
    resp = await client.get("/api/v1/dashboard/summary", headers=auth_headers(token))
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["school_attendance_status"] == "not_recorded"
    assert data["school_attendance_percent"] is None
    assert data["attendance_marked_today"] == 0
    assert data["class_performance"] == []
    assert "not been recorded" in data["subtitle"].lower()


@pytest.mark.asyncio
async def test_dashboard_healthy_when_today_rolls_strong(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    student_user: User,
    test_school: School,
    test_class,
):
    student = await db_session.scalar(select(Student).where(Student.school_id == test_school.id))
    assert student is not None
    today = date.today()
    await _mark_attendance(
        db_session,
        school_id=test_school.id,
        student=student,
        class_id=test_class.id,
        marked_by=admin_user.id,
        on_date=today,
        status=AttendanceStatus.PRESENT,
    )
    # Second student also present so enrolled == marked with high rate
    extra = await _add_student(
        db_session, test_school, test_class.id, admission_no="ADM002", roll_no="2"
    )
    await _mark_attendance(
        db_session,
        school_id=test_school.id,
        student=extra,
        class_id=test_class.id,
        marked_by=admin_user.id,
        on_date=today,
        status=AttendanceStatus.PRESENT,
    )

    token = access_token_for(admin_user)
    resp = await client.get("/api/v1/dashboard/summary", headers=auth_headers(token))
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["school_attendance_status"] == "healthy"
    assert data["school_attendance_percent"] == 100.0
    assert len(data["class_performance"]) >= 1


@pytest.mark.asyncio
async def test_dashboard_in_progress_when_partial_rolls(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    test_school: School,
    test_class,
    student_user: User,
):
    student = await db_session.scalar(select(Student).where(Student.school_id == test_school.id))
    assert student is not None
    await _add_student(db_session, test_school, test_class.id, admission_no="ADM003", roll_no="3")
    today = date.today()
    await _mark_attendance(
        db_session,
        school_id=test_school.id,
        student=student,
        class_id=test_class.id,
        marked_by=admin_user.id,
        on_date=today,
        status=AttendanceStatus.PRESENT,
    )

    token = access_token_for(admin_user)
    resp = await client.get("/api/v1/dashboard/summary", headers=auth_headers(token))
    data = resp.json()["data"]
    assert data["school_attendance_status"] == "in_progress"
    assert data["attendance_marked_today"] == 1
    assert data["attendance_enrolled"] >= 2


@pytest.mark.asyncio
async def test_dashboard_attention_needed_when_below_target(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    test_school: School,
    test_class,
    student_user: User,
):
    student = await db_session.scalar(select(Student).where(Student.school_id == test_school.id))
    assert student is not None
    extra = await _add_student(
        db_session, test_school, test_class.id, admission_no="ADM004", roll_no="4"
    )
    today = date.today()
    await _mark_attendance(
        db_session,
        school_id=test_school.id,
        student=student,
        class_id=test_class.id,
        marked_by=admin_user.id,
        on_date=today,
        status=AttendanceStatus.ABSENT,
    )
    await _mark_attendance(
        db_session,
        school_id=test_school.id,
        student=extra,
        class_id=test_class.id,
        marked_by=admin_user.id,
        on_date=today,
        status=AttendanceStatus.PRESENT,
    )

    token = access_token_for(admin_user)
    resp = await client.get("/api/v1/dashboard/summary", headers=auth_headers(token))
    data = resp.json()["data"]
    assert data["school_attendance_status"] == "attention_needed"
    assert data["school_attendance_percent"] == 50.0

"""Tests — Bulk enrollment (DM-3c): year-rollover promotion and section moves."""

import uuid
from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.models.academic import AcademicYear, Class
from app.db.models.attendance import Attendance, AttendanceStatus
from app.db.models.audit import AuditLog
from app.db.models.school import School
from app.db.models.student import Enrollment, EnrollmentStatus, Student, StudentStatus
from app.db.models.user import User, UserRole
from tests.conftest import auth_headers, get_auth_token


async def _make_student(
    db_session: AsyncSession,
    school: School,
    cls: Class,
    *,
    suffix: str,
    roll_no: str,
) -> Student:
    """A student with the per-year enrollment that production guarantees."""
    user = User(
        school_id=school.id,
        username=f"promo_{suffix}",
        mobile=f"+9198765{suffix.zfill(5)}",
        full_name=f"Promo Student {suffix}",
        role=UserRole.STUDENT,
        password_hash=hash_password("Student@123"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    student = Student(
        school_id=school.id,
        user_id=user.id,
        class_id=cls.id,
        admission_no=f"PADM{suffix}",
        roll_no=roll_no,
    )
    db_session.add(student)
    await db_session.flush()

    db_session.add(
        Enrollment(
            school_id=school.id,
            student_id=student.id,
            class_id=cls.id,
            academic_year_id=cls.academic_year_id,
            roll_no=roll_no,
        )
    )
    await db_session.flush()
    return student


async def _next_year(db_session: AsyncSession, school: School) -> AcademicYear:
    year = AcademicYear(
        school_id=school.id,
        year_label="2027-2028",
        start_date=date(2027, 6, 1),
        end_date=date(2028, 5, 31),
        is_active=False,
    )
    db_session.add(year)
    await db_session.flush()
    return year


async def _class_in(
    db_session: AsyncSession,
    school: School,
    year: AcademicYear,
    *,
    grade: str,
    section: str = "A",
) -> Class:
    cls = Class(
        school_id=school.id,
        grade=grade,
        section=section,
        academic_year_id=year.id,
    )
    db_session.add(cls)
    await db_session.flush()
    return cls


async def _enrollments_of(db_session: AsyncSession, student_id: uuid.UUID) -> list[Enrollment]:
    rows = await db_session.execute(
        select(Enrollment).where(Enrollment.student_id == student_id)
    )
    return list(rows.scalars().all())


# ── Preview ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_preview_lists_whole_class_and_changes_nothing(
    client: AsyncClient,
    admin_user: User,
    test_school: School,
    test_class: Class,
    db_session: AsyncSession,
):
    """Preview is read-only: it describes the rollover without performing it."""
    student = await _make_student(
        db_session, test_school, test_class, suffix="01", roll_no="1"
    )
    year = await _next_year(db_session, test_school)
    target = await _class_in(db_session, test_school, year, grade="Grade 2")

    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.post(
        "/api/v1/academic/enrollments/promote/preview",
        json={"from_class_id": str(test_class.id), "to_class_id": str(target.id)},
        headers=auth_headers(token),
    )
    assert resp.status_code == 200
    data = resp.json()["data"]

    assert data["summary"]["total"] == 1
    assert data["summary"]["promoted"] == 1
    assert data["candidates"][0]["student_id"] == str(student.id)
    assert data["candidates"][0]["target_class_label"] == "Grade 2 A"

    # Nothing was written.
    enrollments = await _enrollments_of(db_session, student.id)
    assert len(enrollments) == 1
    assert enrollments[0].status == EnrollmentStatus.ACTIVE
    assert enrollments[0].ended_on is None


@pytest.mark.asyncio
async def test_preview_rejects_same_academic_year(
    client: AsyncClient,
    admin_user: User,
    test_school: School,
    test_class: Class,
    academic_year: AcademicYear,
    db_session: AsyncSession,
):
    """Promotion crosses years; a same-year move is a section change."""
    sibling = await _class_in(
        db_session, test_school, academic_year, grade="Grade 1", section="B"
    )

    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.post(
        "/api/v1/academic/enrollments/promote/preview",
        json={"from_class_id": str(test_class.id), "to_class_id": str(sibling.id)},
        headers=auth_headers(token),
    )
    assert resp.status_code == 400
    assert "bulk class move" in resp.json()["detail"].lower()


# ── Commit ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_commit_closes_old_enrollment_and_opens_new(
    client: AsyncClient,
    admin_user: User,
    test_school: School,
    test_class: Class,
    academic_year: AcademicYear,
    db_session: AsyncSession,
):
    """Promotion is additive: last year closes as promoted, next year opens."""
    student = await _make_student(
        db_session, test_school, test_class, suffix="02", roll_no="7"
    )
    year = await _next_year(db_session, test_school)
    target = await _class_in(db_session, test_school, year, grade="Grade 2")

    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.post(
        "/api/v1/academic/enrollments/promote",
        json={
            "from_class_id": str(test_class.id),
            "to_class_id": str(target.id),
            "reason": "Annual rollover 2027-2028",
        },
        headers=auth_headers(token),
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["enrollments_created"] == 1
    assert data["enrollments_closed"] == 1

    enrollments = await _enrollments_of(db_session, student.id)
    assert len(enrollments) == 2
    by_year = {e.academic_year_id: e for e in enrollments}

    old = by_year[academic_year.id]
    assert old.status == EnrollmentStatus.PROMOTED
    assert old.ended_on == academic_year.end_date
    assert old.class_id == test_class.id  # history keeps its class

    new = by_year[year.id]
    assert new.status == EnrollmentStatus.ACTIVE
    assert new.class_id == target.id
    assert new.enrolled_on == year.start_date
    assert new.roll_no == "7"  # roll carries forward

    await db_session.refresh(student)
    assert student.class_id == target.id
    assert student.status == StudentStatus.ACTIVE


@pytest.mark.asyncio
async def test_promotion_leaves_history_attached_to_old_class(
    client: AsyncClient,
    admin_user: User,
    test_school: School,
    test_class: Class,
    db_session: AsyncSession,
):
    """Last year's attendance stays attached to last year's class."""
    student = await _make_student(
        db_session, test_school, test_class, suffix="03", roll_no="3"
    )
    db_session.add(
        Attendance(
            school_id=test_school.id,
            student_id=student.id,
            class_id=test_class.id,
            date=date(2026, 9, 15),
            status=AttendanceStatus.PRESENT,
            marked_by=admin_user.id,
        )
    )
    await db_session.flush()

    year = await _next_year(db_session, test_school)
    target = await _class_in(db_session, test_school, year, grade="Grade 2")

    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.post(
        "/api/v1/academic/enrollments/promote",
        json={
            "from_class_id": str(test_class.id),
            "to_class_id": str(target.id),
            "reason": "Annual rollover",
        },
        headers=auth_headers(token),
    )
    assert resp.status_code == 200

    attendance = (
        await db_session.execute(
            select(Attendance).where(Attendance.student_id == student.id)
        )
    ).scalars().all()
    assert [a.class_id for a in attendance] == [test_class.id]


@pytest.mark.asyncio
async def test_detained_student_repeats_in_nominated_class(
    client: AsyncClient,
    admin_user: User,
    test_school: School,
    test_class: Class,
    db_session: AsyncSession,
):
    """A detained student gets next year's row in the class they repeat."""
    promoted = await _make_student(
        db_session, test_school, test_class, suffix="04", roll_no="4"
    )
    detained = await _make_student(
        db_session, test_school, test_class, suffix="05", roll_no="5"
    )
    year = await _next_year(db_session, test_school)
    grade_two = await _class_in(db_session, test_school, year, grade="Grade 2")
    repeat_class = await _class_in(db_session, test_school, year, grade="Grade 1")

    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.post(
        "/api/v1/academic/enrollments/promote",
        json={
            "from_class_id": str(test_class.id),
            "to_class_id": str(grade_two.id),
            "reason": "Annual rollover",
            "exclusions": [
                {
                    "student_id": str(detained.id),
                    "outcome": "detained",
                    "target_class_id": str(repeat_class.id),
                }
            ],
        },
        headers=auth_headers(token),
    )
    assert resp.status_code == 200
    summary = resp.json()["data"]["summary"]
    assert summary["promoted"] == 1
    assert summary["detained"] == 1

    await db_session.refresh(promoted)
    await db_session.refresh(detained)
    assert promoted.class_id == grade_two.id
    assert detained.class_id == repeat_class.id

    detained_rows = await _enrollments_of(db_session, detained.id)
    closed = [e for e in detained_rows if e.status == EnrollmentStatus.DETAINED]
    assert len(closed) == 1


@pytest.mark.asyncio
async def test_detained_student_requires_target_class(
    client: AsyncClient,
    admin_user: User,
    test_school: School,
    test_class: Class,
    db_session: AsyncSession,
):
    """We refuse to guess which class a detained student repeats in."""
    student = await _make_student(
        db_session, test_school, test_class, suffix="06", roll_no="6"
    )
    year = await _next_year(db_session, test_school)
    target = await _class_in(db_session, test_school, year, grade="Grade 2")

    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.post(
        "/api/v1/academic/enrollments/promote/preview",
        json={
            "from_class_id": str(test_class.id),
            "to_class_id": str(target.id),
            "exclusions": [{"student_id": str(student.id), "outcome": "detained"}],
        },
        headers=auth_headers(token),
    )
    assert resp.status_code == 400
    assert "target class" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_graduating_student_becomes_alumni_without_new_enrollment(
    client: AsyncClient,
    admin_user: User,
    test_school: School,
    test_class: Class,
    academic_year: AcademicYear,
    db_session: AsyncSession,
):
    """Final-grade students leave the roll rather than gaining a new year."""
    student = await _make_student(
        db_session, test_school, test_class, suffix="07", roll_no="8"
    )
    year = await _next_year(db_session, test_school)
    target = await _class_in(db_session, test_school, year, grade="Grade 2")

    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.post(
        "/api/v1/academic/enrollments/promote",
        json={
            "from_class_id": str(test_class.id),
            "to_class_id": str(target.id),
            "reason": "Class 10 completion",
            "exclusions": [{"student_id": str(student.id), "outcome": "graduated"}],
        },
        headers=auth_headers(token),
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["enrollments_created"] == 0

    await db_session.refresh(student)
    assert student.status == StudentStatus.ALUMNI

    enrollments = await _enrollments_of(db_session, student.id)
    assert len(enrollments) == 1
    assert enrollments[0].status == EnrollmentStatus.COMPLETED
    assert enrollments[0].ended_on == academic_year.end_date


@pytest.mark.asyncio
async def test_exited_student_is_skipped_with_a_reason(
    client: AsyncClient,
    admin_user: User,
    test_school: School,
    test_class: Class,
    db_session: AsyncSession,
):
    """A student who already left is reported, never silently dropped."""
    student = await _make_student(
        db_session, test_school, test_class, suffix="08", roll_no="9"
    )
    student.status = StudentStatus.TRANSFERRED
    await db_session.flush()

    year = await _next_year(db_session, test_school)
    target = await _class_in(db_session, test_school, year, grade="Grade 2")

    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.post(
        "/api/v1/academic/enrollments/promote/preview",
        json={"from_class_id": str(test_class.id), "to_class_id": str(target.id)},
        headers=auth_headers(token),
    )
    assert resp.status_code == 200
    candidate = next(
        c for c in resp.json()["data"]["candidates"] if c["student_id"] == str(student.id)
    )
    assert candidate["outcome"] == "skipped"
    assert "transferred" in candidate["warnings"][0].lower()


@pytest.mark.asyncio
async def test_promotion_is_not_repeatable(
    client: AsyncClient,
    admin_user: User,
    test_school: School,
    test_class: Class,
    db_session: AsyncSession,
):
    """Running the rollover twice must not create a second enrollment."""
    student = await _make_student(
        db_session, test_school, test_class, suffix="09", roll_no="10"
    )
    year = await _next_year(db_session, test_school)
    target = await _class_in(db_session, test_school, year, grade="Grade 2")

    token = await get_auth_token(client, "test_admin", "Admin@123")
    payload = {
        "from_class_id": str(test_class.id),
        "to_class_id": str(target.id),
        "reason": "Annual rollover",
    }
    first = await client.post(
        "/api/v1/academic/enrollments/promote",
        json=payload,
        headers=auth_headers(token),
    )
    assert first.status_code == 200

    second = await client.post(
        "/api/v1/academic/enrollments/promote",
        json=payload,
        headers=auth_headers(token),
    )
    assert second.status_code == 200
    # The roster is read from enrollments, and this student's row for the old
    # year is now closed, so there is nothing left to promote.
    assert second.json()["data"]["enrollments_created"] == 0

    enrollments = await _enrollments_of(db_session, student.id)
    assert len(enrollments) == 2


@pytest.mark.asyncio
async def test_promotion_writes_an_audit_entry(
    client: AsyncClient,
    admin_user: User,
    test_school: School,
    test_class: Class,
    db_session: AsyncSession,
):
    await _make_student(db_session, test_school, test_class, suffix="10", roll_no="11")
    year = await _next_year(db_session, test_school)
    target = await _class_in(db_session, test_school, year, grade="Grade 2")

    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.post(
        "/api/v1/academic/enrollments/promote",
        json={
            "from_class_id": str(test_class.id),
            "to_class_id": str(target.id),
            "reason": "Annual rollover 2027-2028",
        },
        headers=auth_headers(token),
    )
    assert resp.status_code == 200

    entry = (
        await db_session.execute(
            select(AuditLog).where(AuditLog.action == "enrollment.promoted_batch")
        )
    ).scalars().first()
    assert entry is not None
    assert entry.details["reason"] == "Annual rollover 2027-2028"
    assert entry.details["to_year"] == "2027-2028"
    assert entry.details["summary"]["promoted"] == 1


@pytest.mark.asyncio
async def test_teacher_cannot_promote(
    client: AsyncClient,
    teacher_user: User,
    test_school: School,
    test_class: Class,
    db_session: AsyncSession,
):
    """Rollover is an administrative act."""
    year = await _next_year(db_session, test_school)
    target = await _class_in(db_session, test_school, year, grade="Grade 2")

    token = await get_auth_token(client, "test_teacher", "Teacher@123")
    resp = await client.post(
        "/api/v1/academic/enrollments/promote",
        json={
            "from_class_id": str(test_class.id),
            "to_class_id": str(target.id),
            "reason": "Annual rollover",
        },
        headers=auth_headers(token),
    )
    assert resp.status_code == 403


# ── Bulk section move ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_bulk_class_change_moves_selected_students(
    client: AsyncClient,
    admin_user: User,
    test_school: School,
    test_class: Class,
    academic_year: AcademicYear,
    db_session: AsyncSession,
):
    """Selective section move updates the current enrollment only."""
    moving = await _make_student(
        db_session, test_school, test_class, suffix="11", roll_no="12"
    )
    staying = await _make_student(
        db_session, test_school, test_class, suffix="12", roll_no="13"
    )
    section_b = await _class_in(
        db_session, test_school, academic_year, grade="Grade 1", section="B"
    )

    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.post(
        "/api/v1/academic/enrollments/bulk-change-class",
        json={
            "from_class_id": str(test_class.id),
            "to_class_id": str(section_b.id),
            "student_ids": [str(moving.id)],
            "reason": "Section rebalancing",
        },
        headers=auth_headers(token),
    )
    assert resp.status_code == 200
    assert len(resp.json()["data"]["moved"]) == 1

    await db_session.refresh(moving)
    await db_session.refresh(staying)
    assert moving.class_id == section_b.id
    assert staying.class_id == test_class.id

    rows = await _enrollments_of(db_session, moving.id)
    assert len(rows) == 1  # still one row for the year, now pointing at 1B
    assert rows[0].class_id == section_b.id
    assert rows[0].academic_year_id == academic_year.id


@pytest.mark.asyncio
async def test_bulk_class_change_rejects_cross_year(
    client: AsyncClient,
    admin_user: User,
    test_school: School,
    test_class: Class,
    db_session: AsyncSession,
):
    """Moving across years is promotion, and must not masquerade as a move."""
    year = await _next_year(db_session, test_school)
    target = await _class_in(db_session, test_school, year, grade="Grade 2")

    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.post(
        "/api/v1/academic/enrollments/bulk-change-class",
        json={
            "from_class_id": str(test_class.id),
            "to_class_id": str(target.id),
            "reason": "Wrong tool for the job",
        },
        headers=auth_headers(token),
    )
    assert resp.status_code == 400
    assert "same academic year" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_bulk_class_change_rejects_students_from_another_class(
    client: AsyncClient,
    admin_user: User,
    test_school: School,
    test_class: Class,
    academic_year: AcademicYear,
    db_session: AsyncSession,
):
    """Guards against a stale roster in the caller's UI."""
    section_b = await _class_in(
        db_session, test_school, academic_year, grade="Grade 1", section="B"
    )
    outsider = await _make_student(
        db_session, test_school, section_b, suffix="13", roll_no="14"
    )

    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.post(
        "/api/v1/academic/enrollments/bulk-change-class",
        json={
            "from_class_id": str(test_class.id),
            "to_class_id": str(section_b.id),
            "student_ids": [str(outsider.id)],
            "reason": "Section rebalancing",
        },
        headers=auth_headers(token),
    )
    assert resp.status_code == 400
    assert "not in this class" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_bulk_operations_are_tenant_isolated(
    client: AsyncClient,
    admin_user: User,
    test_school: School,
    test_class: Class,
    db_session: AsyncSession,
):
    """A class from another school is invisible, not merely forbidden."""
    other_school = School(
        name="Other Promo School",
        code="OPS",
        tenant_slug="other-promo",
        board="CBSE",
        contact_email="admin@other-promo.test",
        contact_phone="+919000000111",
        is_active=True,
    )
    db_session.add(other_school)
    await db_session.flush()
    other_year = AcademicYear(
        school_id=other_school.id,
        year_label="2027-2028",
        start_date=date(2027, 6, 1),
        end_date=date(2028, 5, 31),
        is_active=True,
    )
    db_session.add(other_year)
    await db_session.flush()
    other_class = Class(
        school_id=other_school.id,
        grade="Grade 2",
        section="A",
        academic_year_id=other_year.id,
    )
    db_session.add(other_class)
    await db_session.flush()

    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.post(
        "/api/v1/academic/enrollments/promote/preview",
        json={"from_class_id": str(test_class.id), "to_class_id": str(other_class.id)},
        headers=auth_headers(token),
    )
    assert resp.status_code == 404

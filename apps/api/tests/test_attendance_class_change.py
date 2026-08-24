"""Attendance must follow a student who changes class (audit P1-DATA-001).

`uq_attendance_student_date` is `(school_id, student_id, date)` — deliberately one row per
student per day. So when a student moves class mid-day, the existing row has to be *moved*,
not just re-statused. The `ON CONFLICT ... set_` clause omitted `class_id`, so:

  * the receiving teacher marked the student and got "Attendance marked for 1 students",
  * the student never appeared in the receiving class's register, and
  * the student kept counting against the register of the class they had left.

Reproduced live before the fix (student `Aryan Choudhary`, Grade 1 B -> Grade 1 C, tenant
`sia`): the row stayed on Grade 1 B while the API reported success.

These tests assert on the **register views a teacher actually sees**, not only the raw row,
because the row alone would not have revealed the double-counting.
"""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import AcademicYear, Class
from app.db.models.attendance import Attendance
from app.db.models.school import School
from app.db.models.student import Student
from app.db.models.user import User
from tests.conftest import auth_headers, get_auth_token

MARK_DATE = "2026-07-02"


@pytest.fixture
def att_date() -> date:
    return date.fromisoformat(MARK_DATE)


async def _second_class(
    db_session: AsyncSession, test_school: School, academic_year: AcademicYear
) -> Class:
    """A second class in the same school/year to move the student into."""
    other = Class(
        school_id=test_school.id,
        academic_year_id=academic_year.id,
        grade="5",
        section="B",
    )
    db_session.add(other)
    await db_session.flush()
    return other


async def _student(db_session: AsyncSession, student_user: User) -> Student:
    result = await db_session.execute(select(Student).where(Student.user_id == student_user.id))
    return result.scalar_one()


async def _attendance_row(
    db_session: AsyncSession, student_id: uuid.UUID, att_date: date
) -> Attendance | None:
    result = await db_session.execute(
        select(Attendance).where(
            Attendance.student_id == student_id,
            Attendance.date == att_date,
        )
    )
    return result.scalars().first()


async def _register(client: AsyncClient, headers: dict, class_id: uuid.UUID) -> list[dict]:
    resp = await client.get(
        f"/api/v1/attendance/class/{class_id}?date={MARK_DATE}", headers=headers
    )
    assert resp.status_code == 200
    return resp.json()["data"]


async def _summary(client: AsyncClient, headers: dict, class_id: uuid.UUID) -> dict:
    resp = await client.get(
        f"/api/v1/attendance/class/{class_id}/summary?date={MARK_DATE}", headers=headers
    )
    assert resp.status_code == 200
    return resp.json()["data"]


@pytest.mark.asyncio
async def test_attendance_row_moves_to_the_new_class(
    client: AsyncClient,
    admin_user: User,
    student_user: User,
    test_class: Class,
    test_school: School,
    academic_year: AcademicYear,
    db_session: AsyncSession,
    att_date: date,
) -> None:
    """The stored row must carry the class that actually marked the student."""
    token = await get_auth_token(client, "test_admin", "Admin@123")
    headers = auth_headers(token)
    student = await _student(db_session, student_user)
    new_class = await _second_class(db_session, test_school, academic_year)

    # Original class marks the student absent.
    resp = await client.post(
        "/api/v1/attendance/mark",
        json={
            "class_id": str(test_class.id),
            "date": MARK_DATE,
            "entries": [{"student_id": str(student.id), "status": "absent"}],
        },
        headers=headers,
    )
    assert resp.status_code == 200

    row = await _attendance_row(db_session, student.id, att_date)
    assert row is not None
    assert row.class_id == test_class.id

    # Student moves class, and the receiving class marks them present the same day.
    student.class_id = new_class.id
    await db_session.flush()

    resp = await client.post(
        "/api/v1/attendance/mark",
        json={
            "class_id": str(new_class.id),
            "date": MARK_DATE,
            "entries": [{"student_id": str(student.id), "status": "present"}],
        },
        headers=headers,
    )
    assert resp.status_code == 200

    await db_session.refresh(row)
    assert row.class_id == new_class.id, (
        "attendance stayed on the previous class: the receiving teacher's mark was reported "
        "as successful but filed against a class the student had left"
    )
    assert row.status.value.lower() == "present"


@pytest.mark.asyncio
async def test_student_is_not_counted_by_two_classes_on_the_same_day(
    client: AsyncClient,
    admin_user: User,
    student_user: User,
    test_class: Class,
    test_school: School,
    academic_year: AcademicYear,
    db_session: AsyncSession,
) -> None:
    """The register a teacher sees is the real symptom — assert on both registers.

    Before the fix the student was visible in the *old* class and absent from the *new* one,
    so each teacher's screen contradicted the other and the day was double-counted.
    """
    token = await get_auth_token(client, "test_admin", "Admin@123")
    headers = auth_headers(token)
    student = await _student(db_session, student_user)
    new_class = await _second_class(db_session, test_school, academic_year)

    await client.post(
        "/api/v1/attendance/mark",
        json={
            "class_id": str(test_class.id),
            "date": MARK_DATE,
            "entries": [{"student_id": str(student.id), "status": "absent"}],
        },
        headers=headers,
    )

    student.class_id = new_class.id
    await db_session.flush()

    await client.post(
        "/api/v1/attendance/mark",
        json={
            "class_id": str(new_class.id),
            "date": MARK_DATE,
            "entries": [{"student_id": str(student.id), "status": "present"}],
        },
        headers=headers,
    )

    old_register = await _register(client, headers, test_class.id)
    new_register = await _register(client, headers, new_class.id)
    old_ids = {entry["student_id"] for entry in old_register}
    new_ids = {entry["student_id"] for entry in new_register}

    assert str(student.id) in new_ids, "student missing from the register that marked them"
    assert str(student.id) not in old_ids, "student still counted by the class they left"

    old_summary = await _summary(client, headers, test_class.id)
    new_summary = await _summary(client, headers, new_class.id)
    assert old_summary["total"] == 0
    assert new_summary["total"] == 1
    assert new_summary["present"] == 1


@pytest.mark.asyncio
async def test_remarking_in_the_same_class_still_updates_in_place(
    client: AsyncClient,
    admin_user: User,
    student_user: User,
    test_class: Class,
    db_session: AsyncSession,
    att_date: date,
) -> None:
    """Guard against over-correcting: the ordinary correction path must be unaffected."""
    token = await get_auth_token(client, "test_admin", "Admin@123")
    headers = auth_headers(token)
    student = await _student(db_session, student_user)

    for status in ("absent", "present"):
        resp = await client.post(
            "/api/v1/attendance/mark",
            json={
                "class_id": str(test_class.id),
                "date": MARK_DATE,
                "entries": [{"student_id": str(student.id), "status": status}],
            },
            headers=headers,
        )
        assert resp.status_code == 200

    result = await db_session.execute(
        select(Attendance).where(
            Attendance.student_id == student.id,
            Attendance.date == att_date,
        )
    )
    rows = list(result.scalars().all())
    assert len(rows) == 1, "correction must update one row, not create a duplicate"
    assert rows[0].class_id == test_class.id
    assert rows[0].status.value.lower() == "present"

"""Student search scope: incharges search every class they own; subject teachers do not."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.models.academic import AcademicYear, Class, Subject, TeacherSubjectMapping
from app.db.models.student import Student
from app.db.models.user import User, UserRole
from tests.conftest import auth_headers, get_auth_token


async def _student(db: AsyncSession, school_id, cls: Class, n: int, name: str) -> Student:
    user = User(
        school_id=school_id,
        username=f"search_stu_{n}",
        mobile=f"+9190000{n:05d}",
        full_name=name,
        role=UserRole.STUDENT,
        password_hash=hash_password("Student@123"),
        is_active=True,
    )
    db.add(user)
    await db.flush()
    student = Student(
        school_id=school_id,
        user_id=user.id,
        class_id=cls.id,
        admission_no=f"SRCH{n:03d}",
        roll_no=str(n),
    )
    db.add(student)
    await db.flush()
    return student


async def _classes(db: AsyncSession, school_id, ay: AcademicYear, count: int, incharge=None):
    out = []
    tag = "I" if incharge else "O"
    for i in range(count):
        cls = Class(
            school_id=school_id,
            grade=f"Grade {i + 2}",
            section=f"{tag}{i}",
            academic_year_id=ay.id,
            class_incharge_id=incharge.id if incharge else None,
        )
        db.add(cls)
        out.append(cls)
    await db.flush()
    return out


@pytest.mark.asyncio
async def test_incharge_search_covers_all_owned_classes_beyond_four(
    client: AsyncClient,
    teacher_user: User,
    test_school,
    academic_year: AcademicYear,
    db_session: AsyncSession,
):
    owned = await _classes(db_session, test_school.id, academic_year, 6, incharge=teacher_user)
    other = (await _classes(db_session, test_school.id, academic_year, 1))[0]
    for i, cls in enumerate(owned):
        await _student(db_session, test_school.id, cls, i, f"Ravi Owned {i}")
    await _student(db_session, test_school.id, other, 99, "Ravi Foreign")

    token = await get_auth_token(client, "test_teacher", "Teacher@123")
    resp = await client.get(
        "/api/v1/academic/students?search=Ravi&page_size=100", headers=auth_headers(token)
    )
    assert resp.status_code == 200
    body = resp.json()
    names = sorted(r["student_name"] for r in body["items"])
    assert names == [f"Ravi Owned {i}" for i in range(6)]
    assert body["total"] == 6


@pytest.mark.asyncio
async def test_incharge_search_paginates_server_side(
    client: AsyncClient,
    teacher_user: User,
    test_school,
    academic_year: AcademicYear,
    db_session: AsyncSession,
):
    owned = await _classes(db_session, test_school.id, academic_year, 5, incharge=teacher_user)
    for i, cls in enumerate(owned):
        await _student(db_session, test_school.id, cls, i, f"Asha {i}")
    other = (await _classes(db_session, test_school.id, academic_year, 1))[0]
    await _student(db_session, test_school.id, other, 50, "Asha Foreign")

    token = await get_auth_token(client, "test_teacher", "Teacher@123")
    page1 = (
        await client.get(
            "/api/v1/academic/students?search=Asha&page=1&page_size=2",
            headers=auth_headers(token),
        )
    ).json()
    page3 = (
        await client.get(
            "/api/v1/academic/students?search=Asha&page=3&page_size=2",
            headers=auth_headers(token),
        )
    ).json()
    assert page1["total"] == 5
    assert page1["total_pages"] == 3
    assert len(page1["items"]) == 2
    assert len(page3["items"]) == 1
    assert all(r["student_name"] != "Asha Foreign" for r in page1["items"] + page3["items"])


@pytest.mark.asyncio
async def test_subject_teacher_cannot_search_school_roster(
    client: AsyncClient,
    teacher_user: User,
    test_school,
    academic_year: AcademicYear,
    db_session: AsyncSession,
):
    cls = (await _classes(db_session, test_school.id, academic_year, 1))[0]
    subject = Subject(school_id=test_school.id, class_id=cls.id, name="Maths", code="MTH")
    db_session.add(subject)
    await db_session.flush()
    db_session.add(
        TeacherSubjectMapping(
            school_id=test_school.id,
            teacher_id=teacher_user.id,
            subject_id=subject.id,
            class_id=cls.id,
            is_primary=True,
        )
    )
    await _student(db_session, test_school.id, cls, 7, "Kiran Taught")
    await db_session.flush()

    token = await get_auth_token(client, "test_teacher", "Teacher@123")
    resp = await client.get(
        "/api/v1/academic/students?search=Kiran", headers=auth_headers(token)
    )
    assert resp.status_code == 403
    resp = await client.get(
        f"/api/v1/academic/students?class_id={cls.id}&search=Kiran",
        headers=auth_headers(token),
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_staff_search_stays_manager_only(
    client: AsyncClient,
    teacher_user: User,
    admin_user: User,
):
    token = await get_auth_token(client, "test_teacher", "Teacher@123")
    resp = await client.get("/api/v1/users?search=Test", headers=auth_headers(token))
    assert resp.status_code == 403
    admin = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.get("/api/v1/users?search=Test", headers=auth_headers(admin))
    assert resp.status_code == 200

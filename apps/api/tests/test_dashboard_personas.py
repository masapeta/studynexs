"""Stage 1 role homes: my_classes == teaching ∪ incharge; operations gets an ops summary."""
from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.models.academic import AcademicYear, Class, Subject, TeacherSubjectMapping
from app.db.models.school import School
from app.db.models.user import User, UserRole
from tests.conftest import access_token_for, auth_headers


async def _user(db, school, role, name, mobile) -> User:
    u = User(school_id=school.id, username=name, mobile=mobile, full_name=name, role=role,
             password_hash=hash_password("Pw@12345678"), is_active=True)
    db.add(u)
    await db.flush()
    return u


async def _summary(client: AsyncClient, user: User) -> dict:
    r = await client.get("/api/v1/dashboard/summary",
                         headers=auth_headers(access_token_for(user)))
    assert r.status_code == 200, r.text
    return r.json()["data"]


@pytest.mark.asyncio
async def test_my_classes_is_teaching_union_incharge(
    client: AsyncClient, db_session: AsyncSession, test_school: School,
    academic_year: AcademicYear,
):
    db = db_session
    c6, c7, c8 = (Class(school_id=test_school.id, grade=g, section="A",
                        academic_year_id=academic_year.id) for g in ("6", "7", "8"))
    db.add_all([c6, c7, c8])
    await db.flush()
    t = await _user(db, test_school, UserRole.TEACHER, "t_union", "+910000000601")
    c6.class_incharge_id = t.id  # TEACHER-role incharge (P-R9 case)
    sci = Subject(school_id=test_school.id, name="Science", class_id=c7.id)
    db.add(sci)
    await db.flush()
    db.add(TeacherSubjectMapping(school_id=test_school.id, teacher_id=t.id, class_id=c7.id,
                                 subject_id=sci.id))
    await db.flush()

    data = await _summary(client, t)
    assert data["persona"] == "class_incharge"
    got = {m["class_id"]: m for m in data["my_classes"]}
    assert set(got) == {str(c6.id), str(c7.id)}  # never c8
    assert got[str(c6.id)]["is_incharge"] is True
    assert got[str(c7.id)]["subjects"] == ["Science"]
    assert data["teacher_home"] is not None


@pytest.mark.asyncio
async def test_operations_gets_ops_summary_not_teacher_home(
    client: AsyncClient, db_session: AsyncSession, test_school: School
):
    ops = await _user(db_session, test_school, UserRole.OPERATIONS, "ops1", "+910000000602")
    data = await _summary(client, ops)
    assert data["persona"] == "operations"
    assert data["teacher_home"] is None
    assert data["admissions_pipeline"] == 0 and data["upcoming_events"] == 0
    assert data["my_classes"] == []
    # No school-wide academic/financial stats leak to operations.
    assert data["pending_fees"] is None and data["total_students"] is None


@pytest.mark.asyncio
async def test_admin_summary_unchanged_shape(
    client: AsyncClient, admin_user: User
):
    data = await _summary(client, admin_user)
    assert data["persona"] == "admin"
    assert data["my_classes"] == []

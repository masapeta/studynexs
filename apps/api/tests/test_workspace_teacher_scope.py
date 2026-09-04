from __future__ import annotations

import pytest

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.models.academic import Class
from app.db.models.student import Enrollment, Student
from app.db.models.user import User, UserRole
from tests.conftest import auth_headers, get_auth_token
from tests.test_workspace_tool_registry import _seed_grounded_flagging_report


@pytest.fixture(autouse=True)
def workspace_settings(monkeypatch):
    monkeypatch.setenv("WORKSPACE_ORCHESTRATION_ENABLED", "true")
    monkeypatch.setenv("WORKSPACE_MODEL_ROUTING_ENABLED", "false")
    monkeypatch.setenv("WORKSPACE_CLOUD_FALLBACK_ENABLED", "false")
    monkeypatch.setenv("WORKSPACE_ENABLED_SCHOOLS", "test")
    monkeypatch.setenv("WORKSPACE_ENABLED_ROLES", "teacher,class_incharge")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


async def _create_out_of_scope_student(db_session, test_school, academic_year) -> User:
    other_class = Class(
        school_id=test_school.id,
        grade="Grade 1",
        section="B",
        academic_year_id=academic_year.id,
    )
    db_session.add(other_class)
    await db_session.flush()

    user = User(
        school_id=test_school.id,
        username="outside_student",
        mobile="+919876543299",
        full_name="Outside Student",
        role=UserRole.STUDENT,
        password_hash=hash_password("Student@123"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    student = Student(
        school_id=test_school.id,
        user_id=user.id,
        class_id=other_class.id,
        admission_no="ADM999",
        roll_no="99",
    )
    db_session.add(student)
    await db_session.flush()

    db_session.add(
        Enrollment(
            school_id=test_school.id,
            student_id=student.id,
            class_id=other_class.id,
            academic_year_id=academic_year.id,
        )
    )
    await db_session.flush()
    return user


@pytest.mark.asyncio
async def test_workspace_turn_blocks_students_outside_teacher_scope(
    client,
    db_session,
    admin_user,
    teacher_user,
    student_user,
    test_school,
    test_class,
    academic_year,
):
    await _seed_grounded_flagging_report(
        client,
        db_session,
        admin_user=admin_user,
        teacher_user=teacher_user,
        student_user=student_user,
        test_school=test_school,
        test_class=test_class,
    )
    await _create_out_of_scope_student(db_session, test_school, academic_year)
    token = await get_auth_token(client, "test_teacher", "Teacher@123")

    response = await client.post(
        "/api/v1/workspace/turn",
        headers=auth_headers(token),
        json={"mode": "read", "text": "show Outside Student's learning report"},
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["message"]["tone"] == "blocked"
    assert data["telemetry"]["tool_calls"] == 1
    assert data["verification"]["status"] == "missing"
    assert data["errors"][0]["code"] == "student_out_of_scope"
    assert data["blocks"][0]["type"] == "error_state"

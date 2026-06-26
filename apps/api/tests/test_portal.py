"""Portal context API — parent and student home data."""
from __future__ import annotations

import pytest
from sqlalchemy import select

from app.db.models.student import Student
from tests.conftest import access_token_for, auth_headers


@pytest.mark.asyncio
async def test_portal_context_parent(client, parent_user, student_user, test_school, db_session):
    student = (
        await db_session.execute(select(Student).where(Student.user_id == student_user.id))
    ).scalar_one()
    token = access_token_for(parent_user)
    resp = await client.get(
        "/api/v1/portal/context",
        headers=auth_headers(token),
    )
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["portal"] == "parent"
    assert body["role"] == "parent"
    assert len(body["children"]) >= 1
    assert body["children"][0]["student_id"] == str(student.id)


@pytest.mark.asyncio
async def test_portal_context_student(client, student_user, test_school, db_session):
    student = (
        await db_session.execute(select(Student).where(Student.user_id == student_user.id))
    ).scalar_one()
    token = access_token_for(student_user)
    resp = await client.get(
        "/api/v1/portal/context",
        headers=auth_headers(token),
    )
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["portal"] == "student"
    assert body["role"] == "student"
    assert body["student_id"] == str(student.id)
    assert len(body["children"]) == 1


@pytest.mark.asyncio
async def test_portal_features(client, admin_user, test_school):
    token = access_token_for(admin_user)
    resp = await client.get(
        "/api/v1/portal/features",
        headers=auth_headers(token),
    )
    assert resp.status_code == 200
    features = resp.json()["data"]
    assert len(features) >= 5
    assert any(f["status"] == "live" for f in features)


@pytest.mark.asyncio
async def test_parent_permissions_hide_staff_dashboard(client, parent_user, student_user):
    token = access_token_for(parent_user)
    resp = await client.get("/api/v1/users/me/permissions", headers=auth_headers(token))
    assert resp.status_code == 200
    perms = resp.json()["data"]
    assert perms["role"] == "parent"
    assert perms["can_view_dashboard"] is False


@pytest.mark.asyncio
async def test_student_permissions_hide_staff_dashboard(client, student_user):
    token = access_token_for(student_user)
    resp = await client.get("/api/v1/users/me/permissions", headers=auth_headers(token))
    assert resp.status_code == 200
    perms = resp.json()["data"]
    assert perms["role"] == "student"
    assert perms["can_view_dashboard"] is False


@pytest.mark.asyncio
async def test_parent_fees_batch(client, parent_user, student_user, fee_setup, db_session):
    from datetime import date

    from sqlalchemy import select

    from app.db.models.fee import StudentFeeRecord
    from app.db.models.student import Student

    student = (
        await db_session.execute(select(Student).where(Student.user_id == student_user.id))
    ).scalar_one()
    db_session.add(
        StudentFeeRecord(
            school_id=student.school_id,
            student_id=student.id,
            fee_structure_id=fee_setup.id,
            amount=fee_setup.amount,
            due_date=date(2026, 8, 1),
        )
    )
    await db_session.flush()

    token = access_token_for(parent_user)
    resp = await client.get("/api/v1/portal/parent/fees", headers=auth_headers(token))
    assert resp.status_code == 200
    rows = resp.json()["data"]
    assert len(rows) >= 1
    child = next(r for r in rows if r["student_id"] == str(student.id))
    assert child["records"]


@pytest.mark.asyncio
async def test_parent_children_progress(client, parent_user, student_user, db_session):
    from sqlalchemy import select

    from app.db.models.student import Student

    student = (
        await db_session.execute(select(Student).where(Student.user_id == student_user.id))
    ).scalar_one()
    token = access_token_for(parent_user)

    list_resp = await client.get(
        "/api/v1/portal/parent/children-progress",
        headers=auth_headers(token),
    )
    assert list_resp.status_code == 200
    rows = list_resp.json()["data"]
    assert len(rows) >= 1
    child = next(r for r in rows if r["student_id"] == str(student.id))
    assert child["name"]
    assert "weak_topics" in child
    assert "feedbacks" in child

    detail_resp = await client.get(
        f"/api/v1/portal/child/{student.id}/progress",
        headers=auth_headers(token),
    )
    assert detail_resp.status_code == 200
    detail = detail_resp.json()["data"]
    assert detail["student_id"] == str(student.id)


@pytest.mark.asyncio
async def test_parent_children_progress_denied_for_student(client, student_user):
    token = access_token_for(student_user)
    resp = await client.get(
        "/api/v1/portal/parent/children-progress",
        headers=auth_headers(token),
    )
    assert resp.status_code == 403

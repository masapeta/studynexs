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

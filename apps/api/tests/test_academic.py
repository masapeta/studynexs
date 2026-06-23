"""Tests — Academic module."""

from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import AcademicYear, Class
from app.db.models.user import User
from tests.conftest import auth_headers, get_auth_token


@pytest.mark.asyncio
async def test_list_classes(client: AsyncClient, admin_user: User):
    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.get("/api/v1/academic/classes", headers=auth_headers(token))
    assert resp.status_code == 200
    assert "items" in resp.json()


@pytest.mark.asyncio
async def test_create_class(client: AsyncClient, admin_user: User, db_session: AsyncSession, test_school):
    # Need an academic year first
    ay = AcademicYear(
        school_id=test_school.id,
        year_label="2026-2028",
        start_date=date(2026, 4, 1),
        end_date=date(2028, 3, 31),
        is_active=True,
    )
    db_session.add(ay)
    await db_session.flush()

    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.post("/api/v1/academic/classes", headers=auth_headers(token), json={
        "grade": "Grade 1",
        "section": "A",
        "academic_year_id": str(ay.id),
    })
    assert resp.status_code == 201
    assert resp.json()["data"]["grade"] == "Grade 1"


@pytest.mark.asyncio
async def test_list_subjects(client: AsyncClient, admin_user: User):
    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.get("/api/v1/academic/subjects", headers=auth_headers(token))
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_list_students(client: AsyncClient, admin_user: User):
    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.get("/api/v1/academic/students", headers=auth_headers(token))
    assert resp.status_code == 200
    assert "items" in resp.json()


@pytest.mark.asyncio
async def test_class_roster(
    client: AsyncClient, admin_user: User, test_class: Class, student_user: User
):
    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.get(
        f"/api/v1/academic/classes/{test_class.id}/roster",
        headers=auth_headers(token),
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert isinstance(data, list)
    assert len(data) >= 1
    row = next(r for r in data if r["student_name"])
    assert "attendance_pct" in row
    assert row["admission_no"]

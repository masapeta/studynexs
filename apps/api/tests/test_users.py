"""Tests — Users module."""

import pytest
from httpx import AsyncClient

from app.db.models.user import User
from tests.conftest import auth_headers, get_auth_token


@pytest.mark.asyncio
async def test_get_my_profile(client: AsyncClient, admin_user: User):
    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.get("/api/v1/users/me", headers=auth_headers(token))
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["full_name"] == "Test Admin"
    assert data["role"] == "super_admin"


@pytest.mark.asyncio
async def test_list_users_requires_admin(client: AsyncClient, teacher_user: User):
    token = await get_auth_token(client, "test_teacher", "Teacher@123")
    resp = await client.get("/api/v1/users", headers=auth_headers(token))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_list_users_admin(client: AsyncClient, admin_user: User):
    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.get("/api/v1/users", headers=auth_headers(token))
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_create_user(client: AsyncClient, admin_user: User):
    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.post("/api/v1/users", headers=auth_headers(token), json={
        "mobile": "+919999888877",
        "full_name": "New User",
        "role": "parent",
    })
    assert resp.status_code == 201
    assert resp.json()["data"]["full_name"] == "New User"


@pytest.mark.asyncio
async def test_cannot_deactivate_self(client: AsyncClient, admin_user: User):
    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.delete(f"/api/v1/users/{admin_user.id}", headers=auth_headers(token))
    assert resp.status_code == 400

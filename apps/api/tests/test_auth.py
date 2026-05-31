"""Tests — Auth module."""

import pytest
from httpx import AsyncClient

from app.db.models.user import User


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, admin_user: User):
    resp = await client.post("/api/v1/auth/login", json={
        "username": "test_admin",
        "password": "Admin@123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, admin_user: User):
    resp = await client.post("/api/v1/auth/login", json={
        "username": "test_admin",
        "password": "wrong_password",
    })
    assert resp.status_code in (401, 400)


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient, test_school):
    resp = await client.post("/api/v1/auth/login", json={
        "username": "nobody",
        "password": "anything",
    })
    assert resp.status_code in (401, 400)

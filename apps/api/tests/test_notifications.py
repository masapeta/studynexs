"""Tests — Notifications module."""

import pytest
from httpx import AsyncClient

from app.db.models.user import User
from tests.conftest import auth_headers, get_auth_token


@pytest.mark.asyncio
async def test_list_notifications_empty(client: AsyncClient, admin_user: User):
    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.get("/api/v1/notifications", headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.json()["data"] == []


@pytest.mark.asyncio
async def test_unread_count(client: AsyncClient, admin_user: User):
    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.get("/api/v1/notifications/count", headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.json()["data"]["unread_count"] == 0


@pytest.mark.asyncio
async def test_mark_all_read(client: AsyncClient, admin_user: User):
    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.post("/api/v1/notifications/read-all", headers=auth_headers(token))
    assert resp.status_code == 200

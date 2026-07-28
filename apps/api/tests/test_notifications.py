"""Tests — Notifications module."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.notification import Notification
from app.db.models.school import School
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


@pytest.mark.asyncio
async def test_notification_reads_and_mutations_are_tenant_scoped(
    client: AsyncClient,
    admin_user: User,
    test_school: School,
    db_session: AsyncSession,
):
    """A matching user UUID must never bypass the mandatory school predicate."""
    other_school = School(
        name="Other School",
        code="OTH",
        tenant_slug="other-notification-tenant",
        board="CBSE",
        contact_email="admin@other.example",
        contact_phone="+919000000001",
        is_active=True,
    )
    db_session.add(other_school)
    await db_session.flush()

    own_notification = Notification(
        school_id=test_school.id,
        user_id=admin_user.id,
        title="Own notification",
        body="Visible only inside the authenticated school.",
        is_read=False,
    )
    other_tenant_notification = Notification(
        school_id=other_school.id,
        user_id=admin_user.id,
        title="Other tenant notification",
        body="Must remain invisible and immutable from the authenticated school.",
        is_read=False,
    )
    db_session.add_all([own_notification, other_tenant_notification])
    await db_session.flush()

    token = await get_auth_token(client, "test_admin", "Admin@123")
    headers = auth_headers(token)

    listed = await client.get("/api/v1/notifications", headers=headers)
    assert listed.status_code == 200
    assert [row["id"] for row in listed.json()["data"]] == [str(own_notification.id)]

    count = await client.get("/api/v1/notifications/count", headers=headers)
    assert count.status_code == 200
    assert count.json()["data"]["unread_count"] == 1

    cross_tenant_mark = await client.post(
        f"/api/v1/notifications/{other_tenant_notification.id}/read",
        headers=headers,
    )
    assert cross_tenant_mark.status_code == 200
    await db_session.refresh(other_tenant_notification)
    assert other_tenant_notification.is_read is False

    mark_all = await client.post("/api/v1/notifications/read-all", headers=headers)
    assert mark_all.status_code == 200
    await db_session.refresh(own_notification)
    await db_session.refresh(other_tenant_notification)
    assert own_notification.is_read is True
    assert other_tenant_notification.is_read is False

"""Notice visibility — role escalation and expiry."""

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.communication import Notice, NoticePriority
from app.db.models.user import User, UserRole
from tests.conftest import auth_headers, get_auth_token


@pytest.mark.asyncio
async def test_student_cannot_see_admin_notices_via_query_param(
    client: AsyncClient,
    student_user: User,
    db_session: AsyncSession,
):
    notice = Notice(
        school_id=student_user.school_id,
        title="Admin only",
        content="Secret",
        target_roles=["admin"],
        priority=NoticePriority.HIGH,
        created_by=student_user.id,
    )
    db_session.add(notice)
    await db_session.flush()

    token = await get_auth_token(client, "test_student", "Student@123")
    resp = await client.get(
        "/api/v1/notices?role=admin",
        headers=auth_headers(token),
    )
    assert resp.status_code == 200
    titles = [n["title"] for n in resp.json()["data"]]
    assert "Admin only" not in titles


@pytest.mark.asyncio
async def test_expired_notice_hidden(
    client: AsyncClient,
    student_user: User,
    db_session: AsyncSession,
):
    notice = Notice(
        school_id=student_user.school_id,
        title="Expired",
        content="Old",
        target_roles=["student"],
        priority=NoticePriority.LOW,
        created_by=student_user.id,
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    db_session.add(notice)
    await db_session.flush()

    token = await get_auth_token(client, "test_student", "Student@123")
    resp = await client.get("/api/v1/notices", headers=auth_headers(token))
    assert resp.status_code == 200
    titles = [n["title"] for n in resp.json()["data"]]
    assert "Expired" not in titles

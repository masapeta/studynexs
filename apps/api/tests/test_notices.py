"""Notice visibility — role escalation, expiry, and class scoping."""

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import Class
from app.db.models.communication import Notice, NoticeAudience, NoticePriority
from app.db.models.user import User
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


@pytest.mark.asyncio
async def test_parent_cannot_see_other_class_external_notice(
    client: AsyncClient,
    parent_user: User,
    student_user: User,
    test_school,
    test_class: Class,
    academic_year,
    db_session: AsyncSession,
):
    """Regression: class-scoped external notices must not leak school-wide to all parents."""
    other_class = Class(
        school_id=test_school.id,
        grade="Grade 2",
        section="B",
        academic_year_id=academic_year.id,
    )
    db_session.add(other_class)
    await db_session.flush()

    visible = Notice(
        school_id=test_school.id,
        title="Class A picnic",
        content="Bring lunch",
        audience=NoticeAudience.EXTERNAL,
        target_roles=["parent"],
        priority=NoticePriority.MEDIUM,
        created_by=parent_user.id,
        class_id=test_class.id,
    )
    hidden = Notice(
        school_id=test_school.id,
        title="Class B only",
        content="Secret for other section",
        audience=NoticeAudience.EXTERNAL,
        target_roles=["parent"],
        priority=NoticePriority.MEDIUM,
        created_by=parent_user.id,
        class_id=other_class.id,
    )
    db_session.add_all([visible, hidden])
    await db_session.flush()

    token = await get_auth_token(client, "test_parent", "Parent@123")
    resp = await client.get("/api/v1/notices", headers=auth_headers(token))
    assert resp.status_code == 200
    titles = [n["title"] for n in resp.json()["data"]]
    assert "Class A picnic" in titles
    assert "Class B only" not in titles


@pytest.mark.asyncio
async def test_student_cannot_see_other_class_external_notice(
    client: AsyncClient,
    student_user: User,
    test_school,
    test_class: Class,
    academic_year,
    db_session: AsyncSession,
):
    other_class = Class(
        school_id=test_school.id,
        grade="Grade 2",
        section="B",
        academic_year_id=academic_year.id,
    )
    db_session.add(other_class)
    await db_session.flush()

    db_session.add(
        Notice(
            school_id=test_school.id,
            title="Other class exam",
            content="Not for you",
            audience=NoticeAudience.EXTERNAL,
            target_roles=["student"],
            priority=NoticePriority.MEDIUM,
            created_by=student_user.id,
            class_id=other_class.id,
        )
    )
    await db_session.flush()

    token = await get_auth_token(client, "test_student", "Student@123")
    resp = await client.get("/api/v1/notices", headers=auth_headers(token))
    assert resp.status_code == 200
    titles = [n["title"] for n in resp.json()["data"]]
    assert "Other class exam" not in titles

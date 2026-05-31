"""School-scoped login — same username/mobile allowed per school, tenant resolves identity."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.models.school import School
from app.db.models.user import User, UserRole
from tests.conftest import auth_headers, get_auth_token


@pytest.mark.asyncio
async def test_login_wrong_tenant_returns_401(
    client: AsyncClient,
    admin_user: User,
    db_session: AsyncSession,
):
    """Credentials valid at home school must not log in under another tenant slug."""
    other = School(
        name="Other Tenant",
        code="OTH3",
        tenant_slug="other-tenant",
        board="CBSE",
        contact_email="x@test.com",
        contact_phone="+917777777777",
        is_active=True,
    )
    db_session.add(other)
    await db_session.flush()

    resp = await client.post(
        "/api/v1/auth/login",
        headers={"X-Tenant-Slug": "other-tenant"},
        json={"username": "test_admin", "password": "Admin@123"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_same_username_different_schools_both_login(
    client: AsyncClient,
    admin_user: User,
    db_session: AsyncSession,
):
    other = School(
        name="Sibling School",
        code="SIB",
        tenant_slug="sibling",
        board="CBSE",
        contact_email="s@test.com",
        contact_phone="+916666666666",
        is_active=True,
    )
    db_session.add(other)
    await db_session.flush()

    other_admin = User(
        school_id=other.id,
        username="test_admin",
        mobile="+916666666665",
        full_name="Sibling Admin",
        role=UserRole.ADMIN,
        password_hash=hash_password("Admin@123"),
        is_active=True,
    )
    db_session.add(other_admin)
    await db_session.flush()

    token_test = await get_auth_token(client, "test_admin", "Admin@123")
    assert token_test

    resp = await client.post(
        "/api/v1/auth/login",
        headers={"X-Tenant-Slug": "sibling"},
        json={"username": "test_admin", "password": "Admin@123"},
    )
    assert resp.status_code == 200
    assert resp.json()["school_id"] == str(other.id)

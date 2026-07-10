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
    resp = await client.post(
        "/api/v1/users",
        headers=auth_headers(token),
        json={
            "mobile": "+919999888877",
            "full_name": "New User",
            "role": "parent",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["data"]["full_name"] == "New User"


@pytest.mark.asyncio
async def test_cannot_deactivate_self(client: AsyncClient, admin_user: User):
    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.delete(f"/api/v1/users/{admin_user.id}", headers=auth_headers(token))
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_patch_user_cannot_escalate_role(
    client: AsyncClient,
    admin_user: User,
    teacher_user: User,
    db_session,
):
    from app.core.security import hash_password
    from app.db.models.user import User, UserRole

    limited = User(
        school_id=admin_user.school_id,
        username="limited_admin",
        mobile="+919876543299",
        full_name="Limited Admin",
        role=UserRole.ADMIN,
        password_hash=hash_password("Admin@123"),
        is_active=True,
    )
    db_session.add(limited)
    await db_session.flush()

    token = await get_auth_token(client, "limited_admin", "Admin@123")
    resp = await client.patch(
        f"/api/v1/users/{teacher_user.id}",
        headers=auth_headers(token),
        json={"role": "super_admin"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_dashboard_summary_requires_staff(client: AsyncClient, student_user: User):
    token = await get_auth_token(client, "test_student", "Student@123")
    resp = await client.get("/api/v1/dashboard/summary", headers=auth_headers(token))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_cannot_edit_or_deactivate_super_admin(
    client: AsyncClient,
    admin_user: User,
    db_session,
):
    """Regression: the role ceiling must apply to the target's CURRENT role, not just a new
    role. An admin must not be able to edit or deactivate a principal (super_admin)."""
    from app.core.security import hash_password
    from app.db.models.user import UserRole

    limited = User(
        school_id=admin_user.school_id,
        username="limited_admin2",
        mobile="+919876543298",
        full_name="Limited Admin 2",
        role=UserRole.ADMIN,
        password_hash=hash_password("Admin@123"),
        is_active=True,
    )
    db_session.add(limited)
    await db_session.flush()
    token = await get_auth_token(client, "limited_admin2", "Admin@123")

    # admin_user is a super_admin (the Principal).
    edit = await client.patch(
        f"/api/v1/users/{admin_user.id}",
        headers=auth_headers(token),
        json={"full_name": "Hacked Principal"},
    )
    assert edit.status_code == 403

    deactivate = await client.delete(f"/api/v1/users/{admin_user.id}", headers=auth_headers(token))
    assert deactivate.status_code == 403


@pytest.mark.asyncio
async def test_class_incharge_user_list_masks_contact_pii(
    client: AsyncClient,
    admin_user: User,
    teacher_user: User,
    db_session,
):
    """Regression: a class incharge gets the staff-picker list without harvesting full PII."""
    from app.core.security import hash_password
    from app.db.models.user import UserRole

    incharge = User(
        school_id=admin_user.school_id,
        username="incharge1",
        mobile="+919876543297",
        full_name="Incharge One",
        role=UserRole.CLASS_INCHARGE,
        password_hash=hash_password("Incharge@123"),
        is_active=True,
    )
    db_session.add(incharge)
    await db_session.flush()

    token = await get_auth_token(client, "incharge1", "Incharge@123")
    resp = await client.get("/api/v1/users", headers=auth_headers(token))
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert items
    for it in items:
        assert it["email"] is None
        assert "*" in it["mobile"]  # masked, never the full number

    # Admins still see full contact details.
    admin_token = await get_auth_token(client, "test_admin", "Admin@123")
    admin_resp = await client.get("/api/v1/users", headers=auth_headers(admin_token))
    admin_items = admin_resp.json()["items"]
    assert any("*" not in it["mobile"] for it in admin_items)

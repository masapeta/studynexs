"""H4 — role ceiling. An admin must not be able to mint a super_admin (privilege
escalation); a super_admin can, and an admin can still create lower roles.
"""
import os

import pytest


async def _login(client, username, password, slug="a"):
    r = await client.post(
        "/api/v1/auth/login",
        headers={"X-Tenant-Slug": slug},
        json={"username": username, "password": password},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    return body.get("access_token") or body.get("data", {}).get("access_token")


def _new_user(role):
    suffix = os.urandom(4).hex()[:6]
    return {
        "mobile": f"+9190{suffix}00",
        "full_name": "New User",
        "role": role,
        "username": f"u{suffix}",
        "password": "Pw@12345",
    }


async def _create(client, token, payload):
    return await client.post(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {token}", "X-Tenant-Slug": "a"},
        json=payload,
    )


@pytest.mark.asyncio
async def test_admin_cannot_mint_super_admin(make_client):
    factory, info = make_client
    client = factory()
    token = await _login(client, info["admin_username"], info["admin_password"])
    r = await _create(client, token, _new_user("super_admin"))
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_mint_teacher(make_client):
    factory, info = make_client
    client = factory()
    token = await _login(client, info["admin_username"], info["admin_password"])
    r = await _create(client, token, _new_user("teacher"))
    assert r.status_code == 201, r.text


@pytest.mark.asyncio
async def test_super_admin_can_mint_super_admin(make_client):
    factory, info = make_client
    client = factory()
    token = await _login(client, info["username"], info["password"])
    r = await _create(client, token, _new_user("super_admin"))
    assert r.status_code == 201, r.text

"""M8 — session-keyed refresh rotation.

Two independent devices (separate cookie jars) each get their own rotation chain, and
replaying a stale token revokes only that one session — the other keeps working. The
pre-M8 single per-user slot would have let the second login clobber the first.
"""
import pytest

from app.core.config import get_settings
from tests_security.conftest import ALLOWED_ORIGIN

COOKIE = get_settings().REFRESH_COOKIE_NAME


async def _login(client, info):
    r = await client.post(
        "/api/v1/auth/login",
        headers={"X-Tenant-Slug": info["slug"]},
        json={"username": info["username"], "password": info["password"]},
    )
    assert r.status_code == 200, r.text
    return r


async def _refresh(client, token=None):
    headers = {"X-Tenant-Slug": "a", "Origin": ALLOWED_ORIGIN}
    if token is not None:
        # Explicit Cookie header (probe client has an empty jar) — unambiguous and avoids
        # httpx's deprecated per-request cookies= path.
        headers["Cookie"] = f"{COOKIE}={token}"
    return await client.post("/api/v1/auth/refresh", headers=headers)


@pytest.mark.asyncio
async def test_two_devices_refresh_independently(make_client):
    factory, info = make_client
    a, b = factory(), factory()
    await _login(a, info)          # device A session
    await _login(b, info)          # device B session (pre-M8 this clobbered A's slot)

    ra = await _refresh(a)
    rb = await _refresh(b)
    assert ra.status_code == 200, ra.text   # pre-M8: A would be 401 "reuse detected"
    assert rb.status_code == 200, rb.text


@pytest.mark.asyncio
async def test_reuse_revokes_only_that_session(make_client):
    factory, info = make_client
    a, b = factory(), factory()
    await _login(a, info)
    await _login(b, info)

    stale_a = a.cookies.get(COOKIE)          # A's first refresh token
    r1 = await _refresh(a)
    assert r1.status_code == 200, r1.text
    current_a = a.cookies.get(COOKIE)        # A's rotated (currently-valid) token

    probe = factory()
    replay = await _refresh(probe, token=stale_a)
    assert replay.status_code == 401         # stale jti != stored → reuse detected

    dead = await _refresh(probe, token=current_a)
    assert dead.status_code == 401           # A's whole session was revoked by the reuse

    rb = await _refresh(b)
    assert rb.status_code == 200, rb.text    # B is a different sid → untouched

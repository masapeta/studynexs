"""M8 — session-keyed refresh rotation.

Two independent devices (separate cookie jars) each get their own rotation chain, and
replaying a stale token revokes only that one session — the other keeps working. The
pre-M8 single per-user slot would have let the second login clobber the first.
"""

import asyncio

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
    await _login(a, info)  # device A session
    await _login(b, info)  # device B session (pre-M8 this clobbered A's slot)

    ra = await _refresh(a)
    rb = await _refresh(b)
    assert ra.status_code == 200, ra.text  # pre-M8: A would be 401 "reuse detected"
    assert rb.status_code == 200, rb.text


@pytest.mark.asyncio
async def test_reuse_revokes_only_that_session(make_client):
    factory, info = make_client
    a, b = factory(), factory()
    await _login(a, info)
    await _login(b, info)

    old_a = a.cookies.get(COOKIE)  # token gen 0
    assert (await _refresh(a)).status_code == 200  # gen 0 -> gen 1
    assert (await _refresh(a)).status_code == 200  # gen 1 -> gen 2; gen 0 now beyond grace
    current_a = a.cookies.get(COOKIE)  # gen 2 (currently valid)

    probe = factory()
    replay = await _refresh(probe, token=old_a)
    assert replay.status_code == 401  # 2 generations old → reuse, not the grace window

    dead = await _refresh(probe, token=current_a)
    assert dead.status_code == 401  # A's whole session was revoked by the reuse

    rb = await _refresh(b)
    assert rb.status_code == 200, rb.text  # B is a different sid → untouched


@pytest.mark.asyncio
async def test_predecessor_within_grace_is_not_reuse(make_client):
    """The immediate predecessor (one rotation back) is the benign multi-tab case: it must
    still rotate, not revoke."""
    factory, info = make_client
    a = factory()
    await _login(a, info)

    gen0 = a.cookies.get(COOKIE)
    assert (await _refresh(a)).status_code == 200  # gen0 -> gen1
    probe = factory()
    again = await _refresh(probe, token=gen0)  # replay the immediate predecessor
    assert again.status_code == 200  # accepted within the one-rotation grace
    # session is alive: the current token still refreshes
    assert (await _refresh(a)).status_code == 200


@pytest.mark.asyncio
async def test_logout_revokes_refresh_session_via_access_token(make_client):
    """Regression: logout must kill the server-side refresh session for browser clients.

    The refresh cookie is path-scoped to /auth/refresh, so the browser never sends it to
    /auth/logout — pre-fix the revocation branch was dead code and the session stayed valid
    for up to 30 days. Now the access token carries the sid, so logout revokes the exact
    session; a subsequent refresh with the (still-jarred) cookie must fail.
    """
    factory, info = make_client
    a = factory()
    login = await _login(a, info)
    access = login.json()["access_token"]
    assert (await _refresh(a)).status_code == 200  # session alive before logout

    out = await a.post(
        "/api/v1/auth/logout",
        headers={"X-Tenant-Slug": info["slug"], "Authorization": f"Bearer {access}"},
    )
    assert out.status_code == 200, out.text

    # Session is gone — the cookie in the jar can no longer be exchanged for a new token.
    assert (await _refresh(a)).status_code == 401


@pytest.mark.asyncio
async def test_concurrent_same_session_refresh_does_not_self_revoke(make_client):
    """Two tabs share the cookie and fire a refresh with the SAME token at once. Both must
    succeed (grace) and the session must stay alive — the bug was the loser deleting the
    winner's freshly-minted key and logging the session out."""
    factory, info = make_client
    a = factory()
    await _login(a, info)
    token = a.cookies.get(COOKIE)

    p1, p2 = factory(), factory()
    r1, r2 = await asyncio.gather(_refresh(p1, token=token), _refresh(p2, token=token))
    assert {r1.status_code, r2.status_code} == {200}, (r1.status_code, r2.status_code)
    # The session survived: a token issued by the race (now current/predecessor) still works.
    # p1's jar holds the token from its successful refresh.
    assert (await _refresh(p1)).status_code == 200

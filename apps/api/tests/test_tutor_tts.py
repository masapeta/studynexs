"""Tutor TTS endpoints — graceful fallback when Azure Speech isn't configured."""

import pytest
from httpx import AsyncClient

from app.db.models.user import User
from tests.conftest import auth_headers, get_auth_token


@pytest.mark.asyncio
async def test_tts_status_reports_disabled_without_key(client: AsyncClient, admin_user: User):
    """No AZURE_SPEECH_KEY in the test env → status says disabled (client uses Web Speech)."""
    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.get("/api/v1/tutor/tts/status", headers=auth_headers(token))
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["enabled"] is False
    assert data["voice"]  # the configured default voice name is still surfaced


@pytest.mark.asyncio
async def test_tts_synth_returns_503_when_unconfigured(client: AsyncClient, admin_user: User):
    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.post(
        "/api/v1/tutor/tts", headers=auth_headers(token), json={"text": "Hello class."}
    )
    assert resp.status_code == 503


@pytest.mark.asyncio
async def test_tts_requires_auth(client: AsyncClient):
    resp = await client.post("/api/v1/tutor/tts", json={"text": "Hello"})
    assert resp.status_code in (401, 403)

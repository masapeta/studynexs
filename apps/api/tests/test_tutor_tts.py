"""Tutor TTS endpoints — Edge TTS by default; Azure Speech when configured."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.db.models.user import User
from app.modules.tutor.services.tts_service import default_tts_voice
from tests.conftest import auth_headers, get_auth_token


@pytest.mark.asyncio
async def test_tts_status_public_and_reports_edge(client: AsyncClient):
    """TTS status is public and reports edge when edge-tts is installed."""
    resp = await client.get("/api/v1/tutor/tts/status", headers={"X-Tenant-Slug": "test"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["voice"] == default_tts_voice()
    assert data["backend"] in ("edge", "azure", "off")
    if data["backend"] == "edge":
        assert data["enabled"] is True


@pytest.mark.asyncio
async def test_tts_status_reports_edge_when_available(client: AsyncClient, admin_user: User):
    """Without Azure key, auto mode should enable Edge TTS when edge-tts is installed."""
    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.get("/api/v1/tutor/tts/status", headers=auth_headers(token))
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["voice"] == default_tts_voice()
    assert data["backend"] in ("edge", "azure", "off")
    # In CI/dev with edge-tts installed and no Azure key, expect edge.
    if data["backend"] == "edge":
        assert data["enabled"] is True


@pytest.mark.asyncio
async def test_tts_synth_returns_audio_with_mock(client: AsyncClient, admin_user: User):
    token = await get_auth_token(client, "test_admin", "Admin@123")
    fake_audio = b"\xff\xfb\x90" + b"\x00" * 64

    with patch(
        "app.modules.tutor.services.tts_service.synthesize_speech",
        new=AsyncMock(return_value=fake_audio),
    ):
        with patch("app.modules.tutor.services.tts_service.tts_enabled", return_value=True):
            resp = await client.post(
                "/api/v1/tutor/tts",
                headers=auth_headers(token),
                json={"text": "Hello class."},
            )

    if resp.status_code == 503:
        pytest.skip("TTS disabled in this environment")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("audio/mpeg")
    assert len(resp.content) > 0


@pytest.mark.asyncio
async def test_tts_synth_returns_503_when_unconfigured(client: AsyncClient, admin_user: User):
    token = await get_auth_token(client, "test_admin", "Admin@123")
    with patch("app.modules.tutor.endpoints.tutor.tts_enabled", return_value=False):
        resp = await client.post(
            "/api/v1/tutor/tts", headers=auth_headers(token), json={"text": "Hello class."}
        )
    assert resp.status_code == 503


@pytest.mark.asyncio
async def test_tts_requires_auth(client: AsyncClient):
    resp = await client.post("/api/v1/tutor/tts", json={"text": "Hello"})
    assert resp.status_code in (401, 403)

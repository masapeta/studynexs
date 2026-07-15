"""Tests for platform engineering visibility."""

import pytest

from tests.conftest import access_token_for, auth_headers


@pytest.mark.asyncio
async def test_engineering_status_requires_admin(client, teacher_user):
    res = await client.get("/api/v1/platform/engineering-status")
    assert res.status_code == 401

    teacher_token = access_token_for(teacher_user)
    res = await client.get(
        "/api/v1/platform/engineering-status",
        headers=auth_headers(teacher_token),
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_engineering_status_admin_ok(client, admin_user):
    admin_token = access_token_for(admin_user)
    res = await client.get(
        "/api/v1/platform/engineering-status",
        headers=auth_headers(admin_token),
    )
    assert res.status_code == 200
    body = res.json()["data"]
    assert body["schema_version"] == 2
    assert body["architecture_version"]
    assert "capability_matrix" in body
    assert body["capability_matrix"][0].get("verified")
    assert len(body["capability_matrix"]) >= 10
    assert body["modules"][0].get("depends_on") is not None
    assert body["next_milestone"]["batch"] == 23
    assert body["runtime"]["git_commit"]

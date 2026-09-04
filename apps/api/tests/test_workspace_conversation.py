from __future__ import annotations

import pytest

from app.core.config import get_settings
from tests.conftest import auth_headers, get_auth_token
from tests.test_workspace_tool_registry import _seed_grounded_flagging_report


@pytest.fixture(autouse=True)
def workspace_settings(monkeypatch):
    monkeypatch.setenv("WORKSPACE_ORCHESTRATION_ENABLED", "true")
    monkeypatch.setenv("WORKSPACE_MODEL_ROUTING_ENABLED", "false")
    monkeypatch.setenv("WORKSPACE_CLOUD_FALLBACK_ENABLED", "false")
    monkeypatch.setenv("WORKSPACE_ENABLED_SCHOOLS", "test")
    monkeypatch.setenv("WORKSPACE_ENABLED_ROLES", "teacher,class_incharge")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_workspace_turn_returns_grounded_deterministic_response(
    client,
    db_session,
    admin_user,
    teacher_user,
    student_user,
    test_school,
    test_class,
):
    await _seed_grounded_flagging_report(
        client,
        db_session,
        admin_user=admin_user,
        teacher_user=teacher_user,
        student_user=student_user,
        test_school=test_school,
        test_class=test_class,
    )
    token = await get_auth_token(client, "test_teacher", "Teacher@123")

    response = await client.post(
        "/api/v1/workspace/turn",
        headers=auth_headers(token),
        json={"mode": "read", "text": "show Test Student's learning report"},
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["schema_version"] == "workspace.response.v1"
    assert data["mode"] == "read"
    assert data["message"]["title"] == "Student learning evidence report"
    assert data["verification"]["status"] == "verified"
    assert data["telemetry"]["used_model"] is None
    assert data["telemetry"]["used_fallback"] is False
    assert data["telemetry"]["tool_calls"] == 3
    assert data["telemetry"]["tool_failures"] == 0
    assert {block["type"] for block in data["blocks"]} >= {
        "student_card",
        "metric_row",
        "table",
        "citation_list",
        "action_list",
    }
    assert data["citations"]
    assert all(action["action_type"] == "navigate" for action in data["actions"])


@pytest.mark.asyncio
async def test_workspace_turn_accepts_phase0_starter_prompt_shape(
    client,
    db_session,
    admin_user,
    teacher_user,
    student_user,
    test_school,
    test_class,
):
    await _seed_grounded_flagging_report(
        client,
        db_session,
        admin_user=admin_user,
        teacher_user=teacher_user,
        student_user=student_user,
        test_school=test_school,
        test_class=test_class,
    )
    token = await get_auth_token(client, "test_teacher", "Teacher@123")

    response = await client.post(
        "/api/v1/workspace/turn",
        headers=auth_headers(token),
        json={"mode": "read", "text": "Show learning evidence for Test Student in class 7A."},
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["message"]["title"] == "Student learning evidence report"
    assert data["verification"]["status"] == "verified"
    assert data["telemetry"]["tool_calls"] == 3
    assert data["errors"] == []


@pytest.mark.asyncio
async def test_workspace_turn_returns_bounded_response_for_unsupported_request(
    client,
    teacher_user,
):
    token = await get_auth_token(client, "test_teacher", "Teacher@123")

    response = await client.post(
        "/api/v1/workspace/turn",
        headers=auth_headers(token),
        json={"mode": "read", "text": "summarize my class performance"},
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["message"]["title"] == "Request not supported yet"
    assert data["message"]["tone"] == "blocked"
    assert data["telemetry"]["tool_calls"] == 0
    assert data["errors"][0]["code"] == "unsupported_request"
    assert data["blocks"][0]["type"] == "error_state"

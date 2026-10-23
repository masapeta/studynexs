"""Phase 11: the bounded MCP Apps adapter.

These tests prove the adapter is a thin, SECURE shim over existing capabilities — not a new
runtime. They assert, at the HTTP/JSON-RPC boundary: tool discovery + input validation, the
structured+text dual output, UI-resource registration/retrieval, server-side identity
enforcement, tenant isolation, that a spoofed identity in the JSON-RPC body is ignored, that only
the allowlisted read-only tool is reachable (no mutation surface), and that a host without MCP
Apps still gets a usable text result.

Identity is always the authenticated bearer user; nothing in the JSON-RPC body can change it.
"""

from __future__ import annotations

from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import AcademicYear, Class
from app.db.models.attendance import Attendance, AttendanceStatus
from app.db.models.school import School
from app.db.models.student import Student
from app.db.models.user import User, UserRole
from tests.conftest import access_token_for, auth_headers

_UI_URI = "ui://studynexs/class-attendance.html"


async def _seed_school(db: AsyncSession, *, slug: str, code: str) -> School:
    school = School(
        name=f"School {code}", code=code, tenant_slug=slug, board="SSC",
        contact_email=f"{code}@t.com", contact_phone="+910000000000", is_active=True,
    )
    db.add(school)
    await db.flush()
    return school


async def _seed_class_with_attendance(
    db: AsyncSession, school: School, marker_id
) -> Class:
    ay = AcademicYear(
        school_id=school.id, year_label="2026-2027",
        start_date=date(2026, 6, 1), end_date=date(2027, 5, 31), is_active=True,
    )
    db.add(ay)
    await db.flush()
    cls = Class(school_id=school.id, grade="5", section="A", academic_year_id=ay.id)
    db.add(cls)
    await db.flush()
    # Two present, one absent today.
    for i, status in enumerate(
        [AttendanceStatus.PRESENT, AttendanceStatus.PRESENT, AttendanceStatus.ABSENT]
    ):
        u = User(
            school_id=school.id, mobile=f"+91900000{i:04d}", full_name=f"S{i}",
            role=UserRole.STUDENT, is_active=True,
        )
        db.add(u)
        await db.flush()
        s = Student(
            school_id=school.id, user_id=u.id, class_id=cls.id,
            admission_no=f"ADM{i}", roll_no=str(i),
        )
        db.add(s)
        await db.flush()
        db.add(Attendance(
            school_id=school.id, student_id=s.id, class_id=cls.id,
            date=date.today(), status=status, marked_by=marker_id,
        ))
    await db.flush()
    return cls


async def _admin(db: AsyncSession, school: School) -> User:
    u = User(
        school_id=school.id, username=f"admin_{school.code}", mobile=f"+9199{school.code}0001",
        full_name="Principal", role=UserRole.SUPER_ADMIN, is_active=True,
    )
    db.add(u)
    await db.flush()
    return u


def _rpc(method: str, params: dict | None = None, rpc_id: int = 1) -> dict:
    body: dict = {"jsonrpc": "2.0", "id": rpc_id, "method": method}
    if params is not None:
        body["params"] = params
    return body


# ── Transport + identity ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_unauthenticated_request_is_rejected(client: AsyncClient):
    resp = await client.post("/api/v1/mcp", json=_rpc("tools/list"))
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_initialize_advertises_mcp_apps_extension(client: AsyncClient, db_session):
    school = await _seed_school(db_session, slug="test", code="T1")
    admin = await _admin(db_session, school)
    resp = await client.post(
        "/api/v1/mcp",
        json=_rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {}}),
        headers=auth_headers(access_token_for(admin)),
    )
    assert resp.status_code == 200
    result = resp.json()["result"]
    assert "io.modelcontextprotocol/ui" in result["capabilities"]["extensions"]
    assert result["capabilities"]["extensions"]["io.modelcontextprotocol/ui"]["mimeTypes"] == [
        "text/html;profile=mcp-app"
    ]


# ── Discovery ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_tools_list_exposes_only_the_allowlisted_readonly_tool(client: AsyncClient, db_session):
    school = await _seed_school(db_session, slug="test", code="T1")
    admin = await _admin(db_session, school)
    resp = await client.post(
        "/api/v1/mcp", json=_rpc("tools/list"), headers=auth_headers(access_token_for(admin))
    )
    tools = resp.json()["result"]["tools"]
    assert len(tools) == 1
    tool = tools[0]
    assert tool["name"] == "school_class_attendance_today"
    assert tool["annotations"]["readOnlyHint"] is True
    assert tool["_meta"]["ui"]["resourceUri"] == _UI_URI
    assert tool["inputSchema"]["required"] == ["class_label"]


@pytest.mark.asyncio
async def test_resources_list_and_read_serve_the_ui_app(client: AsyncClient, db_session):
    school = await _seed_school(db_session, slug="test", code="T1")
    admin = await _admin(db_session, school)
    listed = await client.post(
        "/api/v1/mcp", json=_rpc("resources/list"), headers=auth_headers(access_token_for(admin))
    )
    uris = [r["uri"] for r in listed.json()["result"]["resources"]]
    assert uris == [_UI_URI]

    read = await client.post(
        "/api/v1/mcp",
        json=_rpc("resources/read", {"uri": _UI_URI}),
        headers=auth_headers(access_token_for(admin)),
    )
    content = read.json()["result"]["contents"][0]
    assert content["mimeType"] == "text/html;profile=mcp-app"
    assert "<!DOCTYPE html>" in content["text"]
    assert content["_meta"]["ui"]["csp"] == {}  # deny-by-default; no external origins


@pytest.mark.asyncio
async def test_read_unknown_resource_errors(client: AsyncClient, db_session):
    school = await _seed_school(db_session, slug="test", code="T1")
    admin = await _admin(db_session, school)
    resp = await client.post(
        "/api/v1/mcp",
        json=_rpc("resources/read", {"uri": "ui://evil/other.html"}),
        headers=auth_headers(access_token_for(admin)),
    )
    assert resp.json()["error"]["code"] == -32602


# ── tools/call: structured + text ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_tool_call_returns_structured_and_text(client: AsyncClient, db_session):
    school = await _seed_school(db_session, slug="test", code="T1")
    admin = await _admin(db_session, school)
    await _seed_class_with_attendance(db_session, school, admin.id)
    resp = await client.post(
        "/api/v1/mcp",
        json=_rpc("tools/call", {
            "name": "school_class_attendance_today",
            "arguments": {"class_label": "5A"},
        }),
        headers=auth_headers(access_token_for(admin)),
    )
    result = resp.json()["result"]
    # Text fallback for hosts without MCP Apps.
    assert result["content"][0]["type"] == "text"
    assert "Attendance" in result["content"][0]["text"]
    # Structured block for the interactive app (the existing capability block, unchanged).
    block = result["structuredContent"]
    assert block["kind"] == "metrics"
    labels = {m["label"]: m["value"] for m in block["metrics"]}
    assert labels["Present"] == 2
    assert labels["Absent"] == 1


@pytest.mark.asyncio
async def test_tool_call_missing_required_arg_clarifies_not_crashes(client: AsyncClient, db_session):
    school = await _seed_school(db_session, slug="test", code="T1")
    admin = await _admin(db_session, school)
    resp = await client.post(
        "/api/v1/mcp",
        json=_rpc("tools/call", {"name": "school_class_attendance_today", "arguments": {}}),
        headers=auth_headers(access_token_for(admin)),
    )
    # The capability returns a not_found/clarify block rather than throwing — still a 200 result.
    result = resp.json()["result"]
    assert result["structuredContent"]["kind"] in ("not_found", "clarify")


@pytest.mark.asyncio
async def test_unknown_tool_is_rejected(client: AsyncClient, db_session):
    school = await _seed_school(db_session, slug="test", code="T1")
    admin = await _admin(db_session, school)
    resp = await client.post(
        "/api/v1/mcp",
        json=_rpc("tools/call", {"name": "publish_notice", "arguments": {}}),
        headers=auth_headers(access_token_for(admin)),
    )
    # Not on the allowlist -> JSON-RPC method-not-found. No mutation tool is reachable.
    assert resp.json()["error"]["code"] == -32601


@pytest.mark.asyncio
async def test_unknown_method_is_rejected(client: AsyncClient, db_session):
    school = await _seed_school(db_session, slug="test", code="T1")
    admin = await _admin(db_session, school)
    resp = await client.post(
        "/api/v1/mcp", json=_rpc("resources/subscribe", {"uri": _UI_URI}),
        headers=auth_headers(access_token_for(admin)),
    )
    assert resp.json()["error"]["code"] == -32601


# ── Authorization: role + tenant + spoofing ──────────────────────────────────────


@pytest.mark.asyncio
async def test_parent_role_cannot_reach_the_adapter(client: AsyncClient, db_session):
    school = await _seed_school(db_session, slug="test", code="T1")
    parent = User(
        school_id=school.id, username="p1", mobile="+919900000099",
        full_name="Parent", role=UserRole.PARENT, is_active=True,
    )
    db_session.add(parent)
    await db_session.flush()
    resp = await client.post(
        "/api/v1/mcp", json=_rpc("tools/list"), headers=auth_headers(access_token_for(parent))
    )
    assert resp.status_code == 403  # require_roles gate — not a staff role


@pytest.mark.asyncio
async def test_spoofed_identity_in_body_is_ignored(client: AsyncClient, db_session):
    """A tenant/user/role supplied in the JSON-RPC params must NOT change the server identity."""
    school = await _seed_school(db_session, slug="test", code="T1")
    admin = await _admin(db_session, school)
    await _seed_class_with_attendance(db_session, school, admin.id)
    resp = await client.post(
        "/api/v1/mcp",
        json=_rpc("tools/call", {
            "name": "school_class_attendance_today",
            "arguments": {
                "class_label": "5A",
                "school_id": "00000000-0000-0000-0000-000000000000",
                "user_id": "00000000-0000-0000-0000-000000000000",
                "role": "super_admin",
            },
        }),
        headers=auth_headers(access_token_for(admin)),
    )
    # Still scoped to the authenticated admin's school — the spoofed ids were ignored, not honored.
    block = resp.json()["result"]["structuredContent"]
    assert block["kind"] == "metrics"
    labels = {m["label"]: m["value"] for m in block["metrics"]}
    assert labels["Present"] == 2


@pytest.mark.asyncio
async def test_cross_tenant_class_is_not_found(client: AsyncClient, db_session):
    """School A's user asking for School B's class gets 'not found' — never B's data."""
    school_a = await _seed_school(db_session, slug="test", code="AAA")
    school_b = await _seed_school(db_session, slug="sibling", code="BBB")
    admin_a = await _admin(db_session, school_a)
    await _seed_class_with_attendance(db_session, school_b, admin_a.id)  # class exists only in B
    resp = await client.post(
        "/api/v1/mcp",
        json=_rpc("tools/call", {
            "name": "school_class_attendance_today",
            "arguments": {"class_label": "5A"},
        }),
        headers=auth_headers(access_token_for(admin_a, tenant_slug="test")),
    )
    block = resp.json()["result"]["structuredContent"]
    # A's school has no class 5A -> not_found. B's attendance is never returned.
    assert block["kind"] == "not_found"


@pytest.mark.asyncio
async def test_teacher_without_scope_is_denied_class(client: AsyncClient, db_session):
    """A teacher not mapped to the class must not read it — object-level authz in the capability."""
    school = await _seed_school(db_session, slug="test", code="T1")
    admin = await _admin(db_session, school)
    await _seed_class_with_attendance(db_session, school, admin.id)
    teacher = User(
        school_id=school.id, username="t1", mobile="+919900000055",
        full_name="Teacher", role=UserRole.TEACHER, is_active=True,
    )
    db_session.add(teacher)
    await db_session.flush()
    resp = await client.post(
        "/api/v1/mcp",
        json=_rpc("tools/call", {
            "name": "school_class_attendance_today",
            "arguments": {"class_label": "5A"},
        }),
        headers=auth_headers(access_token_for(teacher)),
    )
    block = resp.json()["result"]["structuredContent"]
    # The capability's _authorize_class denies -> a safe denied/error block, never the data.
    assert block["kind"] in ("error", "not_found", "guide")
    assert "Present" not in {m.get("label") for m in block.get("metrics", [])}

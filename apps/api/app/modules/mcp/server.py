"""MCP JSON-RPC handler + the exact tool allowlist.

This is a thin protocol shim, not a runtime. It implements only the small JSON-RPC subset an MCP
host needs to discover and call an allowlisted tool and to read its UI resource. Every tool maps
to an EXISTING assistant capability (``app.modules.workspace.assistant.tools``); the capability
runs under the authenticated ``CurrentUser`` and re-enforces tenant/role/object authorization. The
shim adds no business logic, no data access and no authorization of its own.

Protocol: SEP-1865 (MCP Apps). The UI resource uses ``text/html;profile=mcp-app`` and a tool
declares it via ``_meta.ui.resourceUri``. ``tools/call`` returns a human-readable ``content`` text
block (the model/text-only fallback) plus ``structuredContent`` for the interactive app.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.modules.workspace.assistant.tools import get_tool

logger = structlog.get_logger()

# MCP Apps extension identifier + the required UI content type (SEP-1865).
MCP_APPS_EXTENSION = "io.modelcontextprotocol/ui"
UI_MIME_TYPE = "text/html;profile=mcp-app"
# We speak this MCP protocol revision; hosts negotiate their own and we echo a supported value.
PROTOCOL_VERSION = "2025-06-18"
SERVER_INFO = {"name": "studynexs-mcp", "version": "1.0.0"}

_UI_DIR = Path(__file__).parent / "ui"


@dataclass(frozen=True)
class McpToolSpec:
    """One allowlisted MCP tool, bound to an existing assistant capability.

    ``capability_tool`` is the name of the EXISTING ``AssistantTool`` whose handler + role gate are
    reused verbatim. ``resource_uri`` points at the bundled UI App. Keeping this list tiny and
    explicit is the whole security posture: nothing is exposed that isn't named here.
    """

    name: str
    title: str
    description: str
    input_schema: dict[str, Any]
    capability_tool: str
    resource_uri: str
    resource_file: str
    summarize: Any  # (block: dict) -> str  : human-readable text fallback


def _summarize_class_attendance(block: dict[str, Any]) -> str:
    title = block.get("title") or "Class attendance today"
    metrics = block.get("metrics") or []
    if not metrics:
        msg = block.get("message") or "Attendance hasn't been marked for this class today."
        return f"{title}: {msg}"
    parts = []
    for m in metrics:
        label = m.get("label", "")
        value = m.get("value")
        if m.get("format") == "percent" and isinstance(value, (int, float)):
            parts.append(f"{label} {round(value)}%")
        else:
            parts.append(f"{label} {value}")
    return f"{title}: " + ", ".join(parts) + "."


# ── The allowlist (exactly one read-only tool for the first slice) ─────────────

_ALLOWLIST: tuple[McpToolSpec, ...] = (
    McpToolSpec(
        name="school_class_attendance_today",
        title="Class Attendance Today",
        description=(
            "Today's attendance summary (present/absent/late and overall %) for ONE class you are "
            "authorized to see. Read-only; returns aggregate counts, never individual student "
            "records."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "class_label": {
                    "type": "string",
                    "description": "A class like '5A' or 'Class 2 A'.",
                }
            },
            "required": ["class_label"],
            "additionalProperties": False,
        },
        capability_tool="class_attendance_today",
        resource_uri="ui://studynexs/class-attendance.html",
        resource_file="class_attendance.html",
        summarize=_summarize_class_attendance,
    ),
)

_BY_NAME = {t.name: t for t in _ALLOWLIST}
_BY_RESOURCE = {t.resource_uri: t for t in _ALLOWLIST}


class McpError(Exception):
    """A JSON-RPC error with a code + safe message."""

    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


# JSON-RPC 2.0 standard error codes we use.
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602


def _tool_descriptor(spec: McpToolSpec) -> dict[str, Any]:
    return {
        "name": spec.name,
        "title": spec.title,
        "description": spec.description,
        "inputSchema": spec.input_schema,
        "annotations": {"readOnlyHint": True},
        "_meta": {"ui": {"resourceUri": spec.resource_uri, "visibility": ["model", "app"]}},
    }


def list_tools() -> dict[str, Any]:
    return {"tools": [_tool_descriptor(t) for t in _ALLOWLIST]}


def list_resources() -> dict[str, Any]:
    return {
        "resources": [
            {
                "uri": t.resource_uri,
                "name": t.title,
                "description": f"Interactive view for {t.title}.",
                "mimeType": UI_MIME_TYPE,
            }
            for t in _ALLOWLIST
        ]
    }


def read_resource(uri: str) -> dict[str, Any]:
    spec = _BY_RESOURCE.get(uri)
    if spec is None:
        raise McpError(INVALID_PARAMS, "Unknown resource")
    html = (_UI_DIR / spec.resource_file).read_text(encoding="utf-8")
    return {
        "contents": [
            {
                "uri": uri,
                "mimeType": UI_MIME_TYPE,
                "text": html,
                # Deny-by-default CSP: the app is fully self-contained (no external origins).
                "_meta": {"ui": {"csp": {}, "prefersBorder": True}},
            }
        ]
    }


def initialize_result(client_protocol: str | None) -> dict[str, Any]:
    return {
        # Echo the client's protocol when provided; otherwise advertise ours.
        "protocolVersion": client_protocol or PROTOCOL_VERSION,
        "serverInfo": SERVER_INFO,
        "capabilities": {
            "tools": {},
            "resources": {},
            "extensions": {MCP_APPS_EXTENSION: {"mimeTypes": [UI_MIME_TYPE]}},
        },
    }


async def call_tool(
    db: AsyncSession, user: CurrentUser, *, name: str, arguments: dict[str, Any]
) -> dict[str, Any]:
    """Run an allowlisted tool through its EXISTING governed capability.

    Authorization is NOT performed here beyond the coarse role gate that the assistant itself uses;
    the capability re-resolves the class and enforces object-level access under ``user``. A tool
    name not on the allowlist is rejected before any capability runs.
    """
    spec = _BY_NAME.get(name)
    if spec is None:
        raise McpError(METHOD_NOT_FOUND, "Unknown tool")

    tool = get_tool(spec.capability_tool)
    if tool is None:  # pragma: no cover - allowlist is static and validated by tests
        raise McpError(METHOD_NOT_FOUND, "Capability unavailable")

    # Coarse role gate (same catalog gate the assistant applies). Object-level access is still
    # enforced inside the capability under the authenticated user.
    if not tool.allowed_for(user.role):
        return _error_result("You don't have access to this information.")

    if not isinstance(arguments, dict):
        raise McpError(INVALID_PARAMS, "arguments must be an object")

    block = await tool.handler(db, user, arguments)
    text = spec.summarize(block)
    logger.info(
        "mcp_tool_call",
        tool=name,
        capability=spec.capability_tool,
        user_id=user.id,
        school_id=user.school_id,
        result_kind=block.get("kind"),
    )
    # content = text/model fallback (shown by hosts without MCP Apps); structuredContent = for the
    # interactive app. structuredContent is intentionally the existing capability block unchanged.
    return {
        "content": [{"type": "text", "text": text}],
        "structuredContent": block,
    }


def _error_result(message: str) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": message}], "isError": True}


async def handle_rpc(
    db: AsyncSession, user: CurrentUser, payload: dict[str, Any]
) -> dict[str, Any] | None:
    """Dispatch a single JSON-RPC request. Returns the response dict (None for a notification)."""
    rpc_id = payload.get("id")
    method = payload.get("method")
    params = payload.get("params") or {}

    # A JSON-RPC notification (no id) that we don't act on — acknowledge by returning nothing.
    if rpc_id is None and method not in ("initialize",):
        return None

    try:
        if method == "initialize":
            result = initialize_result(params.get("protocolVersion"))
        elif method == "tools/list":
            result = list_tools()
        elif method == "resources/list":
            result = list_resources()
        elif method == "resources/read":
            uri = params.get("uri")
            if not isinstance(uri, str):
                raise McpError(INVALID_PARAMS, "uri is required")
            result = read_resource(uri)
        elif method == "tools/call":
            tool_name = params.get("name")
            if not isinstance(tool_name, str):
                raise McpError(INVALID_PARAMS, "tool name is required")
            result = await call_tool(
                db, user, name=tool_name, arguments=params.get("arguments") or {}
            )
        elif method == "ping":
            result = {}
        else:
            raise McpError(METHOD_NOT_FOUND, f"Unknown method: {method}")
    except McpError as exc:
        return {"jsonrpc": "2.0", "id": rpc_id, "error": {"code": exc.code, "message": exc.message}}

    return {"jsonrpc": "2.0", "id": rpc_id, "result": result}


def allowlisted_tool_names() -> list[str]:
    return [t.name for t in _ALLOWLIST]

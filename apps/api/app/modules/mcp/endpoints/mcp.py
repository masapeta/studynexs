"""MCP Apps transport — a single authenticated Streamable-HTTP JSON-RPC endpoint.

Identity is derived server-side from the Bearer token via the EXISTING ``get_current_user``
dependency (which also enforces the tenant/school match). The MCP host supplies the same
credentials a browser does — it never supplies identity, tenant or role in the JSON-RPC body, and
any such field would be ignored. Audit + rate limiting are the platform's existing middleware.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_route import CommitOnSuccessRoute
from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_roles
from app.core.rate_limit import rate_limit
from app.modules.mcp.server import handle_rpc

router = APIRouter(route_class=CommitOnSuccessRoute)

# Only StudyNexs staff roles may connect an MCP host. Parents/students are excluded from the
# adapter in this first slice (the single tool is a staff capability anyway).
_MCP_ROLES = ("admin", "super_admin", "class_incharge", "teacher", "operations")

# Max JSON-RPC requests per batch, to bound work per HTTP call.
_MAX_BATCH = 20


@router.post("", dependencies=[rate_limit("mcp")])
async def mcp_rpc(
    request: Request,
    current_user: CurrentUser = Depends(require_roles(*_MCP_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Handle one JSON-RPC request (or a bounded batch). Returns raw JSON-RPC (no APIResponse
    envelope — this endpoint speaks the MCP wire protocol, not the StudyNexs API envelope)."""
    body = await request.json()

    if isinstance(body, list):
        batch = body[:_MAX_BATCH]
        responses = []
        for item in batch:
            if not isinstance(item, dict):
                continue
            resp = await handle_rpc(db, current_user, item)
            if resp is not None:
                responses.append(resp)
        return responses

    if not isinstance(body, dict):
        return {
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32600, "message": "Invalid request"},
        }

    resp = await handle_rpc(db, current_user, body)
    # A notification yields no response body; return an empty 200 payload.
    return resp if resp is not None else {}

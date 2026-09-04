"""Build backend-injected workspace tool context from the authenticated user."""

from __future__ import annotations

import uuid
from typing import cast

from app.core.dependencies import CurrentUser
from app.modules.ai.orchestration.tool_types import ToolRole, WorkspaceToolContext


def build_workspace_tool_context(
    current_user: CurrentUser,
    *,
    correlation_id: str,
) -> WorkspaceToolContext:
    if current_user.role not in {"teacher", "class_incharge"}:
        raise ValueError("Workspace tool context only supports teaching roles")

    return WorkspaceToolContext(
        teacher_user_id=uuid.UUID(current_user.id),
        school_id=uuid.UUID(current_user.school_id),
        role=cast(ToolRole, current_user.role),
        tenant_slug=current_user.tenant_slug,
        correlation_id=correlation_id,
    )

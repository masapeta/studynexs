"""Entry service for the Phase 0 teacher workspace read path."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.dependencies import CurrentUser
from app.modules.ai.orchestration.context_builder import build_workspace_tool_context
from app.modules.ai.orchestration.orchestrator import (
    WorkspaceOrchestrationError,
    WorkspaceReadOrchestrator,
)
from app.modules.ai.orchestration.policies import enforce_workspace_access
from app.modules.ai.orchestration.response_builder import (
    build_read_response,
    build_tool_failure_response,
    build_unsupported_request_response,
)
from app.modules.ai.orchestration.router import route_workspace_read_turn
from app.modules.ai.orchestration.tool_registry import WorkspaceToolRegistry
from app.modules.workspace.schemas.request import WorkspaceTurnRequest
from app.modules.workspace.schemas.response import WorkspaceResponse
from app.modules.workspace.services.session_service import WorkspaceSessionService


class WorkspaceService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._session_service = WorkspaceSessionService()

    async def handle_turn(
        self,
        *,
        current_user: CurrentUser,
        body: WorkspaceTurnRequest,
    ) -> WorkspaceResponse:
        settings = get_settings()
        policy = enforce_workspace_access(current_user, settings=settings)
        session = self._session_service.begin_turn(body.session_id)
        request_id = uuid.uuid4()
        correlation_id = f"workspace-{request_id.hex}"

        route = route_workspace_read_turn(body.text, policy=policy)
        if route.strategy != "deterministic":
            return build_unsupported_request_response(
                request_id=request_id,
                correlation_id=correlation_id,
                route=route,
                retention=session.retention,
            )

        context = build_workspace_tool_context(
            current_user,
            correlation_id=correlation_id,
        )
        registry = WorkspaceToolRegistry.load_default(settings=settings)
        orchestrator = WorkspaceReadOrchestrator(
            registry,
            max_tool_calls=policy.max_tool_calls_per_turn,
        )
        try:
            result = await orchestrator.run(
                db=self.db,
                context=context,
                route=route,
            )
        except WorkspaceOrchestrationError as exc:
            return build_tool_failure_response(
                request_id=request_id,
                correlation_id=correlation_id,
                detail=exc.detail,
                tool_calls=exc.tool_calls,
                tool_failures=exc.tool_failures,
                retention=session.retention,
            )

        return build_read_response(
            request_id=request_id,
            correlation_id=correlation_id,
            result=result,
            retention=session.retention,
        )

"""Read-only Phase 0 workspace conversation endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_route import CommitOnSuccessRoute
from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_roles
from app.core.rate_limit import rate_limit
from app.modules.workspace.schemas.request import WorkspaceTurnRequest
from app.modules.workspace.schemas.response import WorkspaceResponse
from app.modules.workspace.services.workspace_service import WorkspaceService
from app.shared.schemas.common import APIResponse

router = APIRouter(route_class=CommitOnSuccessRoute)


@router.post(
    "/turn",
    response_model=APIResponse[WorkspaceResponse],
    dependencies=[rate_limit("workspace_turn")],
)
async def workspace_turn(
    body: WorkspaceTurnRequest,
    current_user: CurrentUser = Depends(require_roles("teacher", "class_incharge")),
    db: AsyncSession = Depends(get_db),
):
    response = await WorkspaceService(db).handle_turn(
        current_user=current_user,
        body=body,
    )
    return APIResponse(data=response)

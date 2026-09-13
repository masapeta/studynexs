"""Agentic assistant endpoints: turn (plan+execute), session list, session messages."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_route import CommitOnSuccessRoute
from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_roles
from app.core.rate_limit import rate_limit
from app.modules.workspace.assistant.service import AssistantService
from app.shared.schemas.common import APIResponse

router = APIRouter(route_class=CommitOnSuccessRoute)

_ASSISTANT_ROLES = (
    "admin",
    "super_admin",
    "class_incharge",
    "teacher",
    "operations",
    "parent",
    "student",
)


class AssistantTurnRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1000)
    session_id: uuid.UUID | None = None


@router.post(
    "/turn",
    response_model=APIResponse,
    dependencies=[rate_limit("workspace_turn")],
)
async def assistant_turn(
    body: AssistantTurnRequest,
    current_user: CurrentUser = Depends(require_roles(*_ASSISTANT_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    result = await AssistantService(db).handle_turn(
        current_user=current_user, text=body.text, session_id=body.session_id
    )
    return APIResponse(data=result)


@router.get("/sessions", response_model=APIResponse)
async def list_sessions(
    current_user: CurrentUser = Depends(require_roles(*_ASSISTANT_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    sessions = await AssistantService(db).list_sessions(current_user=current_user)
    return APIResponse(data=sessions)


@router.get("/sessions/{session_id}", response_model=APIResponse)
async def get_session(
    session_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_ASSISTANT_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    messages = await AssistantService(db).get_session_messages(
        current_user=current_user, session_id=session_id
    )
    return APIResponse(data=messages)

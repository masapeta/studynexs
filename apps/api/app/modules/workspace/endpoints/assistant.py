"""Agentic assistant endpoints: turn (plan+execute), session list, session messages."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_route import CommitOnSuccessRoute
from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_roles
from app.core.rate_limit import rate_limit
from app.modules.workspace.assistant.page_context import PageContextIn
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
    page_context: PageContextIn | None = None


class SessionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, max_length=200)
    archived: bool | None = None

    @field_validator("title")
    @classmethod
    def _clean_title(cls, v: str | None) -> str | None:
        if v is None:
            return v
        cleaned = " ".join(v.split())
        if not cleaned:
            raise ValueError("title cannot be empty")
        return cleaned

    @model_validator(mode="after")
    def _something_to_change(self) -> "SessionUpdate":
        if self.title is None and self.archived is None:
            raise ValueError("provide title and/or archived")
        return self


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
        current_user=current_user,
        text=body.text,
        session_id=body.session_id,
        page_context=body.page_context,
    )
    return APIResponse(data=result)


@router.get("/sessions", response_model=APIResponse)
async def list_sessions(
    archived: bool = Query(False),
    current_user: CurrentUser = Depends(require_roles(*_ASSISTANT_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    sessions = await AssistantService(db).list_sessions(
        current_user=current_user, archived=archived
    )
    return APIResponse(data=sessions)


@router.patch("/sessions/{session_id}", response_model=APIResponse)
async def update_session(
    session_id: uuid.UUID,
    body: SessionUpdate,
    current_user: CurrentUser = Depends(require_roles(*_ASSISTANT_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    session = await AssistantService(db).update_session(
        current_user=current_user,
        session_id=session_id,
        title=body.title,
        archived=body.archived,
    )
    return APIResponse(data=session)


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

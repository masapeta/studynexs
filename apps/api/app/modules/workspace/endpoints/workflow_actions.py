"""Governed workflow ACTION endpoints — server-side, authenticated state changes.

The first action consumer is Parent Intervention's approve-and-notify. A model can never call
this; only an authenticated staff user with the right scope can, and the action re-validates
tenant/authorization/recipient, is idempotent, and is audited inside the service.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_route import CommitOnSuccessRoute
from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_roles
from app.modules.workspace.workflows.notice_action_service import (
    NoticeActionError,
    NoticeActionService,
)
from app.modules.workspace.workflows.parent_intervention_service import (
    InterventionError,
    ParentInterventionService,
)
from app.shared.schemas.common import APIResponse

router = APIRouter(route_class=CommitOnSuccessRoute)
_STAFF = ("teacher", "class_incharge", "admin", "super_admin")


class ConfirmPublishNotice(BaseModel):
    """The confirm payload echoed back from the preview. The server re-authorizes + re-validates
    everything; the client cannot smuggle authorization through this body."""

    action_token: uuid.UUID
    title: str = Field(max_length=200)
    content: str
    audience: str
    target_roles: list[str]
    priority: str = "medium"
    class_id: uuid.UUID | None = None


@router.post("/parent-intervention/drafts/{draft_id}/approve", response_model=APIResponse)
async def approve_parent_intervention(
    draft_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_STAFF)),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """Approve one 1:1 draft and create the IN_APP notification. Authenticated + idempotent."""
    service = ParentInterventionService(db)
    try:
        draft = await service.approve_and_notify(current_user, draft_id=draft_id)
    except InterventionError as exc:
        raise HTTPException(status_code=400, detail=exc.message)
    return APIResponse(
        data={
            "draft_id": str(draft.id),
            "status": draft.status,
            "notification_id": str(draft.notification_id) if draft.notification_id else None,
        },
        message="Parent notified" if draft.notification_id else "Not sent",
    )


@router.post("/actions/publish-notice/confirm", response_model=APIResponse)
async def confirm_publish_notice(
    body: ConfirmPublishNotice,
    current_user: CurrentUser = Depends(require_roles(*_STAFF)),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """Publish the previewed notice. Authenticated + server-authorized + idempotent on the token.

    A model-supplied confirmation flag can never reach here — only an authenticated user action
    with the server-issued action_token does. Re-authorization + validation happen in the service.
    """
    service = NoticeActionService(db)
    try:
        notice, created = await service.confirm_publish(
            current_user,
            action_token=body.action_token,
            title=body.title,
            content=body.content,
            audience=body.audience,
            class_id=body.class_id,
            target_roles=body.target_roles,
            priority=body.priority,
        )
    except NoticeActionError as exc:
        raise HTTPException(status_code=400, detail=exc.message)
    return APIResponse(
        data={
            "kind": "action_result",
            "action": "publish_notice",
            "status": "completed",
            "notice_id": str(notice.id),
            "audience": notice.audience.value,
            "created": created,
        },
        message="Notice published" if created else "Already published",
    )

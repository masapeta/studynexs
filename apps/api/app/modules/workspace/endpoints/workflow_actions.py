"""Governed workflow ACTION endpoints — server-side, authenticated state changes.

The first action consumer is Parent Intervention's approve-and-notify. A model can never call
this; only an authenticated staff user with the right scope can, and the action re-validates
tenant/authorization/recipient, is idempotent, and is audited inside the service.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_route import CommitOnSuccessRoute
from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_roles
from app.modules.workspace.workflows.parent_intervention_service import (
    InterventionError,
    ParentInterventionService,
)
from app.shared.schemas.common import APIResponse

router = APIRouter(route_class=CommitOnSuccessRoute)
_STAFF = ("teacher", "class_incharge", "admin", "super_admin")


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

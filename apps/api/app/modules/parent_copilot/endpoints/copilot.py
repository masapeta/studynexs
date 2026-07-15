"""Parent Copilot endpoints — grounded briefings for linked children (Batch 27)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_route import CommitOnSuccessRoute
from app.core.authorization import assert_can_access_student
from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user
from app.core.rate_limit import rate_limit
from app.modules.parent_copilot.schemas.copilot import (
    ParentAnswerOut,
    ParentAskIn,
    ParentBriefingOut,
)
from app.modules.parent_copilot.services.parent_copilot_service import ParentCopilotService
from app.shared.schemas.common import APIResponse

router = APIRouter(route_class=CommitOnSuccessRoute)

_BRIEFING_RATE = {"max_requests": 10, "window_seconds": 3600}
_ASK_RATE = {"max_requests": 15, "window_seconds": 60}


@router.get(
    "/students/{student_id}/briefing",
    response_model=APIResponse[ParentBriefingOut],
    dependencies=[rate_limit("parent_copilot_briefing", **_BRIEFING_RATE)],
)
async def parent_briefing(
    student_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Grounded progress briefing with home support tips (metered)."""
    await assert_can_access_student(current_user, db, student_id)
    try:
        briefing = await ParentCopilotService(db).generate_briefing(
            school_id=uuid.UUID(current_user.school_id),
            student_id=student_id,
            user_id=uuid.UUID(current_user.id),
            role=current_user.role,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return APIResponse(data=briefing)


@router.post(
    "/students/{student_id}/ask",
    response_model=APIResponse[ParentAnswerOut],
    dependencies=[rate_limit("parent_copilot_ask", **_ASK_RATE)],
)
async def parent_ask(
    student_id: uuid.UUID,
    body: ParentAskIn,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Parent Q&A on child's learning — grounded, minimal PII in prompts."""
    await assert_can_access_student(current_user, db, student_id)
    try:
        answer = await ParentCopilotService(db).ask(
            school_id=uuid.UUID(current_user.school_id),
            student_id=student_id,
            body=body,
            user_id=uuid.UUID(current_user.id),
            role=current_user.role,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return APIResponse(data=answer)

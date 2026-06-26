"""Portal endpoints — parent, student, and teacher home context."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import assert_can_access_student
from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user
from app.modules.portal.schemas.portal import (
    ChildSummaryOut,
    FeatureTeaserOut,
    ParentChildFeesOut,
    ParentChildProgressOut,
    PortalContextOut,
)
from app.modules.portal.services.portal_service import (
    build_portal_context,
    features_for_role,
    list_parent_children_fees,
    list_parent_children_progress,
    parent_child_progress,
    parent_child_summary,
)
from app.shared.schemas.common import APIResponse

router = APIRouter()


@router.get("/context", response_model=APIResponse[PortalContextOut])
async def portal_context(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Role-aware portal routing — children for parents, self for students."""
    ctx = await build_portal_context(
        db,
        school_id=uuid.UUID(current_user.school_id),
        user_id=uuid.UUID(current_user.id),
        role=current_user.role,
    )
    return APIResponse(data=ctx)


@router.get("/features", response_model=APIResponse[list[FeatureTeaserOut]])
async def product_features(
    current_user: CurrentUser = Depends(get_current_user),
):
    """Product roadmap teasers, scoped to the caller's audience — parents/students
    never see staff-only features (and their 'Open' links)."""
    return APIResponse(data=features_for_role(current_user.role))


@router.get("/parent/fees", response_model=APIResponse[list[ParentChildFeesOut]])
async def parent_fees_batch(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fee records for all linked children — one round trip for the parent portal."""
    if current_user.role != "parent":
        raise HTTPException(status_code=403, detail="Access denied")
    rows = await list_parent_children_fees(
        db,
        school_id=uuid.UUID(current_user.school_id),
        parent_user_id=uuid.UUID(current_user.id),
    )
    return APIResponse(data=rows)


@router.get("/child/{student_id}/summary", response_model=APIResponse[ChildSummaryOut])
async def child_summary(
    student_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lightweight child summary for parent portal — avoids full academic profile."""
    await assert_can_access_student(current_user, db, student_id)
    summary = await parent_child_summary(
        db,
        school_id=uuid.UUID(current_user.school_id),
        student_id=student_id,
    )
    if not summary:
        raise HTTPException(status_code=404, detail="Student not found")
    return APIResponse(data=summary)


@router.get("/parent/children-progress", response_model=APIResponse[list[ParentChildProgressOut]])
async def parent_children_progress(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Progress, weak topics, and teacher feedback for all linked children."""
    if current_user.role != "parent":
        raise HTTPException(status_code=403, detail="Access denied")
    rows = await list_parent_children_progress(
        db,
        school_id=uuid.UUID(current_user.school_id),
        parent_user_id=uuid.UUID(current_user.id),
    )
    return APIResponse(data=rows)


@router.get("/child/{student_id}/progress", response_model=APIResponse[ParentChildProgressOut])
async def child_progress(
    student_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Full child progress for parent portal — summary, weak topics, teacher feedback."""
    await assert_can_access_student(current_user, db, student_id)
    if current_user.role != "parent":
        raise HTTPException(status_code=403, detail="Access denied")
    progress = await parent_child_progress(
        db,
        school_id=uuid.UUID(current_user.school_id),
        parent_user_id=uuid.UUID(current_user.id),
        student_id=student_id,
    )
    if not progress:
        raise HTTPException(status_code=404, detail="Student not found")
    return APIResponse(data=progress)

"""Portal endpoints — parent, student, and teacher home context."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_route import CommitOnSuccessRoute
from app.core.authorization import assert_can_access_student
from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user
from app.db.models.student import Student
from app.modules.examinations.schemas.release import LearnerResultDetail, LearnerResultSummary
from app.modules.portal.schemas.portal import (
    ChildSummaryOut,
    FeatureTeaserOut,
    ParentChildFeesOut,
    ParentChildProgressOut,
    PortalContextOut,
)
from app.modules.portal.services.learner_results_service import list_results, result_detail
from app.modules.portal.services.portal_service import (
    build_portal_context,
    features_for_role,
    list_parent_children_fees,
    list_parent_children_progress,
    parent_child_progress,
    parent_child_summary,
)
from app.shared.schemas.common import APIResponse

router = APIRouter(route_class=CommitOnSuccessRoute)


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


# ── Released results (E13) — learner roles only; staff use the gradebook ───────


async def _self_student(db: AsyncSession, current_user: CurrentUser) -> Student:
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Access denied")
    student = (
        await db.execute(
            select(Student).where(
                Student.user_id == uuid.UUID(current_user.id),
                Student.school_id == uuid.UUID(current_user.school_id),
            )
        )
    ).scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


async def _child_student(
    db: AsyncSession, current_user: CurrentUser, student_id: uuid.UUID
) -> Student:
    if current_user.role != "parent":
        raise HTTPException(status_code=403, detail="Access denied")
    return await assert_can_access_student(current_user, db, student_id)


@router.get("/results", response_model=APIResponse[list[LearnerResultSummary]])
async def my_results(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    student = await _self_student(db, current_user)
    rows = await list_results(db, school_id=uuid.UUID(current_user.school_id), student=student)
    return APIResponse(data=rows)


@router.get("/results/{exam_id}", response_model=APIResponse[LearnerResultDetail])
async def my_result_detail(
    exam_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    student = await _self_student(db, current_user)
    detail = await result_detail(
        db, school_id=uuid.UUID(current_user.school_id), student=student, exam_id=exam_id
    )
    if detail is None:
        raise HTTPException(status_code=404, detail="Result not found")
    return APIResponse(data=detail)


@router.get(
    "/child/{student_id}/results", response_model=APIResponse[list[LearnerResultSummary]]
)
async def child_results(
    student_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    student = await _child_student(db, current_user, student_id)
    rows = await list_results(db, school_id=uuid.UUID(current_user.school_id), student=student)
    return APIResponse(data=rows)


@router.get(
    "/child/{student_id}/results/{exam_id}", response_model=APIResponse[LearnerResultDetail]
)
async def child_result_detail(
    student_id: uuid.UUID,
    exam_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    student = await _child_student(db, current_user, student_id)
    detail = await result_detail(
        db, school_id=uuid.UUID(current_user.school_id), student=student, exam_id=exam_id
    )
    if detail is None:
        raise HTTPException(status_code=404, detail="Result not found")
    return APIResponse(data=detail)

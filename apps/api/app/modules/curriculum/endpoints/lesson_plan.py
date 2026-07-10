"""Lesson plan API — teacher-scoped draft → approve workflow."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_roles
from app.core.rate_limit import rate_limit
from app.core.staff_permissions import get_staff_scope
from app.db.models.lesson_plan import LessonPlan, LessonPlanStatus
from app.modules.curriculum.schemas.lesson_plan import (
    GenerateLessonPlanRequest,
    LessonPlanOut,
    LessonSegmentOut,
    UpdateLessonPlanRequest,
)
from app.modules.curriculum.services.lesson_plan_service import LessonPlanService
from app.shared.schemas.common import APIResponse

router = APIRouter()
_TEACH = ("teacher", "class_incharge", "admin", "super_admin")
_LP_RATE = {"max_requests": 20, "window_seconds": 60}


def _out(plan: LessonPlan, scope, svc: LessonPlanService) -> LessonPlanOut:
    return LessonPlanOut(
        id=plan.id,
        class_id=plan.class_id,
        subject_id=plan.subject_id,
        title=plan.title,
        chapter=plan.chapter,
        topic=plan.topic,
        scheduled_for=plan.scheduled_for,
        segments=[LessonSegmentOut(**s) for s in (plan.segments or [])],
        status=plan.status.value,
        notes=plan.notes,
        can_edit=svc.can_edit(scope, plan),
        can_approve=svc.can_approve(scope, plan),
    )


async def _get_plan(db: AsyncSession, school_id: str, plan_id: uuid.UUID) -> LessonPlan:
    plan = (
        await db.execute(
            select(LessonPlan).where(
                LessonPlan.id == plan_id,
                LessonPlan.school_id == uuid.UUID(school_id),
            )
        )
    ).scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Lesson plan not found")
    return plan


@router.post(
    "/generate",
    response_model=LessonPlanOut,
    status_code=201,
    dependencies=[rate_limit("lesson_plan_generate", **_LP_RATE)],
)
async def generate_lesson_plan(
    body: GenerateLessonPlanRequest,
    current_user: CurrentUser = Depends(require_roles(*_TEACH)),
    db: AsyncSession = Depends(get_db),
) -> LessonPlanOut:
    scope = await get_staff_scope(db, current_user)
    svc = LessonPlanService(db)
    try:
        plan = await svc.generate(
            uuid.UUID(current_user.school_id),
            scope,
            class_id=body.class_id,
            subject_id=body.subject_id,
            topic=body.topic,
            chapter=body.chapter,
            scheduled_for=body.scheduled_for,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    await db.commit()
    return _out(plan, scope, svc)


@router.get("/next", response_model=APIResponse[LessonPlanOut | None])
async def get_next_lesson_plan(
    current_user: CurrentUser = Depends(require_roles(*_TEACH)),
    db: AsyncSession = Depends(get_db),
):
    scope = await get_staff_scope(db, current_user)
    svc = LessonPlanService(db)
    plan = await svc.next_draft(uuid.UUID(current_user.school_id), scope)
    return APIResponse(data=_out(plan, scope, svc) if plan else None)


@router.put("/{plan_id}", response_model=LessonPlanOut)
async def update_lesson_plan(
    plan_id: uuid.UUID,
    body: UpdateLessonPlanRequest,
    current_user: CurrentUser = Depends(require_roles(*_TEACH)),
    db: AsyncSession = Depends(get_db),
) -> LessonPlanOut:
    scope = await get_staff_scope(db, current_user)
    svc = LessonPlanService(db)
    plan = await _get_plan(db, current_user.school_id, plan_id)
    if not svc.can_edit(scope, plan):
        raise HTTPException(status_code=403, detail="Cannot edit this lesson plan")
    if body.title is not None:
        plan.title = body.title
    if body.chapter is not None:
        plan.chapter = body.chapter
    if body.topic is not None:
        plan.topic = body.topic
    if body.notes is not None:
        plan.notes = body.notes
    if body.segments is not None:
        plan.segments = [s.model_dump() for s in body.segments]
    await db.commit()
    return _out(plan, scope, svc)


@router.post("/{plan_id}/approve", response_model=LessonPlanOut)
async def approve_lesson_plan(
    plan_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_TEACH)),
    db: AsyncSession = Depends(get_db),
) -> LessonPlanOut:
    scope = await get_staff_scope(db, current_user)
    svc = LessonPlanService(db)
    plan = await _get_plan(db, current_user.school_id, plan_id)
    if not svc.can_approve(scope, plan):
        raise HTTPException(status_code=403, detail="Cannot approve this lesson plan")
    plan.status = LessonPlanStatus.APPROVED
    await db.commit()
    return _out(plan, scope, svc)


@router.post(
    "/{plan_id}/regenerate",
    response_model=LessonPlanOut,
    status_code=201,
    dependencies=[rate_limit("lesson_plan_generate", **_LP_RATE)],
)
async def regenerate_lesson_plan(
    plan_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_TEACH)),
    db: AsyncSession = Depends(get_db),
) -> LessonPlanOut:
    scope = await get_staff_scope(db, current_user)
    svc = LessonPlanService(db)
    source = await _get_plan(db, current_user.school_id, plan_id)
    plan = await svc.generate(
        uuid.UUID(current_user.school_id),
        scope,
        class_id=source.class_id,
        subject_id=source.subject_id,
        topic=source.topic,
        chapter=source.chapter,
        scheduled_for=source.scheduled_for,
    )
    await db.commit()
    return _out(plan, scope, svc)

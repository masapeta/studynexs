"""Lesson plan API — teacher-scoped draft → approve workflow."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.api_route import CommitOnSuccessRoute
from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_roles
from app.core.rate_limit import rate_limit
from app.core.staff_permissions import get_staff_scope
from app.db.models.academic import Class, Subject
from app.db.models.lesson_plan import LessonPlan, LessonPlanStatus
from app.db.models.user import User
from app.modules.ai.gateway.errors import raise_http_for_llm_error
from app.modules.ai.services.teacher_copilot_service import TeacherCopilotService
from app.modules.ai.services.usage_caps import enforce_monthly_ai_cap
from app.modules.ai.telemetry import bind_ai_context
from app.modules.curriculum.schemas.lesson_plan import (
    GenerateLessonPlanRequest,
    LessonPlanOut,
    LessonSegmentOut,
    UpdateLessonPlanRequest,
)
from app.modules.curriculum.schemas.provenance import provenance_from_sources
from app.modules.curriculum.services.lesson_plan_pdf import generate_lesson_plan_pdf
from app.modules.curriculum.services.lesson_plan_service import LessonPlanService
from app.shared.schemas.common import APIResponse

router = APIRouter(route_class=CommitOnSuccessRoute)
_TEACH = ("teacher", "class_incharge", "admin", "super_admin")
_LP_RATE = {"max_requests": 20, "window_seconds": 60}


def _segment_out(raw: dict) -> LessonSegmentOut:
    return LessonSegmentOut(
        duration_min=int(raw.get("duration_min") or 0),
        activity=str(raw.get("activity") or ""),
        description=raw.get("description"),
        notes=raw.get("notes"),
        citations=raw.get("citations"),
        citation_sources=raw.get("citation_sources"),
    )


async def _plan_context(
    db: AsyncSession, school_id: uuid.UUID, plan: LessonPlan
) -> dict[str, str | int | None]:
    teacher_name: str | None = None
    class_label: str | None = None
    subject_name: str | None = None

    user = (
        await db.execute(
            select(User.full_name).where(
                User.id == plan.created_by,
                User.school_id == school_id,
            )
        )
    ).scalar_one_or_none()
    if user:
        teacher_name = user

    cls = (
        await db.execute(
            select(Class.grade, Class.section).where(
                Class.id == plan.class_id,
                Class.school_id == school_id,
            )
        )
    ).one_or_none()
    if cls:
        class_label = f"{cls.grade} {cls.section}".strip()

    subj = (
        await db.execute(
            select(Subject.name).where(
                Subject.id == plan.subject_id,
                Subject.school_id == school_id,
            )
        )
    ).scalar_one_or_none()
    if subj:
        subject_name = subj

    duration_minutes = sum(int(s.get("duration_min") or 0) for s in (plan.segments or []))

    return {
        "teacher_name": teacher_name,
        "class_label": class_label,
        "subject_name": subject_name,
        "duration_minutes": duration_minutes,
    }


async def _out(
    db: AsyncSession,
    plan: LessonPlan,
    scope,
    svc: LessonPlanService,
    school_id: uuid.UUID,
) -> LessonPlanOut:
    prov = provenance_from_sources(
        plan.grounding_sources,
        pack_id=str(plan.pack_id) if plan.pack_id else None,
        grounded=bool(plan.grounded),
        created_at=plan.created_at,
    )
    grounded_at = plan.created_at.date() if plan.grounded and plan.created_at else None
    ctx = await _plan_context(db, school_id, plan)
    objectives = list(plan.learning_objectives or [])
    materials = list(plan.materials or [])
    return LessonPlanOut(
        id=plan.id,
        class_id=plan.class_id,
        subject_id=plan.subject_id,
        title=plan.title,
        chapter=plan.chapter,
        topic=plan.topic,
        scheduled_for=plan.scheduled_for,
        segments=[_segment_out(s) for s in (plan.segments or [])],
        learning_objectives=objectives,
        materials=materials,
        duration_minutes=int(ctx["duration_minutes"] or 0),
        teacher_name=ctx["teacher_name"],
        class_label=ctx["class_label"],
        subject_name=ctx["subject_name"],
        status=plan.status.value,
        notes=plan.notes,
        pack_id=plan.pack_id,
        pack_status=prov.get("pack_status"),
        pack_version=prov.get("pack_version"),
        grounded=bool(plan.grounded),
        grounding_sources=plan.grounding_sources,
        ai_model=plan.ai_model,
        grounded_at=grounded_at,
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
    school_id = uuid.UUID(current_user.school_id)
    try:
        if body.generation_mode == "copilot":
            if body.pack_id is None:
                raise ValueError(
                    "Select an approved curriculum pack for Teacher Copilot generation."
                )
            bind_ai_context(
                school_id=current_user.school_id,
                user_id=current_user.id,
                feature="teacher_copilot",
            )
            credits = await enforce_monthly_ai_cap(
                db,
                school_id,
                user_id=uuid.UUID(current_user.id),
                role=current_user.role,
                feature="teacher_copilot",
                purpose_tag="lesson_plan",
            )
            copilot = TeacherCopilotService(db)
            try:
                plan = await copilot.generate_grounded_lesson_plan(
                    school_id,
                    scope,
                    class_id=body.class_id,
                    subject_id=body.subject_id,
                    pack_id=body.pack_id,
                    topic=body.topic,
                    chapter=body.chapter,
                    scheduled_for=body.scheduled_for,
                    created_by=uuid.UUID(current_user.id),
                    role=current_user.role,
                    credits_charged=credits,
                )
            except ValueError:
                raise
            except Exception as exc:
                raise_http_for_llm_error(exc)
                raise
        else:
            svc = LessonPlanService(db)
            plan = await svc.generate(
                school_id,
                scope,
                class_id=body.class_id,
                subject_id=body.subject_id,
                topic=body.topic,
                chapter=body.chapter,
                scheduled_for=body.scheduled_for,
                pack_id=body.pack_id,
            )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    await db.commit()
    svc = LessonPlanService(db)
    return await _out(db, plan, scope, svc, school_id)


@router.get("/next", response_model=APIResponse[LessonPlanOut | None])
async def get_next_lesson_plan(
    current_user: CurrentUser = Depends(require_roles(*_TEACH)),
    db: AsyncSession = Depends(get_db),
):
    scope = await get_staff_scope(db, current_user)
    svc = LessonPlanService(db)
    plan = await svc.next_draft(uuid.UUID(current_user.school_id), scope)
    return APIResponse(
        data=await _out(db, plan, scope, svc, uuid.UUID(current_user.school_id))
        if plan
        else None
    )


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
    if body.scheduled_for is not None:
        plan.scheduled_for = body.scheduled_for
    if body.notes is not None:
        plan.notes = body.notes
    if body.learning_objectives is not None:
        plan.learning_objectives = body.learning_objectives
    if body.materials is not None:
        plan.materials = body.materials
    if body.segments is not None:
        plan.segments = [s.model_dump(exclude_none=True) for s in body.segments]
    await db.commit()
    return await _out(db, plan, scope, svc, uuid.UUID(current_user.school_id))


@router.get("/{plan_id}/pdf")
async def download_lesson_plan_pdf(
    plan_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_TEACH)),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Render a server-generated lesson-plan PDF."""
    scope = await get_staff_scope(db, current_user)
    svc = LessonPlanService(db)
    plan = await _get_plan(db, current_user.school_id, plan_id)
    if not svc.can_view(scope, plan):
        raise HTTPException(status_code=403, detail="Cannot access this lesson plan")
    school_id = uuid.UUID(current_user.school_id)
    ctx = await _plan_context(db, school_id, plan)
    topic = plan.topic or plan.title
    content, media_type = await run_in_threadpool(
        generate_lesson_plan_pdf,
        teacher_name=str(ctx["teacher_name"] or "—"),
        subject_name=str(ctx["subject_name"] or "—"),
        class_label=str(ctx["class_label"] or "—"),
        scheduled_for=plan.scheduled_for,
        topic=topic,
        duration_minutes=int(ctx["duration_minutes"] or 0),
        learning_objectives=list(plan.learning_objectives or []),
        materials=list(plan.materials or []),
        segments=list(plan.segments or []),
        notes=plan.notes,
    )
    safe_topic = (topic or "lesson_plan").replace(" ", "_")[:40]
    filename = f"lesson_plan_{safe_topic}.pdf"
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"inline; filename={filename}"},
    )


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
    return await _out(db, plan, scope, svc, uuid.UUID(current_user.school_id))


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
    return await _out(db, plan, scope, svc, uuid.UUID(current_user.school_id))

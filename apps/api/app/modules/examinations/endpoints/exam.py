"""Examination endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_route import CommitOnSuccessRoute
from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_roles
from app.core.staff_permissions import assert_exam_class, assert_exams_access, get_staff_scope
from app.core.tenant_scope import TenantScope
from app.db.models.academic import Class
from app.db.models.examination import Exam, ExamMark
from app.modules.examinations.endpoints.evaluation import router as evaluation_router
from app.modules.examinations.schemas.exam import (
    BulkMarkEntryRequest,
    ExamCreate,
    ExamMarkOut,
    ExamOut,
    QuestionDef,
    QuestionSchemaSet,
)
from app.modules.examinations.services.exam_service import ExamService
from app.shared.schemas.common import APIResponse

router = APIRouter(route_class=CommitOnSuccessRoute)
_STAFF = ("teacher", "class_incharge", "admin", "super_admin")


async def _scoped_exam(db: AsyncSession, current_user: CurrentUser, exam_id: uuid.UUID) -> Exam:
    scope = await get_staff_scope(db, current_user)
    assert_exams_access(scope)
    exam = await TenantScope(db, uuid.UUID(current_user.school_id)).exam(exam_id)
    assert_exam_class(scope, exam.class_id)
    return exam


@router.post("", response_model=APIResponse[ExamOut], status_code=201)
async def create_exam(
    body: ExamCreate,
    current_user: CurrentUser = Depends(require_roles(*_STAFF)),
    db: AsyncSession = Depends(get_db),
):
    scope = await get_staff_scope(db, current_user)
    assert_exam_class(scope, body.class_id)
    service = ExamService(db)
    exam = await service.create_exam(
        uuid.UUID(current_user.school_id), body, uuid.UUID(current_user.id)
    )
    return APIResponse(data=ExamOut.from_exam(exam), message="Exam created")


@router.get("", response_model=APIResponse[list[ExamOut]])
async def list_exams(
    class_id: uuid.UUID | None = None,
    current_user: CurrentUser = Depends(require_roles(*_STAFF)),
    db: AsyncSession = Depends(get_db),
):
    scope = await get_staff_scope(db, current_user)
    assert_exams_access(scope)
    if class_id:
        assert_exam_class(scope, class_id)
    elif not scope.is_admin:
        raise HTTPException(status_code=400, detail="Select a class to list exams")
    service = ExamService(db)
    exams = await service.list_exams(uuid.UUID(current_user.school_id), class_id)
    return APIResponse(data=[ExamOut.from_exam(e) for e in exams])


@router.get("/gradebook", response_model=APIResponse)
async def gradebook(
    class_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_STAFF)),
    db: AsyncSession = Depends(get_db),
):
    scope = await get_staff_scope(db, current_user)
    assert_exams_access(scope)
    assert_exam_class(scope, class_id)
    service = ExamService(db)
    data = await service.get_gradebook(uuid.UUID(current_user.school_id), class_id)
    return APIResponse(data=data)


@router.get("/class-performance", response_model=APIResponse)
async def class_performance(
    limit: int = Query(5, ge=1, le=20),
    current_user: CurrentUser = Depends(require_roles(*_STAFF)),
    db: AsyncSession = Depends(get_db),
):
    """Top classes by overall average % — admin and class incharges only."""
    scope = await get_staff_scope(db, current_user)
    assert_exams_access(scope)
    avg_pct = func.avg(ExamMark.marks_obtained / Exam.total_marks * 100)
    query = (
        select(Class.grade, Class.section, avg_pct.label("pct"))
        .join(Exam, Exam.class_id == Class.id)
        .join(ExamMark, ExamMark.exam_id == Exam.id)
        .where(Class.school_id == uuid.UUID(current_user.school_id))
    )
    if not scope.is_admin:
        query = query.where(Class.id.in_(scope.incharge_class_ids))
    rows = (
        await db.execute(
            query.group_by(Class.id, Class.grade, Class.section)
            .order_by(avg_pct.desc())
            .limit(limit)
        )
    ).all()
    data = [
        {"label": f"{grade} - {section}", "percentage": round(float(pct or 0), 1)}
        for grade, section, pct in rows
    ]
    return APIResponse(data=data)


@router.put("/{exam_id}/questions", response_model=APIResponse[ExamOut])
async def set_question_schema(
    exam_id: uuid.UUID,
    body: QuestionSchemaSet,
    current_user: CurrentUser = Depends(require_roles(*_STAFF)),
    db: AsyncSession = Depends(get_db),
):
    """Define per-question max marks + topic mapping (or import from an approved paper)."""
    await _scoped_exam(db, current_user, exam_id)
    service = ExamService(db)
    try:
        exam = await service.set_question_schema(uuid.UUID(current_user.school_id), exam_id, body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return APIResponse(data=ExamOut.from_exam(exam), message="Question schema saved")


@router.get("/{exam_id}/questions", response_model=APIResponse[list[QuestionDef]])
async def get_question_schema(
    exam_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_STAFF)),
    db: AsyncSession = Depends(get_db),
):
    exam = await _scoped_exam(db, current_user, exam_id)
    questions = [QuestionDef(**q) for q in (exam.question_schema or [])]
    return APIResponse(data=questions)


@router.post("/marks", response_model=APIResponse)
async def enter_marks(
    body: BulkMarkEntryRequest,
    current_user: CurrentUser = Depends(require_roles(*_STAFF)),
    db: AsyncSession = Depends(get_db),
):
    await _scoped_exam(db, current_user, body.exam_id)
    service = ExamService(db)
    try:
        count = await service.enter_marks(
            uuid.UUID(current_user.school_id), body.exam_id, body.entries
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return APIResponse(message=f"Marks entered for {count} students")


@router.get("/{exam_id}/marks", response_model=APIResponse[list[ExamMarkOut]])
async def get_marks(
    exam_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_STAFF)),
    db: AsyncSession = Depends(get_db),
):
    await _scoped_exam(db, current_user, exam_id)
    service = ExamService(db)
    marks = await service.get_exam_marks(uuid.UUID(current_user.school_id), exam_id)
    return APIResponse(data=[ExamMarkOut.model_validate(m) for m in marks])


router.include_router(evaluation_router)

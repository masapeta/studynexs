"""Examination endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_roles
from app.db.models.academic import Class
from app.db.models.examination import Exam, ExamMark
from app.modules.examinations.schemas.exam import (
    BulkMarkEntryRequest,
    ExamCreate,
    ExamMarkOut,
    ExamOut,
)
from app.modules.examinations.services.exam_service import ExamService
from app.shared.schemas.common import APIResponse

router = APIRouter()


@router.post("", response_model=APIResponse[ExamOut], status_code=201)
async def create_exam(
    body: ExamCreate,
    current_user: CurrentUser = Depends(require_roles("teacher", "class_incharge", "admin", "super_admin")),
    db: AsyncSession = Depends(get_db),
):
    service = ExamService(db)
    exam = await service.create_exam(uuid.UUID(current_user.school_id), body, uuid.UUID(current_user.id))
    return APIResponse(data=ExamOut.model_validate(exam), message="Exam created")


@router.get("", response_model=APIResponse[list[ExamOut]])
async def list_exams(
    class_id: uuid.UUID | None = None,
    current_user: CurrentUser = Depends(require_roles("teacher", "class_incharge", "admin", "super_admin")),
    db: AsyncSession = Depends(get_db),
):
    service = ExamService(db)
    exams = await service.list_exams(uuid.UUID(current_user.school_id), class_id)
    return APIResponse(data=[ExamOut.model_validate(e) for e in exams])


@router.get("/class-performance", response_model=APIResponse)
async def class_performance(
    limit: int = Query(5, ge=1, le=20),
    current_user: CurrentUser = Depends(require_roles("teacher", "class_incharge", "admin", "super_admin")),
    db: AsyncSession = Depends(get_db),
):
    """Top classes by overall average % across all exams — powers the dashboard card."""
    avg_pct = func.avg(ExamMark.marks_obtained / Exam.total_marks * 100)
    rows = (
        await db.execute(
            select(Class.grade, Class.section, avg_pct.label("pct"))
            .join(Exam, Exam.class_id == Class.id)
            .join(ExamMark, ExamMark.exam_id == Exam.id)
            .where(Class.school_id == uuid.UUID(current_user.school_id))
            .group_by(Class.id, Class.grade, Class.section)
            .order_by(avg_pct.desc())
            .limit(limit)
        )
    ).all()
    data = [
        {"label": f"{grade} - {section}", "percentage": round(float(pct or 0), 1)}
        for grade, section, pct in rows
    ]
    return APIResponse(data=data)


@router.post("/marks", response_model=APIResponse)
async def enter_marks(
    body: BulkMarkEntryRequest,
    current_user: CurrentUser = Depends(require_roles("teacher", "class_incharge", "admin", "super_admin")),
    db: AsyncSession = Depends(get_db),
):
    service = ExamService(db)
    count = await service.enter_marks(uuid.UUID(current_user.school_id), body.exam_id, body.entries)
    return APIResponse(message=f"Marks entered for {count} students")


@router.get("/{exam_id}/marks", response_model=APIResponse[list[ExamMarkOut]])
async def get_marks(
    exam_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles("teacher", "class_incharge", "admin", "super_admin")),
    db: AsyncSession = Depends(get_db),
):
    service = ExamService(db)
    marks = await service.get_exam_marks(uuid.UUID(current_user.school_id), exam_id)
    return APIResponse(data=[ExamMarkOut.model_validate(m) for m in marks])

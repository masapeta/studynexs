"""Answer sheet evaluation endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_route import CommitOnSuccessRoute
from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_roles
from app.core.rate_limit import rate_limit
from app.core.staff_permissions import (
    assert_exam_class,
    assert_exam_eval_access,
    assert_exams_access,
    get_staff_scope,
)
from app.core.tenant_scope import TenantScope
from app.db.models.examination import Exam
from app.db.models.school import School
from app.modules.examinations.schemas.evaluation import (
    CorrectionHistoryItem,
    EvaluationApprove,
    EvaluationCreate,
    EvaluationOut,
    MisconceptionOut,
)
from app.modules.examinations.services.answer_sheet_eval_service import (
    AnswerSheetEvalService,
    EvalError,
)
from app.modules.examinations.services.misconception_service import list_misconceptions
from app.shared.schemas.common import APIResponse

router = APIRouter(route_class=CommitOnSuccessRoute)
_STAFF = ("teacher", "class_incharge", "admin", "super_admin")
_EVAL_RATE = {"max_requests": 8, "window_seconds": 60}


def _subject_ids_for_list(scope, class_id: uuid.UUID | None) -> set[uuid.UUID] | None:
    """None = no subject filter (admin or class incharge for that class)."""
    if scope.is_admin:
        return None
    if class_id and scope.is_class_incharge(class_id):
        return None
    if class_id:
        return scope.subject_ids_for_class(class_id)
    if scope.teaching_pairs:
        return {sid for _, sid in scope.teaching_pairs}
    return set()


async def _load_school(db: AsyncSession, school_id: uuid.UUID) -> School:
    school = (await db.execute(select(School).where(School.id == school_id))).scalar_one_or_none()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    return school


async def _scoped_exam_for_eval(
    db: AsyncSession, current_user: CurrentUser, exam_id: uuid.UUID
) -> Exam:
    scope = await get_staff_scope(db, current_user)
    assert_exams_access(scope)
    exam = await TenantScope(db, uuid.UUID(current_user.school_id)).exam(exam_id)
    assert_exam_eval_access(scope, exam)
    return exam


@router.get("/corrections", response_model=APIResponse[list[CorrectionHistoryItem]])
async def list_corrections(
    class_id: uuid.UUID | None = None,
    exam_id: uuid.UUID | None = None,
    student_id: uuid.UUID | None = None,
    limit: int = Query(100, ge=1, le=500),
    current_user: CurrentUser = Depends(require_roles(*_STAFF)),
    db: AsyncSession = Depends(get_db),
):
    """Past approved AI corrections — AI suggestion vs teacher final marks."""
    scope = await get_staff_scope(db, current_user)
    assert_exams_access(scope)
    school_id = uuid.UUID(current_user.school_id)
    if exam_id:
        exam = await TenantScope(db, school_id).exam(exam_id)
        assert_exam_eval_access(scope, exam)
        class_id = class_id or exam.class_id
    elif class_id:
        assert_exam_class(scope, class_id)
    elif not scope.is_admin:
        raise HTTPException(status_code=400, detail="Select a class to view corrections")

    subject_ids = _subject_ids_for_list(scope, class_id)
    service = AnswerSheetEvalService(db)
    rows = await service.list_corrections_history(
        school_id,
        class_id=class_id,
        exam_id=exam_id,
        student_id=student_id,
        subject_ids=subject_ids,
        limit=limit,
    )
    return APIResponse(data=[CorrectionHistoryItem(**r) for r in rows])


@router.get("/misconceptions", response_model=APIResponse[list[MisconceptionOut]])
async def list_misconception_library(
    class_id: uuid.UUID | None = None,
    topic: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    current_user: CurrentUser = Depends(require_roles(*_STAFF)),
    db: AsyncSession = Depends(get_db),
):
    """School-private misconception library from past evaluations."""
    scope = await get_staff_scope(db, current_user)
    assert_exams_access(scope)
    school_id = uuid.UUID(current_user.school_id)
    if class_id:
        assert_exam_class(scope, class_id)
    elif not scope.is_admin:
        raise HTTPException(status_code=400, detail="Select a class to view misconceptions")

    subject_ids = _subject_ids_for_list(scope, class_id)
    rows = await list_misconceptions(
        db,
        school_id=school_id,
        class_id=class_id,
        topic=topic,
        subject_ids=subject_ids,
        limit=limit,
    )
    return APIResponse(data=[MisconceptionOut.model_validate(r) for r in rows])


@router.post(
    "/{exam_id}/evaluations",
    response_model=APIResponse[EvaluationOut],
    status_code=201,
    dependencies=[rate_limit("exam_eval", **_EVAL_RATE)],
)
async def create_evaluation(
    exam_id: uuid.UUID,
    body: EvaluationCreate,
    current_user: CurrentUser = Depends(require_roles(*_STAFF)),
    db: AsyncSession = Depends(get_db),
):
    exam = await _scoped_exam_for_eval(db, current_user, exam_id)
    school_id = uuid.UUID(current_user.school_id)
    school = await _load_school(db, school_id)
    service = AnswerSheetEvalService(db)
    try:
        row = await service.create_and_evaluate(
            school_id=school_id,
            exam_id=exam.id,
            student_id=body.student_id,
            created_by=uuid.UUID(current_user.id),
            role=current_user.role,
            school=school,
            file_id=body.file_id,
            student_answers=body.student_answers,
        )
    except EvalError as e:
        raise HTTPException(status_code=400, detail=str(e))
    msg = "Evaluation queued" if row.status == "processing" else "Evaluation complete"
    return APIResponse(data=EvaluationOut.model_validate(row), message=msg)


@router.get("/{exam_id}/evaluations", response_model=APIResponse[list[EvaluationOut]])
async def list_evaluations(
    exam_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_STAFF)),
    db: AsyncSession = Depends(get_db),
):
    await _scoped_exam_for_eval(db, current_user, exam_id)
    service = AnswerSheetEvalService(db)
    rows = await service.list_for_exam(uuid.UUID(current_user.school_id), exam_id)
    return APIResponse(data=[EvaluationOut.model_validate(r) for r in rows])


@router.get("/evaluations/{evaluation_id}", response_model=APIResponse[EvaluationOut])
async def get_evaluation(
    evaluation_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_STAFF)),
    db: AsyncSession = Depends(get_db),
):
    scope = await get_staff_scope(db, current_user)
    assert_exams_access(scope)
    service = AnswerSheetEvalService(db)
    row = await service.get_evaluation(uuid.UUID(current_user.school_id), evaluation_id)
    if not row:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    exam = await TenantScope(db, uuid.UUID(current_user.school_id)).exam(row.exam_id)
    assert_exam_eval_access(scope, exam)
    return APIResponse(data=EvaluationOut.model_validate(row))


@router.post(
    "/evaluations/{evaluation_id}/approve",
    response_model=APIResponse[EvaluationOut],
)
async def approve_evaluation(
    evaluation_id: uuid.UUID,
    body: EvaluationApprove,
    current_user: CurrentUser = Depends(require_roles(*_STAFF)),
    db: AsyncSession = Depends(get_db),
):
    scope = await get_staff_scope(db, current_user)
    assert_exams_access(scope)
    service = AnswerSheetEvalService(db)
    school_id = uuid.UUID(current_user.school_id)
    row = await service.get_evaluation(school_id, evaluation_id)
    if not row:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    exam = await TenantScope(db, school_id).exam(row.exam_id)
    assert_exam_eval_access(scope, exam)
    try:
        approved = await service.approve(
            school_id=school_id,
            evaluation_id=evaluation_id,
            data=body,
            approved_by=uuid.UUID(current_user.id),
        )
    except EvalError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return APIResponse(data=EvaluationOut.model_validate(approved), message="Marks approved")

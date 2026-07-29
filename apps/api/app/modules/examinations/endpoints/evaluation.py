"""Answer sheet evaluation endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_route import CommitOnSuccessRoute
from app.core.config import get_settings
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
from app.db.models.question_paper import QuestionPaper
from app.db.models.school import School
from app.modules.examinations.schemas.evaluation import (
    CorrectionHistoryItem,
    EvaluationApprove,
    EvaluationCreate,
    EvaluationOut,
    MisconceptionOut,
)
from app.modules.examinations.services.aei_activation_trust import (
    activation_trust_profile_enabled,
    build_activation_trust_evidence,
)
from app.modules.examinations.services.aei_v1_evidence_ledger import (
    build_approved_evidence_metadata,
)
from app.modules.examinations.services.answer_sheet_eval_service import (
    AnswerSheetEvalService,
    EvalError,
)
from app.modules.examinations.services.misconception_service import list_misconceptions
from app.shared.schemas.common import APIResponse

router = APIRouter(route_class=CommitOnSuccessRoute)
settings = get_settings()
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


def _citation_ids_from_suggestions(suggestions: dict | None) -> list[str]:
    refs: list[str] = []
    for suggestion in (suggestions or {}).values():
        if not isinstance(suggestion, dict):
            continue
        for source in suggestion.get("grounding_sources") or []:
            if isinstance(source, dict) and source.get("ref_id"):
                refs.append(str(source["ref_id"]))
        for citation in suggestion.get("citations") or []:
            refs.append(str(citation))
    return sorted(set(refs))


def _suggestions_are_grounded(suggestions: dict | None) -> bool:
    return any(
        isinstance(suggestion, dict)
        and bool(suggestion.get("grounded"))
        and bool(suggestion.get("grounding_sources"))
        for suggestion in (suggestions or {}).values()
    )


async def _question_paper_for_exam(
    db: AsyncSession, school_id: uuid.UUID, exam: Exam
) -> QuestionPaper | None:
    if not exam.source_paper_id:
        return None
    return (
        await db.execute(
            select(QuestionPaper).where(
                QuestionPaper.id == exam.source_paper_id,
                QuestionPaper.school_id == school_id,
            )
        )
    ).scalar_one_or_none()


async def _evaluation_out(
    db: AsyncSession,
    school_id: uuid.UUID,
    row,
    *,
    exam: Exam | None = None,
    paper: QuestionPaper | None = None,
) -> EvaluationOut:
    exam = exam or await TenantScope(db, school_id).exam(row.exam_id)
    paper = paper or await _question_paper_for_exam(db, school_id, exam)
    out = EvaluationOut.model_validate(row)
    out.question_paper_id = exam.source_paper_id
    out.curriculum_pack_id = paper.pack_id if paper else None
    out.question_paper_grounded = bool(paper and paper.grounded)
    out.evaluation_grounded = _suggestions_are_grounded(row.ai_suggestions)
    out.citation_ids = _citation_ids_from_suggestions(row.ai_suggestions)
    evidence_ledger = {
        "tenant_id": str(row.school_id),
        "curriculum_pack_id": str(paper.pack_id) if paper and paper.pack_id else None,
        "question_paper_id": str(exam.source_paper_id) if exam.source_paper_id else None,
        "exam_id": str(row.exam_id),
        "student_id": str(row.student_id),
        "answer_sheet_file_id": str(row.file_id) if row.file_id else None,
        "evaluation_id": str(row.id),
        "evaluation_status": row.status,
        "teacher_approved_by": str(row.approved_by) if row.approved_by else None,
        "teacher_approved_at": row.approved_at.isoformat() if row.approved_at else None,
        "question_paper_grounded": bool(paper and paper.grounded),
        "evaluation_grounded": _suggestions_are_grounded(row.ai_suggestions),
        "citation_ids": _citation_ids_from_suggestions(row.ai_suggestions),
    }
    if settings.AEI_V1_EVIDENCE_LEDGER_METADATA_ENABLED:
        evidence_ledger["aei_v1_approved_evidence"] = build_approved_evidence_metadata(
            evaluation_status=row.status,
            suggestions=row.ai_suggestions,
            teacher_overrides=row.teacher_overrides,
            approved_by=row.approved_by,
            approved_at=row.approved_at,
        )
    if activation_trust_profile_enabled(settings):
        evidence_ledger["aei_v1_activation_trust"] = build_activation_trust_evidence(
            suggestions=row.ai_suggestions,
            teacher_overrides=row.teacher_overrides,
            manual_review_acknowledgement_required=settings.AEI_V1_MANUAL_REVIEW_ACK_REQUIRED,
        )
    out.evidence_ledger = evidence_ledger
    return out


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
    return APIResponse(data=await _evaluation_out(db, school_id, row, exam=exam), message=msg)


@router.get("/{exam_id}/evaluations", response_model=APIResponse[list[EvaluationOut]])
async def list_evaluations(
    exam_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_STAFF)),
    db: AsyncSession = Depends(get_db),
):
    await _scoped_exam_for_eval(db, current_user, exam_id)
    service = AnswerSheetEvalService(db)
    rows = await service.list_for_exam(uuid.UUID(current_user.school_id), exam_id)
    school_id = uuid.UUID(current_user.school_id)
    exam = await TenantScope(db, school_id).exam(exam_id)
    paper = await _question_paper_for_exam(db, school_id, exam)
    return APIResponse(
        data=[await _evaluation_out(db, school_id, r, exam=exam, paper=paper) for r in rows]
    )


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
    school_id = uuid.UUID(current_user.school_id)
    return APIResponse(data=await _evaluation_out(db, school_id, row, exam=exam))


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
    return APIResponse(
        data=await _evaluation_out(db, school_id, approved, exam=exam),
        message="Marks approved",
    )

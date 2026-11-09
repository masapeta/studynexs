"""Exam submissions, evaluation reopen/revisions, and governed result release (plan §5.2–§5.3).

Authority (P-R1, P5, P12) lives in ``StaffScope`` and is re-checked inside the service at
execution time. ``school_id`` always comes from the authenticated user.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_route import CommitOnSuccessRoute
from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_roles
from app.core.rate_limit import rate_limit
from app.core.staff_permissions import (
    assert_exam_eval_access,
    assert_exams_access,
    get_staff_scope,
)
from app.core.tenant_scope import TenantScope
from app.db.models.answer_sheet_evaluation import AnswerSheetEvaluation, AnswerSheetPage
from app.db.models.exam_result import ExamResultPublished, ExamResultVersion
from app.db.models.examination import Exam
from app.db.models.student import Student, StudentStatus
from app.db.models.user import User
from app.modules.examinations.schemas.evaluation import (
    EvaluationOut,
    EvaluationReopen,
    RevisionOut,
)
from app.modules.examinations.schemas.exam import ExamOut
from app.modules.examinations.schemas.release import (
    GovernedReleaseActionIn,
    ReleaseConfirmIn,
    ReleaseConfirmOut,
    ReleaseEventOut,
    ReleasePreviewOut,
    ReleaseStateOut,
    SubmissionRow,
)
from app.modules.examinations.services.answer_sheet_eval_service import (
    AnswerSheetEvalService,
    EvalError,
)
from app.modules.examinations.services.release_service import (
    ReleaseError,
    ResultReleaseService,
)
from app.modules.examinations.services.result_version_service import latest_versions
from app.shared.schemas.common import APIResponse

router = APIRouter(route_class=CommitOnSuccessRoute)
_STAFF = ("teacher", "class_incharge", "admin", "super_admin")
_RELEASE_RATE = {"max_requests": 20, "window_seconds": 60}


def _release_error(exc: ReleaseError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "code": exc.code, **exc.extra},
    )


async def _exam_for_staff(
    db: AsyncSession, current_user: CurrentUser, exam_id: uuid.UUID
) -> tuple[Exam, object]:
    scope = await get_staff_scope(db, current_user)
    assert_exams_access(scope)
    exam = await TenantScope(db, uuid.UUID(current_user.school_id)).exam(exam_id)
    assert_exam_eval_access(scope, exam)
    return exam, scope


# ── Exam + submissions ──────────────────────────────────────────────────────────


@router.get("/{exam_id}", response_model=APIResponse[ExamOut])
async def get_exam(
    exam_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_STAFF)),
    db: AsyncSession = Depends(get_db),
):
    exam, _ = await _exam_for_staff(db, current_user, exam_id)
    return APIResponse(data=ExamOut.from_exam(exam))


@router.get("/{exam_id}/submissions", response_model=APIResponse[list[SubmissionRow]])
async def list_submissions(
    exam_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_STAFF)),
    db: AsyncSession = Depends(get_db),
):
    """Per-student evaluation state for an exam — available to the exam's subject teacher,
    who otherwise has no roster access (``/academic/students`` stays incharge-only)."""
    exam, _ = await _exam_for_staff(db, current_user, exam_id)
    school_id = uuid.UUID(current_user.school_id)
    students = (
        await db.execute(
            select(Student.id, User.full_name, Student.roll_no)
            .join(User, (User.id == Student.user_id) & (User.school_id == school_id))
            .where(
                Student.school_id == school_id,
                Student.class_id == exam.class_id,
                Student.status == StudentStatus.ACTIVE,
            )
            .order_by(Student.roll_no, User.full_name)
        )
    ).all()
    evals = {
        e.student_id: e
        for e in (
            await db.execute(
                select(AnswerSheetEvaluation).where(
                    AnswerSheetEvaluation.school_id == school_id,
                    AnswerSheetEvaluation.exam_id == exam.id,
                )
            )
        ).scalars().all()
    }
    page_counts: dict[uuid.UUID, int] = {}
    if evals:
        for eval_id, in (
            await db.execute(
                select(AnswerSheetPage.evaluation_id).where(
                    AnswerSheetPage.school_id == school_id,
                    AnswerSheetPage.evaluation_id.in_([e.id for e in evals.values()]),
                )
            )
        ).all():
            page_counts[eval_id] = page_counts.get(eval_id, 0) + 1
    latest = await latest_versions(db, school_id, exam.id)
    published = {
        p.student_id: p.result_version_id
        for p in (
            await db.execute(
                select(ExamResultPublished).where(
                    ExamResultPublished.school_id == school_id,
                    ExamResultPublished.exam_id == exam.id,
                )
            )
        ).scalars().all()
    }
    published_nos: dict[uuid.UUID, int] = {}
    if published:
        for vid, vno in (
            await db.execute(
                select(ExamResultVersion.id, ExamResultVersion.version_no).where(
                    ExamResultVersion.school_id == school_id,
                    ExamResultVersion.id.in_(list(published.values())),
                )
            )
        ).all():
            published_nos[vid] = vno
    rows: list[SubmissionRow] = []
    for sid, name, roll in students:
        ev = evals.get(sid)
        version = latest.get(sid)
        pub_vid = published.get(sid)
        pages = page_counts.get(ev.id, 0) if ev else 0
        if ev and not pages and ev.file_id:
            pages = 1
        rows.append(
            SubmissionRow(
                student_id=sid,
                student_name=name,
                roll_no=roll,
                status=ev.status if ev else ("approved" if version else "not_submitted"),
                evaluation_id=ev.id if ev else None,
                page_count=pages,
                latest_version_no=version.version_no if version else None,
                published_version_no=published_nos.get(pub_vid) if pub_vid else None,
                changed_since_release=bool(pub_vid and version and version.id != pub_vid),
            )
        )
    return APIResponse(data=rows)


# ── Evaluation reopen + revisions ───────────────────────────────────────────────


@router.post("/evaluations/{evaluation_id}/reopen", response_model=APIResponse[EvaluationOut])
async def reopen_evaluation(
    evaluation_id: uuid.UUID,
    body: EvaluationReopen,
    current_user: CurrentUser = Depends(require_roles(*_STAFF)),
    db: AsyncSession = Depends(get_db),
):
    school_id = uuid.UUID(current_user.school_id)
    scope = await get_staff_scope(db, current_user)
    assert_exams_access(scope)
    service = AnswerSheetEvalService(db)
    row = await service.get_evaluation(school_id, evaluation_id)
    if not row:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    exam = await TenantScope(db, school_id).exam(row.exam_id)
    if not scope.can_reopen_evaluation(exam):
        raise HTTPException(
            status_code=403, detail="Only the class incharge or an administrator can reopen"
        )
    try:
        row = await service.reopen(
            school_id=school_id,
            evaluation_id=evaluation_id,
            actor_id=uuid.UUID(current_user.id),
            reason=body.reason,
        )
    except EvalError as e:
        raise HTTPException(status_code=400, detail=str(e))
    out = EvaluationOut.model_validate(row)
    out.page_file_ids = await service.page_file_ids(row)
    return APIResponse(data=out, message="Evaluation reopened for review")


@router.get(
    "/evaluations/{evaluation_id}/revisions", response_model=APIResponse[list[RevisionOut]]
)
async def list_evaluation_revisions(
    evaluation_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_STAFF)),
    db: AsyncSession = Depends(get_db),
):
    school_id = uuid.UUID(current_user.school_id)
    scope = await get_staff_scope(db, current_user)
    assert_exams_access(scope)
    service = AnswerSheetEvalService(db)
    row = await service.get_evaluation(school_id, evaluation_id)
    if not row:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    exam = await TenantScope(db, school_id).exam(row.exam_id)
    assert_exam_eval_access(scope, exam)
    revisions = await service.list_revisions(school_id, evaluation_id)
    return APIResponse(data=[RevisionOut.model_validate(r) for r in revisions])


# ── Release ─────────────────────────────────────────────────────────────────────


@router.get("/{exam_id}/release", response_model=APIResponse[ReleaseStateOut])
async def get_release_state(
    exam_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_STAFF)),
    db: AsyncSession = Depends(get_db),
):
    exam, scope = await _exam_for_staff(db, current_user, exam_id)
    state = await ResultReleaseService(db).get_state(uuid.UUID(current_user.school_id), exam)
    return APIResponse(
        data=ReleaseStateOut(
            **{k: v for k, v in state.items() if k != "history"},
            can_release=scope.can_release_results(exam),
            can_withdraw=scope.can_withdraw_results(exam),
            can_override=scope.can_override_release(exam),
            history=[ReleaseEventOut.model_validate(h) for h in state["history"]],
        )
    )


@router.post(
    "/{exam_id}/release/preview",
    response_model=APIResponse[ReleasePreviewOut],
    dependencies=[rate_limit("exam_release", **_RELEASE_RATE)],
)
async def preview_release(
    exam_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles("class_incharge", "teacher", "super_admin")),
    db: AsyncSession = Depends(get_db),
):
    exam, scope = await _exam_for_staff(db, current_user, exam_id)
    try:
        data = await ResultReleaseService(db).preview(
            school_id=uuid.UUID(current_user.school_id), exam=exam, scope=scope
        )
    except ReleaseError as exc:
        return _release_error(exc)
    return APIResponse(data=ReleasePreviewOut(**data))


@router.post(
    "/{exam_id}/release/confirm",
    response_model=APIResponse[ReleaseConfirmOut],
    dependencies=[rate_limit("exam_release", **_RELEASE_RATE)],
)
async def confirm_release(
    exam_id: uuid.UUID,
    body: ReleaseConfirmIn,
    current_user: CurrentUser = Depends(require_roles("class_incharge", "teacher", "super_admin")),
    db: AsyncSession = Depends(get_db),
):
    exam, scope = await _exam_for_staff(db, current_user, exam_id)
    try:
        outcome = await ResultReleaseService(db).confirm(
            school_id=uuid.UUID(current_user.school_id),
            exam=exam,
            scope=scope,
            preview_token=body.preview_token,
            confirm_partial=body.confirm_partial,
            acknowledged_pending_count=body.acknowledged_pending_count,
        )
    except ReleaseError as exc:
        return _release_error(exc)
    if outcome.no_changes:
        return APIResponse(
            data=ReleaseConfirmOut(no_changes=True),
            message="Nothing new to release — every eligible result is already published.",
        )
    return APIResponse(
        data=ReleaseConfirmOut(
            replayed=outcome.replayed,
            release=ReleaseEventOut.model_validate(outcome.release),
        ),
        message=(
            "Already released"
            if outcome.replayed
            else f"Results released (generation {outcome.release.generation_no})"
        ),
    )


async def _governed(
    action: str,
    exam_id: uuid.UUID,
    body: GovernedReleaseActionIn,
    current_user: CurrentUser,
    db: AsyncSession,
):
    exam, scope = await _exam_for_staff(db, current_user, exam_id)
    service = ResultReleaseService(db)
    fn = {"withdraw": service.withdraw, "block": service.block, "unblock": service.unblock}[action]
    try:
        event, created = await fn(
            school_id=uuid.UUID(current_user.school_id),
            exam=exam,
            scope=scope,
            reason=body.reason,
            action_token=body.action_token,
        )
    except ReleaseError as exc:
        return _release_error(exc)
    return APIResponse(
        data=ReleaseEventOut.model_validate(event),
        message={"withdraw": "Results withdrawn", "block": "Results blocked",
                 "unblock": "Results unblocked"}[action] + ("" if created else " (already done)"),
    )


@router.post("/{exam_id}/release/withdraw", response_model=APIResponse[ReleaseEventOut])
async def withdraw_release(
    exam_id: uuid.UUID,
    body: GovernedReleaseActionIn,
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin")),
    db: AsyncSession = Depends(get_db),
):
    return await _governed("withdraw", exam_id, body, current_user, db)


@router.post("/{exam_id}/release/block", response_model=APIResponse[ReleaseEventOut])
async def block_release(
    exam_id: uuid.UUID,
    body: GovernedReleaseActionIn,
    current_user: CurrentUser = Depends(require_roles(*_STAFF)),
    db: AsyncSession = Depends(get_db),
):
    # Role gate intentionally broad so non-principals get an explicit 403 from the service.
    return await _governed("block", exam_id, body, current_user, db)


@router.post("/{exam_id}/release/unblock", response_model=APIResponse[ReleaseEventOut])
async def unblock_release(
    exam_id: uuid.UUID,
    body: GovernedReleaseActionIn,
    current_user: CurrentUser = Depends(require_roles(*_STAFF)),
    db: AsyncSession = Depends(get_db),
):
    return await _governed("unblock", exam_id, body, current_user, db)

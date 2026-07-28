"""AI module endpoints — status + the Teacher-AI question-paper flow.

Phase-1 hero: generate a board-style question paper from syllabus topics, let the
teacher edit and APPROVE it (human-in-the-loop), then export. Tutor/grading/etc. come later.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.api_route import CommitOnSuccessRoute
from app.core.authorization import get_student_in_school
from app.core.config import get_settings
from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_roles
from app.core.rate_limit import rate_limit
from app.core.staff_permissions import (
    StaffScope,
    assert_qp_approve,
    assert_qp_download,
    assert_qp_edit,
    assert_qp_generate,
    assert_report_cards,
    get_staff_scope,
)
from app.db.models.ai_usage import AIUsage
from app.db.models.question_bank import QuestionBankItem
from app.db.models.question_paper import PaperStatus, QuestionPaper
from app.db.models.report_card import ReportCard, ReportStatus
from app.db.models.school import School
from app.modules.ai.gateway.errors import raise_http_for_llm_error
from app.modules.ai.schemas.credits import (
    CreditStatusOut,
    OverrideRequest,
    SchoolAIReportOut,
    UsageLogEntry,
    UsageLogOut,
)
from app.modules.ai.schemas.question_paper import (
    BankItemConceptsOut,
    BankSummaryOut,
    DuplicatePaperRequest,
    GenerateRequest,
    QuestionPaperOut,
    RejectPaperRequest,
    UpdatePaperRequest,
)
from app.modules.ai.schemas.report_card import (
    GenerateReportRequest,
    ReportCardOut,
    UpdateReportRequest,
)
from app.modules.ai.schemas.teacher_copilot import (
    CopilotFeedbackOut,
    CopilotFeedbackRequest,
    CopilotPaperReviewOut,
    CopilotSuggestionOut,
)
from app.modules.ai.services.ai_credits import (
    get_credit_status,
    get_school_ai_budget,
    month_start_for_school,
    set_principal_override,
)
from app.modules.ai.services.paper_pdf import generate_paper_pdf
from app.modules.ai.services.question_bank_service import (
    BankIngestError,
    count_compose_candidates,
    ingest_from_paper,
)
from app.modules.ai.services.question_paper_service import (
    duplicate_paper,
    generate_paper,
    generate_paper_from_bank,
)
from app.modules.ai.services.report_card_pdf import generate_report_pdf
from app.modules.ai.services.report_card_service import generate_report_for_student
from app.modules.ai.services.teacher_copilot_service import TeacherCopilotService
from app.modules.ai.services.telemetry_summary import db_telemetry_summary, school_month_telemetry
from app.modules.ai.services.usage_caps import enforce_monthly_ai_cap
from app.modules.ai.services.usage_log import list_question_paper_usage_log
from app.modules.ai.telemetry import ai_metrics, bind_ai_context
from app.modules.curriculum.schemas.provenance import provenance_from_sources
from app.modules.knowledge_graph.services.question_concept_link_service import (
    QuestionConceptLinkService,
)
from app.shared.schemas.common import APIResponse

settings = get_settings()
router = APIRouter(route_class=CommitOnSuccessRoute)

_TEACH_ROLES = ("teacher", "class_incharge", "admin", "super_admin")


@router.get("/health")
async def ai_health(
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin")),
) -> dict:
    """AI module status + which providers have API keys configured (booleans only)."""
    return {
        "status": "ok",
        "module": "ai",
        "default_provider": settings.AI_DEFAULT_PROVIDER,
        "fallback_provider": (settings.AI_FALLBACK_PROVIDER or "").strip() or None,
        "providers_configured": {
            "gemini": bool(settings.GEMINI_API_KEY),
            "anthropic": bool(settings.ANTHROPIC_API_KEY),
            "openai": bool(settings.OPENAI_API_KEY),
            "ollama": bool((settings.OLLAMA_BASE_URL or "").strip()),
        },
    }


@router.get("/telemetry")
async def ai_telemetry(
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin")),
    db: AsyncSession = Depends(get_db),
    scope: str = "month",
) -> dict:
    """AI telemetry snapshot — in-process metrics + persisted usage rollups."""
    school_id = uuid.UUID(current_user.school_id)
    bind_ai_context(
        school_id=current_user.school_id,
        user_id=current_user.id,
        feature="telemetry",
    )
    if scope == "all":
        db_summary = await db_telemetry_summary(db, school_id=school_id)
    else:
        db_summary = await school_month_telemetry(db, school_id)
    return {
        "status": "ok",
        "runtime": ai_metrics.snapshot(),
        "database": db_summary,
    }


# Conservative estimates of manual time saved per AI-assisted artifact.
_MINUTES_SAVED_PER_PAPER = 45
_MINUTES_SAVED_PER_REPORT = 10

# Cost guardrails for the LLM-backed generation endpoints. The monthly cap lives
# in usage_caps so every LLM feature (papers, reports, mastery narratives) shares
# one budget.
_AI_GEN_RATE = {"max_requests": 12, "window_seconds": 60}  # per (school, user)
_enforce_monthly_cap = enforce_monthly_ai_cap


@router.get("/usage")
async def ai_usage_summary(
    current_user: CurrentUser = Depends(require_roles(*_TEACH_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """AI value summary — school-wide for admins/incharges, own papers for subject teachers."""
    scope = await get_staff_scope(db, current_user)
    school_id = uuid.UUID(current_user.school_id)
    user_id = uuid.UUID(current_user.id)
    school = (await db.execute(select(School).where(School.id == school_id))).scalar_one()
    billing_month_start = month_start_for_school(school)
    scoped_user = not scope.is_admin and not scope.incharge_class_ids

    def _base(feature: str):
        q = (
            select(func.count())
            .select_from(AIUsage)
            .where(AIUsage.school_id == school_id, AIUsage.feature == feature)
        )
        if scoped_user:
            q = q.where(AIUsage.created_by == user_id)
        return q

    papers_total = await db.scalar(_base("question_paper")) or 0
    papers_month = (
        await db.scalar(_base("question_paper").where(AIUsage.created_at >= billing_month_start))
        or 0
    )
    reports_total = await db.scalar(_base("report_card")) or 0
    reports_month = (
        await db.scalar(_base("report_card").where(AIUsage.created_at >= billing_month_start)) or 0
    )
    if scoped_user:
        reports_total = 0
        reports_month = 0
    est_hours = round(
        (papers_total * _MINUTES_SAVED_PER_PAPER + reports_total * _MINUTES_SAVED_PER_REPORT) / 60,
        1,
    )
    return {
        "papers_total": papers_total,
        "papers_this_month": papers_month,
        "reports_total": reports_total,
        "reports_this_month": reports_month,
        "est_hours_saved": est_hours,
    }


@router.get("/credits", response_model=CreditStatusOut)
async def ai_credit_status(
    current_user: CurrentUser = Depends(require_roles(*_TEACH_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> CreditStatusOut:
    """Credits remaining for the caller — schools see credits, not provider cost."""
    school = (
        await db.execute(select(School).where(School.id == uuid.UUID(current_user.school_id)))
    ).scalar_one()
    status_row = await get_credit_status(
        db, school, user_id=uuid.UUID(current_user.id), role=current_user.role
    )
    billing_month_start = month_start_for_school(school)
    papers_month = (
        await db.scalar(
            select(func.count())
            .select_from(AIUsage)
            .where(
                AIUsage.school_id == school.id,
                AIUsage.feature == "question_paper",
                AIUsage.created_at >= billing_month_start,
            )
        )
        or 0
    )
    est_hours = round(
        (status_row.usage_counts.get("qp_full", 0) * _MINUTES_SAVED_PER_PAPER) / 60, 1
    )
    data = status_row.to_dict()
    data["papers_this_month"] = int(papers_month)
    data["est_hours_saved"] = est_hours
    return CreditStatusOut(**data)


@router.get("/credits/school-report", response_model=SchoolAIReportOut)
async def ai_school_report(
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin")),
    db: AsyncSession = Depends(get_db),
) -> SchoolAIReportOut:
    """Principal/admin monthly AI usage — value metrics + credit burn."""
    school = (
        await db.execute(select(School).where(School.id == uuid.UUID(current_user.school_id)))
    ).scalar_one()
    budget = get_school_ai_budget(school)
    status_row = await get_credit_status(
        db, school, user_id=uuid.UUID(current_user.id), role=current_user.role
    )
    billing_month_start = month_start_for_school(school)
    papers_total = (
        await db.scalar(
            select(func.count())
            .select_from(AIUsage)
            .where(AIUsage.school_id == school.id, AIUsage.feature == "question_paper")
        )
        or 0
    )
    papers_month = (
        await db.scalar(
            select(func.count())
            .select_from(AIUsage)
            .where(
                AIUsage.school_id == school.id,
                AIUsage.feature == "question_paper",
                AIUsage.created_at >= billing_month_start,
            )
        )
        or 0
    )
    reports_month = (
        await db.scalar(
            select(func.count())
            .select_from(AIUsage)
            .where(
                AIUsage.school_id == school.id,
                AIUsage.feature == "report_card",
                AIUsage.created_at >= billing_month_start,
            )
        )
        or 0
    )
    est_hours = round(
        (papers_total * _MINUTES_SAVED_PER_PAPER + reports_month * _MINUTES_SAVED_PER_REPORT) / 60,
        1,
    )
    return SchoolAIReportOut(
        monthly_limit=status_row.monthly_limit,
        credits_used=status_row.credits_used,
        credits_remaining=status_row.credits_remaining,
        at_soft_limit=status_row.at_soft_limit,
        at_hard_limit=status_row.at_hard_limit,
        override_active=status_row.override_active,
        usage_counts=status_row.usage_counts,
        papers_total=int(papers_total),
        papers_this_month=int(papers_month),
        reports_this_month=int(reports_month),
        est_hours_saved=est_hours,
        plan=str(budget.get("plan") or "pilot"),
    )


@router.get("/credits/usage-log", response_model=UsageLogOut)
async def ai_usage_log(
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin")),
    db: AsyncSession = Depends(get_db),
) -> UsageLogOut:
    """Principal/admin log — credits charged at generation vs current approval status."""
    school_id = uuid.UUID(current_user.school_id)
    school = (await db.execute(select(School).where(School.id == school_id))).scalar_one()
    billing_month_start = month_start_for_school(school)
    rows = await list_question_paper_usage_log(db, school_id, since=billing_month_start)
    return UsageLogOut(items=[UsageLogEntry(**r) for r in rows])


@router.post("/credits/override", response_model=APIResponse)
async def ai_emergency_override(
    body: OverrideRequest,
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin")),
    db: AsyncSession = Depends(get_db),
):
    """Principal emergency override — unblocks generation until override expires."""
    school = (
        await db.execute(select(School).where(School.id == uuid.UUID(current_user.school_id)))
    ).scalar_one()
    budget = await set_principal_override(db, school, hours=body.hours)
    await db.commit()
    return APIResponse(
        message=f"AI override active until {budget.get('override_until')}",
        data={"override_until": budget.get("override_until")},
    )


def _to_out(
    p: QuestionPaper,
    scope: StaffScope | None = None,
    *,
    credits_used: int | None = None,
) -> QuestionPaperOut:
    can_edit = scope.can_edit_question_paper(p) if scope else True
    can_approve = scope.can_approve_question_paper(p) if scope else True
    can_submit = scope.can_submit_question_paper(p) if scope else False
    can_reject = scope.can_reject_question_paper(p) if scope else False
    prov = provenance_from_sources(
        p.grounding_sources,
        pack_id=str(p.pack_id) if p.pack_id else None,
        grounded=bool(p.grounded),
        created_at=p.created_at,
    )
    grounded_at = p.created_at.date() if p.grounded and p.created_at else None
    return QuestionPaperOut(
        id=p.id,
        title=p.title,
        board=p.board,
        grade=p.grade,
        subject_name=p.subject_name,
        total_marks=float(p.total_marks),
        duration_minutes=p.duration_minutes,
        general_instructions=p.general_instructions,
        topics=p.topics,
        difficulty_mix=p.difficulty_mix,
        sections=p.sections or [],
        status=p.status.value,
        ai_model=p.ai_model,
        created_by=p.created_by,
        pack_id=p.pack_id,
        pack_status=prov.get("pack_status"),
        pack_version=prov.get("pack_version"),
        grounded=p.grounded,
        grounding_sources=p.grounding_sources,
        grounded_at=grounded_at,
        can_approve=can_approve,
        can_edit=can_edit,
        can_submit=can_submit,
        can_reject=can_reject,
        rejection_reason=p.rejection_reason,
        credits_used=credits_used,
    )


async def _credits_by_paper_ids(
    db: AsyncSession, paper_ids: list[uuid.UUID]
) -> dict[uuid.UUID, int]:
    if not paper_ids:
        return {}
    rows = (
        await db.execute(
            select(AIUsage.ref_id, func.coalesce(func.sum(AIUsage.credits_charged), 0))
            .where(
                AIUsage.ref_type == "question_paper",
                AIUsage.ref_id.in_(paper_ids),
            )
            .group_by(AIUsage.ref_id)
        )
    ).all()
    return {rid: int(total) for rid, total in rows if rid}


async def _to_out_async(
    db: AsyncSession, paper: QuestionPaper, scope: StaffScope | None
) -> QuestionPaperOut:
    credits_map = await _credits_by_paper_ids(db, [paper.id])
    return _to_out(paper, scope, credits_used=credits_map.get(paper.id))


def _paper_visibility_filter(scope: StaffScope):
    """SQLAlchemy filter for question papers visible to scoped staff."""
    if scope.is_admin:
        return None
    clauses = []
    if scope.incharge_class_ids:
        clauses.append(QuestionPaper.class_id.in_(scope.incharge_class_ids))
    clauses.append(QuestionPaper.created_by == scope.user_id)
    for class_id, subject_id in scope.teaching_pairs:
        clauses.append(
            and_(
                QuestionPaper.class_id == class_id,
                QuestionPaper.subject_id == subject_id,
                or_(
                    QuestionPaper.created_by == scope.user_id,
                    QuestionPaper.status == PaperStatus.APPROVED,
                ),
            )
        )
    return or_(*clauses) if clauses else QuestionPaper.id.is_(None)


def _report_visibility_filter(scope: StaffScope):
    if scope.is_admin:
        return None
    if scope.incharge_class_ids:
        return ReportCard.class_id.in_(scope.incharge_class_ids)
    return ReportCard.id.is_(None)


async def _get_owned_paper(db: AsyncSession, school_id: str, paper_id: uuid.UUID) -> QuestionPaper:
    paper = (
        await db.execute(
            select(QuestionPaper).where(
                QuestionPaper.id == paper_id,
                QuestionPaper.school_id == uuid.UUID(school_id),
            )
        )
    ).scalar_one_or_none()
    if paper is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Question paper not found"
        )
    return paper


@router.post(
    "/question-papers/generate",
    response_model=QuestionPaperOut,
    dependencies=[rate_limit("ai_generate", **_AI_GEN_RATE)],
)
async def generate_question_paper(
    body: GenerateRequest,
    current_user: CurrentUser = Depends(require_roles(*_TEACH_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> QuestionPaperOut:
    """Generate a DRAFT paper. With a ``pack_id`` it is grounded in the approved CurriculumPack
    (every question cited); otherwise it falls back to free-text topics. Teacher reviews + approves
    before use — AI never publishes."""
    bind_ai_context(
        school_id=current_user.school_id,
        user_id=current_user.id,
        feature="question_paper",
    )
    scope = await get_staff_scope(db, current_user)
    assert_qp_generate(scope, body.class_id, body.subject_id)
    credits = await _enforce_monthly_cap(
        db,
        uuid.UUID(current_user.school_id),
        user_id=uuid.UUID(current_user.id),
        role=current_user.role,
        feature="question_paper",
        purpose_tag="qp_full",
    )
    try:
        paper = await generate_paper(
            db,
            school_id=uuid.UUID(current_user.school_id),
            created_by=uuid.UUID(current_user.id),
            class_id=body.class_id,
            subject_id=body.subject_id,
            topics=body.topics,
            total_marks=body.total_marks,
            duration_minutes=body.duration_minutes,
            difficulty=body.difficulty,
            title=body.title,
            role=current_user.role,
            purpose_tag="qp_full",
            credits_charged=credits,
            pack_id=body.pack_id,
        )
    except Exception as exc:
        raise_http_for_llm_error(
            exc,
            log_event="question_paper_generate_failed",
            timeout_detail=(
                "AI generation timed out. Please try again — large papers can take up to 2 minutes."
            ),
            generic_detail="AI paper generation failed. Please try again later.",
        )
    return _to_out(paper, scope, credits_used=credits)


@router.get("/question-bank/summary", response_model=BankSummaryOut)
async def question_bank_summary(
    class_id: uuid.UUID,
    subject_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_TEACH_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> BankSummaryOut:
    """How many approved bank items exist for compose-from-bank generation."""
    scope = await get_staff_scope(db, current_user)
    assert_qp_generate(scope, class_id, subject_id)
    school_id = uuid.UUID(current_user.school_id)
    count = await count_compose_candidates(
        db, school_id=school_id, class_id=class_id, subject_id=subject_id
    )
    return BankSummaryOut(count=count, class_id=class_id, subject_id=subject_id)


@router.get(
    "/question-bank/items/{item_id}/concepts",
    response_model=APIResponse[BankItemConceptsOut],
)
async def question_bank_item_concepts(
    item_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_TEACH_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[BankItemConceptsOut]:
    """Concepts linked to an approved question bank item (Knowledge Graph TESTS edges)."""
    school_id = uuid.UUID(current_user.school_id)
    item = (
        await db.execute(
            select(QuestionBankItem).where(
                QuestionBankItem.id == item_id,
                QuestionBankItem.school_id == school_id,
            )
        )
    ).scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bank item not found")

    scope = await get_staff_scope(db, current_user)
    assert_qp_generate(scope, item.class_id, item.subject_id)

    linker = QuestionConceptLinkService(db)
    concepts = await linker.get_concepts_for_item(school_id=school_id, item_id=item_id)
    return APIResponse(
        data=BankItemConceptsOut(
            item_id=item_id,
            concepts=concepts,
        )
    )


@router.post(
    "/question-papers/generate-from-bank",
    response_model=QuestionPaperOut,
    dependencies=[rate_limit("ai_generate", **_AI_GEN_RATE)],
)
async def generate_question_paper_from_bank(
    body: GenerateRequest,
    current_user: CurrentUser = Depends(require_roles(*_TEACH_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> QuestionPaperOut:
    """Compose a DRAFT from the school question bank; LLM fills only missing blueprint slots."""
    bind_ai_context(
        school_id=current_user.school_id,
        user_id=current_user.id,
        feature="question_paper",
    )
    scope = await get_staff_scope(db, current_user)
    assert_qp_generate(scope, body.class_id, body.subject_id)
    credits = await _enforce_monthly_cap(
        db,
        uuid.UUID(current_user.school_id),
        user_id=uuid.UUID(current_user.id),
        role=current_user.role,
        feature="question_paper",
        purpose_tag="qp_from_bank",
    )
    try:
        paper = await generate_paper_from_bank(
            db,
            school_id=uuid.UUID(current_user.school_id),
            created_by=uuid.UUID(current_user.id),
            class_id=body.class_id,
            subject_id=body.subject_id,
            topics=body.topics,
            total_marks=body.total_marks,
            duration_minutes=body.duration_minutes,
            difficulty=body.difficulty,
            title=body.title,
            role=current_user.role,
            purpose_tag="qp_from_bank",
            credits_charged=credits,
        )
    except Exception as exc:
        raise_http_for_llm_error(
            exc,
            log_event="question_paper_from_bank_failed",
            timeout_detail="AI generation timed out. Please try again.",
            generic_detail="AI paper generation failed. Please try again later.",
        )
    return _to_out(paper, scope, credits_used=credits)


@router.get("/question-papers", response_model=list[QuestionPaperOut])
async def list_question_papers(
    class_id: uuid.UUID | None = None,
    current_user: CurrentUser = Depends(require_roles(*_TEACH_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> list[QuestionPaperOut]:
    scope = await get_staff_scope(db, current_user)
    q = select(QuestionPaper).where(QuestionPaper.school_id == uuid.UUID(current_user.school_id))
    vis = _paper_visibility_filter(scope)
    if vis is not None:
        q = q.where(vis)
    if class_id:
        q = q.where(QuestionPaper.class_id == class_id)
    q = q.order_by(QuestionPaper.created_at.desc()).limit(50)
    rows = (await db.execute(q)).scalars().all()
    credits_map = await _credits_by_paper_ids(db, [p.id for p in rows])
    return [_to_out(p, scope, credits_used=credits_map.get(p.id)) for p in rows]


@router.get("/question-papers/{paper_id}", response_model=QuestionPaperOut)
async def get_question_paper(
    paper_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_TEACH_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> QuestionPaperOut:
    scope = await get_staff_scope(db, current_user)
    paper = await _get_owned_paper(db, current_user.school_id, paper_id)
    assert_qp_download(scope, paper)
    return await _to_out_async(db, paper, scope)


@router.put("/question-papers/{paper_id}", response_model=QuestionPaperOut)
async def edit_question_paper(
    paper_id: uuid.UUID,
    body: UpdatePaperRequest,
    current_user: CurrentUser = Depends(require_roles(*_TEACH_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> QuestionPaperOut:
    """Teacher edits (title/instructions/sections) before approval."""
    scope = await get_staff_scope(db, current_user)
    paper = await _get_owned_paper(db, current_user.school_id, paper_id)
    assert_qp_edit(scope, paper)
    if body.title is not None:
        paper.title = body.title
    if body.general_instructions is not None:
        paper.general_instructions = body.general_instructions
    if body.sections is not None:
        paper.sections = [s.model_dump(exclude_none=True) for s in body.sections]
    if paper.status in (PaperStatus.DRAFT, PaperStatus.REJECTED):
        paper.status = PaperStatus.EDITED
        paper.rejection_reason = None
        paper.rejected_by = None
        paper.rejected_at = None
    await db.flush()
    return await _to_out_async(db, paper, scope)


@router.post(
    "/question-papers/{paper_id}/duplicate",
    response_model=QuestionPaperOut,
    status_code=status.HTTP_201_CREATED,
)
async def duplicate_question_paper(
    paper_id: uuid.UUID,
    body: DuplicatePaperRequest,
    current_user: CurrentUser = Depends(require_roles(*_TEACH_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> QuestionPaperOut:
    """Clone a paper into a fresh editable DRAFT owned by the caller — no LLM call and no
    AI-usage recorded. Optionally re-target to another class (subject_id required if class_id
    changes). Deliberately NOT param-keyed caching: this is an explicit, owned, re-reviewable
    copy, never a silent identical paper handed to two classes."""
    scope = await get_staff_scope(db, current_user)
    source = await _get_owned_paper(db, current_user.school_id, paper_id)
    assert_qp_download(scope, source)
    target_class = body.class_id or source.class_id
    target_subject = body.subject_id or source.subject_id
    assert_qp_generate(scope, target_class, target_subject)
    try:
        clone = await duplicate_paper(
            db,
            source=source,
            created_by=uuid.UUID(current_user.id),
            title=body.title,
            class_id=body.class_id,
            subject_id=body.subject_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return _to_out(clone, scope, credits_used=0)


@router.post("/question-papers/{paper_id}/submit", response_model=QuestionPaperOut)
async def submit_question_paper(
    paper_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_TEACH_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> QuestionPaperOut:
    """Subject teacher submits draft for class-incharge / HOD approval."""
    scope = await get_staff_scope(db, current_user)
    paper = await _get_owned_paper(db, current_user.school_id, paper_id)
    if not scope.can_submit_question_paper(paper):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Cannot submit this paper"
        )
    paper.status = PaperStatus.PENDING_APPROVAL
    paper.submitted_at = datetime.now(timezone.utc)
    paper.rejection_reason = None
    paper.rejected_by = None
    paper.rejected_at = None
    await db.flush()
    return await _to_out_async(db, paper, scope)


@router.post("/question-papers/{paper_id}/approve", response_model=QuestionPaperOut)
async def approve_question_paper(
    paper_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_TEACH_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> QuestionPaperOut:
    """Class incharge (or admin) approves — credits were already charged at generation."""
    scope = await get_staff_scope(db, current_user)
    paper = await _get_owned_paper(db, current_user.school_id, paper_id)
    assert_qp_approve(scope, paper)
    approved_by = uuid.UUID(current_user.id)
    approved_at = datetime.now(timezone.utc)
    try:
        await ingest_from_paper(
            db,
            paper,
            approved_by=approved_by,
            approved_at=approved_at,
        )
    except BankIngestError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    paper.status = PaperStatus.APPROVED
    paper.approved_by = approved_by
    paper.approved_at = approved_at
    paper.rejection_reason = None
    paper.rejected_by = None
    paper.rejected_at = None
    await db.flush()
    return await _to_out_async(db, paper, scope)


@router.post("/question-papers/{paper_id}/reject", response_model=QuestionPaperOut)
async def reject_question_paper(
    paper_id: uuid.UUID,
    body: RejectPaperRequest,
    current_user: CurrentUser = Depends(require_roles(*_TEACH_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> QuestionPaperOut:
    """Class incharge rejects — credits already consumed at generation.

    Paper kept as audit + salvage asset: editable, clonable, resubmittable; bank ingest only
    on (re-)approve."""
    scope = await get_staff_scope(db, current_user)
    paper = await _get_owned_paper(db, current_user.school_id, paper_id)
    if not scope.can_reject_question_paper(paper):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Cannot reject this paper"
        )
    paper.status = PaperStatus.REJECTED
    paper.rejected_by = uuid.UUID(current_user.id)
    paper.rejected_at = datetime.now(timezone.utc)
    paper.rejection_reason = body.reason.strip()
    paper.approved_by = None
    paper.approved_at = None
    await db.flush()
    return await _to_out_async(db, paper, scope)


@router.get("/question-papers/{paper_id}/pdf")
async def download_question_paper(
    paper_id: uuid.UUID,
    answers: bool = False,
    current_user: CurrentUser = Depends(require_roles(*_TEACH_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Render a paper PDF; ``answers=true`` returns the teacher-only answer key."""
    scope = await get_staff_scope(db, current_user)
    paper = await _get_owned_paper(db, current_user.school_id, paper_id)
    assert_qp_download(scope, paper)
    school = (
        await db.execute(select(School).where(School.id == paper.school_id))
    ).scalar_one_or_none()
    content, media_type = await run_in_threadpool(
        generate_paper_pdf,
        paper, school_name=(school.name if school else None), include_answers=answers
    )
    filename = f"{paper.subject_name}_{paper.grade}_paper.pdf".replace(" ", "_")
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"inline; filename={filename}"},
    )


# ---------------------------------------------------------------------------
# Report cards — consolidate marks + attendance + an AI-drafted remark; teacher approves.
# ---------------------------------------------------------------------------


def _to_report_out(r: ReportCard) -> ReportCardOut:
    return ReportCardOut(
        id=r.id,
        student_id=r.student_id,
        title=r.title,
        student_name=r.student_name,
        class_name=r.class_name,
        subjects=r.subjects or [],
        total_obtained=float(r.total_obtained or 0),
        total_max=float(r.total_max or 0),
        percentage=float(r.percentage or 0),
        overall_grade=r.overall_grade,
        attendance_percentage=(
            float(r.attendance_percentage) if r.attendance_percentage is not None else None
        ),
        ai_remark=r.ai_remark,
        status=r.status.value,
        ai_model=r.ai_model,
    )


async def _get_owned_report(db: AsyncSession, school_id: str, report_id: uuid.UUID) -> ReportCard:
    report = (
        await db.execute(
            select(ReportCard).where(
                ReportCard.id == report_id,
                ReportCard.school_id == uuid.UUID(school_id),
            )
        )
    ).scalar_one_or_none()
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report card not found")
    return report


@router.post(
    "/report-cards/generate",
    response_model=ReportCardOut,
    dependencies=[rate_limit("ai_generate", **_AI_GEN_RATE)],
)
async def generate_report_card(
    body: GenerateReportRequest,
    current_user: CurrentUser = Depends(require_roles(*_TEACH_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> ReportCardOut:
    """Consolidate a student's marks + attendance and draft a remark (DRAFT; approve after)."""
    bind_ai_context(
        school_id=current_user.school_id,
        user_id=current_user.id,
        feature="report_card",
    )
    school_id = uuid.UUID(current_user.school_id)
    student = await get_student_in_school(db, school_id, body.student_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    scope = await get_staff_scope(db, current_user)
    assert_report_cards(scope, student.class_id)
    credits = await _enforce_monthly_cap(
        db,
        school_id,
        user_id=uuid.UUID(current_user.id),
        role=current_user.role,
        feature="report_card",
        purpose_tag="report_card",
    )
    try:
        report = await generate_report_for_student(
            db,
            school_id=uuid.UUID(current_user.school_id),
            created_by=uuid.UUID(current_user.id),
            student_id=body.student_id,
            title=body.title,
            role=current_user.role,
            credits_charged=credits,
        )
    except Exception as exc:
        raise_http_for_llm_error(
            exc,
            log_event="report_card_generate_failed",
            timeout_detail="AI generation timed out. Please try again.",
            generic_detail="AI remark generation failed. Check your provider API key or try again.",
        )
    return _to_report_out(report)


@router.get("/report-cards", response_model=list[ReportCardOut])
async def list_report_cards(
    class_id: uuid.UUID | None = None,
    student_id: uuid.UUID | None = None,
    current_user: CurrentUser = Depends(require_roles(*_TEACH_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> list[ReportCardOut]:
    scope = await get_staff_scope(db, current_user)
    q = select(ReportCard).where(ReportCard.school_id == uuid.UUID(current_user.school_id))
    vis = _report_visibility_filter(scope)
    if vis is not None:
        q = q.where(vis)
    if class_id:
        q = q.where(ReportCard.class_id == class_id)
    if student_id:
        q = q.where(ReportCard.student_id == student_id)
    q = q.order_by(ReportCard.created_at.desc()).limit(100)
    rows = (await db.execute(q)).scalars().all()
    return [_to_report_out(r) for r in rows]


@router.get("/report-cards/{report_id}", response_model=ReportCardOut)
async def get_report_card(
    report_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_TEACH_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> ReportCardOut:
    scope = await get_staff_scope(db, current_user)
    report = await _get_owned_report(db, current_user.school_id, report_id)
    if not scope.can_access_report_card(report):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return _to_report_out(report)


@router.put("/report-cards/{report_id}", response_model=ReportCardOut)
async def edit_report_card(
    report_id: uuid.UUID,
    body: UpdateReportRequest,
    current_user: CurrentUser = Depends(require_roles(*_TEACH_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> ReportCardOut:
    """Teacher edits the remark (or title) before approving."""
    scope = await get_staff_scope(db, current_user)
    report = await _get_owned_report(db, current_user.school_id, report_id)
    if not scope.can_edit_report_card(report):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if body.title is not None:
        report.title = body.title
    if body.ai_remark is not None:
        report.ai_remark = body.ai_remark
    await db.flush()
    return _to_report_out(report)


@router.post("/report-cards/{report_id}/approve", response_model=ReportCardOut)
async def approve_report_card(
    report_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_TEACH_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> ReportCardOut:
    """Class incharge approves the report card."""
    scope = await get_staff_scope(db, current_user)
    report = await _get_owned_report(db, current_user.school_id, report_id)
    if not scope.can_approve_report_card(report):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only class incharge can approve report cards",
        )
    report.status = ReportStatus.APPROVED
    await db.flush()
    return _to_report_out(report)


@router.get("/report-cards/{report_id}/pdf")
async def download_report_card(
    report_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_TEACH_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Render a server-generated report-card PDF."""
    scope = await get_staff_scope(db, current_user)
    report = await _get_owned_report(db, current_user.school_id, report_id)
    if not scope.can_access_report_card(report):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    school = (
        await db.execute(select(School).where(School.id == report.school_id))
    ).scalar_one_or_none()
    content, media_type = await run_in_threadpool(
        generate_report_pdf,
        report,
        school_name=(school.name if school else None),
    )
    filename = f"{report.student_name}_report.pdf".replace(" ", "_")
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"inline; filename={filename}"},
    )


@router.post(
    "/copilot/question-papers/{paper_id}/review",
    response_model=CopilotPaperReviewOut,
    dependencies=[rate_limit("ai_copilot", **_AI_GEN_RATE)],
)
async def copilot_review_question_paper(
    paper_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_TEACH_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> CopilotPaperReviewOut:
    """Teacher Copilot: curriculum-grounded review suggestions for a question paper (HITL)."""
    bind_ai_context(
        school_id=current_user.school_id,
        user_id=current_user.id,
        feature="teacher_copilot_review",
    )
    scope = await get_staff_scope(db, current_user)
    paper = await _get_owned_paper(db, current_user.school_id, paper_id)
    if not scope.can_edit_question_paper(paper):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    credits = await _enforce_monthly_cap(
        db,
        uuid.UUID(current_user.school_id),
        user_id=uuid.UUID(current_user.id),
        role=current_user.role,
        feature="teacher_copilot_review",
        purpose_tag="quality_check",
    )
    svc = TeacherCopilotService(db)
    try:
        result = await svc.review_question_paper(
            uuid.UUID(current_user.school_id),
            paper=paper,
            user_id=uuid.UUID(current_user.id),
            role=current_user.role,
            credits_charged=credits,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise_http_for_llm_error(exc)
        raise
    await db.commit()
    suggestions = [
        CopilotSuggestionOut(**s) if isinstance(s, dict) else s
        for s in result.get("suggestions", [])
    ]
    return CopilotPaperReviewOut(
        paper_id=uuid.UUID(result["paper_id"]),
        summary=result.get("summary", ""),
        overall_quality=result.get("overall_quality", "needs_work"),
        suggestions=suggestions,
        grounding_sources=result.get("grounding_sources") or [],
        model=result.get("model"),
    )


@router.post(
    "/copilot/feedback-draft",
    response_model=CopilotFeedbackOut,
    dependencies=[rate_limit("ai_copilot", **_AI_GEN_RATE)],
)
async def copilot_feedback_draft(
    body: CopilotFeedbackRequest,
    current_user: CurrentUser = Depends(require_roles(*_TEACH_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> CopilotFeedbackOut:
    """Teacher Copilot: draft constructive feedback grounded in curriculum (HITL)."""
    bind_ai_context(
        school_id=current_user.school_id,
        user_id=current_user.id,
        feature="teacher_copilot_feedback",
    )
    scope = await get_staff_scope(db, current_user)
    assert_qp_generate(scope, body.class_id, body.subject_id)
    credits = await _enforce_monthly_cap(
        db,
        uuid.UUID(current_user.school_id),
        user_id=uuid.UUID(current_user.id),
        role=current_user.role,
        feature="teacher_copilot_feedback",
        purpose_tag="feedback_draft",
    )
    svc = TeacherCopilotService(db)
    try:
        result = await svc.draft_feedback(
            uuid.UUID(current_user.school_id),
            class_id=body.class_id,
            subject_id=body.subject_id,
            pack_id=body.pack_id,
            topic=body.topic,
            student_answer=body.student_answer,
            rubric=body.rubric,
            user_id=uuid.UUID(current_user.id),
            role=current_user.role,
            credits_charged=credits,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise_http_for_llm_error(exc)
        raise
    await db.commit()
    return CopilotFeedbackOut(**result)

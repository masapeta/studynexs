"""AI module endpoints — status + the Teacher-AI question-paper flow.

Phase-1 hero: generate a board-style question paper from syllabus topics, let the
teacher edit and APPROVE it (human-in-the-loop), then export. Tutor/grading/etc. come later.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_roles
from app.core.rate_limit import rate_limit
from app.db.models.ai_usage import AIUsage
from app.db.models.question_paper import PaperStatus, QuestionPaper
from app.db.models.report_card import ReportCard, ReportStatus
from app.db.models.school import School
from app.modules.ai.schemas.question_paper import (
    DuplicatePaperRequest,
    GenerateRequest,
    QuestionPaperOut,
    UpdatePaperRequest,
)
from app.modules.ai.schemas.report_card import (
    GenerateReportRequest,
    ReportCardOut,
    UpdateReportRequest,
)
from app.modules.ai.services.paper_pdf import generate_paper_pdf
from app.modules.ai.services.question_paper_service import duplicate_paper, generate_paper
from app.modules.ai.services.report_card_pdf import generate_report_pdf
from app.modules.ai.services.report_card_service import generate_report_for_student
from app.modules.ai.services.usage_caps import enforce_monthly_ai_cap

settings = get_settings()
router = APIRouter()

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
        "providers_configured": {
            "gemini": bool(settings.GEMINI_API_KEY),
            "anthropic": bool(settings.ANTHROPIC_API_KEY),
            "openai": bool(settings.OPENAI_API_KEY),
        },
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
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """School-facing AI value summary: papers + report cards generated, teacher-hours saved.

    Deliberately does NOT expose provider cost — that is our cost-of-goods (operator-only;
    see scripts/ai_cost_report.py). Schools see value, never our margins.
    """
    school_id = uuid.UUID(current_user.school_id)
    month_start = datetime.now(timezone.utc).replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )

    def _base(feature: str):
        return (
            select(func.count())
            .select_from(AIUsage)
            .where(AIUsage.school_id == school_id, AIUsage.feature == feature)
        )

    papers_total = await db.scalar(_base("question_paper")) or 0
    papers_month = await db.scalar(
        _base("question_paper").where(AIUsage.created_at >= month_start)
    ) or 0
    reports_total = await db.scalar(_base("report_card")) or 0
    reports_month = await db.scalar(
        _base("report_card").where(AIUsage.created_at >= month_start)
    ) or 0
    est_hours = round(
        (papers_total * _MINUTES_SAVED_PER_PAPER + reports_total * _MINUTES_SAVED_PER_REPORT)
        / 60,
        1,
    )
    return {
        "papers_total": papers_total,
        "papers_this_month": papers_month,
        "reports_total": reports_total,
        "reports_this_month": reports_month,
        "est_hours_saved": est_hours,
    }


def _to_out(p: QuestionPaper) -> QuestionPaperOut:
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
    )


async def _get_owned_paper(
    db: AsyncSession, school_id: str, paper_id: uuid.UUID
) -> QuestionPaper:
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
    """Generate a DRAFT paper from topics. Teacher must review + approve before use."""
    await _enforce_monthly_cap(db, uuid.UUID(current_user.school_id))
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
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return _to_out(paper)


@router.get("/question-papers", response_model=list[QuestionPaperOut])
async def list_question_papers(
    class_id: uuid.UUID | None = None,
    current_user: CurrentUser = Depends(require_roles(*_TEACH_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> list[QuestionPaperOut]:
    q = select(QuestionPaper).where(
        QuestionPaper.school_id == uuid.UUID(current_user.school_id)
    )
    if class_id:
        q = q.where(QuestionPaper.class_id == class_id)
    q = q.order_by(QuestionPaper.created_at.desc()).limit(50)
    rows = (await db.execute(q)).scalars().all()
    return [_to_out(p) for p in rows]


@router.get("/question-papers/{paper_id}", response_model=QuestionPaperOut)
async def get_question_paper(
    paper_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_TEACH_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> QuestionPaperOut:
    return _to_out(await _get_owned_paper(db, current_user.school_id, paper_id))


@router.put("/question-papers/{paper_id}", response_model=QuestionPaperOut)
async def edit_question_paper(
    paper_id: uuid.UUID,
    body: UpdatePaperRequest,
    current_user: CurrentUser = Depends(require_roles(*_TEACH_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> QuestionPaperOut:
    """Teacher edits (title/instructions/sections) before approval."""
    paper = await _get_owned_paper(db, current_user.school_id, paper_id)
    if body.title is not None:
        paper.title = body.title
    if body.general_instructions is not None:
        paper.general_instructions = body.general_instructions
    if body.sections is not None:
        paper.sections = [s.model_dump(exclude_none=True) for s in body.sections]
    await db.flush()
    return _to_out(paper)


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
    source = await _get_owned_paper(db, current_user.school_id, paper_id)
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
    return _to_out(clone)


@router.post("/question-papers/{paper_id}/approve", response_model=QuestionPaperOut)
async def approve_question_paper(
    paper_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_TEACH_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> QuestionPaperOut:
    """Mark the paper teacher-approved (the human-in-the-loop sign-off)."""
    paper = await _get_owned_paper(db, current_user.school_id, paper_id)
    paper.status = PaperStatus.APPROVED
    await db.flush()
    return _to_out(paper)


@router.get("/question-papers/{paper_id}/pdf")
async def download_question_paper(
    paper_id: uuid.UUID,
    answers: bool = False,
    current_user: CurrentUser = Depends(require_roles(*_TEACH_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Render the paper for printing (PDF if WeasyPrint present, else print-ready HTML).
    `answers=true` returns the teacher-only answer-key version."""
    paper = await _get_owned_paper(db, current_user.school_id, paper_id)
    school = (
        await db.execute(select(School).where(School.id == paper.school_id))
    ).scalar_one_or_none()
    content, media_type = generate_paper_pdf(
        paper, school_name=(school.name if school else None), include_answers=answers
    )
    ext = "pdf" if media_type == "application/pdf" else "html"
    filename = f"{paper.subject_name}_{paper.grade}_paper.{ext}".replace(" ", "_")
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


async def _get_owned_report(
    db: AsyncSession, school_id: str, report_id: uuid.UUID
) -> ReportCard:
    report = (
        await db.execute(
            select(ReportCard).where(
                ReportCard.id == report_id,
                ReportCard.school_id == uuid.UUID(school_id),
            )
        )
    ).scalar_one_or_none()
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Report card not found"
        )
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
    await _enforce_monthly_cap(db, uuid.UUID(current_user.school_id))
    try:
        report = await generate_report_for_student(
            db,
            school_id=uuid.UUID(current_user.school_id),
            created_by=uuid.UUID(current_user.id),
            student_id=body.student_id,
            title=body.title,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return _to_report_out(report)


@router.get("/report-cards", response_model=list[ReportCardOut])
async def list_report_cards(
    class_id: uuid.UUID | None = None,
    student_id: uuid.UUID | None = None,
    current_user: CurrentUser = Depends(require_roles(*_TEACH_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> list[ReportCardOut]:
    q = select(ReportCard).where(ReportCard.school_id == uuid.UUID(current_user.school_id))
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
    return _to_report_out(await _get_owned_report(db, current_user.school_id, report_id))


@router.put("/report-cards/{report_id}", response_model=ReportCardOut)
async def edit_report_card(
    report_id: uuid.UUID,
    body: UpdateReportRequest,
    current_user: CurrentUser = Depends(require_roles(*_TEACH_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> ReportCardOut:
    """Teacher edits the remark (or title) before approving."""
    report = await _get_owned_report(db, current_user.school_id, report_id)
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
    """Mark the report card teacher-approved (the human-in-the-loop sign-off)."""
    report = await _get_owned_report(db, current_user.school_id, report_id)
    report.status = ReportStatus.APPROVED
    await db.flush()
    return _to_report_out(report)


@router.get("/report-cards/{report_id}/pdf")
async def download_report_card(
    report_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_TEACH_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Render the report card for printing (PDF if WeasyPrint present, else print-ready HTML)."""
    report = await _get_owned_report(db, current_user.school_id, report_id)
    school = (
        await db.execute(select(School).where(School.id == report.school_id))
    ).scalar_one_or_none()
    content, media_type = generate_report_pdf(
        report, school_name=(school.name if school else None)
    )
    ext = "pdf" if media_type == "application/pdf" else "html"
    filename = f"{report.student_name}_report.{ext}".replace(" ", "_")
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"inline; filename={filename}"},
    )

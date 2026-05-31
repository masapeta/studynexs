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
from app.db.models.ai_usage import AIUsage
from app.db.models.question_paper import PaperStatus, QuestionPaper
from app.db.models.school import School
from app.modules.ai.schemas.question_paper import (
    GenerateRequest,
    QuestionPaperOut,
    UpdatePaperRequest,
)
from app.modules.ai.services.paper_pdf import generate_paper_pdf
from app.modules.ai.services.question_paper_service import generate_paper

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


# Conservative estimate of the manual time a teacher spends setting one paper.
_MINUTES_SAVED_PER_PAPER = 45


@router.get("/usage")
async def ai_usage_summary(
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """School-facing AI value summary: papers generated + estimated teacher-hours saved.

    Deliberately does NOT expose provider cost — that is our cost-of-goods (operator-only;
    see scripts/ai_cost_report.py). Schools see value, never our margins.
    """
    school_id = uuid.UUID(current_user.school_id)
    month_start = datetime.now(timezone.utc).replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    base = (
        select(func.count())
        .select_from(AIUsage)
        .where(AIUsage.school_id == school_id, AIUsage.feature == "question_paper")
    )
    total = await db.scalar(base) or 0
    this_month = await db.scalar(base.where(AIUsage.created_at >= month_start)) or 0
    return {
        "papers_total": total,
        "papers_this_month": this_month,
        "est_hours_saved": round(total * _MINUTES_SAVED_PER_PAPER / 60, 1),
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


@router.post("/question-papers/generate", response_model=QuestionPaperOut)
async def generate_question_paper(
    body: GenerateRequest,
    current_user: CurrentUser = Depends(require_roles(*_TEACH_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> QuestionPaperOut:
    """Generate a DRAFT paper from topics. Teacher must review + approve before use."""
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

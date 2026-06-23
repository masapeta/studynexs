"""School admin AI usage log — credits charged vs approval status."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import Class
from app.db.models.ai_usage import AIUsage
from app.db.models.question_paper import QuestionPaper
from app.db.models.user import User


async def list_question_paper_usage_log(
    db: AsyncSession,
    school_id: uuid.UUID,
    *,
    since: datetime | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Principal-facing log: who generated what, credits used, current approval status."""
    q = (
        select(
            AIUsage,
            QuestionPaper,
            User.full_name,
            Class.grade,
            Class.section,
        )
        .join(
            QuestionPaper,
            (AIUsage.ref_id == QuestionPaper.id)
            & (AIUsage.ref_type == "question_paper"),
        )
        .join(User, AIUsage.created_by == User.id)
        .join(Class, QuestionPaper.class_id == Class.id)
        .where(
            AIUsage.school_id == school_id,
            AIUsage.feature == "question_paper",
        )
        .order_by(AIUsage.created_at.desc())
        .limit(min(limit, 200))
    )
    if since:
        q = q.where(AIUsage.created_at >= since)

    rows = (await db.execute(q)).all()
    out: list[dict[str, Any]] = []
    for usage, paper, full_name, grade, section in rows:
        class_label = f"{grade}-{section}" if section else grade
        out.append(
            {
                "usage_id": usage.id,
                "generated_at": usage.created_at,
                "generated_by": full_name,
                "generated_by_id": usage.created_by,
                "class_label": class_label,
                "grade": grade,
                "subject": paper.subject_name,
                "paper_id": paper.id,
                "paper_title": paper.title,
                "purpose_tag": usage.purpose_tag or "qp_full",
                "credits_used": usage.credits_charged,
                "approval_status": paper.status.value,
                "rejection_reason": paper.rejection_reason,
            }
        )
    return out

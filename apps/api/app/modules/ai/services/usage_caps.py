"""Shared AI spend guardrails — used by every LLM-backed feature."""

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.ai_usage import AIUsage

AI_MONTHLY_CAP = 2000  # per-school AI generations / month


async def enforce_monthly_ai_cap(db: AsyncSession, school_id: uuid.UUID) -> None:
    """Block runaway LLM spend: cap AI generations per school per month."""
    month_start = datetime.now(timezone.utc).replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    used = await db.scalar(
        select(func.count())
        .select_from(AIUsage)
        .where(AIUsage.school_id == school_id, AIUsage.created_at >= month_start)
    ) or 0
    if used >= AI_MONTHLY_CAP:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Monthly AI generation limit reached for this school.",
        )

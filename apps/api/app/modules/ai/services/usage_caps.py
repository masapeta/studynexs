"""Shared AI spend guardrails — delegates to credit-based metering."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.school import School
from app.modules.ai.services.ai_credits import (
    FEATURE_DEFAULT_PURPOSE,
    check_ai_credits,
    credits_for_purpose,
)


async def enforce_monthly_ai_cap(
    db: AsyncSession,
    school_id: uuid.UUID,
    *,
    user_id: uuid.UUID | None = None,
    role: str = "teacher",
    feature: str = "question_paper",
    purpose_tag: str | None = None,
) -> int:
    """Pre-flight credit check. Returns credits to charge. Raises 429 when blocked."""
    school = await db.get(School, school_id)
    if not school:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="School not found")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_id is required for AI credit metering",
        )
    tag = purpose_tag or FEATURE_DEFAULT_PURPOSE.get(feature, feature)
    return await check_ai_credits(
        db, school, user_id=user_id, role=role, purpose_tag=tag
    )

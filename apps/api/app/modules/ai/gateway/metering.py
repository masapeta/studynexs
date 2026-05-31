"""Persist an AIUsage row (tokens, cost, latency) from a gateway result."""
from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.ai_usage import AIUsage
from app.modules.ai.gateway.base import LLMResult
from app.modules.ai.gateway.pricing import estimate_cost_usd


async def record_usage(
    db: AsyncSession,
    *,
    feature: str,
    result: LLMResult,
    school_id: uuid.UUID | None = None,
    created_by: uuid.UUID | None = None,
) -> AIUsage:
    """Record one LLM call for billing/analysis. Call after every gateway.generate()."""
    row = AIUsage(
        school_id=school_id,
        created_by=created_by,
        feature=feature,
        provider=result.provider,
        model=result.model,
        tokens_in=result.tokens_in,
        tokens_out=result.tokens_out,
        cost_usd=estimate_cost_usd(result.model, result.tokens_in, result.tokens_out),
        latency_ms=result.latency_ms,
    )
    db.add(row)
    await db.flush()
    return row

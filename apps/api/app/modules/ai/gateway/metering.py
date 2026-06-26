"""Persist an AIUsage row (tokens, cost, latency, credits) from a gateway result."""
from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.ai_usage import AIUsage
from app.modules.ai.gateway.base import LLMResult
from app.modules.ai.gateway.pricing import estimate_cost_usd
from app.modules.ai.services.ai_credits import (
    FEATURE_DEFAULT_PURPOSE,
    assert_credits_for_charge,
    credits_for_purpose,
)


async def finalize_llm_usage(
    db: AsyncSession,
    reserved_row: AIUsage,
    result: LLMResult,
    *,
    ref_id: uuid.UUID | None = None,
    image_count: int = 0,
) -> AIUsage:
    """Update a reserved usage row after the provider returns. No cap re-check."""
    reserved_row.provider = result.provider
    reserved_row.model = result.model
    reserved_row.tokens_in = result.tokens_in
    reserved_row.tokens_out = result.tokens_out
    reserved_row.cost_usd = estimate_cost_usd(result.model, result.tokens_in, result.tokens_out)
    reserved_row.latency_ms = result.latency_ms
    reserved_row.image_count = image_count
    reserved_row.status = "fallback_success" if result.used_fallback else "success"
    reserved_row.primary_provider = result.primary_provider
    reserved_row.used_fallback = result.used_fallback
    if ref_id is not None:
        reserved_row.ref_id = ref_id
    await db.flush()
    return reserved_row


async def record_usage(
    db: AsyncSession,
    *,
    feature: str,
    result: LLMResult,
    school_id: uuid.UUID | None = None,
    created_by: uuid.UUID | None = None,
    role: str | None = None,
    purpose_tag: str | None = None,
    credits_charged: int | None = None,
    ref_type: str | None = None,
    ref_id: uuid.UUID | None = None,
    image_count: int = 0,
    reserved_row: AIUsage | None = None,
) -> AIUsage:
    """Record one LLM call for billing/analysis.

    When ``reserved_row`` is supplied (credit reservation before the provider call),
    finalize that row without re-running cap checks. Otherwise insert a new row and
    enforce caps first — for non-LLM billing paths only.
    """
    if reserved_row is not None:
        return await finalize_llm_usage(
            db,
            reserved_row,
            result,
            ref_id=ref_id,
            image_count=image_count,
        )

    tag = purpose_tag or FEATURE_DEFAULT_PURPOSE.get(feature, feature)
    credits = credits_charged if credits_charged is not None else credits_for_purpose(tag)
    if school_id is not None and created_by is not None and role is not None and credits > 0:
        await assert_credits_for_charge(
            db,
            school_id,
            user_id=created_by,
            role=role,
            purpose_tag=tag,
            credits=credits,
        )
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
        role=role,
        purpose_tag=tag,
        credits_charged=credits,
        ref_type=ref_type,
        ref_id=ref_id,
        image_count=image_count,
        status="fallback_success" if result.used_fallback else "success",
        primary_provider=result.primary_provider,
        used_fallback=result.used_fallback,
    )
    db.add(row)
    await db.flush()
    return row

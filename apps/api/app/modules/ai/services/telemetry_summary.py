"""Aggregate AI usage from the database for operator dashboards."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.ai_usage import AIUsage
from app.db.models.school import School
from app.modules.ai.services.ai_credits import month_start_for_school


async def db_telemetry_summary(
    db: AsyncSession,
    *,
    school_id: uuid.UUID | None = None,
    since: datetime | None = None,
) -> dict:
    """Roll up persisted AIUsage rows — complements in-process Prometheus metrics."""
    filters = []
    if school_id is not None:
        filters.append(AIUsage.school_id == school_id)
    if since is not None:
        filters.append(AIUsage.created_at >= since)

    base = select(
        func.count(AIUsage.id).label("calls"),
        func.coalesce(func.sum(AIUsage.tokens_in), 0).label("tokens_in"),
        func.coalesce(func.sum(AIUsage.tokens_out), 0).label("tokens_out"),
        func.coalesce(func.sum(AIUsage.cost_usd), 0).label("cost_usd"),
        func.coalesce(func.sum(AIUsage.credits_charged), 0).label("credits"),
        func.coalesce(func.avg(AIUsage.latency_ms), 0).label("avg_latency_ms"),
    ).where(*filters)

    totals = (await db.execute(base)).one()

    by_feature_rows = (
        await db.execute(
            select(
                AIUsage.feature,
                func.count(AIUsage.id),
                func.coalesce(func.sum(AIUsage.cost_usd), 0),
            )
            .where(*filters)
            .group_by(AIUsage.feature)
            .order_by(func.count(AIUsage.id).desc())
        )
    ).all()

    by_provider_rows = (
        await db.execute(
            select(
                AIUsage.provider,
                AIUsage.model,
                func.count(AIUsage.id),
                func.coalesce(func.sum(AIUsage.tokens_in + AIUsage.tokens_out), 0),
            )
            .where(*filters)
            .group_by(AIUsage.provider, AIUsage.model)
            .order_by(func.count(AIUsage.id).desc())
        )
    ).all()

    fallback_count = (
        await db.execute(
            select(func.count(AIUsage.id)).where(
                *filters,
                AIUsage.used_fallback.is_(True),
            )
        )
    ).scalar_one()

    return {
        "period": {"since": since.isoformat() if since else None},
        "totals": {
            "calls": int(totals.calls or 0),
            "tokens_in": int(totals.tokens_in or 0),
            "tokens_out": int(totals.tokens_out or 0),
            "cost_usd": float(totals.cost_usd or 0),
            "credits_charged": int(totals.credits or 0),
            "avg_latency_ms": round(float(totals.avg_latency_ms or 0), 1),
            "fallback_calls": int(fallback_count or 0),
        },
        "by_feature": [
            {"feature": row[0], "calls": int(row[1]), "cost_usd": float(row[2])}
            for row in by_feature_rows
        ],
        "by_provider": [
            {
                "provider": row[0],
                "model": row[1],
                "calls": int(row[2]),
                "tokens_total": int(row[3]),
            }
            for row in by_provider_rows
        ],
    }


async def school_month_telemetry(
    db: AsyncSession,
    school_id: uuid.UUID,
) -> dict:
    school = (
        await db.execute(select(School).where(School.id == school_id))
    ).scalar_one_or_none()
    since = month_start_for_school(school)
    return await db_telemetry_summary(db, school_id=school_id, since=since)

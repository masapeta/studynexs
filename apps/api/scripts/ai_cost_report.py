"""Operator-only AI cost + usage report, per school (YOUR margins).

This is platform-operator data — it shows what each school costs YOU to serve (provider
spend). It is intentionally NOT exposed in the product; schools must never see cost-of-goods.

Run: python scripts/ai_cost_report.py
"""
from __future__ import annotations

import asyncio

from sqlalchemy import func, select

from app.core.database import async_session_factory
from app.db.models.ai_usage import AIUsage
from app.db.models.school import School


async def main() -> None:
    async with async_session_factory() as db:
        rows = (
            await db.execute(
                select(
                    School.name,
                    func.count(AIUsage.id),
                    func.coalesce(func.sum(AIUsage.tokens_in + AIUsage.tokens_out), 0),
                    func.coalesce(func.sum(AIUsage.cost_usd), 0),
                )
                .join(School, School.id == AIUsage.school_id)
                .group_by(School.name)
                .order_by(func.sum(AIUsage.cost_usd).desc())
            )
        ).all()

        print(f"{'School':<34}{'Calls':>7}{'Tokens':>11}{'Cost USD':>11}")
        print("-" * 63)
        total_cost = 0.0
        for name, calls, tokens, cost in rows:
            total_cost += float(cost)
            print(f"{(name or '')[:34]:<34}{calls:>7}{int(tokens):>11}{float(cost):>11.4f}")
        print("-" * 63)
        print(f"{'TOTAL':<34}{'':>7}{'':>11}{total_cost:>11.4f}")
        if not rows:
            print("(no AI usage recorded yet)")


if __name__ == "__main__":
    asyncio.run(main())

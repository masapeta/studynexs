"""Apply pilot AI credit budget to demo school (tenant: test).

  python scripts/patch_demo_ai_budget.py
"""
from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.core.database import async_session_factory
from app.db.models.school import School
from app.modules.ai.services.ai_credits import DEFAULT_AI_BUDGET

TENANT = "test"


async def main() -> None:
    async with async_session_factory() as db:
        school = (
            await db.execute(select(School).where(School.tenant_slug == TENANT))
        ).scalar_one_or_none()
        if not school:
            print("Demo school not found.")
            return
        settings = dict(school.settings or {})
        settings["ai_budget"] = {
            **DEFAULT_AI_BUDGET,
            "monthly_credits": 100,
            "teacher_monthly_credits": 25,
            "incharge_monthly_credits": 60,
            "limits": {
                "qp_full_per_month": 5,
                "qp_regen_per_month": 20,
            },
            "plan": "pilot",
        }
        school.settings = settings
        await db.commit()
        print("Pilot AI budget applied:")
        print("  School pool: 100 credits/month")
        print("  Teacher quota: 25 credits/month")
        print("  Max full papers: 5/month (school)")
        print("  Max regenerations: 20/month (school)")


if __name__ == "__main__":
    asyncio.run(main())

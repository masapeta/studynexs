"""Top up admissions pipeline demo data for tenant test.

Ensures each stage (enquiry → enrolled) has enough candidates for the
Admissions page pipeline counters and list.

Run:
    cd apps/api
    python scripts/seed_admissions_progress.py
    python scripts/seed_admissions_progress.py --boost 3   # +3 per stage
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from sqlalchemy import select

_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR.parent))
sys.path.insert(0, str(_SCRIPT_DIR))

from app.core.database import async_session_factory
from app.db.models.school import School
from app.db.models.school_ops import AdmissionStage
from app.db.models.user import User, UserRole
from seed_working_session import (
    ADMISSION_MIN_PER_STAGE,
    admission_pipeline_counts,
    seed_admissions,
)

TENANT = "test"


def _print_pipeline(counts: dict[str, int], label: str) -> None:
    print(label)
    for stage in AdmissionStage:
        print(f"  {stage.value:10} {counts.get(stage.value, 0)}")
    print(f"  {'total':10} {counts.get('total', 0)}")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Seed admissions pipeline demo data")
    parser.add_argument(
        "--boost",
        type=int,
        default=0,
        metavar="N",
        help="Add N extra candidates per stage on top of default minimums",
    )
    args = parser.parse_args()

    async with async_session_factory() as db:
        school = (
            await db.execute(select(School).where(School.tenant_slug == TENANT))
        ).scalar_one_or_none()
        if not school:
            print(f"School tenant_slug='{TENANT}' not found. Run seed_demo_ssc.py first.")
            return

        principal = (
            await db.execute(
                select(User).where(
                    User.school_id == school.id,
                    User.role == UserRole.SUPER_ADMIN,
                ).limit(1)
            )
        ).scalar_one_or_none()
        if not principal:
            print("No principal user found.")
            return

        before = await admission_pipeline_counts(db, school.id)
        _print_pipeline(before, "Pipeline before:")

        targets = {
            stage: ADMISSION_MIN_PER_STAGE[stage] + max(0, args.boost)
            for stage in AdmissionStage
        }
        added = await seed_admissions(
            db, school, principal.id, min_per_stage=targets
        )
        await db.commit()

        after = await admission_pipeline_counts(db, school.id)
        _print_pipeline(after, "\nPipeline after:")
        print(f"\nAdded {added} new candidate(s).")
        if added == 0:
            print(
                "All stages already meet targets. Use --boost 3 to add more, "
                "or open /dashboard/admissions to review existing candidates."
            )


if __name__ == "__main__":
    asyncio.run(main())

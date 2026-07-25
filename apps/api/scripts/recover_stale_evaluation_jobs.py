#!/usr/bin/env python3
"""Recover stale answer-sheet evaluation job rows.

Default mode is a dry-run. Use ``--apply`` only after reviewing the proposed
actions.

Examples:
  python scripts/recover_stale_evaluation_jobs.py --tenant-slug reference
  python scripts/recover_stale_evaluation_jobs.py --tenant-slug reference --apply
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from sqlalchemy import select

_API_ROOT = Path(__file__).resolve().parents[1]
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))

from app.core.database import async_session_factory  # noqa: E402
from app.core.jobs.recovery import recover_stale_answer_sheet_eval_jobs  # noqa: E402
from app.db.models.school import School  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Classify or reconcile stale answer_sheet_eval jobs."
    )
    parser.add_argument(
        "--tenant-slug",
        help="Limit recovery to one tenant slug. Omit only for an all-tenant operator scan.",
    )
    parser.add_argument(
        "--older-than-minutes",
        type=int,
        default=30,
        help="Only classify queued/running jobs older than this many minutes.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Persist safe reconciliation actions. Without this flag, no rows are changed.",
    )
    return parser.parse_args()


async def main() -> int:
    args = _parse_args()
    async with async_session_factory() as db:
        school_id = None
        if args.tenant_slug:
            school = (
                await db.execute(select(School).where(School.tenant_slug == args.tenant_slug))
            ).scalar_one_or_none()
            if school is None:
                print(json.dumps({"error": f"tenant not found: {args.tenant_slug}"}))
                return 2
            school_id = school.id

        result = await recover_stale_answer_sheet_eval_jobs(
            db,
            older_than_minutes=args.older_than_minutes,
            school_id=school_id,
            apply=args.apply,
        )
        if args.apply:
            await db.commit()
        else:
            await db.rollback()
        print(json.dumps(result.as_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

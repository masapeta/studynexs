#!/usr/bin/env python3
"""Run sweep_expired_prospect_tenants cron once (Stage 2B validation).

Creates an expired prospect tenant, runs the Arq cron handler, verifies purge via
enqueued tenant_cleanup + optional run_job completion.

Run from apps/api:
  python scripts/run_demo_sweep_cron_once.py
"""
from __future__ import annotations

import asyncio
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

_API_ROOT = Path(__file__).resolve().parents[1]
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))

from sqlalchemy import select

from app.core.database import async_session_factory
from app.core.jobs.worker import register_job_handlers, run_job
from app.db.models.job import Job, JobStatus
from app.db.models.school import School
from app.modules.demo.jobs.demo_sweep_cron import sweep_expired_prospect_tenants


async def main() -> int:
    from app.core.dependencies import get_redis
    from app.modules.demo.services.demo_session_service import DemoSessionService

    print("1. Provision prospect tenant (service)")
    redis = await get_redis()
    async with async_session_factory() as db:
        svc = DemoSessionService(db, redis=redis)
        session_out, _refresh = await svc.create_session(display_name="Sweep Cron Once")
        await db.commit()
        school_id = uuid.UUID(session_out.school_id)
        slug = session_out.tenant_slug
        print(f"   tenant={slug} school_id={school_id}")

    async with async_session_factory() as db:
        school = await db.get(School, school_id)
        assert school is not None
        school.expires_at = datetime.now(timezone.utc) - timedelta(minutes=5)
        school.is_active = True
        await db.commit()

    print("2. Running sweep_expired_prospect_tenants (Arq cron entrypoint)")
    result = await sweep_expired_prospect_tenants({})
    print(f"   swept={result}")

    if slug not in result.get("tenant_slugs", []):
        print(f"FAIL: expected {slug} in sweep result")
        return 1

    async with async_session_factory() as db:
        school = await db.get(School, school_id)
        if school is not None and school.is_active:
            print("FAIL: school still active after sweep")
            return 1

        jobs = (
            await db.execute(
                select(Job).where(
                    Job.school_id == school_id,
                    Job.type == "tenant_cleanup",
                    Job.status == JobStatus.QUEUED,
                )
            )
        ).scalars().all()
        if not jobs:
            print("FAIL: no queued tenant_cleanup job after sweep")
            return 1
        job_id = jobs[0].id
        print(f"3. Enqueued tenant_cleanup job {job_id}")

    await register_job_handlers()
    print("4. Executing run_job for enqueued cleanup…")
    await run_job({}, str(job_id))

    async with async_session_factory() as db:
        refreshed = await db.get(Job, job_id)
        gone = await db.get(School, school_id)
        if gone is not None:
            print(f"FAIL: school still exists ({slug})")
            return 1
        if refreshed is None or refreshed.status != JobStatus.DONE:
            print(f"FAIL: job status={getattr(refreshed, 'status', None)}")
            return 1
        print(f"5. PASS sweep cron -> cleanup job DONE, tenant purged ({slug})")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

#!/usr/bin/env python3
"""Run tenant_cleanup once through the real Arq run_job entrypoint (Stage 2B validation).

Creates an expired prospect tenant, enqueues cleanup, executes run_job, verifies DONE.

Run from apps/api:
  python scripts/run_demo_arq_cleanup_once.py
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

from app.core.database import async_session_factory
from app.core.jobs.worker import register_job_handlers, run_job
from app.db.models.job import Job, JobStatus
from app.db.models.school import School


async def main() -> int:
    from app.core.dependencies import get_redis
    from app.modules.demo.services.demo_session_service import DemoSessionService

    print("1. Provision prospect tenant (service, not HTTP — avoids rate limit)")
    redis = await get_redis()
    async with async_session_factory() as db:
        svc = DemoSessionService(db, redis=redis)
        session_out, _refresh = await svc.create_session(display_name="Arq Cleanup Once")
        await db.commit()
        school_id = uuid.UUID(session_out.school_id)
        slug = session_out.tenant_slug
        print(f"   tenant={slug} school_id={school_id}")

    async with async_session_factory() as db:
        school = await db.get(School, school_id)
        assert school is not None
        school.expires_at = datetime.now(timezone.utc) - timedelta(minutes=5)
        school.is_active = False
        await db.commit()

        job = Job(
            type="tenant_cleanup",
            params={"school_id": str(school_id)},
            school_id=school_id,
            status=JobStatus.QUEUED,
        )
        db.add(job)
        await db.commit()
        job_id = job.id
        print(f"2. Enqueued tenant_cleanup job {job_id}")

    await register_job_handlers()
    print("3. Executing run_job (worker lifecycle)…")
    await run_job({}, str(job_id))

    async with async_session_factory() as db:
        refreshed = await db.get(Job, job_id)
        gone = await db.get(School, school_id)
        if gone is not None:
            print(f"FAIL: school still exists ({slug})")
            return 1
        if refreshed is None:
            print("FAIL: cleanup job row missing")
            return 1
        if refreshed.status != JobStatus.DONE:
            print(f"FAIL: job status={refreshed.status} error={refreshed.error}")
            return 1
        print(f"4. PASS job={job_id} status=DONE tenant purged ({slug})")
        print(f"   result={refreshed.result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

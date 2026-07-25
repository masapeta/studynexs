"""Arq worker wiring — handler registration and the job-not-found retry contract.

These guard two bugs that made async jobs (answer-sheet evaluation) silently never run:
  1. handlers were imported only inside `if __name__ == "__main__"`, so the documented
     command `arq app.core.jobs.worker.WorkerSettings` (a dotted-path import, never __main__)
     started with an empty handler registry;
  2. `run_job` raised a plain exception for a not-yet-committed job, which arq does NOT retry.
"""

import sys
import uuid
from types import SimpleNamespace

import pytest

from app.core.jobs import worker
from app.core.platform_metrics import platform_metrics
from app.db.models.job import JobStatus


@pytest.mark.asyncio
async def test_worker_on_startup_registers_handlers():
    """`WorkerSettings.on_startup` must populate JOB_HANDLERS on the CLI import path.

    We drop the job module from sys.modules and clear the registry to simulate a fresh worker
    process that only imported app.core.jobs.worker — then assert on_startup wires it up.
    """
    eval_mod = "app.modules.examinations.jobs.answer_sheet_eval_job"
    sys.modules.pop(eval_mod, None)
    worker.JOB_HANDLERS.clear()

    await worker.WorkerSettings.on_startup({})

    assert "answer_sheet_eval" in worker.JOB_HANDLERS, (
        "on_startup did not register the answer-sheet evaluation handler — the documented "
        "`arq ...WorkerSettings` command would run with an empty registry"
    )


@pytest.mark.asyncio
async def test_run_job_retries_when_row_not_yet_committed(monkeypatch):
    """A not-yet-visible job row must raise arq.Retry (which arq honors), not a plain error."""
    from arq import Retry

    class _NoRowSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def execute(self, *_a, **_k):
            class _R:
                def scalar_one_or_none(self_inner):
                    return None

            return _R()

    monkeypatch.setattr(worker, "async_session_factory", lambda: _NoRowSession())

    before = platform_metrics.snapshot()["jobs_by_status"].get("retry_not_found", 0)
    with pytest.raises(Retry):
        await worker.run_job({}, "00000000-0000-0000-0000-000000000000")
    after = platform_metrics.snapshot()["jobs_by_status"].get("retry_not_found", 0)
    assert after >= before + 1


@pytest.mark.asyncio
async def test_run_job_records_success_metrics(monkeypatch):
    job = SimpleNamespace(
        id=uuid.uuid4(),
        type="h6_test",
        params={},
        school_id=None,
        created_by=None,
        status=JobStatus.QUEUED,
        result=None,
        error=None,
        updated_at=None,
    )

    class _JobSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def execute(self, *_a, **_k):
            class _R:
                def scalar_one_or_none(self_inner):
                    return job

            return _R()

        async def commit(self):
            return None

    async def handler(params, _session):
        assert params["_job_id"] == str(job.id)
        return {"ok": True}

    monkeypatch.setitem(worker.JOB_HANDLERS, "h6_test", handler)
    monkeypatch.setattr(worker, "async_session_factory", lambda: _JobSession())

    before = platform_metrics.snapshot()["jobs_by_status"].get(JobStatus.DONE.value, 0)
    await worker.run_job({}, str(job.id))
    after = platform_metrics.snapshot()["jobs_by_status"].get(JobStatus.DONE.value, 0)

    assert job.status == JobStatus.DONE
    assert job.result == {"ok": True}
    assert after >= before + 1

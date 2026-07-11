"""Jobs polling endpoint — a job's params/result are private to its creator (or an admin)."""

import uuid

import pytest
from httpx import AsyncClient

from app.db.models.job import Job, JobStatus
from app.db.models.user import User
from tests.conftest import auth_headers, get_auth_token


@pytest.mark.asyncio
async def test_job_readable_only_by_owner_or_admin(
    client: AsyncClient,
    admin_user: User,
    teacher_user: User,
    student_user: User,
    db_session,
):
    """Regression (IDOR): GET /jobs/{id} was tenant-scoped only, so any user in the school
    could read any job's params/result. Now only the creator or an admin can — others get 404
    (same as missing, so existence isn't leaked)."""
    job = Job(
        type="answer_sheet_eval",
        params={"evaluation_id": str(uuid.uuid4())},
        school_id=teacher_user.school_id,
        created_by=teacher_user.id,
        status=JobStatus.QUEUED,
    )
    db_session.add(job)
    await db_session.flush()

    async def _get(token: str) -> int:
        resp = await client.get(f"/api/v1/jobs/{job.id}", headers=auth_headers(token))
        return resp.status_code

    # Owner (the teacher who created it) can read it.
    assert await _get(await get_auth_token(client, "test_teacher", "Teacher@123")) == 200
    # Another non-admin in the same school cannot — 404, not 403 (no existence leak).
    assert await _get(await get_auth_token(client, "test_student", "Student@123")) == 404
    # A school admin can read any job.
    assert await _get(await get_auth_token(client, "test_admin", "Admin@123")) == 200

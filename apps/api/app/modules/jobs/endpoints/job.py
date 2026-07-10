"""Job polling endpoint."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_route import CommitOnSuccessRoute
from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_roles
from app.db.models.job import Job
from app.modules.jobs.schemas.job import JobOut
from app.shared.schemas.common import APIResponse

router = APIRouter(route_class=CommitOnSuccessRoute)
_STAFF = ("teacher", "class_incharge", "admin", "super_admin", "parent", "student")


@router.get("/{job_id}", response_model=APIResponse[JobOut])
async def get_job(
    job_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_STAFF)),
    db: AsyncSession = Depends(get_db),
):
    school_id = uuid.UUID(current_user.school_id)
    row = (
        await db.execute(select(Job).where(Job.id == job_id, Job.school_id == school_id))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    # Object-level authorization: a job carries its params and result (e.g. answer-sheet
    # evaluation output), so only its creator or a school admin may read it. Anyone else gets
    # 404 — same response as a missing job, so job existence isn't leaked across users.
    is_admin = current_user.role in ("admin", "super_admin")
    if not is_admin and (row.created_by is None or str(row.created_by) != current_user.id):
        raise HTTPException(status_code=404, detail="Job not found")
    return APIResponse(data=JobOut.model_validate(row))

"""Job polling endpoint."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_roles
from app.db.models.job import Job
from app.modules.jobs.schemas.job import JobOut
from app.shared.schemas.common import APIResponse

router = APIRouter()
_STAFF = ("teacher", "class_incharge", "admin", "super_admin", "parent", "student")


@router.get("/{job_id}", response_model=APIResponse[JobOut])
async def get_job(
    job_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_STAFF)),
    db: AsyncSession = Depends(get_db),
):
    school_id = uuid.UUID(current_user.school_id)
    row = (
        await db.execute(
            select(Job).where(Job.id == job_id, Job.school_id == school_id)
        )
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    return APIResponse(data=JobOut.model_validate(row))

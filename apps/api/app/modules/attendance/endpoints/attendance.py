"""Attendance endpoints — bulk mark and query."""
from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_roles
from app.core.rate_limit import rate_limit

settings = get_settings()
from app.modules.attendance.schemas.attendance import AttendanceOut, AttendanceSummary, BulkMarkRequest
from app.modules.attendance.services.attendance_service import AttendanceService
from app.shared.schemas.common import APIResponse

router = APIRouter()


@router.post(
    "/mark",
    response_model=APIResponse,
    dependencies=[
        rate_limit(
            "attendance:mark",
            max_requests=settings.API_RATE_LIMIT_WRITE_PER_MIN,
        )
    ],
)
async def mark_attendance(
    body: BulkMarkRequest,
    current_user: CurrentUser = Depends(
        require_roles("teacher", "class_incharge", "admin", "super_admin")
    ),
    db: AsyncSession = Depends(get_db),
):
    service = AttendanceService(db)
    count = await service.mark_bulk(
        school_id=uuid.UUID(current_user.school_id),
        class_id=body.class_id,
        att_date=body.date,
        entries=body.entries,
        marked_by=uuid.UUID(current_user.id),
    )
    return APIResponse(message=f"Attendance marked for {count} students")


@router.get("/class/{class_id}", response_model=APIResponse[list[AttendanceOut]])
async def get_class_attendance(
    class_id: uuid.UUID,
    att_date: date = Query(..., alias="date"),
    current_user: CurrentUser = Depends(
        require_roles("teacher", "class_incharge", "admin", "super_admin")
    ),
    db: AsyncSession = Depends(get_db),
):
    service = AttendanceService(db)
    records = await service.get_class_attendance(
        uuid.UUID(current_user.school_id), class_id, att_date
    )
    return APIResponse(data=[AttendanceOut.model_validate(r) for r in records])


@router.get("/class/{class_id}/summary", response_model=APIResponse[AttendanceSummary])
async def get_summary(
    class_id: uuid.UUID,
    att_date: date = Query(..., alias="date"),
    current_user: CurrentUser = Depends(
        require_roles("teacher", "class_incharge", "admin", "super_admin")
    ),
    db: AsyncSession = Depends(get_db),
):
    service = AttendanceService(db)
    summary = await service.get_summary(uuid.UUID(current_user.school_id), class_id, att_date)
    return APIResponse(data=AttendanceSummary(**summary))


@router.get("/school-summary", response_model=APIResponse)
async def get_school_summary(
    att_date: date = Query(..., alias="date"),
    current_user: CurrentUser = Depends(
        require_roles("admin", "super_admin")
    ),
    db: AsyncSession = Depends(get_db),
):
    service = AttendanceService(db)
    summary = await service.get_school_summary(uuid.UUID(current_user.school_id), att_date)
    return APIResponse(data=summary)

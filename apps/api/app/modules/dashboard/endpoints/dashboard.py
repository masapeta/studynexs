"""Dashboard API — role-tailored home summary."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_route import CommitOnSuccessRoute
from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_roles
from app.core.staff_permissions import get_staff_scope
from app.modules.dashboard.schemas.dashboard import DashboardSummaryOut
from app.modules.dashboard.services.dashboard_service import DashboardService
from app.shared.schemas.common import APIResponse

router = APIRouter(route_class=CommitOnSuccessRoute)


@router.get("/summary", response_model=APIResponse[DashboardSummaryOut])
async def dashboard_summary(
    current_user: CurrentUser = Depends(
        require_roles(
            "admin",
            "super_admin",
            "class_incharge",
            "teacher",
            "operations",
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    """Home screen data scoped to the caller's role — no school-wide leaks for subject teachers."""
    scope = await get_staff_scope(db, current_user)
    summary = await DashboardService(db).build_summary(
        uuid.UUID(current_user.school_id),
        scope,
        teacher_name=current_user.full_name or "Teacher",
    )
    return APIResponse(data=summary)

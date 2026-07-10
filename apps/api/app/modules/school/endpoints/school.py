"""School settings endpoints — profile + academic years."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_route import CommitOnSuccessRoute
from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user, require_roles
from app.modules.school.schemas.school import (
    AcademicYearCreate,
    AcademicYearOut,
    SchoolProfileOut,
    SchoolProfileUpdate,
)
from app.modules.school.services.school_service import SchoolService
from app.shared.schemas.common import APIResponse

router = APIRouter(route_class=CommitOnSuccessRoute)
_ADMIN = ("admin", "super_admin")


@router.get("/profile", response_model=APIResponse[SchoolProfileOut])
async def get_profile(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    school = await SchoolService(db).get_profile(uuid.UUID(current_user.school_id))
    return APIResponse(data=SchoolProfileOut.model_validate(school))


@router.patch("/profile", response_model=APIResponse[SchoolProfileOut])
async def update_profile(
    body: SchoolProfileUpdate,
    current_user: CurrentUser = Depends(require_roles(*_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    school = await SchoolService(db).update_profile(uuid.UUID(current_user.school_id), body)
    return APIResponse(
        data=SchoolProfileOut.model_validate(school), message="School profile updated"
    )


@router.get("/academic-years", response_model=APIResponse[list[AcademicYearOut]])
async def list_academic_years(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    years = await SchoolService(db).list_years(uuid.UUID(current_user.school_id))
    return APIResponse(data=[AcademicYearOut.model_validate(y) for y in years])


@router.post("/academic-years", response_model=APIResponse[AcademicYearOut], status_code=201)
async def create_academic_year(
    body: AcademicYearCreate,
    current_user: CurrentUser = Depends(require_roles(*_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    year = await SchoolService(db).create_year(uuid.UUID(current_user.school_id), body)
    return APIResponse(data=AcademicYearOut.model_validate(year), message="Academic year created")

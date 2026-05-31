"""Timetable endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user, require_roles
from app.modules.timetable.schemas.timetable import TimetableSlotCreate, TimetableSlotOut
from app.modules.timetable.services.timetable_service import TimetableService
from app.shared.schemas.common import APIResponse

router = APIRouter()


@router.get("/class/{class_id}", response_model=APIResponse[list[TimetableSlotOut]])
async def get_class_timetable(
    class_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = TimetableService(db)
    slots = await service.get_class_timetable(uuid.UUID(current_user.school_id), class_id)
    return APIResponse(data=[TimetableSlotOut.model_validate(s) for s in slots])


@router.get("/teacher/{teacher_id}", response_model=APIResponse[list[TimetableSlotOut]])
async def get_teacher_timetable(
    teacher_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = TimetableService(db)
    slots = await service.get_teacher_timetable(uuid.UUID(current_user.school_id), teacher_id)
    return APIResponse(data=[TimetableSlotOut.model_validate(s) for s in slots])


@router.post("", response_model=APIResponse[TimetableSlotOut], status_code=201)
async def create_slot(
    body: TimetableSlotCreate,
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin")),
    db: AsyncSession = Depends(get_db),
):
    service = TimetableService(db)
    slot = await service.create_slot(uuid.UUID(current_user.school_id), body)
    return APIResponse(data=TimetableSlotOut.model_validate(slot), message="Slot created")


@router.delete("/{slot_id}", response_model=APIResponse)
async def delete_slot(
    slot_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin")),
    db: AsyncSession = Depends(get_db),
):
    service = TimetableService(db)
    ok = await service.delete_slot(uuid.UUID(current_user.school_id), slot_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Slot not found")
    return APIResponse(message="Slot deleted")

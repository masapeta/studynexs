"""Timetable endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_route import CommitOnSuccessRoute
from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user, require_roles
from app.core.staff_permissions import assert_timetable_edit, get_staff_scope
from app.db.models.academic import Subject
from app.db.models.user import User
from app.modules.timetable.schemas.timetable import TimetableSlotCreate, TimetableSlotOut
from app.modules.timetable.services.timetable_service import TimetableService
from app.shared.schemas.common import APIResponse

router = APIRouter(route_class=CommitOnSuccessRoute)


def _slot_out(
    slot, teacher_name: str | None = None, subject_name: str | None = None
) -> TimetableSlotOut:
    base = TimetableSlotOut.model_validate(slot)
    return base.model_copy(update={"teacher_name": teacher_name, "subject_name": subject_name})


@router.get("/class/{class_id}", response_model=APIResponse[list[TimetableSlotOut]])
async def get_class_timetable(
    class_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = TimetableService(db)
    school_id = uuid.UUID(current_user.school_id)
    slots = await service.get_class_timetable(school_id, class_id)
    if not slots:
        return APIResponse(data=[])
    teacher_ids = {s.teacher_id for s in slots}
    subject_ids = {s.subject_id for s in slots}
    teachers = {
        row.id: row.full_name
        for row in (
            await db.execute(
                select(User).where(User.school_id == school_id, User.id.in_(teacher_ids))
            )
        )
        .scalars()
        .all()
    }
    subjects = {
        row.id: row.name
        for row in (
            await db.execute(
                select(Subject).where(Subject.school_id == school_id, Subject.id.in_(subject_ids))
            )
        )
        .scalars()
        .all()
    }
    return APIResponse(
        data=[_slot_out(s, teachers.get(s.teacher_id), subjects.get(s.subject_id)) for s in slots]
    )


@router.get("/teacher/{teacher_id}", response_model=APIResponse[list[TimetableSlotOut]])
async def get_teacher_timetable(
    teacher_id: uuid.UUID,
    current_user: CurrentUser = Depends(
        require_roles("teacher", "class_incharge", "admin", "super_admin", "operations")
    ),
    db: AsyncSession = Depends(get_db),
):
    service = TimetableService(db)
    slots = await service.get_teacher_timetable(uuid.UUID(current_user.school_id), teacher_id)
    return APIResponse(data=[TimetableSlotOut.model_validate(s) for s in slots])


@router.post("", response_model=APIResponse[TimetableSlotOut], status_code=201)
async def create_slot(
    body: TimetableSlotCreate,
    current_user: CurrentUser = Depends(
        require_roles("admin", "super_admin", "class_incharge", "teacher")
    ),
    db: AsyncSession = Depends(get_db),
):
    scope = await get_staff_scope(db, current_user)
    assert_timetable_edit(scope, body.class_id)
    service = TimetableService(db)
    slot = await service.create_slot(uuid.UUID(current_user.school_id), body)
    return APIResponse(data=TimetableSlotOut.model_validate(slot), message="Slot created")


@router.delete("/{slot_id}", response_model=APIResponse)
async def delete_slot(
    slot_id: uuid.UUID,
    current_user: CurrentUser = Depends(
        require_roles("admin", "super_admin", "class_incharge", "teacher")
    ),
    db: AsyncSession = Depends(get_db),
):
    service = TimetableService(db)
    slot = await service.get_slot(uuid.UUID(current_user.school_id), slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    scope = await get_staff_scope(db, current_user)
    assert_timetable_edit(scope, slot.class_id)
    ok = await service.delete_slot(uuid.UUID(current_user.school_id), slot_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Slot not found")
    return APIResponse(message="Slot deleted")

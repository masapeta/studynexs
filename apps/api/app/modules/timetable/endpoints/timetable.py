"""Timetable endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_route import CommitOnSuccessRoute
from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user, require_roles
from app.core.staff_permissions import assert_timetable_edit, get_staff_scope
from app.core.tenant_scope import TenantScope
from app.modules.timetable.schemas.timetable import (
    ClassSubjectTeacherOut,
    TimetableSlotCreate,
    TimetableSlotOut,
)
from app.modules.timetable.services.timetable_service import (
    TimetableAssignmentError,
    TimetableService,
)
from app.shared.schemas.common import APIResponse

router = APIRouter(route_class=CommitOnSuccessRoute)


@router.get("/class/{class_id}", response_model=APIResponse[list[TimetableSlotOut]])
async def get_class_timetable(
    class_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = await TimetableService(db).class_timetable_out(
        uuid.UUID(current_user.school_id), class_id
    )
    return APIResponse(data=rows)


@router.get(
    "/class/{class_id}/teachers", response_model=APIResponse[list[ClassSubjectTeacherOut]]
)
async def list_class_subject_teachers(
    class_id: uuid.UUID,
    subject_id: uuid.UUID | None = None,
    current_user: CurrentUser = Depends(
        require_roles("admin", "super_admin", "class_incharge", "teacher")
    ),
    db: AsyncSession = Depends(get_db),
):
    """Teachers mapped to this class (and subject) — same scope rule as editing its timetable."""
    scope = await get_staff_scope(db, current_user)
    assert_timetable_edit(scope, class_id)
    school_id = uuid.UUID(current_user.school_id)
    await TenantScope(db, school_id).school_class(class_id)
    rows = await TimetableService(db).list_subject_teachers(school_id, class_id, subject_id)
    return APIResponse(
        data=[
            ClassSubjectTeacherOut(teacher_id=t, full_name=n, subject_id=s) for t, n, s in rows
        ]
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
    try:
        slot = await service.create_slot(uuid.UUID(current_user.school_id), body)
    except TimetableAssignmentError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
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

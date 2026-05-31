"""Timetable service."""

import uuid
from datetime import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant_scope import TenantScope
from app.db.models.timetable import TimetableSlot
from app.modules.timetable.schemas.timetable import TimetableSlotCreate


class TimetableService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_class_timetable(
        self, school_id: uuid.UUID, class_id: uuid.UUID
    ) -> list[TimetableSlot]:
        result = await self.db.execute(
            select(TimetableSlot).where(
                TimetableSlot.school_id == school_id,
                TimetableSlot.class_id == class_id,
            ).order_by(TimetableSlot.day_of_week, TimetableSlot.period_number)
        )
        return list(result.scalars().all())

    async def get_teacher_timetable(
        self, school_id: uuid.UUID, teacher_id: uuid.UUID
    ) -> list[TimetableSlot]:
        result = await self.db.execute(
            select(TimetableSlot).where(
                TimetableSlot.school_id == school_id,
                TimetableSlot.teacher_id == teacher_id,
            ).order_by(TimetableSlot.day_of_week, TimetableSlot.period_number)
        )
        return list(result.scalars().all())

    async def create_slot(self, school_id: uuid.UUID, data: TimetableSlotCreate) -> TimetableSlot:
        scope = TenantScope(self.db, school_id)
        await scope.school_class(data.class_id)
        await scope.subject_in_class(data.subject_id, data.class_id)
        await scope.staff_user(data.teacher_id)
        slot = TimetableSlot(
            school_id=school_id,
            class_id=data.class_id,
            subject_id=data.subject_id,
            teacher_id=data.teacher_id,
            day_of_week=data.day_of_week,
            period_number=data.period_number,
            start_time=time.fromisoformat(data.start_time),
            end_time=time.fromisoformat(data.end_time),
        )
        self.db.add(slot)
        await self.db.flush()
        return slot

    async def delete_slot(self, school_id: uuid.UUID, slot_id: uuid.UUID) -> bool:
        result = await self.db.execute(
            select(TimetableSlot).where(
                TimetableSlot.id == slot_id, TimetableSlot.school_id == school_id
            )
        )
        slot = result.scalar_one_or_none()
        if not slot:
            return False
        await self.db.delete(slot)
        await self.db.flush()
        return True

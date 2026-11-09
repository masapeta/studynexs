"""Timetable service."""

import uuid
from datetime import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant_scope import TenantScope
from app.db.models.academic import Subject, TeacherSubjectMapping
from app.db.models.timetable import TimetableSlot
from app.db.models.user import User
from app.modules.timetable.schemas.timetable import TimetableSlotCreate, TimetableSlotOut


class TimetableAssignmentError(ValueError):
    """The chosen teacher is not mapped to teach this subject in this class."""


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

    async def class_timetable_out(
        self, school_id: uuid.UUID, class_id: uuid.UUID
    ) -> list[TimetableSlotOut]:
        """Class timetable with teacher and subject names resolved (tenant-scoped)."""
        slots = await self.get_class_timetable(school_id, class_id)
        if not slots:
            return []
        teachers = dict((await self.db.execute(
            select(User.id, User.full_name).where(
                User.school_id == school_id, User.id.in_({s.teacher_id for s in slots}))
        )).all())
        subjects = dict((await self.db.execute(
            select(Subject.id, Subject.name).where(
                Subject.school_id == school_id, Subject.id.in_({s.subject_id for s in slots}))
        )).all())
        return [
            TimetableSlotOut.model_validate(s).model_copy(update={
                "teacher_name": teachers.get(s.teacher_id),
                "subject_name": subjects.get(s.subject_id),
            })
            for s in slots
        ]

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

    async def list_subject_teachers(
        self, school_id: uuid.UUID, class_id: uuid.UUID, subject_id: uuid.UUID | None
    ) -> list[tuple[uuid.UUID, str, uuid.UUID]]:
        """Teachers mapped to this class (optionally one subject): (teacher_id, name, subject)."""
        query = (
            select(
                TeacherSubjectMapping.teacher_id,
                User.full_name,
                TeacherSubjectMapping.subject_id,
            )
            .join(User, User.id == TeacherSubjectMapping.teacher_id)
            .where(
                TeacherSubjectMapping.school_id == school_id,
                TeacherSubjectMapping.class_id == class_id,
                User.school_id == school_id,
                User.is_active.is_(True),
            )
            .order_by(User.full_name)
        )
        if subject_id is not None:
            query = query.where(TeacherSubjectMapping.subject_id == subject_id)
        return [(r[0], r[1], r[2]) for r in (await self.db.execute(query)).all()]

    async def create_slot(self, school_id: uuid.UUID, data: TimetableSlotCreate) -> TimetableSlot:
        scope = TenantScope(self.db, school_id)
        await scope.school_class(data.class_id)
        await scope.subject_in_class(data.subject_id, data.class_id)
        await scope.staff_user(data.teacher_id)
        mapped = await self.db.scalar(
            select(TeacherSubjectMapping.id).where(
                TeacherSubjectMapping.school_id == school_id,
                TeacherSubjectMapping.teacher_id == data.teacher_id,
                TeacherSubjectMapping.class_id == data.class_id,
                TeacherSubjectMapping.subject_id == data.subject_id,
            ).limit(1)
        )
        if mapped is None:
            raise TimetableAssignmentError(
                "Teacher is not assigned to teach this subject in this class"
            )
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

    async def get_slot(
        self, school_id: uuid.UUID, slot_id: uuid.UUID
    ) -> TimetableSlot | None:
        result = await self.db.execute(
            select(TimetableSlot).where(
                TimetableSlot.id == slot_id,
                TimetableSlot.school_id == school_id,
            )
        )
        return result.scalar_one_or_none()

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

"""Examination service."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant_scope import TenantScope
from app.db.models.examination import Exam, ExamMark
from app.modules.examinations.schemas.exam import ExamCreate, MarkEntry


class ExamService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_exam(self, school_id: uuid.UUID, data: ExamCreate, created_by: uuid.UUID) -> Exam:
        scope = TenantScope(self.db, school_id)
        await scope.school_class(data.class_id)
        await scope.subject_in_class(data.subject_id, data.class_id)
        exam = Exam(
            school_id=school_id,
            class_id=data.class_id,
            subject_id=data.subject_id,
            exam_type=data.exam_type,
            title=data.title,
            total_marks=data.total_marks,
            date=data.exam_date,
            created_by=created_by,
        )
        self.db.add(exam)
        await self.db.flush()
        return exam

    async def list_exams(self, school_id: uuid.UUID, class_id: uuid.UUID | None = None) -> list[Exam]:
        if class_id:
            await TenantScope(self.db, school_id).school_class(class_id)
        query = select(Exam).where(Exam.school_id == school_id)
        if class_id:
            query = query.where(Exam.class_id == class_id)
        result = await self.db.execute(query.order_by(Exam.date.desc()))
        return list(result.scalars().all())

    async def enter_marks(self, school_id: uuid.UUID, exam_id: uuid.UUID, entries: list[MarkEntry]) -> int:
        scope = TenantScope(self.db, school_id)
        exam = await scope.exam(exam_id)
        student_ids = [e.student_id for e in entries]
        await scope.students_in_class(exam.class_id, student_ids)
        count = 0
        for entry in entries:
            result = await self.db.execute(
                select(ExamMark).where(ExamMark.exam_id == exam_id, ExamMark.student_id == entry.student_id)
            )
            existing = result.scalar_one_or_none()
            if existing:
                existing.marks_obtained = entry.marks_obtained
                existing.grade_letter = entry.grade_letter
                existing.remarks = entry.remarks
            else:
                self.db.add(ExamMark(
                    school_id=school_id,
                    exam_id=exam_id,
                    student_id=entry.student_id,
                    marks_obtained=entry.marks_obtained,
                    grade_letter=entry.grade_letter,
                    remarks=entry.remarks,
                ))
            count += 1
        await self.db.flush()
        return count

    async def get_exam_marks(self, school_id: uuid.UUID, exam_id: uuid.UUID) -> list[ExamMark]:
        await TenantScope(self.db, school_id).exam(exam_id)
        result = await self.db.execute(
            select(ExamMark).where(
                ExamMark.exam_id == exam_id,
                ExamMark.school_id == school_id,
            )
        )
        return list(result.scalars().all())

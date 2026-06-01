"""Examination service."""
from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
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
        by_student = {e.student_id: e for e in entries}
        await scope.students_in_class(exam.class_id, list(by_student))
        if not by_student:
            return 0

        # Data integrity (not a race): reject marks above the exam's max.
        for e in by_student.values():
            if e.marks_obtained > exam.total_marks:
                raise ValueError("marks_obtained exceeds exam total_marks")

        rows = [
            {
                "school_id": school_id, "exam_id": exam_id, "student_id": sid,
                "marks_obtained": e.marks_obtained, "grade_letter": e.grade_letter,
                "remarks": e.remarks,
            }
            for sid, e in by_student.items()
        ]

        # Single race-safe upsert (no N+1, no check-then-insert race).
        stmt = pg_insert(ExamMark).values(rows)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_exam_student",
            set_={
                "marks_obtained": stmt.excluded.marks_obtained,
                "grade_letter": stmt.excluded.grade_letter,
                "remarks": stmt.excluded.remarks,
                "updated_at": func.now(),  # Core upsert skips the ORM onupdate
            },
        )
        await self.db.execute(stmt)
        await self.db.flush()
        return len(rows)

    async def get_exam_marks(self, school_id: uuid.UUID, exam_id: uuid.UUID) -> list[ExamMark]:
        await TenantScope(self.db, school_id).exam(exam_id)
        result = await self.db.execute(
            select(ExamMark).where(
                ExamMark.exam_id == exam_id,
                ExamMark.school_id == school_id,
            )
        )
        return list(result.scalars().all())

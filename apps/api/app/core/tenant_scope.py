"""
Tenant-scoped ownership checks — verify foreign IDs belong to the caller's school.
Use before any write that accepts cross-entity IDs from the client.
"""
from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import AcademicYear, Class, Subject, TeacherSubjectMapping
from app.db.models.examination import Exam
from app.db.models.student import Student
from app.db.models.user import User, UserRole


def _not_found(entity: str = "Resource") -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{entity} not found")


class TenantScope:
    """Validates that referenced entities belong to school_id."""

    def __init__(self, db: AsyncSession, school_id: uuid.UUID):
        self.db = db
        self.school_id = school_id

    async def academic_year(self, academic_year_id: uuid.UUID) -> AcademicYear:
        result = await self.db.execute(
            select(AcademicYear).where(
                AcademicYear.id == academic_year_id,
                AcademicYear.school_id == self.school_id,
            )
        )
        row = result.scalar_one_or_none()
        if not row:
            raise _not_found("Academic year")
        return row

    async def school_class(self, class_id: uuid.UUID) -> Class:
        result = await self.db.execute(
            select(Class).where(Class.id == class_id, Class.school_id == self.school_id)
        )
        row = result.scalar_one_or_none()
        if not row:
            raise _not_found("Class")
        return row

    async def subject_in_class(self, subject_id: uuid.UUID, class_id: uuid.UUID) -> Subject:
        await self.school_class(class_id)
        result = await self.db.execute(
            select(Subject).where(
                Subject.id == subject_id,
                Subject.school_id == self.school_id,
                Subject.class_id == class_id,
            )
        )
        row = result.scalar_one_or_none()
        if not row:
            raise _not_found("Subject")
        return row

    async def user_in_school(self, user_id: uuid.UUID) -> User:
        result = await self.db.execute(
            select(User).where(User.id == user_id, User.school_id == self.school_id)
        )
        row = result.scalar_one_or_none()
        if not row:
            raise _not_found("User")
        return row

    async def staff_user(self, user_id: uuid.UUID) -> User:
        """Teacher or admin staff — for class incharge / teacher mappings."""
        user = await self.user_in_school(user_id)
        if user.role not in (
            UserRole.TEACHER,
            UserRole.CLASS_INCHARGE,
            UserRole.ADMIN,
            UserRole.SUPER_ADMIN,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not eligible as teaching staff",
            )
        return user

    async def student(self, student_id: uuid.UUID) -> Student:
        result = await self.db.execute(
            select(Student).where(
                Student.id == student_id,
                Student.school_id == self.school_id,
            )
        )
        row = result.scalar_one_or_none()
        if not row:
            raise _not_found("Student")
        return row

    async def student_in_class(self, student_id: uuid.UUID, class_id: uuid.UUID) -> Student:
        student = await self.student(student_id)
        if student.class_id != class_id:
            raise _not_found("Student")
        return student

    async def students_in_class(
        self, class_id: uuid.UUID, student_ids: list[uuid.UUID]
    ) -> None:
        if not student_ids:
            return
        result = await self.db.execute(
            select(Student.id).where(
                Student.school_id == self.school_id,
                Student.class_id == class_id,
                Student.id.in_(student_ids),
            )
        )
        found = {row[0] for row in result.all()}
        if len(found) != len(set(student_ids)):
            raise _not_found("Student")

    async def exam(self, exam_id: uuid.UUID) -> Exam:
        result = await self.db.execute(
            select(Exam).where(Exam.id == exam_id, Exam.school_id == self.school_id)
        )
        row = result.scalar_one_or_none()
        if not row:
            raise _not_found("Exam")
        return row

    async def teacher_mapping_refs(
        self, teacher_id: uuid.UUID, subject_id: uuid.UUID, class_id: uuid.UUID
    ) -> None:
        await self.staff_user(teacher_id)
        await self.subject_in_class(subject_id, class_id)

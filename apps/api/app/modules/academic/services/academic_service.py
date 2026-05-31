"""Academic service — classes, subjects, enrollment, parent linking."""
from __future__ import annotations

import math
import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant_scope import TenantScope
from app.db.models.academic import Class, Subject, TeacherSubjectMapping
from app.db.models.student import Parent, Relationship, Student, StudentParentMap
from app.db.models.user import User
from app.modules.academic.schemas.academic import (
    ClassCreate,
    ParentLinkRequest,
    StudentEnroll,
    StudentOut,
    SubjectCreate,
    TeacherMappingCreate,
)


class AcademicService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Classes ──────────────────────────────────────────────────

    async def list_classes(
        self, school_id: uuid.UUID, page: int = 1, page_size: int = 50
    ) -> tuple[list[Class], int]:
        query = select(Class).where(Class.school_id == school_id)
        total = (await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )).scalar() or 0
        offset = (page - 1) * page_size
        result = await self.db.execute(
            query.order_by(Class.grade, Class.section).offset(offset).limit(page_size)
        )
        return list(result.scalars().all()), total

    async def create_class(self, school_id: uuid.UUID, data: ClassCreate) -> Class:
        scope = TenantScope(self.db, school_id)
        await scope.academic_year(data.academic_year_id)
        if data.class_incharge_id:
            await scope.staff_user(data.class_incharge_id)
        cls = Class(
            school_id=school_id,
            grade=data.grade,
            section=data.section,
            academic_year_id=data.academic_year_id,
            class_incharge_id=data.class_incharge_id,
            room_number=data.room_number,
        )
        self.db.add(cls)
        await self.db.flush()
        return cls

    async def get_class(self, school_id: uuid.UUID, class_id: uuid.UUID) -> Class | None:
        result = await self.db.execute(
            select(Class).where(Class.id == class_id, Class.school_id == school_id)
        )
        return result.scalar_one_or_none()

    # ── Subjects ─────────────────────────────────────────────────

    async def list_subjects(
        self, school_id: uuid.UUID, class_id: uuid.UUID | None = None
    ) -> list[Subject]:
        if class_id:
            await TenantScope(self.db, school_id).school_class(class_id)
        query = select(Subject).where(Subject.school_id == school_id)
        if class_id:
            query = query.where(Subject.class_id == class_id)
        result = await self.db.execute(query.order_by(Subject.name))
        return list(result.scalars().all())

    async def create_subject(self, school_id: uuid.UUID, data: SubjectCreate) -> Subject:
        await TenantScope(self.db, school_id).school_class(data.class_id)
        subject = Subject(
            school_id=school_id,
            name=data.name,
            code=data.code,
            class_id=data.class_id,
        )
        self.db.add(subject)
        await self.db.flush()
        return subject

    # ── Students ─────────────────────────────────────────────────

    async def list_students(
        self,
        school_id: uuid.UUID,
        class_id: uuid.UUID | None = None,
        page: int = 1,
        page_size: int = 50,
        search: str | None = None,
    ) -> tuple[list[StudentOut], int]:
        if class_id:
            await TenantScope(self.db, school_id).school_class(class_id)

        base = (
            select(Student, User.full_name, Class.grade, Class.section)
            .join(User, User.id == Student.user_id)
            .join(Class, Class.id == Student.class_id)
            .where(Student.school_id == school_id)
        )
        if class_id:
            base = base.where(Student.class_id == class_id)
        if search:
            term = f"%{search.strip()}%"
            base = base.where(
                or_(
                    Student.admission_no.ilike(term),
                    Student.roll_no.ilike(term),
                    User.full_name.ilike(term),
                )
            )

        count_q = select(func.count()).select_from(base.subquery())
        total = (await self.db.execute(count_q)).scalar() or 0
        offset = (page - 1) * page_size
        rows = await self.db.execute(
            base.order_by(Student.admission_no).offset(offset).limit(page_size)
        )
        items: list[StudentOut] = []
        for student, full_name, grade, section in rows.all():
            items.append(
                StudentOut(
                    id=student.id,
                    user_id=student.user_id,
                    class_id=student.class_id,
                    admission_no=student.admission_no,
                    roll_no=student.roll_no,
                    date_of_birth=student.date_of_birth,
                    gender=(
                        student.gender.value
                        if student.gender is not None and hasattr(student.gender, "value")
                        else student.gender
                    ),
                    student_name=full_name,
                    class_name=f"{grade}-{section}",
                )
            )
        return items, total

    async def enroll_student(self, school_id: uuid.UUID, data: StudentEnroll) -> Student:
        scope = TenantScope(self.db, school_id)
        await scope.user_in_school(data.user_id)
        await scope.school_class(data.class_id)
        student = Student(
            school_id=school_id,
            user_id=data.user_id,
            class_id=data.class_id,
            admission_no=data.admission_no,
            roll_no=data.roll_no,
            date_of_birth=data.date_of_birth,
            gender=data.gender,
        )
        self.db.add(student)
        await self.db.flush()
        return student

    # ── Parent Linking ───────────────────────────────────────────

    async def link_parent(
        self, school_id: uuid.UUID, student_id: uuid.UUID, data: ParentLinkRequest
    ) -> StudentParentMap:
        student = await self.get_student(school_id, student_id)
        if not student:
            raise ValueError("Student not found in this school")

        # Get or create parent record
        result = await self.db.execute(
            select(Parent).where(Parent.user_id == data.parent_user_id, Parent.school_id == school_id)
        )
        parent = result.scalar_one_or_none()

        if not parent:
            await TenantScope(self.db, school_id).user_in_school(data.parent_user_id)
            parent = Parent(
                school_id=school_id,
                user_id=data.parent_user_id,
                relationship_type=Relationship(data.relationship),
            )
            self.db.add(parent)
            await self.db.flush()

        link = StudentParentMap(
            student_id=student_id,
            parent_id=parent.id,
            is_primary=data.is_primary,
        )
        self.db.add(link)
        await self.db.flush()
        return link

    async def get_student(
        self, school_id: uuid.UUID, student_id: uuid.UUID
    ) -> Student | None:
        result = await self.db.execute(
            select(Student).where(Student.id == student_id, Student.school_id == school_id)
        )
        return result.scalar_one_or_none()

    async def get_student_parents(
        self, school_id: uuid.UUID, student_id: uuid.UUID
    ) -> list[StudentParentMap]:
        student = await self.get_student(school_id, student_id)
        if not student:
            return []
        result = await self.db.execute(
            select(StudentParentMap).where(StudentParentMap.student_id == student_id)
        )
        return list(result.scalars().all())

    # ── Teacher Mappings ─────────────────────────────────────────

    async def map_teacher(self, school_id: uuid.UUID, data: TeacherMappingCreate) -> TeacherSubjectMapping:
        await TenantScope(self.db, school_id).teacher_mapping_refs(
            data.teacher_id, data.subject_id, data.class_id
        )
        mapping = TeacherSubjectMapping(
            school_id=school_id,
            teacher_id=data.teacher_id,
            subject_id=data.subject_id,
            class_id=data.class_id,
            is_primary=data.is_primary,
        )
        self.db.add(mapping)
        await self.db.flush()
        return mapping

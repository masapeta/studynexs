"""Academic service — classes, subjects, enrollment, parent linking."""
from __future__ import annotations

import re
import uuid
from datetime import date
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant_scope import TenantScope
from app.db.models.academic import AcademicYear, Class, Subject, TeacherSubjectMapping
from app.db.models.attendance import Attendance, AttendanceStatus
from app.db.models.examination import Exam, ExamMark
from app.db.models.fee import StudentFeeRecord
from app.db.models.residential import ResidentialBlock, RoomAllocation
from app.db.models.school_ops import StudentTransport, TransportRoute
from app.db.models.student import (
    Enrollment,
    EnrollmentStatus,
    Parent,
    Relationship,
    Student,
    StudentParentMap,
)
from app.db.models.user import User
from app.modules.academic.schemas.academic import (
    ClassCreate,
    ClassRosterStudentOut,
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
        self,
        school_id: uuid.UUID,
        page: int = 1,
        page_size: int = 50,
        *,
        allowed_class_ids: set[uuid.UUID] | None = None,
    ) -> tuple[list[Class], int]:
        query = select(Class).where(Class.school_id == school_id)
        if allowed_class_ids is not None:
            query = query.where(Class.id.in_(allowed_class_ids))
        total = (await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )).scalar() or 0
        offset = (page - 1) * page_size
        result = await self.db.execute(
            query.order_by(Class.grade, Class.section).offset(offset).limit(page_size)
        )
        classes = list(result.scalars().all())
        classes.sort(
            key=lambda c: (
                int(m.group(1)) if (m := re.search(r"(\d+)", c.grade or "")) else 0,
                c.grade or "",
                c.section or "",
            )
        )
        await self._attach_class_stats(school_id, classes)
        return classes, total

    async def _attach_class_stats(self, school_id: uuid.UUID, classes: list[Class]) -> None:
        """Attach student_count + real attendance% and avg-score% to each Class (for the
        roster cards). None for attendance/score means 'no data yet' — the UI shows '—'
        instead of a misleading placeholder."""
        if not classes:
            return
        ids = [c.id for c in classes]

        counts = dict(
            (await self.db.execute(
                select(Student.class_id, func.count())
                .where(Student.school_id == school_id, Student.class_id.in_(ids))
                .group_by(Student.class_id)
            )).all()
        )

        # Weighted attendance: present/late = 1 day, half-day = 0.5, absent = 0.
        weight = case(
            (Attendance.status == AttendanceStatus.HALF_DAY, 0.5),
            (Attendance.status == AttendanceStatus.ABSENT, 0.0),
            else_=1.0,
        )
        att = (await self.db.execute(
            select(Attendance.class_id, func.count(), func.sum(weight))
            .where(Attendance.school_id == school_id, Attendance.class_id.in_(ids))
            .group_by(Attendance.class_id)
        )).all()
        att_map = {cid: round(float(credited) / n * 100, 1) for cid, n, credited in att if n}

        # Average % across the class's exam marks.
        score = (await self.db.execute(
            select(Exam.class_id, func.avg(ExamMark.marks_obtained / Exam.total_marks * 100))
            .join(Exam, ExamMark.exam_id == Exam.id)
            .where(
                Exam.school_id == school_id,
                Exam.class_id.in_(ids),
                Exam.total_marks > 0,
            )
            .group_by(Exam.class_id)
        )).all()
        score_map = {cid: round(float(avg), 1) for cid, avg in score if avg is not None}

        incharge_ids = [c.class_incharge_id for c in classes if c.class_incharge_id]
        incharge_names: dict[uuid.UUID, str] = {}
        if incharge_ids:
            incharge_names = dict(
                (await self.db.execute(
                    select(User.id, User.full_name).where(
                        User.school_id == school_id,
                        User.id.in_(incharge_ids),
                    )
                )).all()
            )

        for c in classes:
            c.student_count = counts.get(c.id, 0)
            c.attendance_pct = att_map.get(c.id)
            c.avg_score = score_map.get(c.id)
            c.class_incharge_name = (
                incharge_names.get(c.class_incharge_id) if c.class_incharge_id else None
            )

    async def _assert_unique_incharge(
        self,
        school_id: uuid.UUID,
        academic_year_id: uuid.UUID,
        incharge_id: uuid.UUID,
        *,
        exclude_class_id: uuid.UUID | None = None,
    ) -> None:
        """A teacher may be homeroom incharge for at most one class per academic year."""
        query = select(Class.grade, Class.section).where(
            Class.school_id == school_id,
            Class.academic_year_id == academic_year_id,
            Class.class_incharge_id == incharge_id,
        )
        if exclude_class_id is not None:
            query = query.where(Class.id != exclude_class_id)
        existing = (await self.db.execute(query)).first()
        if existing:
            grade, section = existing
            raise HTTPException(
                status_code=409,
                detail=(
                    "This teacher is already the homeroom teacher for "
                    f"{grade} {section} in this academic year"
                ),
            )

    async def create_class(self, school_id: uuid.UUID, data: ClassCreate) -> Class:
        scope = TenantScope(self.db, school_id)
        await scope.academic_year(data.academic_year_id)
        if data.class_incharge_id:
            await scope.staff_user(data.class_incharge_id)
            await self._assert_unique_incharge(
                school_id, data.academic_year_id, data.class_incharge_id
            )
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
        cls = result.scalar_one_or_none()
        if cls:
            await self._attach_class_stats(school_id, [cls])
        return cls

    async def list_class_roster(
        self, school_id: uuid.UUID, class_id: uuid.UUID
    ) -> list[ClassRosterStudentOut]:
        """Students in a class with individual attendance % (present/late/half-day credited)."""
        await TenantScope(self.db, school_id).school_class(class_id)

        weight = case(
            (Attendance.status == AttendanceStatus.HALF_DAY, 0.5),
            (Attendance.status == AttendanceStatus.ABSENT, 0.0),
            else_=1.0,
        )
        att_rows = (
            await self.db.execute(
                select(Attendance.student_id, func.count(), func.sum(weight))
                .where(
                    Attendance.school_id == school_id,
                    Attendance.class_id == class_id,
                )
                .group_by(Attendance.student_id)
            )
        ).all()
        att_map = {
            sid: round(float(credited) / n * 100, 1) for sid, n, credited in att_rows if n
        }

        rows = await self.db.execute(
            select(Student, User.full_name)
            .join(User, User.id == Student.user_id)
            .where(Student.school_id == school_id, Student.class_id == class_id)
            .order_by(Student.roll_no.nulls_last(), Student.admission_no)
        )
        return [
            ClassRosterStudentOut(
                id=student.id,
                admission_no=student.admission_no,
                roll_no=student.roll_no,
                student_name=full_name,
                attendance_pct=att_map.get(student.id),
            )
            for student, full_name in rows.all()
        ]

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
        page_rows = rows.all()
        student_ids = [student.id for student, _, _, _ in page_rows]
        parent_phones = await self._primary_parent_phones(school_id, student_ids)

        items: list[StudentOut] = []
        for student, full_name, grade, section in page_rows:
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
                    parent_phone=parent_phones.get(student.id),
                )
            )
        return items, total

    async def _primary_parent_phones(
        self, school_id: uuid.UUID, student_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, str | None]:
        """First linked parent mobile per student — prefers is_primary."""
        if not student_ids:
            return {}
        rows = (
            await self.db.execute(
                select(StudentParentMap.student_id, User.mobile)
                .join(Parent, Parent.id == StudentParentMap.parent_id)
                .join(User, User.id == Parent.user_id)
                .where(
                    Parent.school_id == school_id,
                    StudentParentMap.student_id.in_(student_ids),
                )
                .order_by(
                    StudentParentMap.student_id,
                    StudentParentMap.is_primary.desc(),
                )
            )
        ).all()
        phones: dict[uuid.UUID, str | None] = {}
        for student_id, mobile in rows:
            if student_id not in phones:
                phones[student_id] = mobile
        return phones

    async def enroll_student(self, school_id: uuid.UUID, data: StudentEnroll) -> Student:
        scope = TenantScope(self.db, school_id)
        await scope.user_in_school(data.user_id)
        cls = await scope.school_class(data.class_id)
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
        # DM-3: per-year history record. students.class_id stays the current
        # pointer; year rollover closes this row and inserts the next year's.
        self.db.add(
            Enrollment(
                school_id=school_id,
                student_id=student.id,
                class_id=data.class_id,
                academic_year_id=cls.academic_year_id,
                roll_no=data.roll_no,
                enrolled_on=date.today(),
            )
        )
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
            select(Parent).where(
                Parent.user_id == data.parent_user_id,
                Parent.school_id == school_id,
            )
        )
        parent = result.scalar_one_or_none()

        if not parent:
            await TenantScope(self.db, school_id).user_in_school(data.parent_user_id)
            parent = Parent(
                school_id=school_id,
                user_id=data.parent_user_id,
            )
            self.db.add(parent)
            await self.db.flush()

        link = StudentParentMap(
            school_id=school_id,
            student_id=student_id,
            parent_id=parent.id,
            is_primary=data.is_primary,
            # The relationship belongs to this specific parent↔student link.
            relationship_type=Relationship(data.relationship),
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

    # ── Enrollment history (DM-3) ────────────────────────────────

    async def current_enrollment(
        self, school_id: uuid.UUID, student_id: uuid.UUID
    ) -> Enrollment | None:
        """The student's open (ACTIVE) enrollment, if any."""
        result = await self.db.execute(
            select(Enrollment).where(
                Enrollment.school_id == school_id,
                Enrollment.student_id == student_id,
                Enrollment.status == EnrollmentStatus.ACTIVE,
            )
        )
        return result.scalar_one_or_none()

    async def enrollments_for_student(
        self, school_id: uuid.UUID, student_id: uuid.UUID, limit: int = 50
    ) -> list[Enrollment]:
        """Full enrollment history, newest academic year first."""
        result = await self.db.execute(
            select(Enrollment)
            .join(AcademicYear, AcademicYear.id == Enrollment.academic_year_id)
            .where(
                Enrollment.school_id == school_id,
                Enrollment.student_id == student_id,
            )
            .order_by(AcademicYear.start_date.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

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

    async def student_profile(self, school_id: uuid.UUID, student_id: uuid.UUID) -> dict | None:
        """Aggregate a student's full profile: info, parents, attendance, fees, transport."""
        student = await self.get_student(school_id, student_id)
        if not student:
            return None
        user = (
            await self.db.execute(select(User).where(User.id == student.user_id))
        ).scalar_one_or_none()
        cls = (
            await self.db.execute(select(Class).where(Class.id == student.class_id))
        ).scalar_one_or_none()

        parents = []
        for m in await self.get_student_parents(school_id, student_id):
            parent = (
                await self.db.execute(select(Parent).where(Parent.id == m.parent_id))
            ).scalar_one_or_none()
            if not parent:
                continue
            pu = (
                await self.db.execute(select(User).where(User.id == parent.user_id))
            ).scalar_one_or_none()
            parents.append({
                "name": pu.full_name if pu else "—",
                "relationship": m.relationship_type.value,
                "mobile": pu.mobile if pu else None,
                "email": pu.email if pu else None,
                "is_primary": m.is_primary,
            })

        att_rows = (
            await self.db.execute(
                select(Attendance.status, func.count())
                .where(Attendance.school_id == school_id, Attendance.student_id == student_id)
                .group_by(Attendance.status)
            )
        ).all()
        att = {(s.value if hasattr(s, "value") else s): c for s, c in att_rows}
        total_att = sum(att.values())
        credited = att.get("present", 0) + att.get("late", 0) + att.get("half_day", 0)
        attendance = {
            "present": att.get("present", 0),
            "absent": att.get("absent", 0),
            "late": att.get("late", 0),
            "total": total_att,
            "percentage": round(credited / total_att * 100, 1) if total_att else None,
        }

        fee_row = (
            await self.db.execute(
                select(
                    func.coalesce(func.sum(StudentFeeRecord.amount), 0),
                    func.coalesce(func.sum(StudentFeeRecord.paid_amount), 0),
                ).where(
                    StudentFeeRecord.school_id == school_id,
                    StudentFeeRecord.student_id == student_id,
                )
            )
        ).first()
        total_fee = (
            fee_row[0] if isinstance(fee_row[0], Decimal) else Decimal(str(fee_row[0] or 0))
        )
        paid = fee_row[1] if isinstance(fee_row[1], Decimal) else Decimal(str(fee_row[1] or 0))
        pending = max(Decimal("0.00"), total_fee - paid).quantize(Decimal("0.01"))
        # Preserve the existing JSON-number response while keeping fee arithmetic exact.
        fees = {"total": float(total_fee), "paid": float(paid), "pending": float(pending)}

        st = (
            await self.db.execute(
                select(StudentTransport).where(StudentTransport.student_id == student_id)
            )
        ).scalar_one_or_none()
        transport = None
        if st:
            route = (
                await self.db.execute(
                    select(TransportRoute).where(TransportRoute.id == st.route_id)
                )
            ).scalar_one_or_none()
            if route:
                transport = {
                    "route_name": route.route_name,
                    "boarding_stop": st.boarding_stop,
                    "driver_name": route.driver_name,
                    "vehicle_number": route.vehicle_number,
                }

        ra = (
            await self.db.execute(
                select(RoomAllocation).where(RoomAllocation.student_id == student_id)
            )
        ).scalar_one_or_none()
        residential = None
        if ra:
            block = (
                await self.db.execute(
                    select(ResidentialBlock).where(ResidentialBlock.id == ra.block_id)
                )
            ).scalar_one_or_none()
            if block:
                residential = {
                    "block_name": block.block_name,
                    "room_number": ra.room_number,
                    "warden_name": block.warden_name,
                    "warden_contact": block.warden_contact,
                }

        dob = student.date_of_birth.isoformat() if student.date_of_birth else None
        adm = student.admission_date.isoformat() if student.admission_date else None
        return {
            "id": str(student.id),
            "admission_no": student.admission_no,
            "roll_no": student.roll_no,
            # Lifecycle state (DM-3b) — drives which actions the admin UI offers.
            "status": student.status.value,
            "class_id": str(student.class_id),
            "student_name": user.full_name if user else "—",
            "mobile": user.mobile if user else None,
            "email": user.email if user else None,
            "class_name": f"{cls.grade} - {cls.section}" if cls else "—",
            "date_of_birth": dob,
            "gender": student.gender.value if student.gender else None,
            "blood_group": student.blood_group,
            "admission_date": adm,
            "apaar_number": student.apaar_number,
            "parents": parents,
            "attendance": attendance,
            "fees": fees,
            "transport": transport,
            "residential": residential,
        }

    # ── Teacher Mappings ─────────────────────────────────────────

    async def map_teacher(
        self, school_id: uuid.UUID, data: TeacherMappingCreate
    ) -> TeacherSubjectMapping:
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

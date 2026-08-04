"""
Student lifecycle service (DM-3b) — class change, grade correction, transfer,
withdrawal, re-admission, alumni.

Two invariants govern everything here:

1. **History stays history.** A class change updates the CURRENT enrollment
   row only. Past attendance, exam marks, and fee receipts keep pointing at
   the class they were recorded against — they are the historical record and
   are never rewritten.
2. **No fee mutation.** Unpaid dues are left exactly as they are. When a
   class change moves a student to a class with a different fee structure,
   the result flags `fee_review_required` so an admin can decide; the
   platform never silently changes what a family owes.
"""

from __future__ import annotations

import uuid
from datetime import date

import structlog
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant_scope import TenantScope
from app.db.models.academic import AcademicYear, Class
from app.db.models.audit import AuditLog
from app.db.models.fee import FeeStatus, FeeStructure, StudentFeeRecord
from app.db.models.student import (
    Enrollment,
    EnrollmentStatus,
    Student,
    StudentStatus,
)

logger = structlog.get_logger()

# Exit transitions: student lifecycle state -> how the enrollment closes.
_EXIT_TRANSITIONS: dict[StudentStatus, EnrollmentStatus] = {
    StudentStatus.TRANSFERRED: EnrollmentStatus.TRANSFERRED,
    StudentStatus.WITHDRAWN: EnrollmentStatus.WITHDRAWN,
    StudentStatus.ALUMNI: EnrollmentStatus.COMPLETED,
}


class StudentLifecycleService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Internals ────────────────────────────────────────────────

    async def _student(self, school_id: uuid.UUID, student_id: uuid.UUID) -> Student:
        result = await self.db.execute(
            select(Student).where(
                Student.id == student_id,
                Student.school_id == school_id,
            )
        )
        student = result.scalar_one_or_none()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Student not found"
            )
        return student

    async def _active_enrollment(
        self, school_id: uuid.UUID, student_id: uuid.UUID
    ) -> Enrollment | None:
        result = await self.db.execute(
            select(Enrollment).where(
                Enrollment.school_id == school_id,
                Enrollment.student_id == student_id,
                Enrollment.status == EnrollmentStatus.ACTIVE,
            )
        )
        return result.scalar_one_or_none()

    async def fee_structures_differ(
        self, school_id: uuid.UUID, from_class_id: uuid.UUID, to_class_id: uuid.UUID
    ) -> bool:
        """
        True when the two classes have different fee structures, meaning the
        student's unpaid dues may no longer match their new class. We only
        report this — we never change dues (see module docstring).

        Public because bulk class moves (DM-3c) apply the same rule; the check
        lives here so single and bulk paths can never drift apart.
        """
        if from_class_id == to_class_id:
            return False

        def _totals_query(class_id: uuid.UUID):
            return select(FeeStructure.fee_type, FeeStructure.amount).where(
                FeeStructure.school_id == school_id,
                FeeStructure.class_id == class_id,
            )

        old = {
            (row.fee_type, row.amount)
            for row in (await self.db.execute(_totals_query(from_class_id))).all()
        }
        new = {
            (row.fee_type, row.amount)
            for row in (await self.db.execute(_totals_query(to_class_id))).all()
        }
        return old != new

    async def _has_unsettled_dues(
        self, school_id: uuid.UUID, student_id: uuid.UUID
    ) -> bool:
        result = await self.db.execute(
            select(StudentFeeRecord.id)
            .where(
                StudentFeeRecord.school_id == school_id,
                StudentFeeRecord.student_id == student_id,
                StudentFeeRecord.status.in_(
                    [FeeStatus.PENDING, FeeStatus.PARTIAL, FeeStatus.OVERDUE]
                ),
            )
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    def _audit(
        self,
        *,
        school_id: uuid.UUID,
        actor_id: uuid.UUID,
        action: str,
        student_id: uuid.UUID,
        details: dict,
    ) -> None:
        """Append-only record of who changed what. Never silently skipped."""
        self.db.add(
            AuditLog(
                school_id=school_id,
                user_id=actor_id,
                action=action,
                resource_type="student_lifecycle",
                resource_id=str(student_id),
                details=details,
            )
        )

    # ── Class change (section rebalance / grade correction) ───────

    async def change_class(
        self,
        *,
        school_id: uuid.UUID,
        actor_id: uuid.UUID,
        student_id: uuid.UUID,
        new_class_id: uuid.UUID,
        reason: str,
        roll_no: str | None = None,
    ) -> dict:
        student = await self._student(school_id, student_id)
        if student.status != StudentStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Student is {student.status.value}; only active students change class",
            )

        new_class = await TenantScope(self.db, school_id).school_class(new_class_id)
        old_class_id = student.class_id
        if old_class_id == new_class_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student is already in this class",
            )

        enrollment = await self._active_enrollment(school_id, student_id)
        if enrollment is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Student has no active enrollment to update",
            )
        # A class change stays within one academic year. Moving across years is
        # promotion/rollover, which creates a new enrollment instead (DM-3c).
        if new_class.academic_year_id != enrollment.academic_year_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Target class belongs to a different academic year; "
                    "use promotion for year changes"
                ),
            )

        # Current enrollment only — history is untouched by design.
        enrollment.class_id = new_class_id
        if roll_no is not None:
            enrollment.roll_no = roll_no
        student.class_id = new_class_id
        if roll_no is not None:
            student.roll_no = roll_no

        fee_review = await self.fee_structures_differ(
            school_id, old_class_id, new_class_id
        ) and await self._has_unsettled_dues(school_id, student_id)

        self._audit(
            school_id=school_id,
            actor_id=actor_id,
            action="student.class_changed",
            student_id=student_id,
            details={
                "from_class_id": str(old_class_id),
                "to_class_id": str(new_class_id),
                "enrollment_id": str(enrollment.id),
                "reason": reason,
                "fee_review_required": fee_review,
            },
        )
        await self.db.flush()
        logger.info(
            "student_class_changed",
            school_id=str(school_id),
            student_id=str(student_id),
            fee_review_required=fee_review,
        )
        return {
            "student": student,
            "enrollment": enrollment,
            "fee_review_required": fee_review,
            "fee_review_note": (
                "Unpaid dues were left unchanged but the new class has a different "
                "fee structure. Review this student's pending fees."
                if fee_review
                else None
            ),
        }

    # ── Exits: transfer out / withdraw / alumni ───────────────────

    async def exit_student(
        self,
        *,
        school_id: uuid.UUID,
        actor_id: uuid.UUID,
        student_id: uuid.UUID,
        new_status: StudentStatus,
        reason: str,
        effective_date: date | None = None,
    ) -> dict:
        if new_status not in _EXIT_TRANSITIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported exit status",
            )

        student = await self._student(school_id, student_id)
        if student.status != StudentStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Student is already {student.status.value}",
            )

        enrollment = await self._active_enrollment(school_id, student_id)
        if enrollment is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Student has no active enrollment to close",
            )

        ended_on = effective_date or date.today()
        enrollment.status = _EXIT_TRANSITIONS[new_status]
        enrollment.ended_on = ended_on
        student.status = new_status

        # Exiting never clears money owed; surface it so admins can settle.
        outstanding = await self._has_unsettled_dues(school_id, student_id)

        self._audit(
            school_id=school_id,
            actor_id=actor_id,
            action=f"student.{new_status.value}",
            student_id=student_id,
            details={
                "enrollment_id": str(enrollment.id),
                "class_id": str(enrollment.class_id),
                "enrollment_status": enrollment.status.value,
                "effective_date": ended_on.isoformat(),
                "reason": reason,
                "outstanding_dues": outstanding,
            },
        )
        await self.db.flush()
        logger.info(
            "student_exited",
            school_id=str(school_id),
            student_id=str(student_id),
            new_status=new_status.value,
            outstanding_dues=outstanding,
        )
        return {
            "student": student,
            "enrollment": enrollment,
            "fee_review_required": outstanding,
            "fee_review_note": (
                "This student has unsettled dues. They were left unchanged — "
                "settle or waive them separately."
                if outstanding
                else None
            ),
        }

    # ── Re-admission ─────────────────────────────────────────────

    async def readmit_student(
        self,
        *,
        school_id: uuid.UUID,
        actor_id: uuid.UUID,
        student_id: uuid.UUID,
        class_id: uuid.UUID,
        reason: str,
        roll_no: str | None = None,
        effective_date: date | None = None,
    ) -> dict:
        student = await self._student(school_id, student_id)
        if student.status == StudentStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Student is already active",
            )

        new_class = await TenantScope(self.db, school_id).school_class(class_id)

        # One enrollment per student per year: if the student already has a row
        # for the target year (e.g. they left mid-year and are returning in the
        # same year), reopen it rather than violating the constraint.
        existing = (
            await self.db.execute(
                select(Enrollment).where(
                    Enrollment.school_id == school_id,
                    Enrollment.student_id == student_id,
                    Enrollment.academic_year_id == new_class.academic_year_id,
                )
            )
        ).scalar_one_or_none()

        enrolled_on = effective_date or date.today()
        if existing is not None:
            existing.status = EnrollmentStatus.ACTIVE
            existing.class_id = class_id
            existing.ended_on = None
            if roll_no is not None:
                existing.roll_no = roll_no
            enrollment = existing
            reopened = True
        else:
            enrollment = Enrollment(
                school_id=school_id,
                student_id=student_id,
                class_id=class_id,
                academic_year_id=new_class.academic_year_id,
                status=EnrollmentStatus.ACTIVE,
                roll_no=roll_no,
                enrolled_on=enrolled_on,
            )
            self.db.add(enrollment)
            reopened = False

        student.status = StudentStatus.ACTIVE
        student.class_id = class_id
        if roll_no is not None:
            student.roll_no = roll_no

        self._audit(
            school_id=school_id,
            actor_id=actor_id,
            action="student.readmitted",
            student_id=student_id,
            details={
                "class_id": str(class_id),
                "academic_year_id": str(new_class.academic_year_id),
                "reopened_existing_enrollment": reopened,
                "effective_date": enrolled_on.isoformat(),
                "reason": reason,
            },
        )
        await self.db.flush()
        logger.info(
            "student_readmitted",
            school_id=str(school_id),
            student_id=str(student_id),
            reopened=reopened,
        )
        return {
            "student": student,
            "enrollment": enrollment,
            "fee_review_required": False,
            "fee_review_note": None,
        }

    # ── History ──────────────────────────────────────────────────

    async def enrollment_history(
        self, school_id: uuid.UUID, student_id: uuid.UUID
    ) -> list[tuple[Enrollment, Class | None]]:
        """Enrollment rows with their class, newest academic year first."""
        await self._student(school_id, student_id)
        result = await self.db.execute(
            select(Enrollment, Class)
            .join(AcademicYear, AcademicYear.id == Enrollment.academic_year_id)
            .outerjoin(Class, Class.id == Enrollment.class_id)
            .where(
                Enrollment.school_id == school_id,
                Enrollment.student_id == student_id,
            )
            .order_by(AcademicYear.start_date.desc())
            .limit(50)
        )
        return [(row[0], row[1]) for row in result.all()]

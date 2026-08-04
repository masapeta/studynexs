"""
Bulk enrollment operations (DM-3c) — year-rollover promotion and bulk
section movement.

April is the moment this platform either works or embarrasses a school:
every student moves up a year at once. Three rules make that safe.

1. **Preview is the contract.** ``commit`` rebuilds the very plan ``preview``
   rendered, so an admin approves the real outcome rather than a guess. If
   the roster shifted in between, the difference surfaces in the summary
   instead of silently doing something else.
2. **Promotion is additive.** The old enrollment closes (promoted / detained
   / completed) and a new row opens for the next year. Nothing is
   overwritten, so last year's attendance, marks and receipts stay attached
   to last year's class.
3. **Nothing is skipped in silence.** A student who cannot be promoted —
   already transferred out, already enrolled next year, no active enrollment
   — appears in the plan as ``skipped`` with the reason attached.

Money is never touched here. Outstanding dues are reported as warnings so an
admin can settle them; the platform does not decide what a family owes.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date

import structlog
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant_scope import TenantScope
from app.db.models.academic import AcademicYear, Class
from app.db.models.audit import AuditLog
from app.db.models.fee import FeeStatus, StudentFeeRecord
from app.db.models.student import Enrollment, EnrollmentStatus, Student, StudentStatus
from app.db.models.user import User
from app.modules.academic.services.student_lifecycle_service import StudentLifecycleService

logger = structlog.get_logger()

# Outcome -> (how the current enrollment closes, does a new one open?)
_OUTCOMES: dict[str, tuple[EnrollmentStatus, bool]] = {
    "promoted": (EnrollmentStatus.PROMOTED, True),
    "detained": (EnrollmentStatus.DETAINED, True),
    "graduated": (EnrollmentStatus.COMPLETED, False),
}

_UNSETTLED = (FeeStatus.PENDING, FeeStatus.PARTIAL, FeeStatus.OVERDUE)


def _class_label(cls: Class) -> str:
    return f"{cls.grade} {cls.section}"


@dataclass
class _Action:
    """One student's promotion, resolved and ready to apply."""

    student: Student
    enrollment: Enrollment
    outcome: str
    target_class_id: uuid.UUID | None


@dataclass
class _Plan:
    from_class: Class
    to_class: Class
    from_year: AcademicYear
    to_year: AcademicYear
    candidates: list[dict] = field(default_factory=list)
    actions: list[_Action] = field(default_factory=list)

    def summary(self) -> dict[str, int]:
        counts = {"promoted": 0, "detained": 0, "graduated": 0, "skipped": 0}
        with_dues = 0
        for candidate in self.candidates:
            counts[candidate["outcome"]] = counts.get(candidate["outcome"], 0) + 1
            if candidate["has_unsettled_dues"]:
                with_dues += 1
        counts["total"] = len(self.candidates)
        counts["with_unsettled_dues"] = with_dues
        return counts

    def as_dict(self) -> dict:
        return {
            "from_class_id": self.from_class.id,
            "from_class_label": _class_label(self.from_class),
            "from_year_label": self.from_year.year_label,
            "to_class_id": self.to_class.id,
            "to_class_label": _class_label(self.to_class),
            "to_year_label": self.to_year.year_label,
            "candidates": self.candidates,
            "summary": self.summary(),
        }


class PromotionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Shared internals ─────────────────────────────────────────

    async def _year(self, school_id: uuid.UUID, year_id: uuid.UUID) -> AcademicYear:
        return await TenantScope(self.db, school_id).academic_year(year_id)

    async def _students_with_dues(
        self, school_id: uuid.UUID, student_ids: list[uuid.UUID]
    ) -> set[uuid.UUID]:
        """Batch form of the single-student dues check — one query, not N."""
        if not student_ids:
            return set()
        rows = await self.db.execute(
            select(StudentFeeRecord.student_id)
            .where(
                StudentFeeRecord.school_id == school_id,
                StudentFeeRecord.student_id.in_(student_ids),
                StudentFeeRecord.status.in_(_UNSETTLED),
            )
            .distinct()
        )
        return set(rows.scalars().all())

    def _audit(
        self,
        *,
        school_id: uuid.UUID,
        actor_id: uuid.UUID,
        action: str,
        resource_id: str,
        details: dict,
    ) -> None:
        self.db.add(
            AuditLog(
                school_id=school_id,
                user_id=actor_id,
                action=action,
                resource_type="enrollment_batch",
                resource_id=resource_id,
                details=details,
            )
        )

    async def _roster(
        self, school_id: uuid.UUID, class_id: uuid.UUID, academic_year_id: uuid.UUID
    ) -> list[tuple[Student, str | None, Enrollment]]:
        """
        The class roster as the enrollment table sees it — the enrollment row
        is what a promotion closes, so a student without one cannot be
        promoted and must not appear here.
        """
        rows = await self.db.execute(
            select(Student, User.full_name, Enrollment)
            .join(User, User.id == Student.user_id)
            .join(Enrollment, Enrollment.student_id == Student.id)
            .where(
                Enrollment.school_id == school_id,
                Enrollment.class_id == class_id,
                Enrollment.academic_year_id == academic_year_id,
            )
            .order_by(Enrollment.roll_no.nulls_last(), Student.admission_no)
        )
        return [(row[0], row[1], row[2]) for row in rows.all()]

    # ── Promotion planning ───────────────────────────────────────

    async def _build_plan(
        self,
        *,
        school_id: uuid.UUID,
        from_class_id: uuid.UUID,
        to_class_id: uuid.UUID,
        exclusions: list,
    ) -> _Plan:
        scope = TenantScope(self.db, school_id)
        from_class = await scope.school_class(from_class_id)
        to_class = await scope.school_class(to_class_id)

        if from_class.academic_year_id == to_class.academic_year_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Promotion moves students into a different academic year. "
                    "Use bulk class move for section changes within a year."
                ),
            )

        from_year = await self._year(school_id, from_class.academic_year_id)
        to_year = await self._year(school_id, to_class.academic_year_id)
        if to_year.start_date <= from_year.start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The target academic year must start after the current one",
            )

        overrides = self._index_exclusions(exclusions)
        targets = await self._resolve_override_classes(school_id, to_class, overrides)

        roster = await self._roster(school_id, from_class_id, from_class.academic_year_id)
        roster_ids = {student.id for student, _, _ in roster}
        unknown = set(overrides) - roster_ids
        if unknown:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{len(unknown)} listed student(s) are not in this class",
            )

        already_enrolled = await self._already_in_target_year(
            school_id, to_class.academic_year_id, list(roster_ids)
        )
        dues = await self._students_with_dues(school_id, list(roster_ids))

        plan = _Plan(
            from_class=from_class, to_class=to_class, from_year=from_year, to_year=to_year
        )
        for student, name, enrollment in roster:
            candidate = {
                "student_id": student.id,
                "student_name": name,
                "admission_no": student.admission_no,
                "roll_no": enrollment.roll_no or student.roll_no,
                "outcome": "skipped",
                "target_class_id": None,
                "target_class_label": None,
                "has_unsettled_dues": student.id in dues,
                "warnings": [],
            }

            reason = self._skip_reason(student, enrollment, student.id in already_enrolled)
            if reason:
                candidate["warnings"].append(reason)
                plan.candidates.append(candidate)
                continue

            override = overrides.get(student.id)
            outcome = override.outcome if override else "promoted"
            target = self._target_for(outcome, override, to_class, targets)

            candidate["outcome"] = outcome
            if target is not None:
                candidate["target_class_id"] = target.id
                candidate["target_class_label"] = _class_label(target)
            if candidate["has_unsettled_dues"]:
                candidate["warnings"].append(
                    "Has unsettled dues — they carry over unchanged"
                )

            plan.candidates.append(candidate)
            plan.actions.append(
                _Action(
                    student=student,
                    enrollment=enrollment,
                    outcome=outcome,
                    target_class_id=target.id if target is not None else None,
                )
            )
        return plan

    @staticmethod
    def _index_exclusions(exclusions: list) -> dict[uuid.UUID, object]:
        indexed: dict[uuid.UUID, object] = {}
        for item in exclusions:
            if item.student_id in indexed:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Student {item.student_id} is listed more than once",
                )
            if item.outcome not in _OUTCOMES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported outcome '{item.outcome}'",
                )
            indexed[item.student_id] = item
        return indexed

    async def _resolve_override_classes(
        self, school_id: uuid.UUID, to_class: Class, overrides: dict
    ) -> dict[uuid.UUID, Class]:
        """Detained students repeat the year in a class the admin nominates."""
        wanted = {
            item.target_class_id for item in overrides.values() if item.target_class_id
        }
        if not wanted:
            return {}
        rows = await self.db.execute(
            select(Class).where(Class.id.in_(wanted), Class.school_id == school_id)
        )
        found = {cls.id: cls for cls in rows.scalars().all()}
        missing = wanted - set(found)
        if missing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{len(missing)} target class(es) not found",
            )
        for cls in found.values():
            if cls.academic_year_id != to_class.academic_year_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Target class {_class_label(cls)} is not in the academic "
                        "year being promoted into"
                    ),
                )
        return found

    async def _already_in_target_year(
        self, school_id: uuid.UUID, year_id: uuid.UUID, student_ids: list[uuid.UUID]
    ) -> set[uuid.UUID]:
        if not student_ids:
            return set()
        rows = await self.db.execute(
            select(Enrollment.student_id).where(
                Enrollment.school_id == school_id,
                Enrollment.academic_year_id == year_id,
                Enrollment.student_id.in_(student_ids),
            )
        )
        return set(rows.scalars().all())

    @staticmethod
    def _skip_reason(
        student: Student, enrollment: Enrollment, already_enrolled: bool
    ) -> str | None:
        if student.status != StudentStatus.ACTIVE:
            return f"Student is {student.status.value}"
        if enrollment.status != EnrollmentStatus.ACTIVE:
            return f"Enrollment is already {enrollment.status.value}"
        if already_enrolled:
            return "Already enrolled in the target academic year"
        return None

    @staticmethod
    def _target_for(
        outcome: str, override, to_class: Class, targets: dict[uuid.UUID, Class]
    ) -> Class | None:
        if outcome == "graduated":
            return None
        if outcome == "detained":
            if override is None or override.target_class_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "A detained student needs a target class for the new year "
                        "(the class they will repeat in)"
                    ),
                )
            return targets[override.target_class_id]
        return to_class

    # ── Promotion: preview + commit ──────────────────────────────

    async def preview_promotion(
        self,
        *,
        school_id: uuid.UUID,
        from_class_id: uuid.UUID,
        to_class_id: uuid.UUID,
        exclusions: list,
    ) -> dict:
        plan = await self._build_plan(
            school_id=school_id,
            from_class_id=from_class_id,
            to_class_id=to_class_id,
            exclusions=exclusions,
        )
        return plan.as_dict()

    async def commit_promotion(
        self,
        *,
        school_id: uuid.UUID,
        actor_id: uuid.UUID,
        from_class_id: uuid.UUID,
        to_class_id: uuid.UUID,
        exclusions: list,
        reason: str,
    ) -> dict:
        plan = await self._build_plan(
            school_id=school_id,
            from_class_id=from_class_id,
            to_class_id=to_class_id,
            exclusions=exclusions,
        )

        # The year boundaries are the truth about when an enrollment starts and
        # ends — not the day an admin happens to run the rollover.
        ended_on: date = plan.from_year.end_date
        enrolled_on: date = plan.to_year.start_date

        created = 0
        for action in plan.actions:
            close_as, opens_new = _OUTCOMES[action.outcome]
            action.enrollment.status = close_as
            action.enrollment.ended_on = ended_on

            if opens_new and action.target_class_id is not None:
                self.db.add(
                    Enrollment(
                        school_id=school_id,
                        student_id=action.student.id,
                        class_id=action.target_class_id,
                        academic_year_id=plan.to_year.id,
                        status=EnrollmentStatus.ACTIVE,
                        roll_no=action.enrollment.roll_no,
                        enrolled_on=enrolled_on,
                    )
                )
                action.student.class_id = action.target_class_id
                created += 1
            else:
                # Graduating students leave the school as alumni.
                action.student.status = StudentStatus.ALUMNI

        summary = plan.summary()
        self._audit(
            school_id=school_id,
            actor_id=actor_id,
            action="enrollment.promoted_batch",
            resource_id=str(from_class_id),
            details={
                "from_class_id": str(from_class_id),
                "to_class_id": str(to_class_id),
                "from_year": plan.from_year.year_label,
                "to_year": plan.to_year.year_label,
                "reason": reason,
                "summary": summary,
                "students": [
                    {
                        "student_id": str(a.student.id),
                        "outcome": a.outcome,
                        "target_class_id": str(a.target_class_id)
                        if a.target_class_id
                        else None,
                    }
                    for a in plan.actions
                ],
            },
        )
        await self.db.flush()
        logger.info(
            "enrollment_promoted_batch",
            school_id=str(school_id),
            from_class_id=str(from_class_id),
            to_class_id=str(to_class_id),
            **summary,
        )

        result = plan.as_dict()
        result["enrollments_created"] = created
        result["enrollments_closed"] = len(plan.actions)
        return result

    # ── Bulk section movement (within one academic year) ─────────

    async def bulk_change_class(
        self,
        *,
        school_id: uuid.UUID,
        actor_id: uuid.UUID,
        from_class_id: uuid.UUID,
        to_class_id: uuid.UUID,
        student_ids: list[uuid.UUID] | None,
        reason: str,
    ) -> dict:
        """
        Move a group of students between sections of the same academic year.
        Like the single-student class change, this updates the CURRENT
        enrollment only — history stays where it was recorded.
        """
        scope = TenantScope(self.db, school_id)
        from_class = await scope.school_class(from_class_id)
        to_class = await scope.school_class(to_class_id)

        if from_class_id == to_class_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Source and target class are the same",
            )
        if from_class.academic_year_id != to_class.academic_year_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Both classes must be in the same academic year. "
                    "Use promotion to move students across years."
                ),
            )

        roster = await self._roster(school_id, from_class_id, from_class.academic_year_id)
        if student_ids is not None:
            wanted = set(student_ids)
            found = {student.id for student, _, _ in roster}
            unknown = wanted - found
            if unknown:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{len(unknown)} listed student(s) are not in this class",
                )
            roster = [row for row in roster if row[0].id in wanted]

        dues = await self._students_with_dues(
            school_id, [student.id for student, _, _ in roster]
        )
        structures_differ = await StudentLifecycleService(self.db).fee_structures_differ(
            school_id, from_class_id, to_class_id
        )

        moved: list[dict] = []
        skipped: list[dict] = []
        for student, name, enrollment in roster:
            reason_to_skip = self._skip_reason(student, enrollment, already_enrolled=False)
            if reason_to_skip:
                skipped.append(
                    {
                        "student_id": student.id,
                        "student_name": name,
                        "reason": reason_to_skip,
                    }
                )
                continue

            enrollment.class_id = to_class_id
            student.class_id = to_class_id
            moved.append(
                {
                    "student_id": student.id,
                    "student_name": name,
                    "fee_review_required": structures_differ and student.id in dues,
                }
            )

        fee_review_count = sum(1 for row in moved if row["fee_review_required"])
        self._audit(
            school_id=school_id,
            actor_id=actor_id,
            action="enrollment.class_changed_batch",
            resource_id=str(from_class_id),
            details={
                "from_class_id": str(from_class_id),
                "to_class_id": str(to_class_id),
                "reason": reason,
                "moved": [str(row["student_id"]) for row in moved],
                "skipped": len(skipped),
                "fee_review_required": fee_review_count,
            },
        )
        await self.db.flush()
        logger.info(
            "enrollment_class_changed_batch",
            school_id=str(school_id),
            from_class_id=str(from_class_id),
            to_class_id=str(to_class_id),
            moved=len(moved),
            skipped=len(skipped),
        )
        return {
            "from_class_id": from_class_id,
            "from_class_label": _class_label(from_class),
            "to_class_id": to_class_id,
            "to_class_label": _class_label(to_class),
            "moved": moved,
            "skipped": skipped,
            "fee_review_required_count": fee_review_count,
            "fee_review_note": (
                f"{fee_review_count} student(s) have unsettled dues and the new class "
                "has a different fee structure. Dues were left unchanged — review them."
                if fee_review_count
                else None
            ),
        }

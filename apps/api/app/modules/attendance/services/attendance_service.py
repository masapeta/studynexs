"""Attendance service — bulk marking and summaries."""
from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant_scope import TenantScope
from app.db.models.attendance import Attendance
from app.modules.attendance.schemas.attendance import AttendanceEntry


class AttendanceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def mark_bulk(
        self, school_id: uuid.UUID, class_id: uuid.UUID,
        att_date: date, entries: list[AttendanceEntry], marked_by: uuid.UUID,
    ) -> int:
        """Mark attendance for an entire class. Returns count of records created."""
        scope = TenantScope(self.db, school_id)
        await scope.school_class(class_id)
        await scope.students_in_class(class_id, [e.student_id for e in entries])

        # De-dupe by student (last write wins) — ON CONFLICT can't touch the same row twice.
        by_student = {e.student_id: e for e in entries}
        if not by_student:
            return 0
        rows = [
            {
                "school_id": school_id, "student_id": sid, "class_id": class_id,
                "date": att_date, "status": e.status, "marked_by": marked_by,
                "remarks": e.remarks,
            }
            for sid, e in by_student.items()
        ]

        # Single race-safe upsert (no N+1, no check-then-insert race).
        stmt = pg_insert(Attendance).values(rows)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_attendance_student_date",
            set_={
                # The constraint is (school_id, student_id, date) — one row per student per
                # day — so a student who changed class must have the row *moved*. Omitting
                # class_id left it on the old class: the new teacher's mark reported success
                # but the student vanished from their register and still counted against the
                # class they had left. (audit P1-DATA-001)
                "class_id": stmt.excluded.class_id,
                "status": stmt.excluded.status,
                "remarks": stmt.excluded.remarks,
                "marked_by": stmt.excluded.marked_by,
                "updated_at": func.now(),  # Core upsert skips the ORM onupdate
            },
        )
        await self.db.execute(stmt)
        await self.db.flush()
        return len(rows)

    async def get_class_attendance(
        self, school_id: uuid.UUID, class_id: uuid.UUID, att_date: date
    ) -> list[Attendance]:
        result = await self.db.execute(
            select(Attendance).where(
                Attendance.school_id == school_id,
                Attendance.class_id == class_id,
                Attendance.date == att_date,
            )
        )
        return list(result.scalars().all())

    async def get_summary(
        self, school_id: uuid.UUID, class_id: uuid.UUID, att_date: date
    ) -> dict:
        result = await self.db.execute(
            select(Attendance.status, func.count()).where(
                Attendance.school_id == school_id,
                Attendance.class_id == class_id,
                Attendance.date == att_date,
            ).group_by(Attendance.status)
        )
        counts = {row[0].value: row[1] for row in result.all()}
        total = sum(counts.values())
        return {
            "total": total,
            "present": counts.get("present", 0),
            "absent": counts.get("absent", 0),
            "late": counts.get("late", 0),
            "half_day": counts.get("half_day", 0),
        }

    async def get_school_summary(
        self, school_id: uuid.UUID, att_date: date
    ) -> dict:
        """Get school-wide attendance summary for the dashboard."""
        result = await self.db.execute(
            select(Attendance.status, func.count()).where(
                Attendance.school_id == school_id,
                Attendance.date == att_date,
            ).group_by(Attendance.status)
        )
        counts = {row[0].value: row[1] for row in result.all()}
        total = sum(counts.values())
        # Calculate percentage (present + late + half_day count as attended)
        attended = counts.get("present", 0) + counts.get("late", 0) + counts.get("half_day", 0)
        percentage = round((attended / total * 100), 1) if total > 0 else 0.0

        return {
            "total": total,
            "present": counts.get("present", 0),
            "absent": counts.get("absent", 0),
            "late": counts.get("late", 0),
            "half_day": counts.get("half_day", 0),
            "percentage": percentage
        }

"""Attendance service — bulk marking and summaries."""
from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant_scope import TenantScope
from app.db.models.attendance import Attendance, AttendanceStatus
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
        count = 0
        for entry in entries:
            # Upsert: check if already exists
            result = await self.db.execute(
                select(Attendance).where(
                    Attendance.school_id == school_id,
                    Attendance.student_id == entry.student_id,
                    Attendance.date == att_date,
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                existing.status = entry.status
                existing.remarks = entry.remarks
                existing.marked_by = marked_by
            else:
                self.db.add(Attendance(
                    school_id=school_id,
                    student_id=entry.student_id,
                    class_id=class_id,
                    date=att_date,
                    status=entry.status,
                    marked_by=marked_by,
                    remarks=entry.remarks,
                ))
            count += 1
        await self.db.flush()
        return count

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

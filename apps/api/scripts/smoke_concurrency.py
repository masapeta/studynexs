"""Concurrency proof for the M2 upsert fix: two simultaneous bulk-marks for the same
class/date must resolve to ONE row per student with no error (the old check-then-insert
crashed the second with a unique-violation). Also checks the de-dupe trap.

Run:  python scripts/smoke_concurrency.py
Uses a far-future date so it can't clash with seeded attendance; cleans up after.
"""
from __future__ import annotations

import asyncio
from datetime import date

from sqlalchemy import delete, func, select

from app.core.database import async_session_factory
from app.db.models.academic import Class
from app.db.models.attendance import Attendance, AttendanceStatus
from app.db.models.school import School
from app.db.models.student import Student
from app.db.models.user import User, UserRole
from app.modules.attendance.schemas.attendance import AttendanceEntry
from app.modules.attendance.services.attendance_service import AttendanceService

TEST_DATE = date(2099, 1, 1)


async def _save(school_id, class_id, student_ids, marked_by, status):
    """One independent session marking the whole class — run several concurrently."""
    async with async_session_factory() as db:
        svc = AttendanceService(db)
        entries = [AttendanceEntry(student_id=sid, status=status) for sid in student_ids]
        await svc.mark_bulk(school_id, class_id, TEST_DATE, entries, marked_by)
        await db.commit()


async def main() -> None:
    async with async_session_factory() as db:
        school = (
            await db.execute(select(School).where(School.tenant_slug == "test"))
        ).scalar_one()
        cls = (await db.execute(
            select(Class).where(Class.school_id == school.id, Class.grade == "Class 10")
        )).scalars().first()
        students = (await db.execute(
            select(Student)
            .where(Student.school_id == school.id, Student.class_id == cls.id)
            .limit(5)
        )).scalars().all()
        sids = [s.id for s in students]
        principal = (await db.execute(
            select(User).where(User.school_id == school.id, User.role == UserRole.SUPER_ADMIN)
        )).scalars().first()
        # clean slate
        await db.execute(delete(Attendance).where(
            Attendance.student_id.in_(sids), Attendance.date == TEST_DATE
        ))
        await db.commit()

    # ── Race: 4 concurrent saves for the same class/date ──────────────────────
    statuses = [
        AttendanceStatus.PRESENT, AttendanceStatus.ABSENT,
        AttendanceStatus.LATE, AttendanceStatus.PRESENT,
    ]
    results = await asyncio.gather(
        *[_save(school.id, cls.id, sids, principal.id, st) for st in statuses],
        return_exceptions=True,
    )
    errors = [r for r in results if isinstance(r, Exception)]

    async with async_session_factory() as db:
        rows = await db.scalar(select(func.count()).select_from(Attendance).where(
            Attendance.student_id.in_(sids), Attendance.date == TEST_DATE
        ))
    print(f">>> concurrent saves: {len(statuses)} tasks, errors={len(errors)}")
    print(f">>> attendance rows for {len(sids)} students on {TEST_DATE}: {rows} "
          f"(expected {len(sids)} - one per student, no duplicates)")
    if errors:
        print(">>> ERROR sample:", repr(errors[0])[:160])

    # ── De-dupe trap: same student twice in one payload must not crash ────────
    dup_ok = True
    try:
        async with async_session_factory() as db:
            svc = AttendanceService(db)
            dupe = [
                AttendanceEntry(student_id=sids[0], status=AttendanceStatus.PRESENT),
                AttendanceEntry(student_id=sids[0], status=AttendanceStatus.ABSENT),
            ]
            await svc.mark_bulk(school.id, cls.id, TEST_DATE, dupe, principal.id)
            await db.commit()
    except Exception as e:  # noqa: BLE001
        dup_ok = False
        print(">>> dedupe trap FAILED:", repr(e)[:160])
    print(f">>> same-student-twice payload handled cleanly: {dup_ok}")

    # cleanup
    async with async_session_factory() as db:
        await db.execute(delete(Attendance).where(
            Attendance.student_id.in_(sids), Attendance.date == TEST_DATE
        ))
        await db.commit()

    ok = not errors and rows == len(sids) and dup_ok
    print(">>> RESULT:", "RACE-SAFE (PASS)" if ok else "NEEDS ATTENTION")


if __name__ == "__main__":
    asyncio.run(main())

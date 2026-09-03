"""Seed notices + a weekly timetable for the SSC demo school, so those pages (and the
dashboard's Recent Notices) show real data instead of empty states / placeholders.

Run:  python scripts/seed_demo_extras.py
Idempotent: skips notices if any exist; skips timetable if any slot exists.
"""
from __future__ import annotations

import asyncio
import sys
from datetime import datetime, time, timedelta, timezone
from pathlib import Path

_scripts_dir = Path(__file__).resolve().parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

from reference_school_config import TENANT_SLUG
from sqlalchemy import func, select

from app.core.database import async_session_factory
from app.db.models.academic import Class, Subject
from app.db.models.communication import Notice, NoticePriority
from app.db.models.school import School
from app.db.models.timetable import DayOfWeek, TimetableSlot
from app.db.models.user import User, UserRole

TENANT = TENANT_SLUG

# (title, content, priority, target_roles, days_ago)
NOTICES = [
    ("Annual Sports Day — 15 June",
     "The Annual Sports Day will be held on 15 June at the school grounds. All students "
     "must report by 8:00 AM in their house colours. Parents are warmly invited.",
     NoticePriority.HIGH, ["student", "parent"], 1),
    ("Parent–Teacher Meeting this Saturday",
     "The term PTM is scheduled for Saturday, 10:00 AM–1:00 PM. Please meet your ward's "
     "class teacher to discuss progress and collect the term report card.",
     NoticePriority.HIGH, ["parent"], 2),
    ("Half-Yearly Examination Schedule",
     "The half-yearly examination timetable has been released. Exams begin 24 June. "
     "The detailed subject-wise schedule is available with class teachers.",
     NoticePriority.HIGH, ["student", "parent"], 4),
    ("Term-1 Fee Payment Reminder",
     "This is a gentle reminder that Term-1 fees are due by the 10th. Payments can be made "
     "online or at the school office. Kindly clear any pending dues at the earliest.",
     NoticePriority.MEDIUM, ["parent"], 6),
    ("Independence Day Celebrations",
     "Independence Day will be celebrated on 15 August with flag hoisting at 8:30 AM, "
     "followed by cultural programmes. Attendance is compulsory for all students.",
     NoticePriority.MEDIUM, ["student", "parent", "teacher"], 9),
]

# (period_number, start, end)
PERIODS = [
    (1, time(9, 0), time(9, 45)),
    (2, time(9, 45), time(10, 30)),
    (3, time(10, 45), time(11, 30)),
    (4, time(11, 30), time(12, 15)),
    (5, time(13, 0), time(13, 45)),
    (6, time(13, 45), time(14, 30)),
]
DAYS = [
    DayOfWeek.MONDAY, DayOfWeek.TUESDAY, DayOfWeek.WEDNESDAY,
    DayOfWeek.THURSDAY, DayOfWeek.FRIDAY,
]


async def main() -> None:
    async with async_session_factory() as db:
        school = (
            await db.execute(select(School).where(School.tenant_slug == TENANT))
        ).scalar_one_or_none()
        if school is None:
            print(f"Demo school (tenant_slug='{TENANT}') not found. Run seed_demo_ssc.py first.")
            return

        principal = (
            await db.execute(
                select(User).where(
                    User.school_id == school.id, User.role == UserRole.SUPER_ADMIN
                )
            )
        ).scalars().first()
        teachers = (
            await db.execute(
                select(User).where(User.school_id == school.id, User.role == UserRole.TEACHER)
            )
        ).scalars().all()

        # ── Notices ──────────────────────────────────────────────────────────
        existing_notices = await db.scalar(
            select(func.count()).select_from(Notice).where(Notice.school_id == school.id)
        )
        n_notices = 0
        if existing_notices:
            print(f"Notices already present (count={existing_notices}); skipping notices.")
        else:
            now = datetime.now(timezone.utc)
            for title, content, priority, roles, days_ago in NOTICES:
                db.add(Notice(
                    school_id=school.id, title=title, content=content,
                    target_roles=roles, priority=priority, created_by=principal.id,
                    created_at=now - timedelta(days=days_ago),
                ))
                n_notices += 1

        # ── Timetable ────────────────────────────────────────────────────────
        existing_slots = await db.scalar(
            select(func.count()).select_from(TimetableSlot).where(
                TimetableSlot.school_id == school.id
            )
        )
        n_slots = 0
        if existing_slots:
            print(f"Timetable already present (count={existing_slots}); skipping timetable.")
        elif not teachers:
            print("No teachers found; skipping timetable.")
        else:
            classes = (
                await db.execute(select(Class).where(Class.school_id == school.id))
            ).scalars().all()
            for cls in classes:
                subjects = (
                    await db.execute(
                        select(Subject).where(
                            Subject.school_id == school.id, Subject.class_id == cls.id
                        )
                    )
                ).scalars().all()
                if not subjects:
                    continue
                for di, day in enumerate(DAYS):
                    for pi, (pnum, st, et) in enumerate(PERIODS):
                        subj = subjects[(di + pi) % len(subjects)]
                        teacher = teachers[(di + pi) % len(teachers)]
                        db.add(TimetableSlot(
                            school_id=school.id, class_id=cls.id, subject_id=subj.id,
                            teacher_id=teacher.id, day_of_week=day, period_number=pnum,
                            start_time=st, end_time=et,
                        ))
                        n_slots += 1

        await db.commit()
        print(f"Seeded extras: notices={n_notices}  timetable_slots={n_slots}")


if __name__ == "__main__":
    asyncio.run(main())

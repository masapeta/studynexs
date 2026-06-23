"""Patch existing demo school (tenant_slug='test') with RBAC assignments.

Run after pulling RBAC changes without recreating the DB:
  cd apps/api && python scripts/patch_demo_ssc_rbac.py
"""
from __future__ import annotations

import asyncio

from datetime import time

from sqlalchemy import delete, select

from app.core.database import async_session_factory
from app.db.models.academic import Class, Subject, TeacherSubjectMapping
from app.db.models.timetable import DayOfWeek, TimetableSlot
from app.db.models.school import School
from app.db.models.user import User, UserRole

TEACHER_SPECS = [
    ("teacher1", "Lakshmi Devi", UserRole.CLASS_INCHARGE),
    ("teacher2", "Ramesh Kumar", UserRole.CLASS_INCHARGE),
    ("teacher3", "Sunitha Rao", UserRole.CLASS_INCHARGE),
    ("teacher4", "Venkat Reddy", UserRole.CLASS_INCHARGE),
    ("teacher5", "Anjali Sharma", UserRole.CLASS_INCHARGE),
    ("teacher6", "Kiran Naidu", UserRole.TEACHER),
    ("teacher7", "Priya Goud", UserRole.TEACHER),
    ("teacher8", "Mahesh Varma", UserRole.TEACHER),
]

INCHARGE_BY_GRADE = {
    ("Class 10", "A"): "teacher1",
    ("Class 10", "B"): "teacher2",
    ("Class 9", "A"): "teacher3",
    ("Class 9", "B"): "teacher4",
    ("Class 8", "A"): "teacher5",
}


async def main() -> None:
    async with async_session_factory() as db:
        school = (
            await db.execute(select(School).where(School.tenant_slug == "test"))
        ).scalar_one_or_none()
        if not school:
            print("Demo school (tenant_slug='test') not found. Run seed_demo_ssc.py first.")
            return

        teachers: dict[str, User] = {}
        for uname, full_name, role in TEACHER_SPECS:
            user = (
                await db.execute(
                    select(User).where(User.school_id == school.id, User.username == uname)
                )
            ).scalar_one_or_none()
            if not user:
                print(f"  Skip: {uname} not found")
                continue
            user.full_name = full_name
            user.role = role
            teachers[uname] = user

        classes = list(
            (await db.execute(select(Class).where(Class.school_id == school.id))).scalars().all()
        )
        for c in classes:
            c.class_incharge_id = None
        for (grade, section), uname in INCHARGE_BY_GRADE.items():
            t = teachers.get(uname)
            if not t:
                continue
            cls = next((x for x in classes if x.grade == grade and x.section == section), None)
            if cls:
                cls.class_incharge_id = t.id

        await db.execute(
            delete(TeacherSubjectMapping).where(TeacherSubjectMapping.school_id == school.id)
        )

        subjects = list(
            (await db.execute(select(Subject).where(Subject.school_id == school.id))).scalars().all()
        )
        by_key = {(s.class_id, s.name): s for s in subjects}

        def map_teacher(uname: str, grade: str, section: str, subject_name: str) -> None:
            t = teachers.get(uname)
            cls = next((x for x in classes if x.grade == grade and x.section == section), None)
            if not t or not cls:
                return
            subj = by_key.get((cls.id, subject_name))
            if not subj:
                return
            db.add(
                TeacherSubjectMapping(
                    school_id=school.id,
                    teacher_id=t.id,
                    subject_id=subj.id,
                    class_id=cls.id,
                    is_primary=True,
                )
            )

        for section in ("A", "B"):
            map_teacher("teacher6", "Class 10", section, "Mathematics")
            map_teacher("teacher7", "Class 10", section, "Science")
            map_teacher("teacher8", "Class 10", section, "English")
        map_teacher("teacher1", "Class 10", "A", "Telugu")
        map_teacher("teacher2", "Class 10", "B", "Telugu")

        # Point Class 10 Mathematics timetable slots at teacher6 (demo dashboard "Today's Classes")
        maths_teacher = teachers.get("teacher6")
        if maths_teacher:
            for section in ("A", "B"):
                cls = next(
                    (x for x in classes if x.grade == "Class 10" and x.section == section),
                    None,
                )
                if not cls:
                    continue
                subj = by_key.get((cls.id, "Mathematics"))
                if not subj:
                    continue
                slots = (
                    await db.execute(
                        select(TimetableSlot).where(
                            TimetableSlot.school_id == school.id,
                            TimetableSlot.class_id == cls.id,
                            TimetableSlot.subject_id == subj.id,
                        )
                    )
                ).scalars().all()
                for slot in slots:
                    slot.teacher_id = maths_teacher.id
                if not slots:
                    for day in (
                        DayOfWeek.MONDAY, DayOfWeek.TUESDAY, DayOfWeek.WEDNESDAY,
                        DayOfWeek.THURSDAY, DayOfWeek.FRIDAY,
                    ):
                        db.add(
                            TimetableSlot(
                                school_id=school.id,
                                class_id=cls.id,
                                subject_id=subj.id,
                                teacher_id=maths_teacher.id,
                                day_of_week=day,
                                period_number=2,
                                start_time=time(9, 45),
                                end_time=time(10, 30),
                            )
                        )

        await db.commit()
        print("Patched demo RBAC for tenant 'test'.")
        print("  teacher1 = Class 10-A incharge | teacher6 = Maths subject teacher")


if __name__ == "__main__":
    asyncio.run(main())

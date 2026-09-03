"""Seed exams + marks for the SSC demo school so Exams and Report Cards have real data.

Two exams per subject per class — a Mid-Term (50) and a Final (100) — so a report card
genuinely *consolidates* marks across exams. Each student gets a stable "ability" with
per-subject variation, so there's an identifiable strongest/weakest subject and the
AI report-card remark has something real to say.

Run:  python scripts/seed_exam_marks.py
Idempotent: skips if any exam already exists for the demo school.
"""
from __future__ import annotations

import asyncio
import random
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

_scripts_dir = Path(__file__).resolve().parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

from reference_school_config import SCHOOL_NAME, TENANT_SLUG
from sqlalchemy import func, select

from app.core.database import async_session_factory
from app.db.models.academic import Class, Subject
from app.db.models.examination import Exam, ExamMark, ExamType
from app.db.models.school import School
from app.db.models.student import Student
from app.db.models.user import User, UserRole

random.seed(2026)

TENANT = TENANT_SLUG

# (exam_type, title, total_marks, date)
EXAM_PLAN = [
    (ExamType.MID_TERM, "Mid-Term Examination", 50, date(2026, 9, 15)),
    (ExamType.FINAL, "Final Examination", 100, date(2027, 3, 10)),
]


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


async def main() -> None:
    async with async_session_factory() as db:
        school = (
            await db.execute(select(School).where(School.tenant_slug == TENANT))
        ).scalar_one_or_none()
        if school is None:
            print(f"Demo school (tenant_slug='{TENANT}') not found. Run seed_demo_ssc.py first.")
            return

        existing = await db.scalar(
            select(func.count()).select_from(Exam).where(Exam.school_id == school.id)
        )
        if existing:
            print(f"Exams already seeded for this school (count={existing}). Skipping.")
            return

        principal = (
            await db.execute(
                select(User).where(
                    User.school_id == school.id,
                    User.role.in_([UserRole.SUPER_ADMIN, UserRole.ADMIN]),
                )
            )
        ).scalars().first()
        if principal is None:
            print("No admin/principal user found; cannot set exam.created_by.")
            return

        classes = (
            await db.execute(select(Class).where(Class.school_id == school.id))
        ).scalars().all()

        n_exams = 0
        n_marks = 0
        for c in classes:
            subjects = (
                await db.execute(
                    select(Subject).where(
                        Subject.school_id == school.id, Subject.class_id == c.id
                    )
                )
            ).scalars().all()
            students = (
                await db.execute(
                    select(Student).where(
                        Student.school_id == school.id, Student.class_id == c.id
                    )
                )
            ).scalars().all()

            # Stable per-student ability + per-(student,subject) lean.
            ability = {s.id: random.uniform(0.45, 0.92) for s in students}
            lean = {
                (s.id, sub.id): random.uniform(-0.18, 0.18)
                for s in students
                for sub in subjects
            }

            for sub in subjects:
                for exam_type, title, total, dt in EXAM_PLAN:
                    exam = Exam(
                        school_id=school.id, class_id=c.id, subject_id=sub.id,
                        exam_type=exam_type, title=f"{title} — {sub.name}",
                        total_marks=Decimal(str(total)), date=dt, created_by=principal.id,
                    )
                    db.add(exam)
                    await db.flush()
                    n_exams += 1
                    for s in students:
                        frac = _clamp(
                            ability[s.id] + lean[(s.id, sub.id)] + random.uniform(-0.05, 0.05),
                            0.30, 0.99,
                        )
                        db.add(ExamMark(
                            school_id=school.id, exam_id=exam.id, student_id=s.id,
                            marks_obtained=Decimal(str(round(total * frac))),
                        ))
                        n_marks += 1

        await db.commit()
        print(f"Seeded exams + marks for '{SCHOOL_NAME}'")
        print(f"  exams={n_exams}  marks={n_marks}  classes={len(classes)}")
        print("  Demo Report Cards on: Class 10 · any student")


if __name__ == "__main__":
    asyncio.run(main())

"""Gate 1 (G1-02): one-command demo E2E seed for the hands-on walkthrough.

Chains idempotent demo seeds, adds a Class 10 Maths exam-mistake for the AI tutor,
and prints login card + verification hints.

Run from apps/api (Postgres + migrations required):
  python scripts/seed_demo_e2e_journey.py
"""
from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path

from sqlalchemy import select

from app.core.database import async_session_factory
from app.db.models.academic import Class, Subject
from app.db.models.misconception import MisconceptionEntry
from app.db.models.school import School
from app.db.models.student import Student
from app.db.models.user import User
from app.modules.examinations.services.misconception_service import _fingerprint

TENANT = "test"
SCRIPTS = [
    "seed_demo_ssc.py",
    "patch_demo_ssc_rbac.py",
    "seed_demo_extras.py",
    "seed_exam_marks.py",
    "seed_parents.py",
    "patch_demo_portal_logins.py",
    "seed_teacher_dashboard.py",
    "seed_working_session.py",
]


def _run_chain() -> None:
    here = Path(__file__).resolve().parent
    py = sys.executable
    for name in SCRIPTS:
        path = here / name
        if not path.exists():
            print(f"SKIP missing {name}")
            continue
        print(f"\n--- {name} ---")
        subprocess.run([py, str(path)], check=False, cwd=here.parent)


async def _seed_tutor_misconception() -> None:
    """Give student_demo a fractions mistake so tutor shows exam-driven lesson."""
    async with async_session_factory() as db:
        school = (
            await db.execute(select(School).where(School.tenant_slug == TENANT))
        ).scalar_one_or_none()
        if school is None:
            print("No demo school — run seed_demo_ssc.py first.")
            return

        principal = (
            await db.execute(
                select(User).where(User.school_id == school.id, User.username == "principal")
            )
        ).scalar_one_or_none()
        if principal is None:
            print("No principal user.")
            return

        cls = (
            await db.execute(
                select(Class).where(
                    Class.school_id == school.id,
                    Class.grade == "Class 10",
                    Class.section == "A",
                )
            )
        ).scalar_one_or_none()
        if cls is None:
            return

        stu = (
            await db.execute(
                select(Student).where(
                    Student.school_id == school.id,
                    Student.class_id == cls.id,
                    Student.roll_no == "1",
                )
            )
        ).scalar_one_or_none()
        if stu is None:
            return

        maths = (
            await db.execute(
                select(Subject).where(
                    Subject.school_id == school.id,
                    Subject.class_id == cls.id,
                    Subject.name == "Mathematics",
                )
            )
        ).scalar_one_or_none()
        if maths is None:
            return

        topic = "Fractions — adding with different denominators"
        mistake = (
            "Added numerators and denominators separately (e.g. 1/2 + 1/3 = 2/5) "
            "instead of finding a common denominator first."
        )
        fp = _fingerprint(topic=topic, mistake=mistake)
        existing = (
            await db.execute(
                select(MisconceptionEntry).where(
                    MisconceptionEntry.school_id == school.id,
                    MisconceptionEntry.content_fingerprint == fp,
                    MisconceptionEntry.student_id == stu.id,
                )
            )
        ).scalar_one_or_none()
        if existing is None:
            db.add(
                MisconceptionEntry(
                    school_id=school.id,
                    class_id=cls.id,
                    subject_id=maths.id,
                    student_id=stu.id,
                    topic=topic,
                    question_no="7",
                    common_mistake=mistake,
                    remedial_activity="Practice LCM and equivalent fractions before adding.",
                    created_by=principal.id,
                    content_fingerprint=fp,
                    occurrence_count=1,
                )
            )
            await db.commit()
            print("  + tutor misconception seeded for student_demo (fractions)")
        else:
            print("  = tutor misconception already present")


def _print_card() -> None:
    print(
        """
=== Demo E2E journey ready (tenant: test) ===

Logins (password for all: Demo@1234):
  principal     -> Admin dashboard
  teacher6      -> Class 10 Maths (AI Papers, Exams, Report Cards)
  parent_demo   -> Parent portal
  student_demo  -> Student portal + AI Tutor (fractions lesson)

Suggested flow:
  Teacher: AI Papers -> Generate/Approve -> Exams -> Report Cards -> Mastery
  Student: /student/tutor -> Play Neerja voice on fractions step
  Parent:  child overview + fees

Smoke (API + web must be running):
  python scripts/smoke_demo_readiness.py
  cd ../admin-web && npm run e2e-smoke
"""
    )


def main() -> None:
    _run_chain()
    asyncio.run(_seed_tutor_misconception())
    _print_card()


if __name__ == "__main__":
    main()

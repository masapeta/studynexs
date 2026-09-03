"""Seed StudyNexs Reference School — ARM International School (full working model).

One command for prospects to experience the platform end-to-end:
  cd apps/api && python scripts/seed_reference_school.py

Chains idempotent demo seeds, curriculum pack, and closed learning-loop demo v1 assets,
prints login card for principal / teacher / parent / student.

Requires: Postgres + migrations applied.
"""
from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path

_scripts_dir = Path(__file__).resolve().parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

from reference_school_config import (
    DEMO_PASSWORD,
    LOGIN_PARENT,
    LOGIN_PRINCIPAL,
    LOGIN_STUDENT,
    LOGIN_TEACHER_MATHS,
    SCHOOL_NAME,
    TENANT_SLUG,
)
from sqlalchemy import select

from app.core.database import async_session_factory
from app.db.models.academic import Class
from app.db.models.misconception import MisconceptionEntry
from app.db.models.school import School
from app.db.models.student import Student

SCRIPTS = [
    "seed_demo_ssc.py",
    "patch_demo_ssc_rbac.py",
    "seed_demo_extras.py",
    "seed_exam_marks.py",
    "seed_parents.py",
    "patch_demo_portal_logins.py",
    "seed_teacher_dashboard.py",
    "seed_working_session.py",
    "seed_reference_school_curriculum.py",
    "seed_reference_school_demo_v1.py",
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


async def _cleanup_legacy_fractions_misconception() -> None:
    """Remove old fractions misconception seed — demo v1 uses exam-derived topics."""
    async with async_session_factory() as db:
        school = (
            await db.execute(select(School).where(School.tenant_slug == TENANT_SLUG))
        ).scalar_one_or_none()
        if school is None:
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

        rows = (
            await db.execute(
                select(MisconceptionEntry).where(
                    MisconceptionEntry.school_id == school.id,
                    MisconceptionEntry.student_id == stu.id,
                    MisconceptionEntry.topic.ilike("%fraction%"),
                )
            )
        ).scalars().all()
        for row in rows:
            await db.delete(row)
        if rows:
            await db.commit()
            print(f"  - removed {len(rows)} legacy fractions misconception(s)")


def _print_login_card() -> None:
    print(
        f"""
=== StudyNexs Reference School ready ===
Display name: {SCHOOL_NAME}
Tenant slug:  {TENANT_SLUG}

Set in admin-web/.env.local:
  NEXT_PUBLIC_TENANT_SLUG={TENANT_SLUG}

Logins (password for all: {DEMO_PASSWORD}):
  {LOGIN_PRINCIPAL:<14} -> Principal dashboard (school health, insights)
  {LOGIN_TEACHER_MATHS:<14} -> Class 10 Maths (AI papers, exams, gradebook)
  {LOGIN_PARENT:<14} -> Parent portal (attendance, child overview, copilot)
  {LOGIN_STUDENT:<14} -> Student portal + AI tutor

Demo v1 journeys:
  1. Principal -> teacher timetable -> curriculum -> lesson plan
  2. Teacher -> exam -> submissions -> review -> analytics
  3. Parent -> attendance -> assigned work -> AI summary
  4. Principal dashboard -> school health -> learning + teacher signals

Validate (API on :8000):
  python scripts/smoke_reference_school.py
"""
    )


def main() -> None:
    print(f"Seeding Reference School: {SCHOOL_NAME} (tenant={TENANT_SLUG})")
    _run_chain()
    asyncio.run(_cleanup_legacy_fractions_misconception())
    _print_login_card()


if __name__ == "__main__":
    main()

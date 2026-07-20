"""Seed parents/guardians for demo students so the student profile shows real guardians.

Each student gets a father (primary) and ~70% also a mother, linked via StudentParentMap.
Parents log in by mobile OTP, so no password hash is set (keeps this fast).

Run:  python scripts/seed_parents.py
Idempotent: skips if any student-parent link already exists.
"""
from __future__ import annotations

import asyncio
import random
import sys
from pathlib import Path

_scripts_dir = Path(__file__).resolve().parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

from sqlalchemy import func, select

from app.core.database import async_session_factory
from app.db.models.school import School
from app.db.models.student import Parent, Relationship, Student, StudentParentMap
from app.db.models.user import User, UserRole

from reference_school_config import TENANT_SLUG

random.seed(7)
MALE = ["Ramesh", "Suresh", "Venkat", "Prakash", "Srinivas",
        "Mohan", "Ravi", "Anil", "Krishna", "Naresh"]
FEMALE = ["Lakshmi", "Padma", "Sunitha", "Radha", "Geetha",
          "Sarita", "Anitha", "Vani", "Madhavi", "Sailaja"]


async def main() -> None:
    async with async_session_factory() as db:
        school = (
            await db.execute(select(School).where(School.tenant_slug == TENANT_SLUG))
        ).scalar_one_or_none()
        if school is None:
            print("Demo school not found. Run seed_demo_ssc.py first.")
            return

        existing = await db.scalar(select(func.count()).select_from(StudentParentMap))
        if existing:
            print(f"Parent links already exist (count={existing}); skipping.")
            return

        students = (
            await db.execute(select(Student).where(Student.school_id == school.id))
        ).scalars().all()

        seq = 60000000
        n_parents = 0
        n_links = 0
        for stu in students:
            su = (
                await db.execute(select(User).where(User.id == stu.user_id))
            ).scalar_one_or_none()
            surname = su.full_name.split()[-1] if su and su.full_name else "Kumar"

            seq += 1
            father = User(
                school_id=school.id, mobile=f"+9196{seq:08d}",
                full_name=f"{random.choice(MALE)} {surname}", role=UserRole.PARENT,
                email=f"parent{seq}@example.com", is_active=True,
            )
            db.add(father)
            await db.flush()
            fp = Parent(
                school_id=school.id, user_id=father.id,
                relationship_type=Relationship.FATHER,
            )
            db.add(fp)
            await db.flush()
            db.add(StudentParentMap(student_id=stu.id, parent_id=fp.id, is_primary=True))
            n_parents += 1
            n_links += 1

            if random.random() < 0.7:
                seq += 1
                mother = User(
                    school_id=school.id, mobile=f"+9196{seq:08d}",
                    full_name=f"{random.choice(FEMALE)} {surname}", role=UserRole.PARENT,
                    email=f"parent{seq}@example.com", is_active=True,
                )
                db.add(mother)
                await db.flush()
                mp = Parent(
                    school_id=school.id, user_id=mother.id,
                    relationship_type=Relationship.MOTHER,
                )
                db.add(mp)
                await db.flush()
                db.add(StudentParentMap(student_id=stu.id, parent_id=mp.id, is_primary=False))
                n_parents += 1
                n_links += 1

        await db.commit()
        print(f"Seeded parents={n_parents} links={n_links} for {len(students)} students")


if __name__ == "__main__":
    asyncio.run(main())

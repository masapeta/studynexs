"""Add password logins for sales demos: parent_demo and student_demo (Class 10-A).

Run after seed_demo_ssc.py (and optionally seed_parents.py):
  cd apps/api && python scripts/patch_demo_portal_logins.py

Idempotent — safe to re-run.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

_scripts_dir = Path(__file__).resolve().parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

from reference_school_config import DEMO_PASSWORD, TENANT_SLUG
from sqlalchemy import select

from app.core.database import async_session_factory
from app.core.security import hash_password
from app.db.models.academic import Class
from app.db.models.school import School
from app.db.models.student import Parent, Relationship, Student, StudentParentMap
from app.db.models.user import User, UserRole

TENANT = TENANT_SLUG


async def main() -> None:
    async with async_session_factory() as db:
        school = (
            await db.execute(select(School).where(School.tenant_slug == TENANT))
        ).scalar_one_or_none()
        if school is None:
            print("Demo school not found. Run seed_demo_ssc.py first.")
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
            print("Class 10-A not found.")
            return

        stu = (
            await db.execute(
                select(Student)
                .where(Student.school_id == school.id, Student.class_id == cls.id, Student.roll_no == "1")
            )
        ).scalar_one_or_none()
        if stu is None:
            stu = (
                await db.execute(
                    select(Student)
                    .where(Student.school_id == school.id, Student.class_id == cls.id)
                    .order_by(Student.roll_no)
                )
            ).scalars().first()
        if stu is None:
            print("No student in Class 10-A.")
            return

        stu_user = (
            await db.execute(select(User).where(User.id == stu.user_id))
        ).scalar_one()
        stu_user.username = "student_demo"
        stu_user.password_hash = hash_password(DEMO_PASSWORD)
        stu_user.role = UserRole.STUDENT
        stu_user.is_active = True

        parent_user = (
            await db.execute(
                select(User).where(User.school_id == school.id, User.username == "parent_demo")
            )
        ).scalar_one_or_none()
        if parent_user is None:
            parent_user = User(
                school_id=school.id,
                username="parent_demo",
                mobile="+919800009999",
                full_name=f"Parent of {stu_user.full_name}",
                email="parent_demo@example.com",
                role=UserRole.PARENT,
                password_hash=hash_password(DEMO_PASSWORD),
                is_active=True,
            )
            db.add(parent_user)
            await db.flush()
        else:
            parent_user.password_hash = hash_password(DEMO_PASSWORD)
            parent_user.is_active = True

        parent_row = (
            await db.execute(select(Parent).where(Parent.user_id == parent_user.id))
        ).scalar_one_or_none()
        if parent_row is None:
            parent_row = Parent(
                school_id=school.id,
                user_id=parent_user.id,
            )
            db.add(parent_row)
            await db.flush()

        existing_link = (
            await db.execute(
                select(StudentParentMap).where(
                    StudentParentMap.student_id == stu.id,
                    StudentParentMap.parent_id == parent_row.id,
                )
            )
        ).scalar_one_or_none()
        if existing_link is None:
            db.add(
                StudentParentMap(
                    school_id=school.id,
                    student_id=stu.id,
                    parent_id=parent_row.id,
                    is_primary=True,
                    relationship_type=Relationship.FATHER,
                )
            )

        await db.commit()
        print(f"Demo portal logins ready (tenant: {TENANT}, password: {DEMO_PASSWORD})")
        print(f"  parent_demo  -> child: {stu_user.full_name} (Class 10-A, roll {stu.roll_no})")
        print(f"  student_demo -> {stu_user.full_name}")
        print("  teacher6     -> Maths teacher (existing seed)")
        print("  principal    -> staff dashboard (existing seed)")


if __name__ == "__main__":
    asyncio.run(main())

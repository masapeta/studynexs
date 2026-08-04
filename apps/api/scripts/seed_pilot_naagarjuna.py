"""Gate 2 (G2-10): minimal pilot tenant for Naagarjuna Talent School.

Class 10 · Mathematics wedge only — separate from demo tenant `test`.
Idempotent: skips if tenant_slug='naagarjuna' already exists.

Run from apps/api (Postgres + migrations required):
  python scripts/seed_pilot_naagarjuna.py

Admin-web: set NEXT_PUBLIC_TENANT_SLUG=naagarjuna when testing this school locally.
"""
from __future__ import annotations

import asyncio
from datetime import date

from sqlalchemy import select

from app.core.database import async_session_factory
from app.core.security import hash_password
from app.db.models.academic import AcademicYear, Class, Subject, TeacherSubjectMapping
from app.db.models.school import School
from app.db.models.student import (
    Enrollment,
    Gender,
    Parent,
    Relationship,
    Student,
    StudentParentMap,
)
from app.db.models.user import User, UserRole
from app.modules.ai.services.ai_credits import DEFAULT_AI_BUDGET

TENANT = "naagarjuna"
PASSWORD = "Demo@1234"

STUDENT_NAMES: list[tuple[str, Gender]] = [
    ("Akhil Reddy", Gender.MALE),
    ("Bhavana Rao", Gender.FEMALE),
    ("Charan Naidu", Gender.MALE),
    ("Deepika Sharma", Gender.FEMALE),
    ("Eswar Goud", Gender.MALE),
    ("Harika Varma", Gender.FEMALE),
    ("Karthik Kumar", Gender.MALE),
    ("Lasya Chowdary", Gender.FEMALE),
    ("Nikhil Mudiraj", Gender.MALE),
    ("Sneha Pillai", Gender.FEMALE),
]


async def main() -> None:
    async with async_session_factory() as db:
        existing = (
            await db.execute(select(School).where(School.tenant_slug == TENANT))
        ).scalar_one_or_none()
        if existing:
            print(f"Pilot school already exists (tenant_slug='{TENANT}'). Nothing to do.")
            _print_login_card()
            return

        school = School(
            name="Naagarjuna Talent School",
            code="NTS01",
            tenant_slug=TENANT,
            board="SSC",
            contact_email="hello@studynexs.com",
            contact_phone="+919000000000",
            address={
                "city": "Telangana",
                "state": "Telangana",
                "note": "Pilot tenant — Class 10 Maths wedge",
            },
            is_active=True,
            settings={
                "ai_budget": {
                    **DEFAULT_AI_BUDGET,
                    "monthly_credits": 100,
                    "teacher_monthly_credits": 25,
                    "incharge_monthly_credits": 60,
                    "limits": {
                        "qp_full_per_month": 5,
                        "qp_regen_per_month": 20,
                    },
                    "plan": "pilot",
                },
                "pilot": {
                    "wedge": "class_10_maths_exam_loop",
                    "gate": 2,
                },
            },
        )
        db.add(school)
        await db.flush()

        ay = AcademicYear(
            school_id=school.id,
            year_label="2026-2027",
            start_date=date(2026, 6, 1),
            end_date=date(2027, 4, 30),
            is_active=True,
        )
        db.add(ay)
        await db.flush()

        principal = User(
            school_id=school.id,
            username="principal",
            mobile="+919900000001",
            full_name="Principal (Naagarjuna)",
            role=UserRole.SUPER_ADMIN,
            email="hello@studynexs.com",
            password_hash=hash_password(PASSWORD),
            is_active=True,
        )
        incharge = User(
            school_id=school.id,
            username="incharge",
            mobile="+919900000002",
            full_name="Class 10 In-charge",
            role=UserRole.CLASS_INCHARGE,
            password_hash=hash_password(PASSWORD),
            is_active=True,
        )
        maths_teacher = User(
            school_id=school.id,
            username="maths_teacher",
            mobile="+919900000003",
            full_name="Class 10 Maths Teacher",
            role=UserRole.TEACHER,
            password_hash=hash_password(PASSWORD),
            is_active=True,
        )
        db.add_all([principal, incharge, maths_teacher])
        await db.flush()

        cls = Class(
            school_id=school.id,
            grade="Class 10",
            section="A",
            academic_year_id=ay.id,
            room_number="10A",
            class_incharge_id=incharge.id,
        )
        db.add(cls)
        await db.flush()

        maths = Subject(
            school_id=school.id,
            name="Mathematics",
            code="MAT10",
            class_id=cls.id,
        )
        db.add(maths)
        await db.flush()

        db.add(
            TeacherSubjectMapping(
                school_id=school.id,
                teacher_id=maths_teacher.id,
                subject_id=maths.id,
                class_id=cls.id,
                is_primary=True,
            )
        )

        parent_user = User(
            school_id=school.id,
            username="parent_demo",
            mobile="+919900000010",
            full_name="Parent Demo",
            role=UserRole.PARENT,
            password_hash=hash_password(PASSWORD),
            is_active=True,
        )
        db.add(parent_user)
        await db.flush()

        parent = Parent(
            school_id=school.id,
            user_id=parent_user.id,
            relationship_type=Relationship.FATHER,
        )
        db.add(parent)
        await db.flush()

        students: list[Student] = []
        for roll, (name, gender) in enumerate(STUDENT_NAMES, start=1):
            u = User(
                school_id=school.id,
                mobile=f"+91987{100000 + roll:06d}",
                full_name=name,
                role=UserRole.STUDENT,
                is_active=True,
            )
            if roll == 1:
                u.username = "student_demo"
                u.password_hash = hash_password(PASSWORD)
            db.add(u)
            await db.flush()
            stu = Student(
                school_id=school.id,
                user_id=u.id,
                class_id=cls.id,
                admission_no=f"NTS{roll:04d}",
                roll_no=str(roll),
                date_of_birth=date(2010, 6, 15),
                gender=gender,
            )
            db.add(stu)
            await db.flush()
            # DM-3: per-year enrollment history alongside the current-class pointer.
            db.add(
                Enrollment(
                    school_id=school.id,
                    student_id=stu.id,
                    class_id=cls.id,
                    academic_year_id=ay.id,
                    roll_no=str(roll),
                    enrolled_on=date(2026, 6, 1),
                )
            )
            await db.flush()
            students.append(stu)

        db.add(
            StudentParentMap(
                student_id=students[0].id,
                parent_id=parent.id,
                is_primary=True,
            )
        )

        await db.commit()
        print("Seeded pilot tenant: Naagarjuna Talent School")
        print(f"  tenant_slug={TENANT}  class=10-A  students={len(students)}  subject=Mathematics")
        _print_login_card()


def _print_login_card() -> None:
    print()
    print("  Login card (set NEXT_PUBLIC_TENANT_SLUG=naagarjuna in admin-web):")
    print(f"    Principal:      principal      / {PASSWORD}")
    print(f"    Class incharge:   incharge       / {PASSWORD}  (approve papers & marks)")
    print(f"    Maths teacher:    maths_teacher  / {PASSWORD}  (generate QP, evaluate)")
    print(f"    Parent (demo):    parent_demo    / {PASSWORD}")
    print(f"    Student (demo):   student_demo   / {PASSWORD}  (roll 1)")
    print()
    print("  Next: python scripts/seed_pilot_naagarjuna_curriculum.py")


if __name__ == "__main__":
    asyncio.run(main())

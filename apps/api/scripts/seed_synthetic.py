"""
StudyNexs — Synthetic Data Seed Script
Generates 3 schools with realistic Indian school data:
- Classes 1-8 with sections
- Students with parent multi-child linking
- Teachers, subjects, class incharges
- Attendance, exams, fees

Usage: cd apps/api && python scripts/seed_synthetic.py
"""
from __future__ import annotations

import asyncio
import json
import random
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from faker import Faker
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# ── Bootstrap ────────────────────────────────────────────────────────────────

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.models.base import Base
from app.db.models.school import School
from app.db.models.user import User, UserRole
from app.db.models.academic import AcademicYear, Class, Subject, TeacherSubjectMapping
from app.db.models.student import (
    Enrollment,
    Gender,
    Parent,
    Relationship,
    Student,
    StudentParentMap,
)
from app.db.models.teacher import Teacher
from app.db.models.attendance import Attendance, AttendanceStatus
from app.db.models.examination import Exam, ExamMark, ExamType
from app.db.models.fee import (
    FeeStructure, StudentFeeRecord, FeeReceipt, ReceiptCounter,
    FeeType, FeeFrequency, FeeStatus, PaymentMode,
)

settings = get_settings()
fake = Faker("en_IN")
Faker.seed(42)
random.seed(42)

# ── School Definitions ───────────────────────────────────────────────────────

SCHOOLS = [
    {
        "name": "Sunrise International Academy",
        "code": "SIA",
        "slug": "sia",
        "board": "CBSE",
        "sections": ["A", "B", "C"],
        "students_per_section": 30,
    },
    {
        "name": "Green Valley Public School",
        "code": "GVPS",
        "slug": "gvps",
        "board": "ICSE",
        "sections": ["A", "B", "C", "D"],
        "students_per_section": 30,
    },
    {
        "name": "Little Stars School",
        "code": "LSS",
        "slug": "lss",
        "board": "State Board",
        "sections": ["A", "B"],
        "students_per_section": 30,
    },
]

SUBJECTS_BY_GRADE = {
    "1-3": ["English", "Hindi", "Mathematics", "EVS", "Art & Craft"],
    "4-5": ["English", "Hindi", "Mathematics", "Science", "Social Studies"],
    "6-8": ["English", "Hindi", "Mathematics", "Science", "Social Studies"],
}

INDIAN_SURNAMES = [
    "Sharma", "Patel", "Reddy", "Kumar", "Singh", "Gupta", "Joshi", "Verma",
    "Nair", "Iyer", "Rao", "Mishra", "Agarwal", "Choudhary", "Das", "Mehta",
    "Pillai", "Chauhan", "Thakur", "Pandey", "Saxena", "Bhat", "Kulkarni",
    "Deshmukh", "Patil", "Hegde", "Menon", "Kaur", "Rathore", "Tiwari",
]

MALE_FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Reyansh", "Sai", "Ayaan",
    "Krishna", "Ishaan", "Dhruv", "Kabir", "Arnav", "Shaurya", "Atharv", "Advait",
    "Rohan", "Pranav", "Rudra", "Harsh", "Kian", "Darsh", "Yash", "Rishi",
    "Parth", "Ansh", "Aaryan", "Dev", "Kunal", "Virat", "Aryan", "Raj",
]

FEMALE_FIRST_NAMES = [
    "Saanvi", "Aanya", "Aadhya", "Aaradhya", "Ananya", "Pari", "Anika", "Navya",
    "Angel", "Diya", "Myra", "Sara", "Ira", "Ahana", "Kiara", "Divya",
    "Prisha", "Kavya", "Riya", "Aarohi", "Mira", "Aisha", "Siya", "Tara",
    "Nisha", "Pooja", "Shreya", "Tanvi", "Aditi", "Meera", "Ishita", "Jiya",
]

FATHER_FIRST_NAMES = [
    "Rajesh", "Suresh", "Vikram", "Amit", "Anil", "Manoj", "Sanjay", "Rahul",
    "Deepak", "Ashok", "Ramesh", "Vijay", "Pramod", "Sunil", "Mukesh", "Ravi",
    "Ajay", "Dinesh", "Pankaj", "Naresh", "Gaurav", "Kiran", "Nitin", "Alok",
]

MOTHER_FIRST_NAMES = [
    "Priya", "Sunita", "Rekha", "Meera", "Kavita", "Lakshmi", "Anita", "Neeta",
    "Suman", "Geeta", "Pooja", "Swati", "Ritu", "Seema", "Nandini", "Padma",
    "Jaya", "Usha", "Archana", "Shobha", "Neha", "Deepa", "Asha", "Radha",
]

credentials: list[dict] = []


def get_subjects_for_grade(grade: int) -> list[str]:
    if grade <= 3:
        return SUBJECTS_BY_GRADE["1-3"]
    elif grade <= 5:
        return SUBJECTS_BY_GRADE["4-5"]
    else:
        return SUBJECTS_BY_GRADE["6-8"]


def gen_mobile() -> str:
    return f"+91{random.randint(7000000000, 9999999999)}"


def gen_dob(grade: int) -> date:
    """Generate realistic DOB for a student in the given grade."""
    age = grade + 5 + random.randint(0, 1)
    year = 2026 - age
    return date(year, random.randint(1, 12), random.randint(1, 28))


# ── Seed Functions ───────────────────────────────────────────────────────────


async def seed_school(session: AsyncSession, school_def: dict) -> None:
    """Seed a complete school with all entities."""
    print(f"\n{'='*60}")
    print(f"  Seeding: {school_def['name']}")
    print(f"{'='*60}")

    # ── 1. Create School ─────────────────────────────────────────
    school = School(
        name=school_def["name"],
        code=school_def["code"],
        tenant_slug=school_def["slug"],
        board=school_def["board"],
        address={"city": fake.city(), "state": "Karnataka", "pincode": fake.postcode()},
        settings={"academic_hours": "8:30 AM - 3:30 PM", "working_days": "Mon-Sat"},
        contact_email=f"admin@{school_def['slug']}.studynexs.com",
        contact_phone=gen_mobile(),
        is_active=True,
    )
    session.add(school)
    await session.flush()
    school_id = school.id
    print(f"  ✓ School created: {school.name} (ID: {school_id})")

    # ── 2. Receipt Counter ───────────────────────────────────────
    counter = ReceiptCounter(
        school_id=school_id,
        last_sequence=0,
        prefix=school_def["code"],
    )
    session.add(counter)

    # ── 3. Admin Users ───────────────────────────────────────────
    admin_password = hash_password("Admin@123")
    principal = User(
        school_id=school_id,
        username=f"{school_def['slug']}_principal",
        mobile=gen_mobile(),
        email=f"principal@{school_def['slug']}.studynexs.com",
        full_name=f"{random.choice(FATHER_FIRST_NAMES)} {random.choice(INDIAN_SURNAMES)}",
        role=UserRole.SUPER_ADMIN,
        password_hash=admin_password,
        is_active=True,
    )
    vice_principal = User(
        school_id=school_id,
        username=f"{school_def['slug']}_vp",
        mobile=gen_mobile(),
        email=f"vp@{school_def['slug']}.studynexs.com",
        full_name=f"{random.choice(FATHER_FIRST_NAMES)} {random.choice(INDIAN_SURNAMES)}",
        role=UserRole.ADMIN,
        password_hash=admin_password,
        is_active=True,
    )
    session.add_all([principal, vice_principal])
    await session.flush()

    credentials.append({
        "school": school_def["name"],
        "role": "super_admin",
        "username": principal.username,
        "password": "Admin@123",
        "mobile": principal.mobile,
    })
    credentials.append({
        "school": school_def["name"],
        "role": "admin",
        "username": vice_principal.username,
        "password": "Admin@123",
        "mobile": vice_principal.mobile,
    })
    print(f"  ✓ 2 admins created")

    # ── 4. Academic Year ─────────────────────────────────────────
    academic_year = AcademicYear(
        school_id=school_id,
        year_label="2026-2027",
        start_date=date(2026, 4, 1),
        end_date=date(2027, 3, 31),
        is_active=True,
    )
    session.add(academic_year)
    await session.flush()

    # ── 5. Teachers ──────────────────────────────────────────────
    teacher_password = hash_password("Teacher@123")
    teacher_users: list[User] = []
    num_teachers = max(len(school_def["sections"]) * 8, 25)  # enough for all classes

    for i in range(num_teachers):
        gender = random.choice(["M", "F"])
        first = random.choice(MALE_FIRST_NAMES if gender == "M" else FEMALE_FIRST_NAMES)
        surname = random.choice(INDIAN_SURNAMES)
        t_user = User(
            school_id=school_id,
            username=f"{school_def['slug']}_teacher_{i+1}",
            mobile=gen_mobile(),
            email=f"{first.lower()}.{surname.lower()}@{school_def['slug']}.studynexs.com",
            full_name=f"{first} {surname}",
            role=UserRole.TEACHER,
            password_hash=teacher_password,
            is_active=True,
        )
        session.add(t_user)
        teacher_users.append(t_user)

    await session.flush()

    # Create teacher records
    for i, t_user in enumerate(teacher_users):
        teacher = Teacher(
            school_id=school_id,
            user_id=t_user.id,
            employee_id=f"{school_def['code']}-T{i+1:03d}",
            department="General",
            joining_date=date(2020 + random.randint(0, 5), random.randint(1, 12), 1),
        )
        session.add(teacher)

    await session.flush()

    # Save first teacher credential
    credentials.append({
        "school": school_def["name"],
        "role": "teacher",
        "username": teacher_users[0].username,
        "password": "Teacher@123",
        "mobile": teacher_users[0].mobile,
    })
    print(f"  ✓ {num_teachers} teachers created")

    # ── 6. Classes, Subjects, Teacher Mappings ───────────────────
    all_classes: list[Class] = []
    teacher_idx = 0

    for grade in range(1, 9):
        for section in school_def["sections"]:
            # Create class
            incharge_user = teacher_users[teacher_idx % len(teacher_users)]
            cls = Class(
                school_id=school_id,
                grade=f"Grade {grade}",
                section=section,
                academic_year_id=academic_year.id,
                class_incharge_id=incharge_user.id,
                room_number=f"{grade}{section}",
            )
            session.add(cls)
            all_classes.append(cls)
            teacher_idx += 1

    await session.flush()

    # Create subjects and teacher mappings
    for cls in all_classes:
        grade_num = int(cls.grade.split()[-1])
        subject_names = get_subjects_for_grade(grade_num)

        for subj_name in subject_names:
            subject = Subject(
                school_id=school_id,
                name=subj_name,
                code=subj_name[:3].upper(),
                class_id=cls.id,
            )
            session.add(subject)
            await session.flush()

            # Map a teacher to this subject
            mapped_teacher = teacher_users[teacher_idx % len(teacher_users)]
            mapping = TeacherSubjectMapping(
                school_id=school_id,
                teacher_id=mapped_teacher.id,
                subject_id=subject.id,
                class_id=cls.id,
                is_primary=True,
            )
            session.add(mapping)
            teacher_idx += 1

    await session.flush()
    num_classes = len(all_classes)
    print(f"  ✓ {num_classes} classes (Grade 1-8, sections {','.join(school_def['sections'])})")

    # ── 7. Students & Parents (with multi-child linking) ─────────
    # Build family pools: 65% single-child, 30% two-child, 5% three-child
    total_students = num_classes * school_def["students_per_section"]

    # Distribute students across classes
    student_records: list[dict] = []
    for cls in all_classes:
        grade_num = int(cls.grade.split()[-1])
        for s in range(school_def["students_per_section"]):
            gender = random.choice(["M", "F"])
            surname = random.choice(INDIAN_SURNAMES)
            first = random.choice(
                MALE_FIRST_NAMES if gender == "M" else FEMALE_FIRST_NAMES
            )
            student_records.append({
                "first_name": first,
                "surname": surname,
                "gender": gender,
                "grade": grade_num,
                "class_id": cls.id,
                "class_label": f"{cls.grade}-{cls.section}",
            })

    # Group into families
    random.shuffle(student_records)
    families: list[list[dict]] = []
    i = 0
    while i < len(student_records):
        roll = random.random()
        if roll < 0.05 and i + 2 < len(student_records):
            # 3-child family — share surname
            shared_surname = student_records[i]["surname"]
            family = [student_records[i], student_records[i+1], student_records[i+2]]
            for s in family:
                s["surname"] = shared_surname
            families.append(family)
            i += 3
        elif roll < 0.35 and i + 1 < len(student_records):
            # 2-child family
            shared_surname = student_records[i]["surname"]
            family = [student_records[i], student_records[i+1]]
            for s in family:
                s["surname"] = shared_surname
            families.append(family)
            i += 2
        else:
            # 1-child family
            families.append([student_records[i]])
            i += 1

    # Create all families
    student_count = 0
    parent_count = 0
    first_parent_cred_saved = False

    for family in families:
        shared_surname = family[0]["surname"]

        # Create father
        father_user = User(
            school_id=school_id,
            mobile=gen_mobile(),
            email=f"{random.choice(FATHER_FIRST_NAMES).lower()}.{shared_surname.lower()}{random.randint(1,999)}@gmail.com",
            full_name=f"{random.choice(FATHER_FIRST_NAMES)} {shared_surname}",
            role=UserRole.PARENT,
            is_active=True,
        )
        # Create mother
        mother_user = User(
            school_id=school_id,
            mobile=gen_mobile(),
            email=f"{random.choice(MOTHER_FIRST_NAMES).lower()}.{shared_surname.lower()}{random.randint(1,999)}@gmail.com",
            full_name=f"{random.choice(MOTHER_FIRST_NAMES)} {shared_surname}",
            role=UserRole.PARENT,
            is_active=True,
        )
        session.add_all([father_user, mother_user])
        await session.flush()

        father_parent = Parent(
            school_id=school_id,
            user_id=father_user.id,
            relationship_type=Relationship.FATHER,
        )
        mother_parent = Parent(
            school_id=school_id,
            user_id=mother_user.id,
            relationship_type=Relationship.MOTHER,
        )
        session.add_all([father_parent, mother_parent])
        await session.flush()
        parent_count += 2

        if not first_parent_cred_saved:
            credentials.append({
                "school": school_def["name"],
                "role": "parent",
                "username": None,
                "password": None,
                "mobile": father_user.mobile,
                "login_method": "OTP",
            })
            first_parent_cred_saved = True

        # Create students and link to parents
        for s_data in family:
            s_user = User(
                school_id=school_id,
                mobile=gen_mobile(),
                full_name=f"{s_data['first_name']} {s_data['surname']}",
                role=UserRole.STUDENT,
                is_active=True,
            )
            session.add(s_user)
            await session.flush()

            student = Student(
                school_id=school_id,
                user_id=s_user.id,
                class_id=s_data["class_id"],
                admission_no=f"{school_def['code']}-{date.today().year}-{student_count+1:04d}",
                roll_no=str(student_count % school_def["students_per_section"] + 1),
                date_of_birth=gen_dob(s_data["grade"]),
                gender=Gender.MALE if s_data["gender"] == "M" else Gender.FEMALE,
                admission_date=date(2026, 4, random.randint(1, 15)),
            )
            session.add(student)
            await session.flush()

            # DM-3: per-year enrollment history alongside the current-class pointer.
            session.add(Enrollment(
                school_id=school_id,
                student_id=student.id,
                class_id=s_data["class_id"],
                academic_year_id=academic_year.id,
                roll_no=student.roll_no,
                enrolled_on=student.admission_date,
            ))

            # Link to both parents
            session.add(StudentParentMap(
                student_id=student.id,
                parent_id=father_parent.id,
                is_primary=True,
            ))
            session.add(StudentParentMap(
                student_id=student.id,
                parent_id=mother_parent.id,
                is_primary=False,
            ))
            student_count += 1

    await session.flush()
    print(f"  ✓ {student_count} students in {len(families)} families ({parent_count} parents)")

    # ── 8. Fee Structures ────────────────────────────────────────
    tuition = FeeStructure(
        school_id=school_id,
        fee_type=FeeType.TUITION,
        amount=3500.00,
        frequency=FeeFrequency.MONTHLY,
        academic_year_id=academic_year.id,
        due_day=10,
    )
    transport = FeeStructure(
        school_id=school_id,
        fee_type=FeeType.TRANSPORT,
        amount=4500.00,
        frequency=FeeFrequency.QUARTERLY,
        academic_year_id=academic_year.id,
        due_day=5,
    )
    library = FeeStructure(
        school_id=school_id,
        fee_type=FeeType.LIBRARY,
        amount=1200.00,
        frequency=FeeFrequency.ANNUAL,
        academic_year_id=academic_year.id,
        due_day=15,
    )
    session.add_all([tuition, transport, library])
    await session.flush()
    print(f"  ✓ 3 fee structures (tuition/transport/library)")

    # ── 9. Commit ────────────────────────────────────────────────
    await session.commit()
    print(f"  ✅ {school_def['name']} — COMPLETE")


# ── Main ─────────────────────────────────────────────────────────────────────


async def main():
    print("\n" + "=" * 60)
    print("  STUDYNEXS — Synthetic Data Seed")
    print("=" * 60)

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    for school_def in SCHOOLS:
        async with session_factory() as session:
            # Check if school already exists
            result = await session.execute(
                select(School).where(School.tenant_slug == school_def["slug"])
            )
            if result.scalar_one_or_none():
                print(f"\n  ⏭ {school_def['name']} already exists — skipping")
                continue

            await seed_school(session, school_def)

    # Save credentials
    cred_path = Path(__file__).parent / "seed_credentials.json"
    with open(cred_path, "w") as f:
        json.dump(credentials, f, indent=2)

    print(f"\n{'='*60}")
    print(f"  Credentials saved to: {cred_path}")
    print(f"{'='*60}")

    # Summary
    async with session_factory() as session:
        for table_name in ["schools", "users", "students", "parents", "classes", "subjects"]:
            result = await session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            count = result.scalar()
            print(f"  {table_name:20s}: {count}")

    await engine.dispose()
    print("\n  ✅ Seed complete!\n")


if __name__ == "__main__":
    asyncio.run(main())

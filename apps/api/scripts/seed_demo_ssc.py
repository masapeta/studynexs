"""Seed a believable SSC demo school (grades 1-10) for the pilot demo.

One Telangana-style SSC school with classes, subjects, ~24 students/class (real-sounding
names), recent attendance, and fees — so the dashboard feels inhabited and there's a real
Class 10 + Mathematics to drive the AI question-paper generator.

Run:  python scripts/seed_demo_ssc.py
Idempotent: skips if the demo school (tenant_slug='test') already exists.
"""
from __future__ import annotations

import asyncio
import random
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select

from app.core.database import async_session_factory
from app.core.security import hash_password
from app.db.models.academic import AcademicYear, Class, Subject, TeacherSubjectMapping
from app.db.models.attendance import Attendance, AttendanceStatus
from app.db.models.fee import (
    FeeFrequency,
    FeeReceipt,
    FeeStatus,
    FeeStructure,
    FeeType,
    PaymentMode,
    ReceiptCounter,
    StudentFeeRecord,
)
from app.db.models.school import School
from app.db.models.student import Gender, Student
from app.db.models.user import User, UserRole

random.seed(2026)

TENANT = "test"  # matches the admin-web default NEXT_PUBLIC_TENANT_SLUG, so it works out of the box

MALE = ["Aarav", "Vivaan", "Aditya", "Arjun", "Sai", "Rohan", "Karthik", "Teja", "Nikhil",
        "Charan", "Bhargav", "Manish", "Ranbir", "Yashwanth", "Akhil", "Praneeth", "Surya", "Vamsi"]
FEMALE = ["Ananya", "Sahasra", "Keerthana", "Sneha", "Divya", "Harika", "Lasya", "Meghana",
          "Navya", "Pooja", "Ramya", "Sravani", "Bhavana", "Akshara", "Deepika", "Nithya", "Varsha"]
SURNAMES = ["Reddy", "Rao", "Naidu", "Sharma", "Goud", "Yadav", "Chowdary", "Kumar", "Varma",
            "Shetty", "Pillai", "Mudiraj", "Achari", "Bhupathi", "Komuravelli", "Gangula"]
SUBJECTS = ["Telugu", "Hindi", "English", "Mathematics", "Science", "Social Studies"]


async def main() -> None:
    async with async_session_factory() as db:
        existing = (
            await db.execute(select(School).where(School.tenant_slug == TENANT))
        ).scalar_one_or_none()
        if existing:
            print(f"Demo school already exists (tenant_slug='{TENANT}'). "
                  "Recreate the DB to reseed (docker compose down -v && up).")
            return

        school = School(
            name="Sri Saraswathi High School",
            code="SSHS01",
            tenant_slug=TENANT,
            board="SSC",
            contact_email="office@srisaraswathi.edu.in",
            contact_phone="+914023456789",
            address={"city": "Hyderabad", "state": "Telangana"},
            is_active=True,
        )
        db.add(school)
        await db.flush()

        ay = AcademicYear(
            school_id=school.id, year_label="2026-2027",
            start_date=date(2026, 6, 1), end_date=date(2027, 4, 30), is_active=True,
        )
        db.add(ay)
        await db.flush()

        # Staff: principal (login) + a few teachers
        principal = User(
            school_id=school.id, username="principal", mobile="+919800000001",
            full_name="Padmaja Rao", role=UserRole.SUPER_ADMIN,
            email="principal@srisaraswathi.edu.in",
            password_hash=hash_password("Demo@1234"), is_active=True,
        )
        db.add(principal)
        # Named teachers for believable demo logins (password: Demo@1234)
        teacher_specs = [
            ("teacher1", "Lakshmi Devi", UserRole.CLASS_INCHARGE),   # Class 10-A incharge
            ("teacher2", "Ramesh Kumar", UserRole.CLASS_INCHARGE),   # Class 10-B incharge
            ("teacher3", "Sunitha Rao", UserRole.CLASS_INCHARGE),    # Class 9-A incharge
            ("teacher4", "Venkat Reddy", UserRole.CLASS_INCHARGE),  # Class 9-B incharge
            ("teacher5", "Anjali Sharma", UserRole.CLASS_INCHARGE), # Class 8-A incharge
            ("teacher6", "Kiran Naidu", UserRole.TEACHER),          # Maths subject teacher
            ("teacher7", "Priya Goud", UserRole.TEACHER),           # Science subject teacher
            ("teacher8", "Mahesh Varma", UserRole.TEACHER),         # English subject teacher
        ]
        teachers: list[User] = []
        for i, (uname, name, role) in enumerate(teacher_specs):
            t = User(
                school_id=school.id, username=uname, mobile=f"+9198100000{i + 10}",
                full_name=name, role=role, password_hash=hash_password("Demo@1234"), is_active=True,
            )
            teachers.append(t)
        db.add_all(teachers)
        await db.flush()

        # Classes: grades 1-8 (section A), grades 9-10 (sections A & B)
        class_specs = [(str(g), "A") for g in range(1, 9)]
        class_specs += [("9", "A"), ("9", "B"), ("10", "A"), ("10", "B")]
        classes: list[Class] = []
        for grade, section in class_specs:
            c = Class(
                school_id=school.id, grade=f"Class {grade}", section=section,
                academic_year_id=ay.id, room_number=f"{grade}{section}",
            )
            classes.append(c)
        db.add_all(classes)
        await db.flush()

        # Class incharges (sub-admins for their class)
        incharge_by_grade = {
            ("Class 10", "A"): teachers[0],
            ("Class 10", "B"): teachers[1],
            ("Class 9", "A"): teachers[2],
            ("Class 9", "B"): teachers[3],
            ("Class 8", "A"): teachers[4],
        }
        for c in classes:
            incharge = incharge_by_grade.get((c.grade, c.section))
            if incharge:
                c.class_incharge_id = incharge.id

        # Subjects per class + subject-teacher mappings for demo RBAC
        subject_index: dict[tuple[uuid.UUID, str], Subject] = {}
        for c in classes:
            for name in SUBJECTS:
                subj = Subject(
                    school_id=school.id, name=name,
                    code=f"{name[:3].upper()}{c.grade.split()[-1]}", class_id=c.id,
                )
                db.add(subj)
                subject_index[(c.id, name)] = subj
        await db.flush()

        def _map(teacher: User, grade: str, section: str, subject_name: str) -> None:
            cls = next(x for x in classes if x.grade == grade and x.section == section)
            subj = subject_index[(cls.id, subject_name)]
            db.add(TeacherSubjectMapping(
                school_id=school.id, teacher_id=teacher.id,
                subject_id=subj.id, class_id=cls.id, is_primary=True,
            ))

        # Class 10 pilot wedge: teacher6 Maths, teacher7 Science, teacher8 English (both sections)
        for section in ("A", "B"):
            _map(teachers[5], "Class 10", section, "Mathematics")
            _map(teachers[6], "Class 10", section, "Science")
            _map(teachers[7], "Class 10", section, "English")
        # Incharges also teach a subject in their class
        _map(teachers[0], "Class 10", "A", "Telugu")
        _map(teachers[1], "Class 10", "B", "Telugu")
        await db.flush()

        # Students (+ their user rows), attendance, fees
        fee_structure = FeeStructure(
            school_id=school.id, class_id=None, fee_type=FeeType.TUITION,
            amount=Decimal("2500.00"), frequency=FeeFrequency.MONTHLY,
            academic_year_id=ay.id, due_day=10,
        )
        db.add(fee_structure)
        counter = ReceiptCounter(school_id=school.id, prefix="SSHS", last_sequence=0)
        db.add(counter)
        await db.flush()

        recent_days = [date.today() - timedelta(days=d) for d in range(0, 5)]
        mobile_seq = 1000
        admission_seq = 1
        total_students = 0
        total_attendance = 0
        receipts = 0

        for c in classes:
            for roll in range(1, 25):  # 24 students per class
                gender = random.choice([Gender.MALE, Gender.FEMALE])
                first = random.choice(MALE if gender == Gender.MALE else FEMALE)
                name = f"{first} {random.choice(SURNAMES)}"
                mobile_seq += 1
                admission_seq += 1
                age = int(c.grade.split()[-1]) + 5
                u = User(
                    school_id=school.id, mobile=f"+9197{mobile_seq:08d}", full_name=name,
                    role=UserRole.STUDENT, is_active=True,
                )
                db.add(u)
                await db.flush()
                stu = Student(
                    school_id=school.id, user_id=u.id, class_id=c.id,
                    admission_no=f"SSHS{admission_seq:04d}", roll_no=str(roll),
                    date_of_birth=date(2026 - age, random.randint(1, 12), random.randint(1, 28)),
                    gender=gender,
                )
                db.add(stu)
                await db.flush()
                total_students += 1

                # recent attendance (mostly present)
                for d in recent_days:
                    st = random.choices(
                        [AttendanceStatus.PRESENT, AttendanceStatus.ABSENT, AttendanceStatus.LATE],
                        weights=[88, 8, 4],
                    )[0]
                    db.add(Attendance(
                        school_id=school.id, student_id=stu.id, class_id=c.id, date=d,
                        status=st, marked_by=principal.id,
                    ))
                    total_attendance += 1

                # one monthly fee record; ~45% paid (with receipt)
                paid = random.random() < 0.45
                rec = StudentFeeRecord(
                    school_id=school.id, student_id=stu.id, fee_structure_id=fee_structure.id,
                    amount=Decimal("2500.00"), due_date=date.today().replace(day=10),
                    status=FeeStatus.PAID if paid else FeeStatus.PENDING,
                    paid_amount=Decimal("2500.00") if paid else Decimal("0"),
                )
                if paid:
                    counter.last_sequence += 1
                    seq = counter.last_sequence
                    now = datetime.now(timezone.utc) - timedelta(days=random.randint(0, 20))
                    receipt = FeeReceipt(
                        school_id=school.id, receipt_number=f"SSHS-2026-{seq:05d}",
                        student_id=stu.id, student_name=name, class_name=f"{c.grade}-{c.section}",
                        amount_paid=Decimal("2500.00"), payment_mode=PaymentMode.UPI,
                        fee_type="Tuition", fee_period="June 2026", paid_at=now,
                        school_name=school.name, receipt_sequence=seq,
                    )
                    db.add(receipt)
                    await db.flush()
                    rec.paid_at = now
                    rec.payment_mode = PaymentMode.UPI
                    rec.receipt_id = receipt.id
                    receipts += 1
                db.add(rec)

        await db.commit()
        print("Seeded demo school 'Sri Saraswathi High School' (SSC)")
        print(f"  classes={len(classes)}  students={total_students}  "
              f"attendance_rows={total_attendance}  receipts={receipts}")
        print("  LOGIN  ->  tenant: test   username: principal   password: Demo@1234")
        print("  Class incharge (10-A): teacher1 / Demo@1234  — attendance, notices, approve QPs")
        print("  Subject teacher (Maths): teacher6 / Demo@1234  — generate QP only (teacher1 approves)")
        print("  Demo the AI generator on: Class 10 · Mathematics (login as teacher6)")


if __name__ == "__main__":
    asyncio.run(main())

"""Populate the demo school (tenant_slug=test) with synthetic data for a full UI walkthrough.

Covers: modules flags, library + issues, events, notifications, admissions, expenses,
payroll, extra staff roles, parents, transport, and parent-facing notices.

Prerequisites: seed_demo_ssc.py (creates the test school). Safe to re-run — each section
is idempotent.

Usage:
    cd apps/api
    python scripts/seed_working_session.py

Recommended fresh-demo chain:
    python scripts/seed_demo_ssc.py
    python scripts/patch_demo_ssc_rbac.py
    python scripts/seed_demo_extras.py
    python scripts/seed_exam_marks.py
    python scripts/seed_working_session.py
"""
from __future__ import annotations

import asyncio
import random
import sys
import uuid
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

_scripts_dir = Path(__file__).resolve().parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

from reference_school_config import DEMO_PASSWORD, TENANT_SLUG
from sqlalchemy import func, select

from app.core.database import async_session_factory
from app.core.security import hash_password
from app.db.models.communication import Notice, NoticeAudience, NoticePriority
from app.db.models.notification import Notification, NotificationChannel
from app.db.models.school import School
from app.db.models.school_ops import (
    AdmissionCandidate,
    AdmissionStage,
    Event,
    LibraryBook,
    LibraryIssue,
    LibraryIssueStatus,
    PayrollStatus,
    SchoolExpense,
    StaffPayrollEntry,
    StudentTransport,
    TransportRoute,
)
from app.db.models.student import Parent, Relationship, Student, StudentParentMap
from app.db.models.user import User, UserRole

TENANT = TENANT_SLUG
random.seed(42)

BOOKS = [
    ("To Kill a Mockingbird", "Harper Lee", "9780061120084", "Literature", 12),
    ("The Three-Body Problem", "Liu Cixin", "9780765382030", "Sci-Fi", 10),
    ("Sapiens", "Yuval Noah Harari", "9780062316097", "History", 8),
    ("The Kite Runner", "Khaled Hosseini", "9781594631931", "Literature", 10),
    ("1984", "George Orwell", "9780451524935", "Literature", 10),
    ("A Brief History of Time", "Stephen Hawking", "9780553380163", "Science", 8),
    ("Introduction to Quantum Mechanics", "David J. Griffiths", "9781107189638", "Science", 5),
    ("Wings of Fire", "A.P.J. Abdul Kalam", "9788173711468", "Biography", 15),
    ("Telugu Sahitya Charitra", "Kandukuri Veeresalingam", None, "Telugu", 6),
    ("NCERT Mathematics Class 10", "NCERT", None, "Textbook", 20),
]

EVENT_SPECS = [
    ("Parent-Teacher Conference", 3, time(14, 0), "Multi-Purpose Hall", "All class parents invited"),
    ("English Open Class", 5, time(10, 0), "Building A — Room 201", "Observation lesson for parents"),
    ("Annual Sports Day", 8, time(8, 0), "Sports Field", "House colours required"),
    ("Fire Drill", 6, time(14, 30), "Campus-wide", "Mandatory safety exercise"),
    ("Midterm Examinations", 12, time(9, 0), "All Classrooms", "Half-yearly exam week begins"),
    ("Science Exhibition", 15, time(11, 0), "Science Block", "Class 8–10 projects on display"),
    ("Grade 10 Mock Exam", 18, time(9, 0), "Building C", "SSC pattern practice test"),
]

NOTIFICATION_SPECS = [
    ("New student enrolled", "Aarav Reddy enrolled in Class 10-A.", False),
    ("Tuition payment received", "Fee receipt SSHS-2026-00142 — ₹2,500 via UPI.", False),
    ("Attendance update", "School-wide attendance today: 96.4%.", False),
    ("Library books added", "120 new titles added to the catalog.", True),
    ("Parent message", "A parent requested a meeting slot for Saturday.", False),
    ("Payroll reminder", "June staff payroll pending approval.", True),
]

ADMISSION_NOTES = {
    AdmissionStage.ENQUIRY: "Walk-in enquiry; brochure shared.",
    AdmissionStage.APPLIED: "Application form and previous report card submitted.",
    AdmissionStage.INTERVIEW: "Interview scheduled with class incharge.",
    AdmissionStage.OFFER: "Provisional seat offered; awaiting fee confirmation.",
    AdmissionStage.ENROLLED: "Admission fee received; student ID assigned.",
}

# (name, grade, days_ago) — stage assigned when topping up each pipeline column
ADMISSION_POOL: dict[AdmissionStage, list[tuple[str, str, int]]] = {
    AdmissionStage.ENQUIRY: [
        ("Tara Krishnan", "6", 2),
        ("Arjun Goud", "1", 1),
        ("Meghana Pillai", "8", 3),
        ("Rohan Deshmukh", "9", 4),
        ("Anika Sharma", "5", 2),
        ("Vikram Naidu", "10", 1),
        ("Sneha Reddy", "7", 5),
        ("Ayaan Thomas", "2", 2),
        ("Isabella Moore", "4", 3),
    ],
    AdmissionStage.APPLIED: [
        ("Dev Malhotra", "7", 8),
        ("Ira Banerjee", "6", 10),
        ("Karthik Rao", "4", 12),
        ("Lasya Varma", "9", 9),
        ("Pranav Kumar", "3", 14),
        ("Harika Chowdary", "8", 11),
        ("Mason Taylor", "5", 13),
        ("Ava Anderson", "7", 15),
    ],
    AdmissionStage.INTERVIEW: [
        ("Sara Pinto", "6", 5),
        ("Bhargav Singh", "10", 7),
        ("Navya Iyer", "7", 6),
        ("Charan Mudiraj", "5", 8),
        ("Deepika Achari", "9", 4),
        ("Lucas Thomas", "8", 6),
        ("Amelia Lewis", "6", 9),
    ],
    AdmissionStage.OFFER: [
        ("Yuvraj Sethi", "7", 28),
        ("Aadhya Menon", "6", 22),
        ("Sai Kulkarni", "8", 18),
        ("Ramya Hegde", "10", 20),
        ("Henry White", "9", 24),
        ("Charlotte Harris", "10", 26),
    ],
    AdmissionStage.ENROLLED: [
        ("Nikhil Rao", "7", 35),
        ("Keerthana Joshi", "6", 40),
        ("Teja Patil", "9", 32),
        ("Divya Bhupathi", "8", 38),
        ("Manish Gangula", "10", 45),
        ("James Clark", "7", 42),
        ("Benjamin Walker", "8", 48),
    ],
}

# Minimum candidates per stage for a convincing pipeline demo
ADMISSION_MIN_PER_STAGE: dict[AdmissionStage, int] = {
    AdmissionStage.ENQUIRY: 8,
    AdmissionStage.APPLIED: 6,
    AdmissionStage.INTERVIEW: 6,
    AdmissionStage.OFFER: 5,
    AdmissionStage.ENROLLED: 6,
}

EXPENSE_DEMOS = [
    ("MSEB", "Utilities", 42000, 20),
    ("Navneet Stationers", "Supplies", 15600, 18),
    ("CoolAir Services", "Maintenance", 8900, 15),
    ("Bharat Petroleum", "Transport", 31200, 12),
    ("Cambridge University Press", "Library", 24800, 8),
]

PARENT_NOTICES = [
    ("Regarding next week's PTM", "Could the parent meeting be scheduled for Saturday morning?", 1),
    ("Leave application", "My ward needs a day off tomorrow due to a family function.", 2),
    ("Tuition payment confirmation", "Term fee paid via UPI — please confirm receipt.", 3),
]

ROUTES = [
    {
        "route_name": "Route 1 — Kukatpally",
        "vehicle_number": "TS09 AB 1234",
        "driver_name": "Ramesh Kumar",
        "driver_contact": "+919800012001",
        "stops": ["Kukatpally", "KPHB", "Miyapur"],
        "capacity": 40,
    },
    {
        "route_name": "Route 2 — Ameerpet",
        "vehicle_number": "TS09 CD 5678",
        "driver_name": "Suresh Rao",
        "driver_contact": "+919800012002",
        "stops": ["Ameerpet", "SR Nagar", "Punjagutta"],
        "capacity": 35,
    },
    {
        "route_name": "Route 3 — Dilsukhnagar",
        "vehicle_number": "TS09 EF 9012",
        "driver_name": "Venkat Reddy",
        "driver_contact": "+919800012003",
        "stops": ["Dilsukhnagar", "Kothapet", "LB Nagar"],
        "capacity": 38,
    },
]

MALE_PARENT = ["Ramesh", "Suresh", "Venkat", "Prakash", "Srinivas", "Mohan", "Ravi", "Anil"]
FEMALE_PARENT = ["Lakshmi", "Padma", "Sunitha", "Radha", "Geetha", "Sarita", "Anitha", "Vani"]


async def enable_modules(school: School) -> None:
    modules = {
        **(school.enabled_modules or {}),
        "library": True,
        "transport": True,
        "attendance": True,
        "exams": True,
        "finance": True,
        "notices": True,
        "timetable": True,
        "ai_papers": True,
        "mastery": True,
        "report_cards": True,
    }
    school.enabled_modules = modules


async def seed_extra_staff(db, school: School) -> int:
    specs = [
        ("admin1", "Rajesh Verma", UserRole.ADMIN, "admin@srisaraswathi.edu.in"),
        ("ops1", "Lakshmi Operations", UserRole.OPERATIONS, "ops@srisaraswathi.edu.in"),
    ]
    added = 0
    for username, name, role, email in specs:
        exists = await db.scalar(
            select(User.id).where(User.school_id == school.id, User.username == username)
        )
        if exists:
            continue
        db.add(
            User(
                school_id=school.id,
                username=username,
                mobile=f"+9198200{1000 + added:05d}",
                full_name=name,
                role=role,
                email=email,
                password_hash=hash_password("Demo@1234"),
                is_active=True,
            )
        )
        added += 1
    if added:
        await db.flush()
    return added


async def seed_library(db, school: School) -> tuple[int, int]:
    existing = await db.scalar(
        select(func.count()).select_from(LibraryBook).where(LibraryBook.school_id == school.id)
    )
    if existing:
        return 0, 0

    books: list[LibraryBook] = []
    for title, author, isbn, category, copies in BOOKS:
        borrowed = random.randint(0, min(4, copies - 1))
        book = LibraryBook(
            school_id=school.id,
            title=title,
            author=author,
            isbn=isbn,
            category=category,
            total_copies=copies,
            available_copies=copies - borrowed,
        )
        db.add(book)
        books.append(book)
    await db.flush()

    students = (
        await db.execute(
            select(Student, User)
            .join(User, User.id == Student.user_id)
            .where(Student.school_id == school.id)
            .limit(20)
        )
    ).all()

    issues = 0
    for book in books:
        to_issue = book.total_copies - book.available_copies
        for i in range(to_issue):
            if not students:
                break
            stu, user = students[(issues + i) % len(students)]
            db.add(
                LibraryIssue(
                    school_id=school.id,
                    book_id=book.id,
                    user_id=user.id,
                    due_date=date.today() + timedelta(days=14),
                    status=LibraryIssueStatus.ISSUED,
                )
            )
            issues += 1
    await db.flush()
    return len(books), issues


async def seed_events(db, school: School, created_by: uuid.UUID) -> int:
    existing = await db.scalar(
        select(func.count()).select_from(Event).where(Event.school_id == school.id)
    )
    if existing:
        return 0

    for title, days_ahead, evt_time, venue, description in EVENT_SPECS:
        db.add(
            Event(
                school_id=school.id,
                title=title,
                description=description,
                event_date=date.today() + timedelta(days=days_ahead),
                event_time=evt_time,
                venue=venue,
                target_roles=["admin", "teacher", "parent", "student"],
                created_by=created_by,
            )
        )
    await db.flush()
    return len(EVENT_SPECS)


async def seed_notifications(db, school: School, user_id: uuid.UUID) -> int:
    existing = await db.scalar(
        select(func.count())
        .select_from(Notification)
        .where(Notification.school_id == school.id, Notification.user_id == user_id)
    )
    if existing:
        return 0

    now = datetime.now(timezone.utc)
    for i, (title, body, is_read) in enumerate(NOTIFICATION_SPECS):
        db.add(
            Notification(
                school_id=school.id,
                user_id=user_id,
                title=title,
                body=body,
                channel=NotificationChannel.IN_APP,
                is_read=is_read,
                created_at=now - timedelta(hours=i + 1),
            )
        )
    await db.flush()
    return len(NOTIFICATION_SPECS)


async def admission_pipeline_counts(db, school_id: uuid.UUID) -> dict[str, int]:
    counts = {s.value: 0 for s in AdmissionStage}
    rows = (
        await db.execute(
            select(AdmissionCandidate.stage, func.count())
            .where(AdmissionCandidate.school_id == school_id)
            .group_by(AdmissionCandidate.stage)
        )
    ).all()
    for stage, n in rows:
        counts[stage.value] = int(n)
    counts["total"] = sum(counts[s.value] for s in AdmissionStage)
    return counts


async def seed_admissions(
    db,
    school: School,
    created_by: uuid.UUID,
    *,
    min_per_stage: dict[AdmissionStage, int] | None = None,
) -> int:
    """Top up each pipeline stage to min_per_stage (default ADMISSION_MIN_PER_STAGE)."""
    targets = min_per_stage or ADMISSION_MIN_PER_STAGE
    today = date.today()
    added = 0

    existing_names = set(
        (
            await db.execute(
                select(AdmissionCandidate.name).where(AdmissionCandidate.school_id == school.id)
            )
        ).scalars().all()
    )

    for stage, min_count in targets.items():
        current = await db.scalar(
            select(func.count())
            .select_from(AdmissionCandidate)
            .where(
                AdmissionCandidate.school_id == school.id,
                AdmissionCandidate.stage == stage,
            )
        )
        need = max(0, min_count - int(current or 0))
        if need <= 0:
            continue

        pool = ADMISSION_POOL.get(stage, [])
        used_from_pool = 0
        for name, grade, days_ago in pool:
            if used_from_pool >= need:
                break
            if name in existing_names:
                continue
            db.add(
                AdmissionCandidate(
                    school_id=school.id,
                    name=name,
                    grade_applied=grade,
                    stage=stage,
                    enquiry_date=today - timedelta(days=days_ago),
                    notes=ADMISSION_NOTES.get(stage),
                    created_by=created_by,
                )
            )
            existing_names.add(name)
            used_from_pool += 1
            added += 1

        # Fallback synthetic rows if pool exhausted
        seq = int(datetime.now(timezone.utc).timestamp()) % 10000
        while used_from_pool < need:
            seq += 1
            grade = str(random.randint(1, 10))
            name = f"Applicant {seq}"
            while name in existing_names:
                seq += 1
                name = f"Applicant {seq}"
            db.add(
                AdmissionCandidate(
                    school_id=school.id,
                    name=name,
                    grade_applied=grade,
                    stage=stage,
                    enquiry_date=today - timedelta(days=random.randint(1, 30)),
                    notes=ADMISSION_NOTES.get(stage),
                    created_by=created_by,
                )
            )
            existing_names.add(name)
            used_from_pool += 1
            added += 1

    if added:
        await db.flush()
    return added


async def seed_expenses(db, school: School, created_by: uuid.UUID) -> int:
    existing = await db.scalar(
        select(SchoolExpense.id).where(SchoolExpense.school_id == school.id).limit(1)
    )
    if existing:
        return 0

    today = date.today()
    for vendor, category, amount, days_ago in EXPENSE_DEMOS:
        db.add(
            SchoolExpense(
                school_id=school.id,
                vendor=vendor,
                category=category,
                amount=amount,
                expense_date=today - timedelta(days=days_ago),
                created_by=created_by,
            )
        )
    await db.flush()
    return len(EXPENSE_DEMOS)


async def seed_payroll(db, school: School) -> int:
    month = date.today().replace(day=1)
    existing = await db.scalar(
        select(func.count())
        .select_from(StaffPayrollEntry)
        .where(StaffPayrollEntry.school_id == school.id, StaffPayrollEntry.period_month == month)
    )
    if existing:
        return 0

    staff = (
        await db.execute(
            select(User).where(
                User.school_id == school.id,
                User.role.in_(
                    (
                        UserRole.SUPER_ADMIN,
                        UserRole.ADMIN,
                        UserRole.CLASS_INCHARGE,
                        UserRole.TEACHER,
                        UserRole.OPERATIONS,
                    )
                ),
                User.is_active.is_(True),
            )
        )
    ).scalars().all()

    default_gross = {
        UserRole.SUPER_ADMIN: 145000,
        UserRole.ADMIN: 85000,
        UserRole.CLASS_INCHARGE: 65000,
        UserRole.TEACHER: 62000,
        UserRole.OPERATIONS: 45000,
    }
    added = 0
    for i, u in enumerate(staff):
        paid = i % 3 == 0
        db.add(
            StaffPayrollEntry(
                school_id=school.id,
                user_id=u.id,
                period_month=month,
                gross_amount=default_gross.get(u.role, 50000),
                status=PayrollStatus.PAID if paid else PayrollStatus.PENDING,
                paid_at=datetime.now(timezone.utc) if paid else None,
            )
        )
        added += 1
    await db.flush()
    return added


async def seed_parents(db, school: School) -> tuple[int, int]:
    link_count = await db.scalar(select(func.count()).select_from(StudentParentMap))
    if link_count:
        return 0, 0

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
            school_id=school.id,
            mobile=f"+9196{seq:08d}",
            full_name=f"{random.choice(MALE_PARENT)} {surname}",
            role=UserRole.PARENT,
            email=f"parent{seq}@example.com",
            is_active=True,
        )
        db.add(father)
        await db.flush()
        fp = Parent(
            school_id=school.id,
            user_id=father.id,
        )
        db.add(fp)
        await db.flush()
        db.add(StudentParentMap(
            school_id=school.id,
            student_id=stu.id, parent_id=fp.id, is_primary=True,
            relationship_type=Relationship.FATHER,
        ))
        n_parents += 1
        n_links += 1

        if random.random() < 0.65:
            seq += 1
            mother = User(
                school_id=school.id,
                mobile=f"+9196{seq:08d}",
                full_name=f"{random.choice(FEMALE_PARENT)} {surname}",
                role=UserRole.PARENT,
                email=f"parent{seq}@example.com",
                is_active=True,
            )
            db.add(mother)
            await db.flush()
            mp = Parent(
                school_id=school.id,
                user_id=mother.id,
            )
            db.add(mp)
            await db.flush()
            db.add(StudentParentMap(
                school_id=school.id,
                student_id=stu.id, parent_id=mp.id, is_primary=False,
                relationship_type=Relationship.MOTHER,
            ))
            n_parents += 1
            n_links += 1

    await db.flush()
    return n_parents, n_links


async def seed_transport(db, school: School) -> tuple[int, int]:
    existing = await db.scalar(
        select(func.count()).select_from(TransportRoute).where(TransportRoute.school_id == school.id)
    )
    if existing:
        return 0, 0

    routes: list[TransportRoute] = []
    for rd in ROUTES:
        r = TransportRoute(school_id=school.id, is_active=True, **rd)
        db.add(r)
        routes.append(r)
    await db.flush()

    students = (
        await db.execute(select(Student).where(Student.school_id == school.id))
    ).scalars().all()
    assigned = 0
    for i, stu in enumerate(students):
        if i % 3 != 0:
            continue
        route = routes[i % len(routes)]
        stop = random.choice(route.stops or ["Main Gate"])
        db.add(
            StudentTransport(
                school_id=school.id,
                student_id=stu.id,
                route_id=route.id,
                boarding_stop=stop,
            )
        )
        assigned += 1
    await db.flush()
    return len(routes), assigned


async def seed_parent_notices(db, school: School, created_by: uuid.UUID) -> int:
    """Extra external notices so the Parents page has content."""
    count = await db.scalar(
        select(func.count())
        .select_from(Notice)
        .where(Notice.school_id == school.id, Notice.audience == NoticeAudience.EXTERNAL)
    )
    if count and count >= 3:
        return 0

    now = datetime.now(timezone.utc)
    added = 0
    for title, content, days_ago in PARENT_NOTICES:
        db.add(
            Notice(
                school_id=school.id,
                title=title,
                content=content,
                target_roles=["parent"],
                audience=NoticeAudience.EXTERNAL,
                priority=NoticePriority.MEDIUM,
                created_by=created_by,
                created_at=now - timedelta(days=days_ago),
            )
        )
        added += 1
    await db.flush()
    return added


async def main() -> None:
    async with async_session_factory() as db:
        school = (
            await db.execute(select(School).where(School.tenant_slug == TENANT))
        ).scalar_one_or_none()
        if not school:
            print(f"School tenant_slug='{TENANT}' not found. Run seed_demo_ssc.py first.")
            return

        principal = (
            await db.execute(
                select(User).where(
                    User.school_id == school.id,
                    User.role == UserRole.SUPER_ADMIN,
                ).limit(1)
            )
        ).scalar_one_or_none()
        if not principal:
            print("No principal user found.")
            return

        await enable_modules(school)

        staff_added = await seed_extra_staff(db, school)
        books, issues = await seed_library(db, school)
        events = await seed_events(db, school, principal.id)
        notifs = await seed_notifications(db, school, principal.id)
        admissions = await seed_admissions(db, school, principal.id)
        expenses = await seed_expenses(db, school, principal.id)
        payroll = await seed_payroll(db, school)
        parents, parent_links = await seed_parents(db, school)
        routes, transport_assign = await seed_transport(db, school)
        parent_notices = await seed_parent_notices(db, school, principal.id)

        await db.commit()

        print(f"Working session seed complete for tenant '{TENANT}'")
        print("  modules enabled (library, transport, finance, …)")
        print(f"  staff roles added: {staff_added}")
        print(f"  library: {books} books, {issues} active issues")
        print(f"  events: {events}")
        print(f"  notifications: {notifs}")
        print(f"  admissions: {admissions}")
        print(f"  expenses: {expenses}")
        print(f"  payroll entries: {payroll}")
        print(f"  parents: {parents} users, {parent_links} links")
        print(f"  transport: {routes} routes, {transport_assign} assignments")
        print(f"  parent notices: {parent_notices}")
        print(f"  Login: tenant={TENANT}  username=principal  password={DEMO_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(main())

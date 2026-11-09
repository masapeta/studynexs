# ruff: noqa: E402, I001
"""Disposable browser-acceptance fixture for the P2 results/release journeys.

NOT for the shared reference tenant and NOT for any shared/deployed database.

Safeguards (all enforced; the script refuses to run otherwise):

- ``POSTGRES_DB`` must match ``^studynexs_e2e_[a-z0-9_]+$`` (a throwaway database).
- ``DEPLOYMENT_TIER`` must be ``development`` or ``internal`` and ``ENVIRONMENT`` must
  not be production.
- The tenant slug always starts with ``e2e-``; an existing non-``e2e-`` slug is never touched.
- Passwords are random per run and written only to a file under ``%TEMP%`` (never printed,
  never committed). The browser harness reads that file.

Usage (from ``apps/api``)::

    python scripts/e2e_fixture.py create   # creates DB, migrates, seeds, writes creds file
    python scripts/e2e_fixture.py teardown # drops the database and deletes the creds file

Personas seeded: admin, operations, subject teacher, class incharge, principal
(super_admin), parent (of student 1), student 1, student 2.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import secrets
import subprocess
import sys
import tempfile
from pathlib import Path

DB_NAME_RE = re.compile(r"^studynexs_e2e_[a-z0-9_]+$")
ALLOWED_TIERS = {"development", "internal"}
CREDS_FILE = Path(tempfile.gettempdir()) / "studynexs_e2e_fixture.json"
TENANT_PREFIX = "e2e-"

_scripts_dir = Path(__file__).resolve().parent
_api_root = _scripts_dir.parent
if str(_api_root) not in sys.path:
    sys.path.insert(0, str(_api_root))


def _guard() -> str:
    db = os.environ.get("POSTGRES_DB", "")
    if not DB_NAME_RE.match(db):
        raise SystemExit(f"Refusing: POSTGRES_DB must match {DB_NAME_RE.pattern} (got {db!r}).")
    tier = os.environ.get("DEPLOYMENT_TIER", "").strip().lower()
    if tier not in ALLOWED_TIERS:
        raise SystemExit(f"Refusing: DEPLOYMENT_TIER must be one of {sorted(ALLOWED_TIERS)}.")
    if os.environ.get("ENVIRONMENT", "development").strip().lower() == "production":
        raise SystemExit("Refusing: ENVIRONMENT=production.")
    return db


def _psql(sql: str) -> None:
    """Run admin SQL against the maintenance DB inside the local postgres container."""
    container = os.environ.get("E2E_PG_CONTAINER", "studynexs-postgres")
    user = os.environ.get("POSTGRES_USER", "studynexs")
    subprocess.run(
        ["docker", "exec", container, "psql", "-U", user, "-d", "postgres", "-v",
         "ON_ERROR_STOP=1", "-c", sql],
        check=True, capture_output=True,
    )


def _password() -> str:
    return "E2e!" + secrets.token_urlsafe(18)


async def _seed(run_id: str) -> dict:
    from datetime import date, time
    from decimal import Decimal

    from app.core.database import async_session_factory
    from app.core.security import hash_password
    from app.db.models.academic import AcademicYear, Class, Subject, TeacherSubjectMapping
    from app.db.models.examination import Exam, ExamType
    from app.db.models.question_paper import PaperStatus, QuestionPaper
    from app.db.models.school import School
    from app.db.models.student import Parent, Relationship, Student, StudentParentMap
    from app.db.models.timetable import DayOfWeek, TimetableSlot
    from app.db.models.user import User, UserRole
    from app.modules.ai.services.question_bank_service import ingest_from_paper

    slug = f"{TENANT_PREFIX}{run_id}"
    sections = [{
        "title": "Section A",
        "instructions": "Answer all.",
        "questions": [
            {"number": "1", "text": "What is 2+2?", "marks": 2, "type": "short", "answer_key": "4",
             "topic": "Number sense"},
            {"number": "2", "text": "Capital of India?", "marks": 1, "type": "mcq",
             "options": ["Mumbai", "Delhi", "Kolkata", "Chennai"], "answer_key": "B",
             "topic": "Civics"},
            {"number": "3", "text": "Define photosynthesis.", "marks": 3, "type": "long",
             "answer_key": "Process by which plants make food using sunlight.",
             "topic": "Plants"},
        ],
    }]
    creds: dict = {"tenant_slug": slug, "run_id": run_id, "personas": {}}

    async with async_session_factory() as db:
        school = School(
            name=f"E2E School {run_id}", code=f"E2E{run_id[:12]}".upper(), tenant_slug=slug,
            board="SSC", contact_email=f"{run_id}@e2e.invalid", contact_phone="+910000009999",
            is_active=True,
        )
        db.add(school)
        await db.flush()
        ay = AcademicYear(school_id=school.id, year_label="2026-2027", start_date=date(2026, 6, 1),
                          end_date=date(2027, 5, 31), is_active=True)
        db.add(ay)
        await db.flush()

        async def persona(key: str, role: UserRole, name: str, mobile: str) -> User:
            pw = _password()
            u = User(school_id=school.id, username=f"e2e_{key}", mobile=mobile, full_name=name,
                     role=role, password_hash=hash_password(pw), is_active=True)
            db.add(u)
            await db.flush()
            creds["personas"][key] = {"username": u.username, "password": pw, "role": role.value}
            return u

        principal = await persona("principal", UserRole.SUPER_ADMIN, "Priya Principal", "+910000009001")
        await persona("admin", UserRole.ADMIN, "Arun Admin", "+910000009002")
        await persona("operations", UserRole.OPERATIONS, "Omar Operations", "+910000009003")
        incharge = await persona("incharge", UserRole.CLASS_INCHARGE, "Ila Incharge", "+910000009004")
        teacher = await persona("teacher", UserRole.TEACHER, "Tara Teacher", "+910000009005")
        s1_user = await persona("student", UserRole.STUDENT, "Ravi Student", "+910000009006")
        s2_user = await persona("student2", UserRole.STUDENT, "Sita Student", "+910000009007")
        p_user = await persona("parent", UserRole.PARENT, "Pavan Parent", "+910000009008")

        cls = Class(school_id=school.id, grade="7", section="A", academic_year_id=ay.id,
                    class_incharge_id=incharge.id)
        db.add(cls)
        await db.flush()
        subj = Subject(school_id=school.id, name="General Science", class_id=cls.id)
        db.add(subj)
        await db.flush()
        db.add(TeacherSubjectMapping(school_id=school.id, teacher_id=teacher.id,
                                     class_id=cls.id, subject_id=subj.id))
        s1 = Student(school_id=school.id, user_id=s1_user.id, class_id=cls.id, roll_no="1",
                     admission_no=f"E2E-{run_id}-1")
        s2 = Student(school_id=school.id, user_id=s2_user.id, class_id=cls.id, roll_no="2",
                     admission_no=f"E2E-{run_id}-2")
        parent = Parent(school_id=school.id, user_id=p_user.id)
        db.add_all([s1, s2, parent])
        await db.flush()
        db.add(StudentParentMap(school_id=school.id, student_id=s1.id, parent_id=parent.id,
                                is_primary=True, relationship_type=Relationship.FATHER))
        paper = QuestionPaper(
            school_id=school.id, class_id=cls.id, subject_id=subj.id, created_by=teacher.id,
            title="E2E Unit Test", board="SSC", grade="7", subject_name="General Science",
            total_marks=Decimal("6"), duration_minutes=45, topics=["Plants"], sections=sections,
            status=PaperStatus.APPROVED,
        )
        db.add(paper)
        await db.flush()
        await ingest_from_paper(db, paper, approved_by=principal.id, approved_at=paper.updated_at)
        exam = Exam(
            school_id=school.id, class_id=cls.id, subject_id=subj.id, exam_type=ExamType.UNIT_TEST,
            title="E2E Unit Test", total_marks=6, date=date(2026, 7, 15), created_by=teacher.id,
            source_paper_id=paper.id,
            question_schema=[
                {"no": "1", "max_marks": 2, "topic": "Number sense"},
                {"no": "2", "max_marks": 1, "topic": "Civics"},
                {"no": "3", "max_marks": 3, "topic": "Plants"},
            ],
        )
        db.add(exam)
        # Second exam: driven through gen 1 → late approval → gen 2 → changed marks → gen 3
        # → withdraw → restore, independently of the first exam's journey.
        lifecycle_exam = Exam(
            school_id=school.id, class_id=cls.id, subject_id=subj.id, exam_type=ExamType.UNIT_TEST,
            title="E2E Lifecycle Test", total_marks=6, date=date(2026, 7, 20),
            created_by=teacher.id, source_paper_id=paper.id,
            question_schema=[
                {"no": "1", "max_marks": 2, "topic": "Number sense"},
                {"no": "2", "max_marks": 1, "topic": "Civics"},
                {"no": "3", "max_marks": 3, "topic": "Plants"},
            ],
        )
        db.add(lifecycle_exam)
        db.add(TimetableSlot(
            school_id=school.id, class_id=cls.id, subject_id=subj.id, teacher_id=teacher.id,
            day_of_week=DayOfWeek.MONDAY, period_number=1,
            start_time=time(9, 0), end_time=time(9, 45),
        ))
        await db.commit()
        creds.update(exam_id=str(exam.id), lifecycle_exam_id=str(lifecycle_exam.id),
                     class_id=str(cls.id), student_id=str(s1.id),
                     student2_id=str(s2.id), school_id=str(school.id))
    return creds


def create() -> None:
    db = _guard()
    run_id = re.sub(r"^studynexs_e2e_", "", db).replace("_", "")[:20] or secrets.token_hex(4)
    _psql(f'DROP DATABASE IF EXISTS "{db}"')
    _psql(f'CREATE DATABASE "{db}"')
    mig = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=_api_root,
                         capture_output=True, text=True)
    if mig.returncode != 0:
        raise SystemExit(f"alembic upgrade failed:\n{mig.stderr[-2000:]}")
    creds = asyncio.run(_seed(run_id))
    creds["database"] = db
    CREDS_FILE.write_text(json.dumps(creds, indent=2), encoding="utf-8")
    print(f"fixture ready: tenant={creds['tenant_slug']} db={db} creds={CREDS_FILE}")


def teardown() -> None:
    db = _guard()
    _psql(f'DROP DATABASE IF EXISTS "{db}" WITH (FORCE)')
    CREDS_FILE.unlink(missing_ok=True)
    print(f"dropped {db}; removed creds file")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "create":
        create()
    elif cmd == "teardown":
        teardown()
    else:
        raise SystemExit("usage: e2e_fixture.py create|teardown")

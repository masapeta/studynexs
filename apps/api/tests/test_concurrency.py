"""Bucket 1 — real concurrency regression tests for the race fixes (8eb133b/1403ad7).

These do NOT use the shared db_session/client fixtures: those run one rolled-back
transaction on one connection, so ON CONFLICT can't fire and no lock contention happens.
Each test seeds-and-commits, then races with independent committing sessions against a DB
where the partial unique indexes actually exist (create_all builds them from the models).
"""
from __future__ import annotations

import asyncio
from datetime import date
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import Environment, get_settings
from app.db.models.academic import AcademicYear, Class, Subject
from app.db.models.answer_sheet_evaluation import EVAL_STATUS_SUGGESTED, AnswerSheetEvaluation
from app.db.models.attendance import Attendance, AttendanceStatus
from app.db.models.base import Base
from app.db.models.examination import Exam, ExamMark, ExamType
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
from app.db.models.job import Job, JobStatus
from app.db.models.misconception import MisconceptionEntry
from app.db.models.question_paper import PaperStatus, QuestionPaper
from app.db.models.school import School
from app.db.models.student import Student
from app.db.models.user import User, UserRole
from app.modules.attendance.schemas.attendance import AttendanceEntry
from app.modules.attendance.services.attendance_service import AttendanceService
from app.modules.examinations.schemas.evaluation import EvaluationApprove
from app.modules.examinations.schemas.exam import MarkEntry
from app.modules.examinations.services.answer_sheet_eval_service import (
    AnswerSheetEvalService,
    EvalError,
)
from app.modules.examinations.services.exam_service import ExamService
from app.modules.fees.services.fee_service import FeeService
from app.modules.school.schemas.school import AcademicYearCreate
from app.modules.school.services.school_service import SchoolService

_base = get_settings().DATABASE_URL.rsplit("/", 1)[0]
TEST_DB_URL = f"{_base}/studynexs_test"
DAY = date(2026, 6, 1)


@pytest_asyncio.fixture
async def engine():
    eng = create_async_engine(TEST_DB_URL, poolclass=NullPool)
    async with eng.begin() as c:
        await c.run_sync(Base.metadata.create_all)  # builds the partial unique indexes too
    yield eng
    async with eng.begin() as c:
        await c.run_sync(Base.metadata.drop_all)
    await eng.dispose()


def _sm(engine):
    return async_sessionmaker(engine, expire_on_commit=False)


async def _seed(engine) -> dict:
    """Commit a full fixture so independent concurrent sessions can see it."""
    async with _sm(engine)() as s:
        school = School(name="T", code="T", tenant_slug="t", board="CBSE",
                        contact_email="a@t.com", contact_phone="+910000000000", is_active=True)
        s.add(school)
        await s.flush()
        ay = AcademicYear(school_id=school.id, year_label="2026-2027",
                          start_date=date(2026, 6, 1), end_date=date(2027, 5, 31), is_active=True)
        s.add(ay)
        await s.flush()
        cls = Class(school_id=school.id, grade="1", section="A", academic_year_id=ay.id)
        teach = User(school_id=school.id, mobile="+910000000001", full_name="Teach",
                     role=UserRole.TEACHER, is_active=True)
        s.add_all([cls, teach])
        await s.flush()
        subject = Subject(school_id=school.id, name="Maths", class_id=cls.id)
        suser = User(school_id=school.id, mobile="+910000000002", full_name="Stu",
                     role=UserRole.STUDENT, is_active=True)
        s.add_all([subject, suser])
        await s.flush()
        stu = Student(school_id=school.id, user_id=suser.id, class_id=cls.id, admission_no="A1")
        s.add(stu)
        await s.flush()
        exam = Exam(school_id=school.id, class_id=cls.id, subject_id=subject.id,
                    exam_type=ExamType.FINAL, title="Final", total_marks=Decimal("100"),
                    date=DAY, created_by=teach.id)
        fee_struct = FeeStructure(school_id=school.id, class_id=cls.id, fee_type=FeeType.TUITION,
                                  amount=Decimal("1000"), frequency=FeeFrequency.MONTHLY,
                                  academic_year_id=ay.id, due_day=10)
        counter = ReceiptCounter(school_id=school.id, prefix="T", last_sequence=0)
        s.add_all([exam, fee_struct, counter])
        await s.flush()
        fee_rec = StudentFeeRecord(school_id=school.id, student_id=stu.id,
                                   fee_structure_id=fee_struct.id, amount=Decimal("1000"),
                                   due_date=DAY, status=FeeStatus.PENDING, paid_amount=Decimal("0"))
        s.add(fee_rec)
        await s.commit()
        return {
            "school_id": school.id, "class_id": cls.id, "student_id": stu.id,
            "teacher_id": teach.id, "subject_id": subject.id, "exam_id": exam.id,
            "fee_record_id": fee_rec.id,
        }


@pytest.mark.asyncio
async def test_attendance_concurrent_save_one_row(engine):
    ids = await _seed(engine)

    async def mark(status):
        async with _sm(engine)() as s:
            await AttendanceService(s).mark_bulk(
                ids["school_id"], ids["class_id"], DAY,
                [AttendanceEntry(student_id=ids["student_id"], status=status)], ids["teacher_id"])
            await s.commit()

    results = await asyncio.gather(
        *(mark(AttendanceStatus.PRESENT) for _ in range(4)), return_exceptions=True
    )
    assert not [r for r in results if isinstance(r, Exception)]
    async with _sm(engine)() as s:
        n = await s.scalar(select(func.count()).select_from(Attendance).where(
            Attendance.student_id == ids["student_id"], Attendance.date == DAY))
    assert n == 1  # all four collapsed into one row, no IntegrityError


@pytest.mark.asyncio
async def test_exam_marks_concurrent_save_one_row(engine):
    ids = await _seed(engine)

    async def enter(mark):
        async with _sm(engine)() as s:
            await ExamService(s).enter_marks(
                ids["school_id"], ids["exam_id"],
                [MarkEntry(student_id=ids["student_id"], marks_obtained=Decimal(mark))])
            await s.commit()

    results = await asyncio.gather(*(enter(m) for m in (40, 55, 70, 88)), return_exceptions=True)
    assert not [r for r in results if isinstance(r, Exception)]
    async with _sm(engine)() as s:
        n = await s.scalar(select(func.count()).select_from(ExamMark).where(
            ExamMark.exam_id == ids["exam_id"], ExamMark.student_id == ids["student_id"]))
    assert n == 1


async def _seed_suggested_evaluation(engine) -> dict:
    ids = await _seed(engine)
    async with _sm(engine)() as s:
        paper = QuestionPaper(
            school_id=ids["school_id"],
            class_id=ids["class_id"],
            subject_id=ids["subject_id"],
            created_by=ids["teacher_id"],
            title="Concurrency Paper",
            board="SSC",
            grade="1",
            subject_name="Maths",
            total_marks=Decimal("2"),
            duration_minutes=30,
            topics=["Arithmetic"],
            sections=[
                {
                    "title": "A",
                    "questions": [
                        {
                            "number": "1",
                            "text": "What is 2+2?",
                            "marks": 2,
                            "type": "short",
                            "answer_key": "4",
                        }
                    ],
                }
            ],
            status=PaperStatus.APPROVED,
            grounded=True,
        )
        s.add(paper)
        await s.flush()

        exam = await s.get(Exam, ids["exam_id"])
        exam.source_paper_id = paper.id
        exam.total_marks = Decimal("2")
        exam.question_schema = [{"no": "1", "max_marks": 2, "topic": "Arithmetic"}]

        evaluation = AnswerSheetEvaluation(
            school_id=ids["school_id"],
            exam_id=ids["exam_id"],
            student_id=ids["student_id"],
            created_by=ids["teacher_id"],
            status=EVAL_STATUS_SUGGESTED,
            input_answers={"1": "5"},
            ai_suggestions={
                "1": {
                    "marks_suggested": 0,
                    "max_marks": 2,
                    "feedback": "Incorrect arithmetic answer",
                    "confidence": 0.9,
                    "student_answer": "5",
                    "topic": "Arithmetic",
                    "grounded": True,
                    "grounding_sources": [{"ref_id": "h4-source"}],
                    "citations": [1],
                }
            },
        )
        s.add(evaluation)
        await s.commit()
        ids["evaluation_id"] = evaluation.id
    return ids


async def _seed_evaluation_target(engine) -> dict:
    ids = await _seed(engine)
    async with _sm(engine)() as s:
        paper = QuestionPaper(
            school_id=ids["school_id"],
            class_id=ids["class_id"],
            subject_id=ids["subject_id"],
            created_by=ids["teacher_id"],
            title="Concurrency Create Paper",
            board="SSC",
            grade="1",
            subject_name="Maths",
            total_marks=Decimal("2"),
            duration_minutes=30,
            topics=["Arithmetic"],
            sections=[
                {
                    "title": "A",
                    "questions": [
                        {
                            "number": "1",
                            "text": "What is 2+2?",
                            "marks": 2,
                            "type": "short",
                            "answer_key": "4",
                        }
                    ],
                }
            ],
            status=PaperStatus.APPROVED,
            grounded=True,
        )
        s.add(paper)
        await s.flush()

        exam = await s.get(Exam, ids["exam_id"])
        exam.source_paper_id = paper.id
        exam.total_marks = Decimal("2")
        exam.question_schema = [{"no": "1", "max_marks": 2, "topic": "Arithmetic"}]
        await s.commit()
    return ids


@pytest.mark.asyncio
async def test_evaluation_create_concurrent_only_one_processing_row(engine, monkeypatch):
    ids = await _seed_evaluation_target(engine)

    from app.core.jobs import queue as queue_mod
    from app.modules.examinations.services import answer_sheet_eval_service as eval_mod

    monkeypatch.setattr(eval_mod.settings, "ENVIRONMENT", Environment.DEVELOPMENT)

    async def fake_check_ai_credits(*args, **kwargs):
        return None

    monkeypatch.setattr(eval_mod, "check_ai_credits", fake_check_ai_credits)

    async def fake_enqueue(db, *, task, params, school_id=None, created_by=None):
        job = Job(
            type=task,
            params=params,
            school_id=school_id,
            created_by=created_by,
            status=JobStatus.QUEUED,
        )
        db.add(job)
        await db.flush()
        return job

    monkeypatch.setattr(queue_mod, "enqueue", fake_enqueue)

    async def create_once():
        async with _sm(engine)() as s:
            school = await s.get(School, ids["school_id"])
            service = AnswerSheetEvalService(s)
            try:
                await service.create_and_evaluate(
                    school_id=ids["school_id"],
                    exam_id=ids["exam_id"],
                    student_id=ids["student_id"],
                    created_by=ids["teacher_id"],
                    role="teacher",
                    school=school,
                    student_answers={"1": "4"},
                )
                await s.commit()
                return "success"
            except EvalError as exc:
                await s.rollback()
                return str(exc)

    results = await asyncio.gather(*(create_once() for _ in range(8)))
    assert results.count("success") == 1
    assert results.count("Evaluation already in progress for this student") == 7

    async with _sm(engine)() as s:
        evaluation_count = await s.scalar(
            select(func.count()).select_from(AnswerSheetEvaluation).where(
                AnswerSheetEvaluation.school_id == ids["school_id"],
                AnswerSheetEvaluation.exam_id == ids["exam_id"],
                AnswerSheetEvaluation.student_id == ids["student_id"],
            )
        )
        job_count = await s.scalar(
            select(func.count()).select_from(Job).where(Job.school_id == ids["school_id"])
        )
    assert evaluation_count == 1
    assert job_count == 1


@pytest.mark.asyncio
async def test_evaluation_approve_concurrent_only_one_transition(engine):
    ids = await _seed_suggested_evaluation(engine)

    async def approve_once():
        async with _sm(engine)() as s:
            service = AnswerSheetEvalService(s)
            try:
                await service.approve(
                    school_id=ids["school_id"],
                    evaluation_id=ids["evaluation_id"],
                    data=EvaluationApprove(),
                    approved_by=ids["teacher_id"],
                )
                await s.commit()
                return "success"
            except EvalError as exc:
                await s.rollback()
                return str(exc)

    results = await asyncio.gather(*(approve_once() for _ in range(8)))
    assert results.count("success") == 1
    assert results.count("Only suggested evaluations can be approved") == 7

    async with _sm(engine)() as s:
        mark_count = await s.scalar(
            select(func.count()).select_from(ExamMark).where(
                ExamMark.exam_id == ids["exam_id"],
                ExamMark.student_id == ids["student_id"],
            )
        )
        misconception_count = await s.scalar(
            select(func.count()).select_from(MisconceptionEntry).where(
                MisconceptionEntry.school_id == ids["school_id"],
            )
        )
        misconception_occurrences = await s.scalar(
            select(func.coalesce(func.sum(MisconceptionEntry.occurrence_count), 0)).where(
                MisconceptionEntry.school_id == ids["school_id"],
            )
        )
    assert mark_count == 1
    assert misconception_count == 1
    assert misconception_occurrences == 1


@pytest.mark.asyncio
async def test_enter_marks_rejects_over_max(engine):
    ids = await _seed(engine)
    async with _sm(engine)() as s:
        with pytest.raises(ValueError):
            await ExamService(s).enter_marks(
                ids["school_id"], ids["exam_id"],
                [MarkEntry(student_id=ids["student_id"], marks_obtained=Decimal("200"))])


@pytest.mark.asyncio
async def test_active_year_double_activate(engine):
    ids = await _seed(engine)  # seed already has one active year (2026-2027)

    async def create(label):
        async with _sm(engine)() as s:
            await SchoolService(s).create_year(
                ids["school_id"],
                AcademicYearCreate(year_label=label, start_date=date(2027, 6, 1),
                                   end_date=date(2028, 5, 31), is_active=True))
            await s.commit()

    results = await asyncio.gather(create("2027-2028"), create("2028-2029"), return_exceptions=True)
    errs = [r for r in results if isinstance(r, IntegrityError)]
    assert len(errs) == 1  # the partial unique index let exactly one win
    async with _sm(engine)() as s:
        active = await s.scalar(select(func.count()).select_from(AcademicYear).where(
            AcademicYear.school_id == ids["school_id"], AcademicYear.is_active.is_(True)))
    assert active == 1  # invariant held: exactly one active year


async def _pay(engine, ids, idem):
    async with _sm(engine)() as s:
        await FeeService(s).process_payment(
            ids["school_id"], ids["fee_record_id"], Decimal("400"),
            PaymentMode.CASH, idempotency_key=idem)
        await s.commit()


@pytest.mark.asyncio
async def test_cash_idempotency_concurrent(engine):
    ids = await _seed(engine)
    results = await asyncio.gather(
        _pay(engine, ids, "KEY1"), _pay(engine, ids, "KEY1"), return_exceptions=True
    )
    errs = [r for r in results if isinstance(r, IntegrityError)]
    assert len(errs) == 1  # second concurrent same-key dup blocked by the partial unique index
    async with _sm(engine)() as s:
        n = await s.scalar(select(func.count()).select_from(FeeReceipt))
    assert n == 1  # exactly one receipt for the cash payment


@pytest.mark.asyncio
async def test_first_payment_provisions_counter(engine):
    """M5: a school whose ReceiptCounter was never created still takes its first payment —
    the counter self-provisions instead of crashing on scalar_one()."""
    ids = await _seed(engine)
    async with _sm(engine)() as s:
        await s.execute(
            delete(ReceiptCounter).where(ReceiptCounter.school_id == ids["school_id"]))
        await s.commit()

    async with _sm(engine)() as s:
        receipt = await FeeService(s).process_payment(
            ids["school_id"], ids["fee_record_id"], Decimal("400"), PaymentMode.CASH)
        await s.commit()
        assert receipt.receipt_number  # a receipt was issued, no NoResultFound

    async with _sm(engine)() as s:
        n = await s.scalar(select(func.count()).select_from(ReceiptCounter).where(
            ReceiptCounter.school_id == ids["school_id"]))
    assert n == 1  # counter self-provisioned exactly once


@pytest.mark.asyncio
async def test_same_idem_key_returns_same_receipt(engine):
    ids = await _seed(engine)
    async with _sm(engine)() as s:
        svc = FeeService(s)
        r1 = await svc.process_payment(ids["school_id"], ids["fee_record_id"], Decimal("400"),
                                       PaymentMode.CASH, idempotency_key="SEQ")
        await s.commit()
        r2 = await svc.process_payment(ids["school_id"], ids["fee_record_id"], Decimal("400"),
                                       PaymentMode.CASH, idempotency_key="SEQ")
        await s.commit()
    assert r1.id == r2.id  # sequential retry returned the existing receipt, no new row

"""H5 recovery tests for stale answer-sheet evaluation jobs."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.jobs.recovery import recover_stale_answer_sheet_eval_jobs
from app.db.models.academic import AcademicYear, Class, Subject
from app.db.models.answer_sheet_evaluation import (
    EVAL_STATUS_APPROVED,
    EVAL_STATUS_FAILED,
    EVAL_STATUS_PROCESSING,
    EVAL_STATUS_SUGGESTED,
    AnswerSheetEvaluation,
)
from app.db.models.examination import Exam, ExamType
from app.db.models.job import Job, JobStatus
from app.db.models.school import School
from app.db.models.student import Student
from app.db.models.user import User, UserRole


async def _seed_stack(db: AsyncSession, suffix: str) -> dict:
    school = School(
        name=f"Recovery School {suffix}",
        code=f"REC{suffix}",
        tenant_slug=f"recovery-{suffix.lower()}",
        board="SSC",
        contact_email=f"recovery-{suffix.lower()}@test.com",
        contact_phone=f"+91900000{suffix.zfill(4)}",
        is_active=True,
    )
    db.add(school)
    await db.flush()

    year = AcademicYear(
        school_id=school.id,
        year_label="2026-2027",
        start_date=date(2026, 6, 1),
        end_date=date(2027, 5, 31),
        is_active=True,
    )
    teacher = User(
        school_id=school.id,
        mobile=f"+91910000{suffix.zfill(4)}",
        full_name=f"Recovery Teacher {suffix}",
        role=UserRole.TEACHER,
        is_active=True,
    )
    student_user = User(
        school_id=school.id,
        mobile=f"+91920000{suffix.zfill(4)}",
        full_name=f"Recovery Student {suffix}",
        role=UserRole.STUDENT,
        is_active=True,
    )
    db.add_all([year, teacher, student_user])
    await db.flush()

    cls = Class(school_id=school.id, grade="8", section=suffix[:1], academic_year_id=year.id)
    db.add(cls)
    await db.flush()

    subject = Subject(school_id=school.id, name=f"Mathematics {suffix}", class_id=cls.id)
    student = Student(
        school_id=school.id,
        user_id=student_user.id,
        class_id=cls.id,
        admission_no=f"REC-{suffix}",
    )
    db.add_all([subject, student])
    await db.flush()

    exam = Exam(
        school_id=school.id,
        class_id=cls.id,
        subject_id=subject.id,
        exam_type=ExamType.UNIT_TEST,
        title=f"Recovery Exam {suffix}",
        total_marks=Decimal("10"),
        date=date(2026, 7, 23),
        created_by=teacher.id,
    )
    db.add(exam)
    await db.flush()

    return {
        "school": school,
        "teacher": teacher,
        "student": student,
        "exam": exam,
    }


async def _seed_eval_job(
    db: AsyncSession,
    *,
    suffix: str,
    eval_status: str,
    job_status: JobStatus = JobStatus.QUEUED,
    updated_minutes_ago: int = 120,
) -> tuple[Job, AnswerSheetEvaluation, dict]:
    ids = await _seed_stack(db, suffix)
    evaluation = AnswerSheetEvaluation(
        school_id=ids["school"].id,
        exam_id=ids["exam"].id,
        student_id=ids["student"].id,
        created_by=ids["teacher"].id,
        status=eval_status,
        input_answers={"1": "4"},
        ai_suggestions={"1": {"marks_suggested": 1, "max_marks": 1}},
    )
    db.add(evaluation)
    await db.flush()

    job = Job(
        type="answer_sheet_eval",
        params={"evaluation_id": str(evaluation.id), "role": "teacher"},
        school_id=ids["school"].id,
        created_by=ids["teacher"].id,
        status=job_status,
        updated_at=datetime.now(timezone.utc) - timedelta(minutes=updated_minutes_ago),
    )
    db.add(job)
    await db.flush()
    evaluation.job_id = job.id
    await db.flush()
    return job, evaluation, ids


@pytest.mark.asyncio
async def test_stale_evaluation_job_recovery_dry_run_does_not_mutate(db_session: AsyncSession):
    job, _evaluation, ids = await _seed_eval_job(
        db_session,
        suffix="101",
        eval_status=EVAL_STATUS_SUGGESTED,
    )

    result = await recover_stale_answer_sheet_eval_jobs(
        db_session,
        older_than_minutes=30,
        school_id=ids["school"].id,
        apply=False,
    )

    assert result.dry_run is True
    assert result.scanned == 1
    assert result.reconciled_done == 1
    assert result.items[0].action == "mark_job_done"
    assert result.items[0].applied is False

    refreshed = await db_session.get(Job, job.id)
    assert refreshed.status == JobStatus.QUEUED
    assert refreshed.result is None


@pytest.mark.asyncio
async def test_stale_evaluation_job_recovery_marks_terminal_success_done(
    db_session: AsyncSession,
):
    job, evaluation, ids = await _seed_eval_job(
        db_session,
        suffix="102",
        eval_status=EVAL_STATUS_APPROVED,
        job_status=JobStatus.RUNNING,
    )

    result = await recover_stale_answer_sheet_eval_jobs(
        db_session,
        older_than_minutes=30,
        school_id=ids["school"].id,
        apply=True,
    )

    assert result.scanned == 1
    assert result.reconciled_done == 1
    assert result.needs_manual_review == 0

    refreshed = await db_session.get(Job, job.id)
    assert refreshed.status == JobStatus.DONE
    assert refreshed.error is None
    assert refreshed.result["recovered"] is True
    assert refreshed.result["evaluation_id"] == str(evaluation.id)
    assert refreshed.result["evaluation_status"] == EVAL_STATUS_APPROVED


@pytest.mark.asyncio
async def test_stale_evaluation_job_recovery_marks_failed_evaluation_failed(
    db_session: AsyncSession,
):
    job, evaluation, ids = await _seed_eval_job(
        db_session,
        suffix="103",
        eval_status=EVAL_STATUS_FAILED,
    )

    result = await recover_stale_answer_sheet_eval_jobs(
        db_session,
        older_than_minutes=30,
        school_id=ids["school"].id,
        apply=True,
    )

    assert result.scanned == 1
    assert result.reconciled_failed == 1

    refreshed = await db_session.get(Job, job.id)
    assert refreshed.status == JobStatus.FAILED
    assert refreshed.result["evaluation_id"] == str(evaluation.id)
    assert refreshed.error == "Recovered stale job: linked evaluation already failed."


@pytest.mark.asyncio
async def test_stale_evaluation_job_recovery_leaves_processing_for_manual_review(
    db_session: AsyncSession,
):
    job, _evaluation, ids = await _seed_eval_job(
        db_session,
        suffix="104",
        eval_status=EVAL_STATUS_PROCESSING,
    )

    result = await recover_stale_answer_sheet_eval_jobs(
        db_session,
        older_than_minutes=30,
        school_id=ids["school"].id,
        apply=True,
    )

    assert result.scanned == 1
    assert result.needs_manual_review == 1
    assert result.items[0].action == "manual_review"

    refreshed = await db_session.get(Job, job.id)
    assert refreshed.status == JobStatus.QUEUED
    assert refreshed.result is None


@pytest.mark.asyncio
async def test_stale_evaluation_job_recovery_is_tenant_scoped(db_session: AsyncSession):
    job_a, _evaluation_a, ids_a = await _seed_eval_job(
        db_session,
        suffix="105",
        eval_status=EVAL_STATUS_SUGGESTED,
    )
    job_b, _evaluation_b, ids_b = await _seed_eval_job(
        db_session,
        suffix="106",
        eval_status=EVAL_STATUS_SUGGESTED,
    )

    result = await recover_stale_answer_sheet_eval_jobs(
        db_session,
        older_than_minutes=30,
        school_id=ids_a["school"].id,
        apply=True,
    )

    assert result.scanned == 1
    assert result.items[0].school_id == ids_a["school"].id

    refreshed_a = await db_session.get(Job, job_a.id)
    refreshed_b = await db_session.get(Job, job_b.id)
    assert refreshed_a.status == JobStatus.DONE
    assert refreshed_b.status == JobStatus.QUEUED

    count_done_for_other_tenant = await db_session.scalar(
        select(Job).where(Job.id == job_b.id, Job.school_id == ids_b["school"].id)
    )
    assert count_done_for_other_tenant.status == JobStatus.QUEUED

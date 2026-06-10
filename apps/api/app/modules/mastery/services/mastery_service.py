"""Mastery recompute orchestration — DB in, ledger rows out.

Recomputes the whole class × subject on every marks save: class averages need
everyone anyway, the workload is bounded (~60 students × ~30 tagged assessments),
and the upsert is idempotent so reprocessing (worker retries) is always safe.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

import structlog
from sqlalchemy import func, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import Class, Subject
from app.db.models.examination import Exam, ExamMark
from app.db.models.mastery import FlagStatus, MasteryFlag, StudentTopicMastery
from app.db.models.student import Student
from app.db.models.user import User
from app.modules.mastery.services import flag_rules
from app.modules.mastery.services.compute import (
    Datapoint,
    history_of,
    topic_pcts_for_mark,
    trend_of,
    weighted_mastery,
)
from app.modules.mastery.services.topic_norm import display_topic

logger = structlog.get_logger()


async def recompute_class_subject(
    db: AsyncSession,
    school_id: uuid.UUID,
    class_id: uuid.UUID,
    subject_id: uuid.UUID,
) -> int:
    """Rebuild the topic-mastery ledger for one class × subject. Returns rows upserted.

    Exactly three queries: class row, topic-tagged exams, all their marks.
    Everything between is in-memory; the write is one bulk upsert.
    """
    school_class = (
        await db.execute(
            select(Class).where(Class.id == class_id, Class.school_id == school_id)
        )
    ).scalar_one_or_none()
    if not school_class:
        return 0

    exams = list(
        (
            await db.execute(
                select(Exam).where(
                    Exam.school_id == school_id,
                    Exam.class_id == class_id,
                    Exam.subject_id == subject_id,
                    or_(Exam.topic.is_not(None), Exam.question_schema.is_not(None)),
                )
            )
        )
        .scalars()
        .all()
    )
    if not exams:
        return 0

    marks = list(
        (
            await db.execute(
                select(ExamMark).where(
                    ExamMark.school_id == school_id,
                    ExamMark.exam_id.in_([e.id for e in exams]),
                )
            )
        )
        .scalars()
        .all()
    )
    if not marks:
        return 0

    exams_by_id = {e.id: e for e in exams}

    # (student_id, normalized_topic) -> datapoints; remember a display form per topic.
    points: dict[tuple[uuid.UUID, str], list[Datapoint]] = {}
    displays: dict[str, str] = {}

    for mark in marks:
        exam = exams_by_id[mark.exam_id]
        assessed_on = exam.date or exam.created_at.date()
        pcts = topic_pcts_for_mark(
            question_schema=exam.question_schema,
            question_marks=mark.question_marks,
            exam_topic=exam.topic,
            marks_obtained=float(mark.marks_obtained),
            total_marks=float(exam.total_marks),
        )
        if pcts and exam.question_schema:
            for q in exam.question_schema:
                raw = q.get("topic") or exam.topic
                if raw:
                    displays.setdefault(display_topic(raw).casefold(), display_topic(raw))
        if pcts and exam.topic:
            displays.setdefault(display_topic(exam.topic).casefold(), display_topic(exam.topic))
        for topic_key, pct in pcts.items():
            points.setdefault((mark.student_id, topic_key), []).append(
                Datapoint(
                    exam_id=str(exam.id),
                    exam_type=exam.exam_type.value,
                    exam_title=exam.title,
                    assessed_on=assessed_on,
                    pct=pct,
                )
            )

    if not points:
        return 0

    today = date.today()
    per_student: dict[tuple[uuid.UUID, str], dict] = {}
    topic_totals: dict[str, list[float]] = {}

    for (student_id, topic_key), dps in points.items():
        mastery = weighted_mastery(dps, today)
        per_student[(student_id, topic_key)] = {
            "mastery_pct": mastery,
            "assessments_count": len(dps),
            "last_assessed_on": max(dp.assessed_on for dp in dps),
            "trend": trend_of(dps),
            "history": history_of(dps),
        }
        topic_totals.setdefault(topic_key, []).append(mastery)

    class_avg = {
        topic_key: round(sum(vals) / len(vals), 2) for topic_key, vals in topic_totals.items()
    }

    rows = [
        {
            "school_id": school_id,
            "student_id": student_id,
            "class_id": class_id,
            "subject_id": subject_id,
            "academic_year_id": school_class.academic_year_id,
            "topic": topic_key,
            "topic_display": displays.get(topic_key, topic_key),
            "mastery_pct": stats["mastery_pct"],
            "class_avg_pct": class_avg[topic_key],
            "assessments_count": stats["assessments_count"],
            "last_assessed_on": stats["last_assessed_on"],
            "trend": stats["trend"],
            "history": stats["history"],
        }
        for (student_id, topic_key), stats in per_student.items()
    ]

    stmt = pg_insert(StudentTopicMastery).values(rows)
    stmt = stmt.on_conflict_do_update(
        constraint="uq_student_topic_mastery",
        set_={
            "class_id": stmt.excluded.class_id,
            "topic_display": stmt.excluded.topic_display,
            "mastery_pct": stmt.excluded.mastery_pct,
            "class_avg_pct": stmt.excluded.class_avg_pct,
            "assessments_count": stmt.excluded.assessments_count,
            "last_assessed_on": stmt.excluded.last_assessed_on,
            "trend": stmt.excluded.trend,
            "history": stmt.excluded.history,
            "updated_at": func.now(),
        },
    )
    await db.execute(stmt)
    await db.flush()

    flags_raised = await _raise_flags(
        db,
        school_id=school_id,
        class_id=class_id,
        subject_id=subject_id,
        academic_year_id=school_class.academic_year_id,
        ledger_rows=rows,
    )

    logger.info(
        "mastery_recomputed",
        school_id=str(school_id),
        class_id=str(class_id),
        subject_id=str(subject_id),
        rows=len(rows),
        flags_raised=flags_raised,
    )
    return len(rows)


async def _raise_flags(
    db: AsyncSession,
    *,
    school_id: uuid.UUID,
    class_id: uuid.UUID,
    subject_id: uuid.UUID,
    academic_year_id: uuid.UUID,
    ledger_rows: list[dict],
) -> int:
    """Evaluate rules over the fresh ledger rows and raise PENDING_REVIEW flags.

    Race-safe and idempotent: the partial unique index on open flags makes the
    insert ON CONFLICT DO NOTHING; a recent dismissal/notification (cool-off)
    suppresses re-raising the same topic.
    """
    candidates: list[tuple[dict, flag_rules.FlagCandidate]] = []
    for row in ledger_rows:
        candidate = flag_rules.evaluate(
            mastery_pct=row["mastery_pct"],
            class_avg_pct=row["class_avg_pct"],
            trend=row["trend"],
            assessments_count=row["assessments_count"],
        )
        if candidate:
            candidates.append((row, candidate))
    if not candidates:
        return 0

    # Cool-off: one query for recently closed flags on the affected students/topics.
    cooloff_cutoff = datetime.now(timezone.utc) - timedelta(days=flag_rules.COOLOFF_DAYS)
    student_ids = list({row["student_id"] for row, _ in candidates})
    recently_closed = (
        await db.execute(
            select(MasteryFlag.student_id, MasteryFlag.topic).where(
                MasteryFlag.school_id == school_id,
                MasteryFlag.subject_id == subject_id,
                MasteryFlag.academic_year_id == academic_year_id,
                MasteryFlag.student_id.in_(student_ids),
                MasteryFlag.status.in_([FlagStatus.DISMISSED, FlagStatus.NOTIFIED]),
                MasteryFlag.updated_at >= cooloff_cutoff,
            )
        )
    ).all()
    suppressed = {(student_id, topic) for student_id, topic in recently_closed}

    candidates = [
        (row, c) for row, c in candidates if (row["student_id"], row["topic"]) not in suppressed
    ]
    if not candidates:
        return 0

    # Evidence is frozen at raise time — names included so the narrative the
    # teacher approves later is grounded without further queries.
    subject_name = await db.scalar(select(Subject.name).where(Subject.id == subject_id))
    name_rows = (
        await db.execute(
            select(Student.id, User.full_name)
            .join(User, User.id == Student.user_id)
            .where(Student.id.in_([row["student_id"] for row, _ in candidates]))
        )
    ).all()
    student_names = {sid: name for sid, name in name_rows}

    flag_values = []
    for row, candidate in candidates:
        flag_values.append(
            {
                "school_id": school_id,
                "student_id": row["student_id"],
                "class_id": class_id,
                "subject_id": subject_id,
                "academic_year_id": academic_year_id,
                "topic": row["topic"],
                "topic_display": row["topic_display"],
                "severity": candidate.severity,
                "status": FlagStatus.PENDING_REVIEW,
                "reasons": candidate.reasons,
                "evidence": {
                    "student_name": student_names.get(row["student_id"]),
                    "subject_name": subject_name,
                    "topic": row["topic_display"],
                    "mastery_pct": row["mastery_pct"],
                    "class_avg_pct": row["class_avg_pct"],
                    "gap": round((row["class_avg_pct"] or 0) - row["mastery_pct"], 2),
                    "trend": row["trend"].value,
                    "assessments_count": row["assessments_count"],
                    "history": row["history"],
                },
            }
        )

    # Untargeted ON CONFLICT DO NOTHING covers the open-flag partial unique
    # index (dedupe) and concurrent worker retries alike.
    stmt = pg_insert(MasteryFlag).values(flag_values).on_conflict_do_nothing()
    result = await db.execute(stmt)
    await db.flush()
    return result.rowcount or 0

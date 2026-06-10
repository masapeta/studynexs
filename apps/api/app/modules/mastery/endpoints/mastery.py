"""Mastery endpoints — topic profiles, class heatmap, topic typeahead, admin recompute."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import assert_can_access_student
from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user, require_roles
from app.core.tenant_scope import TenantScope
from app.db.models.academic import Subject
from app.db.models.mastery import StudentTopicMastery
from app.db.models.student import Student
from app.db.models.user import User
from app.modules.mastery.schemas.mastery import (
    ClassHeatmapOut,
    HeatmapCellOut,
    MasteryProfileOut,
    RecomputeRequest,
    RecomputeResponse,
    SubjectMasteryOut,
    TopicMasteryOut,
)
from app.modules.mastery.services.mastery_service import recompute_class_subject
from app.shared.schemas.common import APIResponse

router = APIRouter()

_STAFF = ("teacher", "class_incharge", "admin", "super_admin")


@router.get("/students/{student_id}", response_model=APIResponse[MasteryProfileOut])
async def student_topic_profile(
    student_id: uuid.UUID,
    subject_id: uuid.UUID | None = None,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Per-topic mastery — staff: any student; parent: linked child; student: self."""
    await assert_can_access_student(current_user, db, student_id)

    query = (
        select(StudentTopicMastery, Subject.name)
        .join(Subject, Subject.id == StudentTopicMastery.subject_id)
        .where(
            StudentTopicMastery.school_id == uuid.UUID(current_user.school_id),
            StudentTopicMastery.student_id == student_id,
        )
        .order_by(Subject.name, StudentTopicMastery.topic)
    )
    if subject_id:
        query = query.where(StudentTopicMastery.subject_id == subject_id)
    rows = (await db.execute(query)).all()

    by_subject: dict[uuid.UUID, SubjectMasteryOut] = {}
    for stm, subject_name in rows:
        bucket = by_subject.get(stm.subject_id)
        if not bucket:
            bucket = SubjectMasteryOut(
                subject_id=stm.subject_id,
                subject_name=subject_name,
                class_id=stm.class_id,
                topics=[],
            )
            by_subject[stm.subject_id] = bucket
        bucket.topics.append(TopicMasteryOut.model_validate(stm))

    profile = MasteryProfileOut(student_id=student_id, subjects=list(by_subject.values()))
    return APIResponse(data=profile)


@router.get("/classes/{class_id}/heatmap", response_model=APIResponse[ClassHeatmapOut])
async def class_heatmap(
    class_id: uuid.UUID,
    subject_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_STAFF)),
    db: AsyncSession = Depends(get_db),
):
    """Students × topics mastery matrix for one class+subject."""
    school_id = uuid.UUID(current_user.school_id)
    await TenantScope(db, school_id).school_class(class_id)

    rows = (
        await db.execute(
            select(StudentTopicMastery, User.full_name, Student.roll_no)
            .join(Student, Student.id == StudentTopicMastery.student_id)
            .join(User, User.id == Student.user_id)
            .where(
                StudentTopicMastery.school_id == school_id,
                StudentTopicMastery.class_id == class_id,
                StudentTopicMastery.subject_id == subject_id,
            )
            .order_by(Student.roll_no)
        )
    ).all()

    topic_columns: list[str] = []
    cells: dict[uuid.UUID, HeatmapCellOut] = {}
    for stm, student_name, roll_no in rows:
        if stm.topic_display not in topic_columns:
            topic_columns.append(stm.topic_display)
        cell = cells.get(stm.student_id)
        if not cell:
            cell = HeatmapCellOut(
                student_id=stm.student_id,
                student_name=student_name or "—",
                roll_no=roll_no,
                topics={},
            )
            cells[stm.student_id] = cell
        cell.topics[stm.topic_display] = float(stm.mastery_pct)

    heatmap = ClassHeatmapOut(
        class_id=class_id,
        subject_id=subject_id,
        topic_columns=sorted(topic_columns),
        students=list(cells.values()),
    )
    return APIResponse(data=heatmap)


@router.get("/topics", response_model=APIResponse[list[str]])
async def known_topics(
    subject_id: uuid.UUID | None = None,
    current_user: CurrentUser = Depends(require_roles(*_STAFF)),
    db: AsyncSession = Depends(get_db),
):
    """Distinct topics already in use — feeds the schema editor typeahead."""
    query = (
        select(StudentTopicMastery.topic_display)
        .where(StudentTopicMastery.school_id == uuid.UUID(current_user.school_id))
        .distinct()
        .order_by(StudentTopicMastery.topic_display)
    )
    if subject_id:
        query = query.where(StudentTopicMastery.subject_id == subject_id)
    topics = [row[0] for row in (await db.execute(query)).all()]
    return APIResponse(data=topics)


@router.post("/recompute", response_model=APIResponse[RecomputeResponse])
async def recompute(
    body: RecomputeRequest,
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin")),
    db: AsyncSession = Depends(get_db),
):
    """Synchronous backfill — run after tagging historical exams with topics."""
    school_id = uuid.UUID(current_user.school_id)
    scope = TenantScope(db, school_id)
    await scope.subject_in_class(body.subject_id, body.class_id)
    count = await recompute_class_subject(db, school_id, body.class_id, body.subject_id)
    return APIResponse(
        data=RecomputeResponse(rows_upserted=count),
        message=f"Recomputed {count} topic-mastery rows",
    )

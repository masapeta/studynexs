"""Mastery endpoints — topic profiles, heatmap, flags review pipeline, digest."""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import assert_can_access_student
from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user, require_roles
from app.core.rate_limit import rate_limit
from app.core.staff_permissions import assert_mastery_flag_review, get_staff_scope
from app.modules.ai.gateway.errors import raise_http_for_llm_error
from app.core.tenant_scope import TenantScope
from app.db.models.academic import Class, Subject
from app.db.models.mastery import FlagStatus, MasteryFlag, StudentTopicMastery
from app.db.models.notification import NotificationChannel
from app.db.models.student import Parent, Student, StudentParentMap
from app.db.models.user import User
from app.modules.ai.services.usage_caps import enforce_monthly_ai_cap
from app.modules.mastery.schemas.mastery import (
    ClassHeatmapOut,
    DigestEntryOut,
    DigestOut,
    DismissRequest,
    FlagOut,
    HeatmapCellOut,
    MasteryProfileOut,
    NarrativeUpdate,
    NotifyResponse,
    RecomputeRequest,
    RecomputeResponse,
    SubjectMasteryOut,
    TopicMasteryOut,
)
from app.modules.mastery.services.mastery_service import recompute_class_subject
from app.modules.mastery.services.narrative_service import draft_narrative
from app.modules.notifications.services.notification_service import NotificationService
from app.shared.schemas.common import APIResponse

router = APIRouter()

_STAFF = ("teacher", "class_incharge", "admin", "super_admin")
_AI_GEN_RATE = {"max_requests": 12, "window_seconds": 60}


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


# ── Flags review pipeline ────────────────────────────────────────────────────


def _flag_out(flag: MasteryFlag, student_name=None, class_name=None, subject_name=None) -> FlagOut:
    out = FlagOut.model_validate(flag)
    out.student_name = student_name or (flag.evidence or {}).get("student_name")
    out.subject_name = subject_name or (flag.evidence or {}).get("subject_name")
    out.class_name = class_name
    return out


async def _get_school_flag(
    db: AsyncSession, school_id: uuid.UUID, flag_id: uuid.UUID
) -> MasteryFlag:
    flag = (
        await db.execute(
            select(MasteryFlag).where(
                MasteryFlag.id == flag_id, MasteryFlag.school_id == school_id
            )
        )
    ).scalar_one_or_none()
    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")
    return flag


async def _assert_flag_mutation_scope(
    db: AsyncSession, current_user: CurrentUser, flag: MasteryFlag
) -> None:
    scope = await get_staff_scope(db, current_user)
    assert_mastery_flag_review(scope, flag.class_id, flag.subject_id)


@router.get("/flags", response_model=APIResponse[list[FlagOut]])
async def list_flags(
    status: FlagStatus | None = None,
    class_id: uuid.UUID | None = None,
    subject_id: uuid.UUID | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: CurrentUser = Depends(require_roles(*_STAFF)),
    db: AsyncSession = Depends(get_db),
):
    """Weakness flags for review — scoped to teacher's assigned subjects."""
    scope = await get_staff_scope(db, current_user)
    query = (
        select(MasteryFlag, User.full_name, Class.grade, Class.section)
        .join(Student, Student.id == MasteryFlag.student_id)
        .join(User, User.id == Student.user_id)
        .join(Class, Class.id == MasteryFlag.class_id)
        .where(MasteryFlag.school_id == uuid.UUID(current_user.school_id))
        .order_by(MasteryFlag.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    if status:
        query = query.where(MasteryFlag.status == status)
    if class_id:
        query = query.where(MasteryFlag.class_id == class_id)
    if subject_id:
        query = query.where(MasteryFlag.subject_id == subject_id)
    elif scope.teaching_pairs and not scope.is_admin:
        subject_ids = {sid for _, sid in scope.teaching_pairs}
        query = query.where(MasteryFlag.subject_id.in_(subject_ids))
    if class_id and scope.scoped_only and not scope.is_admin:
        if class_id not in scope.teaching_class_ids and class_id not in scope.incharge_class_ids:
            return APIResponse(data=[])

    rows = (await db.execute(query)).all()
    data = [
        _flag_out(flag, student_name=name, class_name=f"{grade} - {section}")
        for flag, name, grade, section in rows
    ]
    return APIResponse(data=data)


@router.post(
    "/flags/{flag_id}/approve",
    response_model=APIResponse[FlagOut],
    dependencies=[rate_limit("ai_generate", **_AI_GEN_RATE)],
)
async def approve_flag(
    flag_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_STAFF)),
    db: AsyncSession = Depends(get_db),
):
    """Teacher approves the flag → the LLM drafts the parent note (editable before send)."""
    school_id = uuid.UUID(current_user.school_id)
    flag = await _get_school_flag(db, school_id, flag_id)
    await _assert_flag_mutation_scope(db, current_user, flag)
    if flag.status != FlagStatus.PENDING_REVIEW:
        raise HTTPException(status_code=409, detail=f"Flag is {flag.status.value}, not pending")

    credits = await enforce_monthly_ai_cap(
        db,
        school_id,
        user_id=uuid.UUID(current_user.id),
        role=current_user.role,
        feature="mastery_flag",
        purpose_tag="mastery_narrative",
    )
    try:
        narrative, model = await draft_narrative(
            db,
            flag,
            created_by=uuid.UUID(current_user.id),
            role=current_user.role,
            credits_charged=credits,
        )
    except Exception as exc:
        raise_http_for_llm_error(
            exc,
            log_event="mastery_narrative_failed",
            timeout_detail="AI generation timed out. Please try again.",
            generic_detail="Could not draft the parent note. Please try again later.",
        )

    flag.status = FlagStatus.APPROVED
    flag.narrative = narrative
    flag.ai_model = model
    flag.reviewed_by = uuid.UUID(current_user.id)
    flag.reviewed_at = datetime.now(timezone.utc)
    await db.flush()
    return APIResponse(data=_flag_out(flag), message="Approved — review the note, then send")


@router.put("/flags/{flag_id}/narrative", response_model=APIResponse[FlagOut])
async def edit_narrative(
    flag_id: uuid.UUID,
    body: NarrativeUpdate,
    current_user: CurrentUser = Depends(require_roles(*_STAFF)),
    db: AsyncSession = Depends(get_db),
):
    flag = await _get_school_flag(db, uuid.UUID(current_user.school_id), flag_id)
    await _assert_flag_mutation_scope(db, current_user, flag)
    if flag.status != FlagStatus.APPROVED:
        raise HTTPException(status_code=409, detail="Narrative is editable only after approval")
    flag.narrative = body.narrative.strip()
    await db.flush()
    return APIResponse(data=_flag_out(flag), message="Note updated")


@router.post("/flags/{flag_id}/dismiss", response_model=APIResponse[FlagOut])
async def dismiss_flag(
    flag_id: uuid.UUID,
    body: DismissRequest,
    current_user: CurrentUser = Depends(require_roles(*_STAFF)),
    db: AsyncSession = Depends(get_db),
):
    flag = await _get_school_flag(db, uuid.UUID(current_user.school_id), flag_id)
    await _assert_flag_mutation_scope(db, current_user, flag)
    if flag.status not in (FlagStatus.PENDING_REVIEW, FlagStatus.APPROVED):
        raise HTTPException(status_code=409, detail=f"Flag is {flag.status.value}")
    flag.status = FlagStatus.DISMISSED
    flag.dismissed_reason = body.reason
    flag.reviewed_by = uuid.UUID(current_user.id)
    flag.reviewed_at = datetime.now(timezone.utc)
    await db.flush()
    return APIResponse(data=_flag_out(flag), message="Dismissed")


@router.post("/flags/{flag_id}/notify", response_model=APIResponse[NotifyResponse])
async def notify_parents(
    flag_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_STAFF)),
    db: AsyncSession = Depends(get_db),
):
    """Send the approved note to the student's linked parent users (in-app).

    No parent portal exists yet — these notifications are latent until it ships;
    the printable digest is the pilot-stage delivery vehicle.
    """
    school_id = uuid.UUID(current_user.school_id)
    flag = await _get_school_flag(db, school_id, flag_id)
    await _assert_flag_mutation_scope(db, current_user, flag)
    if flag.status != FlagStatus.APPROVED or not (flag.narrative or "").strip():
        raise HTTPException(
            status_code=409, detail="Approve the flag and review its note before sending"
        )

    parent_user_ids = [
        row[0]
        for row in (
            await db.execute(
                select(Parent.user_id)
                .join(StudentParentMap, StudentParentMap.parent_id == Parent.id)
                .where(
                    StudentParentMap.student_id == flag.student_id,
                    Parent.school_id == school_id,
                )
            )
        ).all()
    ]

    notifier = NotificationService(db)
    subject_name = (flag.evidence or {}).get("subject_name") or "your child's subject"
    for user_id in parent_user_ids:
        await notifier.send(
            school_id,
            user_id,
            title=f"Learning update: {subject_name} — {flag.topic_display}",
            body=flag.narrative,
            channel=NotificationChannel.IN_APP,
            link=f"/parent/child/{flag.student_id}",
        )

    flag.status = FlagStatus.NOTIFIED
    flag.notified_at = datetime.now(timezone.utc)
    await db.flush()

    message = (
        f"Sent to {len(parent_user_ids)} parent account(s)"
        if parent_user_ids
        else "No parent accounts linked — use the printable digest for the parent meeting"
    )
    return APIResponse(
        data=NotifyResponse(flag=_flag_out(flag), parents_notified=len(parent_user_ids)),
        message=message,
    )


@router.get("/digest", response_model=APIResponse[DigestOut])
async def printable_digest(
    class_id: uuid.UUID | None = None,
    current_user: CurrentUser = Depends(require_roles(*_STAFF)),
    db: AsyncSession = Depends(get_db),
):
    """Approved/notified flags grouped per student — print for parent-teacher meetings."""
    school_id = uuid.UUID(current_user.school_id)
    if class_id:
        await TenantScope(db, school_id).school_class(class_id)

    query = (
        select(MasteryFlag, User.full_name, Class.grade, Class.section)
        .join(Student, Student.id == MasteryFlag.student_id)
        .join(User, User.id == Student.user_id)
        .join(Class, Class.id == MasteryFlag.class_id)
        .where(
            MasteryFlag.school_id == school_id,
            MasteryFlag.status.in_([FlagStatus.APPROVED, FlagStatus.NOTIFIED]),
        )
        .order_by(User.full_name, MasteryFlag.topic)
    )
    if class_id:
        query = query.where(MasteryFlag.class_id == class_id)

    rows = (await db.execute(query)).all()
    by_student: dict[uuid.UUID, DigestEntryOut] = {}
    for flag, name, grade, section in rows:
        entry = by_student.get(flag.student_id)
        if not entry:
            entry = DigestEntryOut(student_id=flag.student_id, student_name=name or "—", flags=[])
            by_student[flag.student_id] = entry
        entry.flags.append(_flag_out(flag, student_name=name, class_name=f"{grade} - {section}"))

    digest = DigestOut(
        class_id=class_id, generated_on=date.today(), students=list(by_student.values())
    )
    return APIResponse(data=digest)

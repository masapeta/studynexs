"""Parent Intervention — identify at-risk students, draft 1:1 parent messages, and (only after an
authenticated human approval) create IN_APP notifications.

Two clearly separated responsibilities:
  * WORKFLOW  — cohort identification + 1:1 draft preparation (no send).
  * ACTION    — `approve_and_notify`: server-side re-validation, idempotency, audit, and IN_APP
                delivery via the EXISTING NotificationService. This is the first governed
                state-changing action consumer.

Nothing is sent during identification, drafting, or planning. Delivery happens ONLY inside the
action, after an authenticated user approves. A model can never approve or send. Strictly 1:1 —
one notification per (parent, student); never a bulk message.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

import structlog
from sqlalchemy import case, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.db.models.attendance import Attendance
from app.db.models.audit import AuditLog
from app.db.models.notification import NotificationChannel
from app.db.models.parent_intervention import (
    INTERVENTION_STATUS_DRAFT,
    INTERVENTION_STATUS_FAILED,
    INTERVENTION_STATUS_NOTIFIED,
    ParentInterventionBatch,
    ParentInterventionDraft,
)
from app.db.models.student import Parent, Student, StudentParentMap
from app.db.models.user import User

logger = structlog.get_logger()

REASON_LOW_ATTENDANCE = "low_attendance"
_DEFAULT_ATTENDANCE_THRESHOLD = 75.0
_MAX_COHORT = 40  # bound the batch; never an unbounded blast radius


class InterventionError(Exception):
    """Recoverable failure carrying a safe, user-facing message."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


@dataclass
class _Target:
    student_id: uuid.UUID
    student_name: str
    admission_no: str
    parent_user_id: uuid.UUID
    parent_name: str
    attendance_pct: float


class ParentInterventionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── WORKFLOW: identify + draft (no send) ──────────────────────────────────

    async def create_batch(
        self,
        *,
        school_id: uuid.UUID,
        created_by: uuid.UUID,
        threshold: float = _DEFAULT_ATTENDANCE_THRESHOLD,
    ) -> tuple[ParentInterventionBatch, list[ParentInterventionDraft]]:
        """Identify students below the attendance threshold, resolve their linked parents, and
        persist one 1:1 DRAFT per (student, parent). Sends nothing."""
        targets = await self._low_attendance_targets(school_id, threshold)
        if not targets:
            raise InterventionError(
                f"No students are below {threshold:.0f}% attendance — nothing to intervene on."
            )

        batch = ParentInterventionBatch(
            school_id=school_id, created_by=created_by, reason=REASON_LOW_ATTENDANCE
        )
        self.db.add(batch)
        await self.db.flush()

        drafts: list[ParentInterventionDraft] = []
        for t in targets:
            draft = ParentInterventionDraft(
                school_id=school_id,
                batch_id=batch.id,
                student_id=t.student_id,
                parent_user_id=t.parent_user_id,
                reason=REASON_LOW_ATTENDANCE,
                message=self._draft_message(t),
                status=INTERVENTION_STATUS_DRAFT,
            )
            self.db.add(draft)
            drafts.append(draft)
        await self.db.flush()
        return batch, drafts

    async def _low_attendance_targets(
        self, school_id: uuid.UUID, threshold: float
    ) -> list[_Target]:
        """Students below the threshold, each expanded to their linked parent recipients (1:1)."""
        weight = case(
            (Attendance.status == "half_day", 0.5),
            (Attendance.status == "absent", 0.0),
            else_=1.0,
        )
        att = (
            select(
                Attendance.student_id.label("sid"),
                func.count().label("n"),
                func.sum(weight).label("present"),
            )
            .where(Attendance.school_id == school_id)
            .group_by(Attendance.student_id)
        ).subquery()

        # student + parent-user join; only parents that have a linked user account are targetable.
        rows = (
            await self.db.execute(
                select(
                    Student.id,
                    Student.admission_no,
                    User.full_name.label("student_name"),
                    Parent.user_id,
                    att.c.n,
                    att.c.present,
                )
                .join(User, User.id == Student.user_id)
                .join(StudentParentMap, StudentParentMap.student_id == Student.id)
                .join(Parent, Parent.id == StudentParentMap.parent_id)
                .join(att, att.c.sid == Student.id)
                .where(
                    Student.school_id == school_id,
                    StudentParentMap.school_id == school_id,
                    Parent.school_id == school_id,
                )
            )
        ).all()

        parent_names = await self._parent_names(school_id, [r[3] for r in rows])

        targets: list[_Target] = []
        for sid, adm, sname, parent_uid, n, present in rows:
            if not n:
                continue
            pct = round(float(present) / n * 100, 1)
            if pct >= threshold:
                continue
            targets.append(
                _Target(
                    student_id=sid,
                    student_name=sname,
                    admission_no=adm,
                    parent_user_id=parent_uid,
                    parent_name=parent_names.get(parent_uid, "Parent"),
                    attendance_pct=pct,
                )
            )
        targets.sort(key=lambda t: t.attendance_pct)
        return targets[:_MAX_COHORT]

    async def _parent_names(
        self, school_id: uuid.UUID, user_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, str]:
        ids = [u for u in set(user_ids) if u]
        if not ids:
            return {}
        rows = (
            await self.db.execute(
                select(User.id, User.full_name).where(
                    User.id.in_(ids), User.school_id == school_id
                )
            )
        ).all()
        return {uid: name for uid, name in rows}

    def _draft_message(self, t: _Target) -> str:
        """Deterministic, factual 1:1 message using only the intervention signal — no unsupported
        claims, no unnecessary student data."""
        return (
            f"Dear {t.parent_name}, this is a note from school regarding {t.student_name}'s "
            f"attendance, which is currently {t.attendance_pct:.0f}%. We'd value your support in "
            "helping improve regular attendance. Please reach out to the class teacher with any "
            "questions."
        )

    # ── ACTION: approve + notify (governed, idempotent, audited) ──────────────

    async def approve_and_notify(
        self, current_user: CurrentUser, *, draft_id: uuid.UUID
    ) -> ParentInterventionDraft:
        """The governed state-changing action. Re-validates tenant/authz/recipient at approval
        time, is idempotent on repeat/retry, creates ONE IN_APP notification, and writes an audit
        row. Authorization is enforced here — the workflow selecting the draft grants nothing."""
        from app.core.authorization import assert_can_access_student
        from app.modules.notifications.services.notification_service import NotificationService

        school_id = uuid.UUID(current_user.school_id)

        # Row-lock the draft for the tenant so concurrent approvals serialize (idempotency).
        draft = (
            await self.db.execute(
                select(ParentInterventionDraft)
                .where(
                    ParentInterventionDraft.id == draft_id,
                    ParentInterventionDraft.school_id == school_id,
                )
                .with_for_update()
            )
        ).scalar_one_or_none()
        if draft is None:
            raise InterventionError("Intervention draft not found.")

        # Idempotent: already delivered -> return as-is, create nothing new.
        if draft.status == INTERVENTION_STATUS_NOTIFIED and draft.notification_id:
            return draft

        # Re-validate authorization on the target student AT APPROVAL TIME (not at draft time).
        await assert_can_access_student(current_user, self.db, draft.student_id)

        # Re-validate the recipient is still a linked parent with a user account in this tenant.
        recipient = (
            await self.db.execute(
                select(Parent.user_id)
                .join(StudentParentMap, StudentParentMap.parent_id == Parent.id)
                .where(
                    Parent.user_id == draft.parent_user_id,
                    Parent.school_id == school_id,
                    StudentParentMap.student_id == draft.student_id,
                    StudentParentMap.school_id == school_id,
                )
                .limit(1)
            )
        ).scalar_one_or_none()
        if recipient is None:
            draft.status = INTERVENTION_STATUS_FAILED
            draft.error_message = "Recipient is no longer a linked parent for this student."
            await self.db.flush()
            raise InterventionError(draft.error_message)

        if not draft.message or not draft.message.strip():
            raise InterventionError("Draft message is empty.")

        # Deliver via the EXISTING notification service — IN_APP only.
        try:
            notif = await NotificationService(self.db).send(
                school_id,
                draft.parent_user_id,
                title="A note about your child",
                body=draft.message,
                channel=NotificationChannel.IN_APP,
            )
        except Exception as exc:  # noqa: BLE001 — record honest failure, never silent COMPLETED
            draft.status = INTERVENTION_STATUS_FAILED
            draft.error_message = "Notification delivery failed."
            await self.db.flush()
            logger.warning("intervention_notify_failed", draft_id=str(draft_id), error=str(exc))
            raise InterventionError("Could not deliver the notification. Please try again.")

        draft.status = INTERVENTION_STATUS_NOTIFIED
        draft.notification_id = notif.id
        draft.approved_by = uuid.UUID(current_user.id)
        draft.approved_at = func.now()

        # Explicit domain audit row (reuses the existing AuditLog model — no second audit system).
        self.db.add(
            AuditLog(
                school_id=school_id,
                user_id=uuid.UUID(current_user.id),
                action="workflow.parent_intervention.notify",
                resource_type="parent_intervention_draft",
                resource_id=str(draft.id),
                details={
                    "batch_id": str(draft.batch_id),
                    "student_id": str(draft.student_id),
                    "parent_user_id": str(draft.parent_user_id),
                    "notification_id": str(notif.id),
                    "reason": draft.reason,
                    "result": "notified",
                },
            )
        )
        try:
            await self.db.flush()
        except IntegrityError as exc:
            raise InterventionError("This intervention was already processed.") from exc
        return draft

    async def get_batch_drafts(
        self, school_id: uuid.UUID, batch_id: uuid.UUID
    ) -> list[ParentInterventionDraft]:
        rows = (
            await self.db.execute(
                select(ParentInterventionDraft).where(
                    ParentInterventionDraft.batch_id == batch_id,
                    ParentInterventionDraft.school_id == school_id,
                )
            )
        ).scalars().all()
        return list(rows)

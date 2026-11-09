"""Governed exam-result release (plan Rev 2 §3.3–§3.6, safeguards 1, 4, 6, 7).

Visibility rule (single source of truth for every learner path):
    a student sees an exam result  ⇔  an ``exam_result_published`` pointer exists
                                       AND ``exam_release_state.status == 'released'``.

Transitions run inside one transaction holding ``SELECT … FOR UPDATE`` on the exam's
``exam_release_state`` row, so concurrent previews/confirms/withdrawals serialise.

Preview tokens (safeguard 4) are HMAC-SHA256 signed and bind: tenant, exam, actor, the
eligible-set fingerprint, an action token and an expiry. Confirm re-verifies the signature
(constant time), re-authorises the actor, recomputes the fingerprint (409 on drift) and
uses the action token as the database-unique replay key (a replay returns the generation the
token already created; it never creates a second one).
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.staff_permissions import StaffScope
from app.db.models.answer_sheet_evaluation import (
    EVAL_STATUS_APPROVED,
    EVAL_STATUS_FAILED,
    EVAL_STATUS_PENDING,
    EVAL_STATUS_PROCESSING,
    EVAL_STATUS_SUGGESTED,
    AnswerSheetEvaluation,
)
from app.db.models.audit import AuditLog
from app.db.models.exam_result import (
    RELEASE_ACTION_BLOCK,
    RELEASE_ACTION_RELEASE,
    RELEASE_ACTION_UNBLOCK,
    RELEASE_ACTION_WITHDRAW,
    RELEASE_STATUS_BLOCKED,
    RELEASE_STATUS_NOT_RELEASED,
    RELEASE_STATUS_RELEASED,
    RELEASE_STATUS_WITHDRAWN,
    ExamReleaseState,
    ExamResultNotification,
    ExamResultPublished,
    ExamResultRelease,
    ExamResultReleaseItem,
    ExamResultVersion,
)
from app.db.models.examination import Exam
from app.db.models.notification import Notification, NotificationChannel
from app.db.models.student import Parent, Student, StudentParentMap, StudentStatus
from app.modules.examinations.services.result_version_service import (
    ensure_historical_baselines,
    latest_versions,
)

settings = get_settings()

PREVIEW_TTL_SECONDS = 15 * 60
_BLOCKED_MSG = "Results for this exam are blocked by the principal."
PENDING_CATEGORIES = (
    "not_submitted",
    "processing",
    "ai_suggested_awaiting_review",
    "needs_manual_review",
    "failed",
    "absent_or_no_mark",
    "reopened_under_review",
)


class ReleaseError(Exception):
    """Release operation rejected. ``status_code`` maps to the HTTP response."""

    def __init__(self, status_code: int, code: str, message: str, extra: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.extra = extra or {}


@dataclass
class EligibleSet:
    versions: dict[uuid.UUID, ExamResultVersion]
    pending: dict[str, int]
    fingerprint: str

    @property
    def pending_total(self) -> int:
        return sum(self.pending.values())


@dataclass
class ConfirmOutcome:
    release: ExamResultRelease | None
    no_changes: bool = False
    replayed: bool = False
    published_student_ids: list[uuid.UUID] = field(default_factory=list)


# ── Preview token (safeguard 4) ─────────────────────────────────────────────────


def _token_key() -> bytes:
    return hmac.new(
        settings.JWT_SECRET_KEY.encode("utf-8"),
        b"studynexs:exam-result-release-preview:v1",
        hashlib.sha256,
    ).digest()


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def issue_preview_token(
    *,
    school_id: uuid.UUID,
    exam_id: uuid.UUID,
    actor_id: uuid.UUID,
    fingerprint: str,
    action_token: uuid.UUID,
    now: float | None = None,
) -> str:
    payload = {
        "v": 1,
        "sid": str(school_id),
        "eid": str(exam_id),
        "uid": str(actor_id),
        "fp": fingerprint,
        "tok": str(action_token),
        "exp": int((now or time.time()) + PREVIEW_TTL_SECONDS),
    }
    body = _b64(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
    mac = _b64(hmac.new(_token_key(), body.encode(), hashlib.sha256).digest())
    return f"{body}.{mac}"


def verify_preview_token(
    token: str,
    *,
    school_id: uuid.UUID,
    exam_id: uuid.UUID,
    actor_id: uuid.UUID,
    now: float | None = None,
) -> dict:
    try:
        body, mac = token.split(".", 1)
        expected = _b64(hmac.new(_token_key(), body.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(mac, expected):
            raise ValueError("bad signature")
        payload = json.loads(_unb64(body))
    except Exception as exc:  # noqa: BLE001 — any malformed token is the same rejection
        raise ReleaseError(400, "invalid_preview", "This release preview is not valid.") from exc
    if payload.get("v") != 1:
        raise ReleaseError(400, "invalid_preview", "This release preview is not valid.")
    if payload.get("sid") != str(school_id) or payload.get("eid") != str(exam_id):
        raise ReleaseError(400, "invalid_preview", "This release preview is not valid.")
    if payload.get("uid") != str(actor_id):
        raise ReleaseError(
            403, "preview_not_yours", "This release preview was created by another user."
        )
    if int(payload.get("exp", 0)) < int(now or time.time()):
        raise ReleaseError(
            409, "preview_expired", "This release preview has expired. Preview again."
        )
    return payload


# ── Service ─────────────────────────────────────────────────────────────────────


class ResultReleaseService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _lock_state(self, school_id: uuid.UUID, exam_id: uuid.UUID) -> ExamReleaseState:
        await self.db.execute(
            pg_insert(ExamReleaseState)
            .values(
                id=uuid.uuid4(),
                school_id=school_id,
                exam_id=exam_id,
                status=RELEASE_STATUS_NOT_RELEASED,
                current_generation_no=0,
                last_event_no=0,
            )
            .on_conflict_do_nothing(constraint="uq_release_state_exam")
        )
        state = (
            await self.db.execute(
                select(ExamReleaseState)
                .where(
                    ExamReleaseState.school_id == school_id,
                    ExamReleaseState.exam_id == exam_id,
                )
                .with_for_update()
                .execution_options(populate_existing=True)
            )
        ).scalar_one()
        return state

    async def _state(self, school_id: uuid.UUID, exam_id: uuid.UUID) -> ExamReleaseState | None:
        return (
            await self.db.execute(
                select(ExamReleaseState).where(
                    ExamReleaseState.school_id == school_id,
                    ExamReleaseState.exam_id == exam_id,
                )
            )
        ).scalar_one_or_none()

    async def _published(
        self, school_id: uuid.UUID, exam_id: uuid.UUID
    ) -> dict[uuid.UUID, ExamResultPublished]:
        rows = (
            await self.db.execute(
                select(ExamResultPublished).where(
                    ExamResultPublished.school_id == school_id,
                    ExamResultPublished.exam_id == exam_id,
                )
            )
        ).scalars().all()
        return {p.student_id: p for p in rows}

    async def compute_eligible(
        self, school_id: uuid.UUID, exam: Exam, status: str
    ) -> EligibleSet:
        """Eligible = latest approved version per student, excluding sheets under re-review."""
        versions = await latest_versions(self.db, school_id, exam.id)
        evals = {
            e.student_id: e
            for e in (
                await self.db.execute(
                    select(AnswerSheetEvaluation).where(
                        AnswerSheetEvaluation.school_id == school_id,
                        AnswerSheetEvaluation.exam_id == exam.id,
                    )
                )
            ).scalars().all()
        }
        roster = list(
            (
                await self.db.execute(
                    select(Student.id).where(
                        Student.school_id == school_id,
                        Student.class_id == exam.class_id,
                        Student.status == StudentStatus.ACTIVE,
                    )
                )
            ).scalars().all()
        )
        pending = {c: 0 for c in PENDING_CATEGORIES}
        eligible: dict[uuid.UUID, ExamResultVersion] = {}
        for sid in set(roster) | set(versions):
            ev = evals.get(sid)
            version = versions.get(sid)
            under_review = ev is not None and ev.status != EVAL_STATUS_APPROVED
            if version is not None and not under_review:
                eligible[sid] = version
                continue
            if version is not None and under_review:
                pending["reopened_under_review"] += 1
            elif ev is None:
                pending["not_submitted" if exam.source_paper_id else "absent_or_no_mark"] += 1
            elif ev.status in (EVAL_STATUS_PROCESSING, EVAL_STATUS_PENDING):
                pending["processing"] += 1
            elif ev.status == EVAL_STATUS_FAILED:
                pending["failed"] += 1
            elif ev.status == EVAL_STATUS_SUGGESTED:
                needs_review = any(
                    isinstance(s, dict) and s.get("manual_review_required")
                    for s in (ev.ai_suggestions or {}).values()
                )
                pending[
                    "needs_manual_review" if needs_review else "ai_suggested_awaiting_review"
                ] += 1
            else:
                pending["absent_or_no_mark"] += 1
        material = {
            "status": status,
            "eligible": sorted(f"{sid}:{v.id}" for sid, v in eligible.items()),
            "pending": pending,
        }
        fingerprint = hashlib.sha256(
            json.dumps(material, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        return EligibleSet(versions=eligible, pending=pending, fingerprint=fingerprint)

    def _changes(
        self, eligible: EligibleSet, published: dict[uuid.UUID, ExamResultPublished], status: str
    ) -> dict[uuid.UUID, ExamResultVersion]:
        if status != RELEASE_STATUS_RELEASED:
            return dict(eligible.versions)
        return {
            sid: v
            for sid, v in eligible.versions.items()
            if sid not in published or published[sid].result_version_id != v.id
        }

    # ── Read ────────────────────────────────────────────────────────────────────

    async def get_state(self, school_id: uuid.UUID, exam: Exam) -> dict:
        state = await self._state(school_id, exam.id)
        status = state.status if state else RELEASE_STATUS_NOT_RELEASED
        published = await self._published(school_id, exam.id)
        eligible = await self.compute_eligible(school_id, exam, status)
        changes = self._changes(eligible, published, RELEASE_STATUS_RELEASED)
        history = (
            await self.db.execute(
                select(ExamResultRelease)
                .where(
                    ExamResultRelease.school_id == school_id,
                    ExamResultRelease.exam_id == exam.id,
                )
                .order_by(ExamResultRelease.event_no.desc())
                .limit(50)
            )
        ).scalars().all()
        return {
            "status": status,
            "current_generation_no": state.current_generation_no if state else 0,
            "published_count": len(published) if status == RELEASE_STATUS_RELEASED else 0,
            "unpublished_changes_count": len(changes),
            "pending": eligible.pending,
            "blocked_reason": state.blocked_reason if state else None,
            "history": list(history),
        }

    # ── Preview ─────────────────────────────────────────────────────────────────

    async def preview(
        self, *, school_id: uuid.UUID, exam: Exam, scope: StaffScope
    ) -> dict:
        if not scope.can_release_results(exam):
            raise ReleaseError(403, "forbidden", "You can't release results for this class.")
        state = await self._lock_state(school_id, exam.id)
        if state.status == RELEASE_STATUS_BLOCKED:
            raise ReleaseError(409, "blocked", _BLOCKED_MSG)
        await ensure_historical_baselines(self.db, school_id=school_id, exam_id=exam.id)
        eligible = await self.compute_eligible(school_id, exam, state.status)
        published = await self._published(school_id, exam.id)
        changes = self._changes(eligible, published, state.status)
        action_token = uuid.uuid4()
        token = issue_preview_token(
            school_id=school_id,
            exam_id=exam.id,
            actor_id=scope.user_id,
            fingerprint=eligible.fingerprint,
            action_token=action_token,
        )
        self.db.add(
            AuditLog(
                school_id=school_id,
                user_id=scope.user_id,
                action="result.release_previewed",
                resource_type="exam_result",
                resource_id=str(exam.id),
                details={
                    "eligible_count": len(eligible.versions),
                    "changes_count": len(changes),
                    "pending": eligible.pending,
                },
            )
        )
        await self.db.flush()
        return {
            "preview_token": token,
            "action_token": action_token,
            "preview_fingerprint": eligible.fingerprint,
            "expected_generation_no": state.current_generation_no + 1,
            "status": state.status,
            "eligible_count": len(eligible.versions),
            "changes_count": len(changes),
            "pending": eligible.pending,
            "pending_total": eligible.pending_total,
            "expires_in_seconds": PREVIEW_TTL_SECONDS,
        }

    # ── Confirm ─────────────────────────────────────────────────────────────────

    async def _existing_event(
        self, school_id: uuid.UUID, action_token: uuid.UUID
    ) -> ExamResultRelease | None:
        return (
            await self.db.execute(
                select(ExamResultRelease).where(
                    ExamResultRelease.school_id == school_id,
                    ExamResultRelease.action_token == action_token,
                )
            )
        ).scalar_one_or_none()

    async def confirm(
        self,
        *,
        school_id: uuid.UUID,
        exam: Exam,
        scope: StaffScope,
        preview_token: str,
        confirm_partial: bool = False,
        acknowledged_pending_count: int | None = None,
    ) -> ConfirmOutcome:
        payload = verify_preview_token(
            preview_token, school_id=school_id, exam_id=exam.id, actor_id=scope.user_id
        )
        action_token = uuid.UUID(payload["tok"])
        # Re-authorise at execution time (never trust the preview).
        if not scope.can_release_results(exam):
            raise ReleaseError(403, "forbidden", "You can't release results for this class.")

        state = await self._lock_state(school_id, exam.id)
        prior = await self._existing_event(school_id, action_token)
        if prior is not None:
            if prior.exam_id != exam.id:
                raise ReleaseError(400, "invalid_preview", "This release preview is not valid.")
            return ConfirmOutcome(release=prior, replayed=True)
        if state.status == RELEASE_STATUS_BLOCKED:
            raise ReleaseError(409, "blocked", _BLOCKED_MSG)

        await ensure_historical_baselines(self.db, school_id=school_id, exam_id=exam.id)
        eligible = await self.compute_eligible(school_id, exam, state.status)
        if not hmac.compare_digest(eligible.fingerprint, payload["fp"]):
            raise ReleaseError(
                409,
                "stale_preview",
                "Results changed since your preview. Review the new counts and preview again.",
                {"pending": eligible.pending, "eligible_count": len(eligible.versions)},
            )
        published = await self._published(school_id, exam.id)
        changes = self._changes(eligible, published, state.status)
        if not changes:
            # Nothing new to publish: no generation, no transition, no notification.
            return ConfirmOutcome(release=None, no_changes=True)
        if eligible.pending_total:
            if not confirm_partial:
                raise ReleaseError(
                    400,
                    "partial_not_confirmed",
                    f"{eligible.pending_total} student(s) are still pending. Confirm a partial "
                    "release to continue.",
                    {"pending": eligible.pending},
                )
            if acknowledged_pending_count != eligible.pending_total:
                raise ReleaseError(
                    400,
                    "pending_count_mismatch",
                    "The acknowledged pending count does not match. Preview again.",
                    {"pending_total": eligible.pending_total},
                )

        prior_status = state.status
        release = ExamResultRelease(
            school_id=school_id,
            exam_id=exam.id,
            event_no=state.last_event_no + 1,
            generation_no=state.current_generation_no + 1,
            action=RELEASE_ACTION_RELEASE,
            actor_id=scope.user_id,
            actor_role=scope.role,
            action_token=action_token,
            preview_fingerprint=eligible.fingerprint,
            published_count=len(changes),
            pending_counts=eligible.pending,
            partial=bool(eligible.pending_total),
            prior_status=prior_status,
            resulting_status=RELEASE_STATUS_RELEASED,
        )
        try:
            async with self.db.begin_nested():
                self.db.add(release)
                await self.db.flush()
        except IntegrityError:
            existing = await self._existing_event(school_id, action_token)
            if existing is not None:
                return ConfirmOutcome(release=existing, replayed=True)
            raise

        for sid, version in changes.items():
            self.db.add(
                ExamResultReleaseItem(
                    school_id=school_id,
                    exam_id=exam.id,
                    release_id=release.id,
                    student_id=sid,
                    result_version_id=version.id,
                )
            )
        await self.db.flush()
        now = datetime.now(timezone.utc)
        rows = [
            {
                "id": uuid.uuid4(),
                "school_id": school_id,
                "exam_id": exam.id,
                "student_id": sid,
                "result_version_id": v.id,
                "release_id": release.id,
                "published_at": now,
            }
            for sid, v in changes.items()
        ]
        stmt = pg_insert(ExamResultPublished).values(rows)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_published_exam_student",
            set_={
                "result_version_id": stmt.excluded.result_version_id,
                "release_id": stmt.excluded.release_id,
                "published_at": stmt.excluded.published_at,
                "updated_at": func.now(),
            },
        )
        await self.db.execute(stmt)

        state.status = RELEASE_STATUS_RELEASED
        state.current_generation_no = release.generation_no
        state.last_event_no = release.event_no
        self.db.add(
            AuditLog(
                school_id=school_id,
                user_id=scope.user_id,
                action="result.released",
                resource_type="exam_result",
                resource_id=str(exam.id),
                details={
                    "generation_no": release.generation_no,
                    "published_count": len(changes),
                    "pending": eligible.pending,
                    "partial": bool(eligible.pending_total),
                    "prior_status": prior_status,
                    "override": scope.role == "super_admin"
                    and exam.class_id not in scope.incharge_class_ids,
                },
            )
        )
        await self.db.flush()
        await self._notify(school_id=school_id, exam=exam, release=release, changes=changes)
        await self._emit_recompute(school_id, exam, release.actor_id)
        return ConfirmOutcome(release=release, published_student_ids=list(changes))

    async def _notify(
        self,
        *,
        school_id: uuid.UUID,
        exam: Exam,
        release: ExamResultRelease,
        changes: dict[uuid.UUID, ExamResultVersion],
    ) -> int:
        """P-R7: notify the student and linked parents once per (generation, student, recipient).

        The payload never carries marks (PII minimisation); details are fetched in-app.
        """
        student_ids = list(changes)
        students = {
            s.id: s.user_id
            for s in (
                await self.db.execute(
                    select(Student).where(
                        Student.school_id == school_id, Student.id.in_(student_ids)
                    )
                )
            ).scalars().all()
        }
        parent_rows = (
            await self.db.execute(
                select(StudentParentMap.student_id, Parent.user_id)
                .join(Parent, Parent.id == StudentParentMap.parent_id)
                .where(
                    StudentParentMap.school_id == school_id,
                    Parent.school_id == school_id,
                    StudentParentMap.student_id.in_(student_ids),
                )
            )
        ).all()
        recipients: list[tuple[uuid.UUID, uuid.UUID, str]] = []
        for sid in student_ids:
            if students.get(sid):
                recipients.append((sid, students[sid], f"/student/results/{exam.id}"))
        for sid, parent_user_id in parent_rows:
            recipients.append(
                (sid, parent_user_id, f"/parent/child/{sid}/results/{exam.id}")
            )
        updated = (release.generation_no or 1) > 1
        title = (
            f"Updated results: {exam.title}" if updated else f"Results released: {exam.title}"
        )
        sent = 0
        for sid, user_id, link in recipients:
            inserted = await self.db.scalar(
                pg_insert(ExamResultNotification)
                .values(
                    id=uuid.uuid4(),
                    school_id=school_id,
                    release_id=release.id,
                    student_id=sid,
                    result_version_id=changes[sid].id,
                    recipient_user_id=user_id,
                )
                .on_conflict_do_nothing(constraint="uq_result_notification")
                .returning(ExamResultNotification.id)
            )
            if inserted is None:
                continue
            notification = Notification(
                school_id=school_id,
                user_id=user_id,
                title=title,
                body="Open StudyNexs to see the results your teacher released.",
                channel=NotificationChannel.IN_APP,
                link=link,
            )
            self.db.add(notification)
            await self.db.flush()
            row = await self.db.get(ExamResultNotification, inserted)
            row.notification_id = notification.id
            sent += 1
        await self.db.flush()
        return sent

    async def _emit_recompute(
        self, school_id: uuid.UUID, exam: Exam, actor_id: uuid.UUID
    ) -> None:
        from app.workers.outbox_helper import emit_event

        await emit_event(
            self.db,
            "exam_results_published",
            {
                "school_id": str(school_id),
                "exam_id": str(exam.id),
                "class_id": str(exam.class_id),
                "subject_id": str(exam.subject_id),
                "actor_id": str(actor_id),
            },
            target_module="mastery",
        )

    # ── Withdraw / block / unblock ──────────────────────────────────────────────

    async def _governed_event(
        self,
        *,
        school_id: uuid.UUID,
        exam: Exam,
        scope: StaffScope,
        action: str,
        reason: str,
        action_token: uuid.UUID,
    ) -> tuple[ExamResultRelease, bool]:
        reason = (reason or "").strip()
        if not reason:
            raise ReleaseError(400, "reason_required", "A reason is required.")
        allowed = {
            RELEASE_ACTION_WITHDRAW: scope.can_withdraw_results(exam),
            RELEASE_ACTION_BLOCK: scope.can_override_release(exam),
            RELEASE_ACTION_UNBLOCK: scope.can_override_release(exam),
        }[action]
        if not allowed:
            raise ReleaseError(403, "forbidden", "You don't have authority for this action.")

        state = await self._lock_state(school_id, exam.id)
        prior = await self._existing_event(school_id, action_token)
        if prior is not None:
            if prior.exam_id != exam.id or prior.action != action:
                raise ReleaseError(400, "invalid_action_token", "This action token is not valid.")
            return prior, False

        prior_status = state.status
        clear_pointers = False
        if action == RELEASE_ACTION_WITHDRAW:
            if state.status == RELEASE_STATUS_RELEASED:
                state.status = RELEASE_STATUS_WITHDRAWN
                clear_pointers = True
            elif (
                state.status == RELEASE_STATUS_BLOCKED
                and state.status_before_block == RELEASE_STATUS_RELEASED
            ):
                # Withdraw underneath a block: the block stays; unblock restores 'withdrawn'.
                state.status_before_block = RELEASE_STATUS_WITHDRAWN
                clear_pointers = True
            else:
                raise ReleaseError(409, "not_released", "These results are not released.")
        elif action == RELEASE_ACTION_BLOCK:
            if state.status == RELEASE_STATUS_BLOCKED:
                raise ReleaseError(409, "already_blocked", "These results are already blocked.")
            # Safeguard 6: remember the exact prior condition; pointers stay but are hidden,
            # because visibility also requires status == 'released'.
            state.status_before_block = state.status
            state.status = RELEASE_STATUS_BLOCKED
            state.blocked_by = scope.user_id
            state.blocked_reason = reason
        else:
            if state.status != RELEASE_STATUS_BLOCKED:
                raise ReleaseError(409, "not_blocked", "These results are not blocked.")
            # Restore exactly the prior condition. Published pointers only ever reference
            # versions a release generation published, so nothing unpublished or withdrawn
            # becomes visible.
            state.status = state.status_before_block or RELEASE_STATUS_NOT_RELEASED
            state.status_before_block = None
            state.blocked_by = None
            state.blocked_reason = None

        event = ExamResultRelease(
            school_id=school_id,
            exam_id=exam.id,
            event_no=state.last_event_no + 1,
            generation_no=None,
            action=action,
            actor_id=scope.user_id,
            actor_role=scope.role,
            reason=reason,
            action_token=action_token,
            prior_status=prior_status,
            resulting_status=state.status,
        )
        try:
            async with self.db.begin_nested():
                self.db.add(event)
                await self.db.flush()
        except IntegrityError:
            existing = await self._existing_event(school_id, action_token)
            if existing is not None:
                return existing, False
            raise
        state.last_event_no = event.event_no
        if clear_pointers:
            await self.db.execute(
                delete(ExamResultPublished).where(
                    ExamResultPublished.school_id == school_id,
                    ExamResultPublished.exam_id == exam.id,
                )
            )
        self.db.add(
            AuditLog(
                school_id=school_id,
                user_id=scope.user_id,
                action={
                    RELEASE_ACTION_WITHDRAW: "result.withdrawn",
                    RELEASE_ACTION_BLOCK: "result.blocked",
                    RELEASE_ACTION_UNBLOCK: "result.unblocked",
                }[action],
                resource_type="exam_result",
                resource_id=str(exam.id),
                details={
                    "reason": reason,
                    "prior_status": prior_status,
                    "resulting_status": state.status,
                },
            )
        )
        await self.db.flush()
        await self._emit_recompute(school_id, exam, scope.user_id)
        return event, True

    async def withdraw(self, **kwargs) -> tuple[ExamResultRelease, bool]:
        return await self._governed_event(action=RELEASE_ACTION_WITHDRAW, **kwargs)

    async def block(self, **kwargs) -> tuple[ExamResultRelease, bool]:
        return await self._governed_event(action=RELEASE_ACTION_BLOCK, **kwargs)

    async def unblock(self, **kwargs) -> tuple[ExamResultRelease, bool]:
        return await self._governed_event(action=RELEASE_ACTION_UNBLOCK, **kwargs)


# ── Learner visibility (the only sanctioned learner read path) ────────────────


def visible_versions_query(school_id: uuid.UUID):
    """Published versions currently visible to learners (pointer AND status == released)."""
    return (
        select(ExamResultVersion, ExamResultPublished, Exam)
        .join(
            ExamResultPublished,
            (ExamResultPublished.result_version_id == ExamResultVersion.id)
            & (ExamResultPublished.school_id == ExamResultVersion.school_id),
        )
        .join(
            ExamReleaseState,
            (ExamReleaseState.exam_id == ExamResultPublished.exam_id)
            & (ExamReleaseState.school_id == ExamResultPublished.school_id),
        )
        .join(Exam, (Exam.id == ExamResultVersion.exam_id) & (Exam.school_id == school_id))
        .where(
            ExamResultVersion.school_id == school_id,
            ExamReleaseState.status == RELEASE_STATUS_RELEASED,
        )
    )

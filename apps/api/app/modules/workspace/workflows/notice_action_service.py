"""Publish Notice — the second governed assistant ACTION (after parent-intervention notify).

Two phases, cleanly separated:
  * PREVIEW  — validate the interpreted notice, resolve/authorize the audience, and mint a
               server-issued `action_token`. Creates NO notice. Ephemeral (nothing persisted
               except the token is only realised on confirm).
  * CONFIRM  — the state change. Re-authorizes at execution time, re-validates, is idempotent via
               the GovernedActionExecution ledger (a retried token returns the same notice; a
               fresh preview mints a new token and may legitimately republish identical content),
               calls the EXISTING NoticeService.create_notice, and writes an audit row.

A model can never publish: it only prepares the preview. Only an authenticated user hitting the
confirm endpoint with the token executes. NoticeService is reused unchanged.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

import structlog
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.db.models.audit import AuditLog
from app.db.models.communication import Notice, NoticeAudience, NoticePriority
from app.db.models.governed_action import (
    ACTION_STATUS_COMPLETED,
    GovernedActionExecution,
)
from app.modules.communications.schemas.notice import NoticeCreate

logger = structlog.get_logger()

ACTION_PUBLISH_NOTICE = "publish_notice"


class NoticeActionError(Exception):
    """Recoverable failure carrying a safe, user-facing message."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


@dataclass
class NoticePreview:
    action_token: uuid.UUID
    title: str
    content: str
    audience: str
    target_roles: list[str]
    priority: str
    class_id: uuid.UUID | None


class NoticeActionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── PREVIEW: validate + authorize + mint token (no notice created) ────────

    async def preview(
        self,
        current_user: CurrentUser,
        *,
        title: str,
        content: str,
        audience: str,
        class_label: str | None = None,
    ) -> NoticePreview:
        """Build a confirm-ready preview. Validates + authorizes but creates nothing."""
        from app.core.staff_permissions import assert_notice_publish, get_staff_scope
        from app.modules.workspace.assistant.resolver import resolve_class

        school_id = uuid.UUID(current_user.school_id)
        audience_norm = (audience or "").strip().lower()
        if audience_norm not in (NoticeAudience.INTERNAL.value, NoticeAudience.EXTERNAL.value):
            raise NoticeActionError(
                "Say whether this is a staff notice (internal) or a parent/student notice."
            )
        if not (title or "").strip() or not (content or "").strip():
            raise NoticeActionError("A notice needs both a title and content.")

        class_id: uuid.UUID | None = None
        if class_label:
            res = await resolve_class(self.db, school_id, class_label)
            if len(res.candidates) != 1:
                raise NoticeActionError(
                    f"I couldn't identify the class '{class_label}'. Please name it clearly."
                )
            class_id = res.candidates[0].id

        # Default recipients follow the audience; NoticeService re-validates role/audience fit.
        target_roles = (
            ["parent", "student"]
            if audience_norm == NoticeAudience.EXTERNAL.value
            else ["admin", "class_incharge", "teacher"]
        )

        # Authorize NOW (and again at confirm). Selection by the planner grants nothing.
        scope = await get_staff_scope(self.db, current_user)
        assert_notice_publish(scope, class_id, audience_norm)

        return NoticePreview(
            action_token=uuid.uuid4(),
            title=title.strip()[:200],
            content=content.strip(),
            audience=audience_norm,
            target_roles=target_roles,
            priority=NoticePriority.MEDIUM.value,
            class_id=class_id,
        )

    # ── CONFIRM: the governed state change (idempotent, audited) ──────────────

    async def confirm_publish(
        self,
        current_user: CurrentUser,
        *,
        action_token: uuid.UUID,
        title: str,
        content: str,
        audience: str,
        class_id: uuid.UUID | None,
        target_roles: list[str],
        priority: str,
    ) -> tuple[Notice, bool]:
        """Publish the notice. Idempotent on action_token. Returns (notice, created_now)."""
        from app.core.staff_permissions import assert_notice_publish, get_staff_scope
        from app.modules.communications.services.notice_service import NoticeService

        school_id = uuid.UUID(current_user.school_id)

        # Idempotency: a prior execution for this token -> return its notice, publish nothing new.
        prior = (
            await self.db.execute(
                select(GovernedActionExecution).where(
                    GovernedActionExecution.school_id == school_id,
                    GovernedActionExecution.action_token == action_token,
                )
            )
        ).scalar_one_or_none()
        if prior is not None:
            if prior.status == ACTION_STATUS_COMPLETED and prior.result_id:
                existing = await self.db.get(Notice, prior.result_id)
                if existing is not None:
                    return existing, False
            raise NoticeActionError("This action was already processed.")

        # Re-authorize AT EXECUTION TIME (never trust the preview/planner).
        scope = await get_staff_scope(self.db, current_user)
        assert_notice_publish(scope, class_id, (audience or "").lower())

        # Reserve the idempotency token first so a concurrent/duplicate confirm collides here.
        execution = GovernedActionExecution(
            school_id=school_id,
            action_type=ACTION_PUBLISH_NOTICE,
            action_token=action_token,
            initiated_by=uuid.UUID(current_user.id),
            status=ACTION_STATUS_COMPLETED,
            result_type="notice",
        )
        self.db.add(execution)
        try:
            await self.db.flush()
        except IntegrityError as exc:
            # A concurrent confirm won the race — treat as idempotent duplicate.
            raise NoticeActionError("This action was already processed.") from exc

        # Validate + create via the EXISTING NoticeService (its own validation is authoritative).
        payload = NoticeCreate(
            title=title,
            content=content,
            audience=NoticeAudience(audience),
            target_roles=target_roles,
            priority=NoticePriority(priority),
            class_id=class_id,
        )
        notice = await NoticeService(self.db).create_notice(
            school_id, payload, uuid.UUID(current_user.id)
        )
        execution.result_id = notice.id

        self.db.add(
            AuditLog(
                school_id=school_id,
                user_id=uuid.UUID(current_user.id),
                action="action.publish_notice",
                resource_type="notice",
                resource_id=str(notice.id),
                details={
                    "action_token": str(action_token),
                    "audience": audience,
                    "class_id": str(class_id) if class_id else None,
                    "target_roles": target_roles,
                    "result": "published",
                },
            )
        )
        await self.db.flush()
        return notice, True

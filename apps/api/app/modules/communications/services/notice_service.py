"""Communication service — notices with internal vs external audiences."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import cast, or_, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.staff_permissions import StaffScope
from app.db.models.communication import Notice, NoticeAudience, NoticeReadReceipt
from app.db.models.student import Parent, Student, StudentParentMap
from app.modules.communications.schemas.notice import NoticeCreate

_STAFF_ROLES = frozenset({"admin", "super_admin", "class_incharge", "teacher", "operations"})
_EXTERNAL_ROLES = frozenset({"student", "parent"})


def _validate_notice_create(data: NoticeCreate) -> None:
    roles = set(data.target_roles)
    if data.audience == NoticeAudience.EXTERNAL:
        if not roles <= _EXTERNAL_ROLES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="External notices may only target student and/or parent roles",
            )
    else:
        if not roles <= _STAFF_ROLES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Internal notices may only target staff roles",
            )


class NoticeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_notice(
        self, school_id: uuid.UUID, data: NoticeCreate, created_by: uuid.UUID
    ) -> Notice:
        _validate_notice_create(data)
        notice = Notice(
            school_id=school_id,
            title=data.title,
            content=data.content,
            audience=data.audience,
            target_roles=data.target_roles,
            priority=data.priority,
            created_by=created_by,
            class_id=data.class_id,
            expires_at=data.expires_at,
        )
        self.db.add(notice)
        await self.db.flush()
        return notice

    def _role_matches(self, scope: StaffScope, target_roles: list) -> bool:
        roles = target_roles if isinstance(target_roles, list) else []
        if scope.role in roles:
            return True
        # Incharges may receive notices addressed to class_incharge even if UserRole is teacher.
        if "class_incharge" in roles and scope.incharge_class_ids:
            return True
        return False

    def _notice_visible_to_staff(self, notice: Notice, scope: StaffScope) -> bool:
        if scope.is_admin:
            return True

        if notice.audience == NoticeAudience.EXTERNAL:
            # Staff see external notices only if they manage that class (or school-wide admin).
            if notice.class_id is None:
                return False
            return notice.class_id in scope.incharge_class_ids

        # Internal staff circulars.
        if not self._role_matches(scope, notice.target_roles):
            return False
        if notice.class_id is None:
            return True
        if scope.incharge_class_ids and notice.class_id in scope.incharge_class_ids:
            return True
        if notice.class_id in scope.teaching_class_ids:
            return True
        return False

    async def list_notices_for_staff(
        self, school_id: uuid.UUID, scope: StaffScope, *, limit: int = 50
    ) -> list[Notice]:
        """Notices visible on the staff portal — respects internal vs external audience."""
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            select(Notice)
            .where(
                Notice.school_id == school_id,
                (Notice.expires_at.is_(None)) | (Notice.expires_at > now),
            )
            .order_by(Notice.created_at.desc())
            .limit(limit * 3)
        )
        notices = [n for n in result.scalars().all() if self._notice_visible_to_staff(n, scope)]
        return notices[:limit]

    async def _viewer_class_ids(
        self, school_id: uuid.UUID, viewer_user_id: uuid.UUID, viewer_role: str
    ) -> set[uuid.UUID]:
        """Classes linked to a parent (via children) or a student (self)."""
        if viewer_role == "student":
            rows = (
                await self.db.execute(
                    select(Student.class_id).where(
                        Student.school_id == school_id,
                        Student.user_id == viewer_user_id,
                    )
                )
            ).all()
            return {row[0] for row in rows}

        if viewer_role == "parent":
            rows = (
                await self.db.execute(
                    select(Student.class_id)
                    .join(StudentParentMap, StudentParentMap.student_id == Student.id)
                    .join(Parent, Parent.id == StudentParentMap.parent_id)
                    .where(
                        Parent.school_id == school_id,
                        Parent.user_id == viewer_user_id,
                        Student.school_id == school_id,
                    )
                )
            ).all()
            return {row[0] for row in rows}

        return set()

    async def list_notices(
        self,
        school_id: uuid.UUID,
        viewer_role: str,
        viewer_user_id: uuid.UUID,
    ) -> list[Notice]:
        """Parent/student external notices — scoped to viewer class(es) or school-wide."""
        now = datetime.now(timezone.utc)
        query = select(Notice).where(
            Notice.school_id == school_id,
            Notice.audience == NoticeAudience.EXTERNAL,
            (Notice.expires_at.is_(None)) | (Notice.expires_at > now),
        )
        if viewer_role not in ("admin", "super_admin"):
            query = query.where(Notice.target_roles.contains(cast([viewer_role], JSONB)))

        viewer_classes = await self._viewer_class_ids(school_id, viewer_user_id, viewer_role)
        if viewer_classes:
            query = query.where(
                or_(Notice.class_id.is_(None), Notice.class_id.in_(viewer_classes))
            )
        else:
            # No linked class — only school-wide external notices.
            query = query.where(Notice.class_id.is_(None))

        query = query.order_by(Notice.created_at.desc()).limit(50)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def mark_read(
        self, school_id: uuid.UUID, notice_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        notice = (
            await self.db.execute(
                select(Notice).where(
                    Notice.id == notice_id,
                    Notice.school_id == school_id,
                )
            )
        ).scalar_one_or_none()
        if not notice:
            raise ValueError("Notice not found")

        existing = await self.db.execute(
            select(NoticeReadReceipt).where(
                NoticeReadReceipt.notice_id == notice_id,
                NoticeReadReceipt.user_id == user_id,
            )
        )
        if not existing.scalar_one_or_none():
            self.db.add(
                NoticeReadReceipt(
                    school_id=school_id,
                    notice_id=notice_id,
                    user_id=user_id,
                    read_at=datetime.now(timezone.utc),
                )
            )
            await self.db.flush()

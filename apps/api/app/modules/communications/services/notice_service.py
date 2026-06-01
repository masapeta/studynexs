"""Communication service — notices."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import cast, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.communication import Notice, NoticeReadReceipt
from app.modules.communications.schemas.notice import NoticeCreate


class NoticeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_notice(
        self, school_id: uuid.UUID, data: NoticeCreate, created_by: uuid.UUID
    ) -> Notice:
        notice = Notice(
            school_id=school_id,
            title=data.title,
            content=data.content,
            target_roles=data.target_roles,
            priority=data.priority,
            created_by=created_by,
            expires_at=data.expires_at,
        )
        self.db.add(notice)
        await self.db.flush()
        return notice

    async def list_notices(self, school_id: uuid.UUID, viewer_role: str) -> list[Notice]:
        """Return notices visible to viewer_role; enforce expiry in SQL.

        Admins/principals administer communications and see every notice for the school;
        students/parents/teachers see only notices addressed to their role.
        """
        now = datetime.now(timezone.utc)
        query = select(Notice).where(
            Notice.school_id == school_id,
            (Notice.expires_at.is_(None)) | (Notice.expires_at > now),
        )
        if viewer_role not in ("admin", "super_admin"):
            query = query.where(Notice.target_roles.contains(cast([viewer_role], JSONB)))
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
                    notice_id=notice_id,
                    user_id=user_id,
                    read_at=datetime.now(timezone.utc),
                )
            )
            await self.db.flush()

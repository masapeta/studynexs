"""Notification service."""

import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.notification import Notification, NotificationChannel


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def send(
        self, school_id: uuid.UUID, user_id: uuid.UUID,
        title: str, body: str,
        channel: NotificationChannel = NotificationChannel.IN_APP,
        link: str | None = None,
    ) -> Notification:
        notif = Notification(
            school_id=school_id,
            user_id=user_id,
            title=title,
            body=body,
            channel=channel,
            link=link,
        )
        self.db.add(notif)
        await self.db.flush()

        # For SMS/Email/Push — dispatch to external service
        if channel == NotificationChannel.SMS:
            pass  # TODO: MSG91 integration
        elif channel == NotificationChannel.EMAIL:
            pass  # TODO: SendGrid / SES
        elif channel == NotificationChannel.PUSH:
            pass  # TODO: Firebase FCM

        return notif

    async def list_user_notifications(
        self,
        *,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
        unread_only: bool = False,
        limit: int = 30,
    ) -> list[Notification]:
        query = select(Notification).where(
            Notification.school_id == school_id,
            Notification.user_id == user_id,
        )
        if unread_only:
            query = query.where(Notification.is_read.is_(False))
        result = await self.db.execute(
            query.order_by(Notification.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def mark_read(
        self,
        *,
        school_id: uuid.UUID,
        notification_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        await self.db.execute(
            update(Notification)
            .where(
                Notification.school_id == school_id,
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
            .values(is_read=True)
        )
        await self.db.flush()

    async def mark_all_read(self, *, school_id: uuid.UUID, user_id: uuid.UUID) -> None:
        await self.db.execute(
            update(Notification)
            .where(
                Notification.school_id == school_id,
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
            .values(is_read=True)
        )
        await self.db.flush()

    async def unread_count(self, *, school_id: uuid.UUID, user_id: uuid.UUID) -> int:
        from sqlalchemy import func
        result = await self.db.execute(
            select(func.count()).where(
                Notification.school_id == school_id,
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
        )
        return result.scalar() or 0

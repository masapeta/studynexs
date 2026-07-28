"""Notification endpoints."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_route import CommitOnSuccessRoute
from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user
from app.modules.notifications.schemas.notification import NotificationOut
from app.modules.notifications.services.notification_service import NotificationService
from app.shared.schemas.common import APIResponse

router = APIRouter(route_class=CommitOnSuccessRoute)


@router.get("", response_model=APIResponse[list[NotificationOut]])
async def list_notifications(
    unread_only: bool = Query(False),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db)
    notifs = await service.list_user_notifications(
        school_id=uuid.UUID(current_user.school_id),
        user_id=uuid.UUID(current_user.id),
        unread_only=unread_only,
    )
    return APIResponse(data=[NotificationOut.model_validate(n) for n in notifs])


@router.get("/count", response_model=APIResponse[dict])
async def unread_count(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db)
    count = await service.unread_count(
        school_id=uuid.UUID(current_user.school_id),
        user_id=uuid.UUID(current_user.id),
    )
    return APIResponse(data={"unread_count": count})


@router.post("/{notification_id}/read", response_model=APIResponse)
async def mark_read(
    notification_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db)
    await service.mark_read(
        school_id=uuid.UUID(current_user.school_id),
        notification_id=notification_id,
        user_id=uuid.UUID(current_user.id),
    )
    return APIResponse(message="Marked as read")


@router.post("/read-all", response_model=APIResponse)
async def mark_all_read(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db)
    await service.mark_all_read(
        school_id=uuid.UUID(current_user.school_id),
        user_id=uuid.UUID(current_user.id),
    )
    return APIResponse(message="All notifications marked as read")

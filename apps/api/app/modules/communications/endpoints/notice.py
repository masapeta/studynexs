"""Communication endpoints — notices."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user, require_roles
from app.modules.communications.schemas.notice import NoticeCreate, NoticeOut
from app.modules.communications.services.notice_service import NoticeService
from app.shared.schemas.common import APIResponse

router = APIRouter()


@router.post("", response_model=APIResponse[NoticeOut], status_code=201)
async def create_notice(
    body: NoticeCreate,
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin")),
    db: AsyncSession = Depends(get_db),
):
    service = NoticeService(db)
    notice = await service.create_notice(
        uuid.UUID(current_user.school_id), body, uuid.UUID(current_user.id)
    )
    return APIResponse(data=NoticeOut.model_validate(notice), message="Notice published")


@router.get("", response_model=APIResponse[list[NoticeOut]])
async def list_notices(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Notices for the caller's role only — query ?role= is ignored (no privilege escalation)."""
    service = NoticeService(db)
    notices = await service.list_notices(
        uuid.UUID(current_user.school_id), current_user.role
    )
    return APIResponse(data=[NoticeOut.model_validate(n) for n in notices])


@router.post("/{notice_id}/read", response_model=APIResponse)
async def mark_read(
    notice_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = NoticeService(db)
    try:
        await service.mark_read(
            uuid.UUID(current_user.school_id), notice_id, uuid.UUID(current_user.id)
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return APIResponse(message="Marked as read")

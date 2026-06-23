"""Portal endpoints — parent, student, and teacher home context."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user
from app.modules.portal.schemas.portal import FeatureTeaserOut, PortalContextOut
from app.modules.portal.services.portal_service import PRODUCT_FEATURES, build_portal_context
from app.shared.schemas.common import APIResponse

router = APIRouter()


@router.get("/context", response_model=APIResponse[PortalContextOut])
async def portal_context(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Role-aware portal routing — children for parents, self for students."""
    ctx = await build_portal_context(
        db,
        school_id=uuid.UUID(current_user.school_id),
        user_id=uuid.UUID(current_user.id),
        role=current_user.role,
    )
    return APIResponse(data=ctx)


@router.get("/features", response_model=APIResponse[list[FeatureTeaserOut]])
async def product_features(
    current_user: CurrentUser = Depends(get_current_user),
):
    """Product roadmap teasers for demo / principal walkthrough."""
    return APIResponse(data=PRODUCT_FEATURES)

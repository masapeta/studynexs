"""Academic onboarding API — AI draft pack proposal and intelligence readiness (Stage 2A)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_route import CommitOnSuccessRoute
from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_roles
from app.core.staff_permissions import get_staff_scope
from app.modules.curriculum.schemas.onboarding import (
    AcademicIntelligenceStatusOut,
    OnboardingProposeRequest,
    OnboardingProposeResponse,
)
from app.modules.curriculum.services.curriculum_authz import (
    assert_curriculum_draft_edit,
    assert_curriculum_draft_edit_pack,
)
from app.modules.curriculum.services.curriculum_extraction_service import (
    CurriculumExtractionError,
    CurriculumExtractionService,
)
from app.modules.curriculum.services.intelligence_status import get_intelligence_status
from app.modules.curriculum.services.pack_service import PackError, PackService
from app.shared.schemas.common import APIResponse

router = APIRouter(route_class=CommitOnSuccessRoute)

_DRAFT_EDIT = ("teacher", "class_incharge", "admin", "super_admin")
_READ = ("teacher", "class_incharge", "admin", "super_admin")


async def _assert_draft_edit_class_subject(
    db: AsyncSession, current_user: CurrentUser, class_id: uuid.UUID, subject_id: uuid.UUID
) -> None:
    scope = await get_staff_scope(db, current_user)
    assert_curriculum_draft_edit(scope, class_id, subject_id)


@router.post(
    "/onboarding/propose",
    response_model=APIResponse[OnboardingProposeResponse],
    status_code=201,
)
async def propose_draft_pack(
    body: OnboardingProposeRequest,
    current_user: CurrentUser = Depends(require_roles(*_DRAFT_EDIT)),
    db: AsyncSession = Depends(get_db),
):
    """Create a draft CurriculumPack from admin inputs + AI extraction."""
    await _assert_draft_edit_class_subject(db, current_user, body.class_id, body.subject_id)
    svc = CurriculumExtractionService(db)
    try:
        result = await svc.propose_draft_pack(
            school_id=uuid.UUID(current_user.school_id),
            user_id=uuid.UUID(current_user.id),
            role=current_user.role,
            request=body,
        )
    except CurriculumExtractionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return APIResponse(
        data=result,
        message="Draft curriculum pack proposed — review and approve when ready",
    )


@router.get(
    "/packs/{pack_id}/intelligence-status",
    response_model=APIResponse[AcademicIntelligenceStatusOut],
)
async def pack_intelligence_status(
    pack_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_READ)),
    db: AsyncSession = Depends(get_db),
):
    try:
        status = await get_intelligence_status(
            db,
            school_id=uuid.UUID(current_user.school_id),
            pack_id=pack_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return APIResponse(data=status)


@router.post("/packs/{pack_id}/retry-rag-index", response_model=APIResponse)
async def retry_rag_index(
    pack_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_DRAFT_EDIT)),
    db: AsyncSession = Depends(get_db),
):
    svc = PackService(db)
    try:
        pack = await svc.get_pack(uuid.UUID(current_user.school_id), pack_id)
    except PackError as e:
        raise HTTPException(status_code=404, detail=str(e))
    await assert_curriculum_draft_edit_pack(db, current_user, pack_id)
    try:
        pack = await svc.retry_rag_index(
            uuid.UUID(current_user.school_id),
            pack_id,
            uuid.UUID(current_user.id),
        )
    except PackError as e:
        raise HTTPException(status_code=400, detail=str(e))
    status = await get_intelligence_status(
        db,
        school_id=uuid.UUID(current_user.school_id),
        pack_id=pack.id,
    )
    return APIResponse(
        data={"pack_id": str(pack.id), "intelligence": status.model_dump()},
        message="RAG index retry completed",
    )

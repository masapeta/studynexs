"""Curriculum pack knowledge graph — read-only spine (Batch 17)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_route import CommitOnSuccessRoute
from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_roles
from app.modules.curriculum.services.pack_service import PackError
from app.modules.knowledge_graph.schemas.graph import SpineOut
from app.modules.knowledge_graph.services.graph_service import (
    KnowledgeGraphError,
    KnowledgeGraphService,
)
from app.shared.schemas.common import APIResponse

router = APIRouter(route_class=CommitOnSuccessRoute)

_READ = ("teacher", "class_incharge", "admin", "super_admin")


@router.get("/packs/{pack_id}/graph", response_model=APIResponse[SpineOut])
async def get_pack_graph(
    pack_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_READ)),
    db: AsyncSession = Depends(get_db),
):
    svc = KnowledgeGraphService(db)
    try:
        spine = await svc.get_spine(
            school_id=uuid.UUID(current_user.school_id), pack_id=pack_id
        )
    except PackError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except KnowledgeGraphError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return APIResponse(data=spine)

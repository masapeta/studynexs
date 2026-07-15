"""Curriculum pack knowledge graph — read-only spine (Batch 17)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_route import CommitOnSuccessRoute
from app.core.authorization import assert_can_access_student
from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user, require_roles
from app.modules.curriculum.services.pack_service import PackError
from app.modules.knowledge_graph.schemas.graph import (
    ConceptContextOut,
    SpineOut,
    StudentWeakConceptsOut,
)
from app.modules.knowledge_graph.services.graph_query_service import GraphQueryService
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


@router.get(
    "/packs/{pack_id}/concepts/{concept_id}/context",
    response_model=APIResponse[ConceptContextOut],
)
async def get_concept_graph_context(
    pack_id: uuid.UUID,
    concept_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Copilot-ready concept context: card status, linked questions, weak students."""
    svc = GraphQueryService(db)
    try:
        ctx = await svc.get_concept_context(
            school_id=uuid.UUID(current_user.school_id),
            pack_id=pack_id,
            concept_id=concept_id,
        )
    except PackError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return APIResponse(data=ctx)


@router.get(
    "/students/{student_id}/weak-concepts",
    response_model=APIResponse[StudentWeakConceptsOut],
)
async def get_student_weak_concepts(
    student_id: uuid.UUID,
    subject_id: uuid.UUID | None = None,
    pack_id: uuid.UUID | None = None,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Weak concepts for a student from the knowledge graph (mastery-derived)."""
    await assert_can_access_student(current_user, db, student_id)
    concepts = await GraphQueryService(db).list_student_weak_concepts(
        school_id=uuid.UUID(current_user.school_id),
        student_id=student_id,
        subject_id=subject_id,
        pack_id=pack_id,
    )
    return APIResponse(
        data=StudentWeakConceptsOut(student_id=student_id, concepts=concepts)
    )

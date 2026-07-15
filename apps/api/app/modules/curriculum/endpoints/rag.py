"""Curriculum RAG — hybrid search for copilots (Batch 24)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_route import CommitOnSuccessRoute
from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_roles
from app.modules.ai.embeddings import EmbeddingService
from app.modules.ai.rag import HybridRetrievalOptions, HybridRetrievalService, RagService
from app.modules.ai.vectorstore import get_vector_store
from app.modules.curriculum.schemas.rag import RagSearchHitOut, RagSearchOut
from app.modules.curriculum.services.pack_service import PackError, PackService
from app.shared.schemas.common import APIResponse

router = APIRouter(route_class=CommitOnSuccessRoute)

_READ = ("teacher", "class_incharge", "admin", "super_admin")


@router.get(
    "/packs/{pack_id}/rag/search",
    response_model=APIResponse[RagSearchOut],
)
async def hybrid_rag_search(
    pack_id: uuid.UUID,
    q: str = Query(..., min_length=1, max_length=500),
    top_k: int = Query(5, ge=1, le=20),
    student_id: uuid.UUID | None = None,
    current_user: CurrentUser = Depends(require_roles(*_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Hybrid vector + graph retrieval for curriculum grounding (copilot/debug)."""
    school_id = uuid.UUID(current_user.school_id)
    try:
        pack = await PackService(db).get_pack(school_id, pack_id)
    except PackError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    rag = RagService(db, embedder=EmbeddingService(), store=get_vector_store())
    hybrid = HybridRetrievalService(db, rag)
    hits = await hybrid.retrieve_hybrid(
        q.strip(),
        school_id=school_id,
        pack_id=pack.id,
        top_k=top_k,
        options=HybridRetrievalOptions(student_id=student_id, rerank=True),
    )
    return APIResponse(
        data=RagSearchOut(
            query=q.strip(),
            pack_id=str(pack_id),
            hits=[
                RagSearchHitOut(
                    ref_id=h.ref_id,
                    text=h.text,
                    score=h.score,
                    chapter=h.chapter,
                    topic=h.topic,
                )
                for h in hits
            ],
        )
    )

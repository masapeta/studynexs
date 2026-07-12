"""Curriculum pack document ingestion — Document Intelligence pipeline (Batch 16)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_route import CommitOnSuccessRoute
from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_roles
from app.db.models.document_ingestion import DocumentType
from app.modules.ai.services.document_intelligence_service import (
    DocumentIntelligenceError,
    DocumentIntelligenceService,
)
from app.modules.curriculum.services.pack_service import PackError, PackService
from app.modules.curriculum.schemas.ingest import (
    IngestDocumentIn,
    IngestDocumentOut,
    IngestStatusOut,
    IngestionSummaryOut,
)
from app.shared.schemas.common import APIResponse

router = APIRouter(route_class=CommitOnSuccessRoute)

_BUILD = ("class_incharge", "admin", "super_admin")
_READ = ("teacher", "class_incharge", "admin", "super_admin")


def _err(e: DocumentIntelligenceError) -> HTTPException:
    msg = str(e)
    code = 404 if "not found" in msg.lower() else 400
    return HTTPException(status_code=code, detail=msg)


@router.post(
    "/packs/{pack_id}/ingest-document",
    response_model=APIResponse[IngestDocumentOut],
    status_code=201,
)
async def ingest_document(
    pack_id: uuid.UUID,
    body: IngestDocumentIn,
    current_user: CurrentUser = Depends(require_roles(*_BUILD)),
    db: AsyncSession = Depends(get_db),
):
    svc = DocumentIntelligenceService(db)
    try:
        result = await svc.ingest_uploaded_file(
            school_id=uuid.UUID(current_user.school_id),
            pack_id=pack_id,
            file_id=body.file_id,
            doc_type=DocumentType(body.doc_type),
            ingested_by=uuid.UUID(current_user.id),
        )
    except DocumentIntelligenceError as e:
        raise _err(e)
    return APIResponse(
        data=IngestDocumentOut.model_validate(result),
        message=f"Document indexed — {result.chunks_indexed} chunks added to pack grounding",
    )


@router.get(
    "/packs/{pack_id}/ingest-status",
    response_model=APIResponse[IngestStatusOut],
)
async def ingest_status(
    pack_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_READ)),
    db: AsyncSession = Depends(get_db),
):
    svc = DocumentIntelligenceService(db)
    try:
        raw = await svc.get_ingest_status(
            school_id=uuid.UUID(current_user.school_id), pack_id=pack_id
        )
    except PackError as e:
        raise HTTPException(status_code=404, detail=str(e))
    ingestions = raw.pop("ingestions", [])
    return APIResponse(
        data=IngestStatusOut(
            indexed_topic_count=raw["indexed_topic_count"],
            indexed_document_chunks=raw["indexed_document_chunks"],
            last_ingested_at=raw["last_ingested_at"],
            recent_ingestions=[
                IngestionSummaryOut.model_validate(i) for i in ingestions
            ],
        )
    )

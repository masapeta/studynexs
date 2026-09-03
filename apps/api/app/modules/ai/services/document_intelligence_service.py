"""Document Intelligence — unified OCR → parse → chunk → embed → index pipeline (Batch 16).

Reuses shared OCR, embeddings, and RAG. All documents are tenant- and pack-scoped.
School-uploaded worksheets/notes/circulars supplement structured curriculum topics.
"""
from __future__ import annotations

import uuid

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.curriculum_pack import PackStatus
from app.db.models.document_ingestion import (
    DocumentIngestion,
    DocumentType,
    IngestStatus,
)
from app.db.models.file import FileCategory
from app.modules.ai.embeddings import EmbeddingService
from app.modules.ai.gateway.input_guard import sanitize_prompt_text
from app.modules.ai.rag import RagService
from app.modules.ai.vectorstore.base import VectorStore
from app.modules.curriculum.services.pack_service import PackService
from app.modules.files.services.document_ocr import extract_text_from_upload
from app.modules.files.services.file_service import FileService
from app.modules.files.services.file_validation import (
    max_upload_bytes,
    read_file_bytes_bounded,
)

logger = structlog.get_logger()

_CHUNK_MAX_CHARS = 800
_CHUNK_MIN_CHARS = 50
_SANITIZE_MAX = 2000


class DocumentIntelligenceError(ValueError):
    """Document cannot be ingested."""


def chunk_text(
    text: str, *, max_chars: int = _CHUNK_MAX_CHARS, min_chars: int = _CHUNK_MIN_CHARS
) -> list[str]:
    """Split extracted text into bounded chunks for embedding."""
    normalized = text.replace("\r\n", "\n").strip()
    if not normalized:
        return []

    paragraphs = [p.strip() for p in normalized.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [ln.strip() for ln in normalized.split("\n") if ln.strip()]

    chunks: list[str] = []
    buf = ""
    for para in paragraphs:
        candidate = f"{buf}\n\n{para}".strip() if buf else para
        if len(candidate) <= max_chars:
            buf = candidate
            continue
        if buf and len(buf) >= min_chars:
            chunks.append(buf)
        if len(para) > max_chars:
            for i in range(0, len(para), max_chars):
                part = para[i : i + max_chars].strip()
                if len(part) >= min_chars:
                    chunks.append(part)
            buf = ""
        else:
            buf = para
    if buf and len(buf) >= min_chars:
        chunks.append(buf)
    return chunks


def sanitize_chunks(chunks: list[str]) -> list[str]:
    """Sanitize OCR output before indexing (untrusted input)."""
    out: list[str] = []
    for raw in chunks:
        cleaned = sanitize_prompt_text(
            raw, max_length=_SANITIZE_MAX, field_name="document_chunk", reject_injection=False
        )
        if cleaned and len(cleaned) >= _CHUNK_MIN_CHARS:
            out.append(cleaned)
    return out


class DocumentIntelligenceService:
    def __init__(
        self,
        db: AsyncSession,
        *,
        embedder: EmbeddingService | None = None,
        store: VectorStore | None = None,
    ) -> None:
        self.db = db
        self.embedder = embedder or EmbeddingService()
        self.store = store
        self.rag = RagService(db, embedder=self.embedder, store=store)
        self.files = FileService(db)
        self.packs = PackService(db)

    async def ingest_uploaded_file(
        self,
        *,
        school_id: uuid.UUID,
        pack_id: uuid.UUID,
        file_id: uuid.UUID,
        doc_type: DocumentType,
        ingested_by: uuid.UUID,
    ) -> DocumentIngestion:
        pack = await self.packs.get_pack(school_id, pack_id)
        if pack.status != PackStatus.APPROVED:
            raise DocumentIntelligenceError(
                "Only approved curriculum packs accept document ingestion"
            )

        record = await self.files.get_file(file_id, school_id=school_id)
        if record is None:
            raise DocumentIntelligenceError("Uploaded file not found")
        if record.category != FileCategory.DOCUMENT:
            raise DocumentIntelligenceError("Only document-category uploads can be ingested")

        prior_version = await self.db.scalar(
            select(func.max(DocumentIngestion.version)).where(
                DocumentIngestion.school_id == school_id,
                DocumentIngestion.pack_id == pack_id,
                DocumentIngestion.file_id == file_id,
            )
        )
        version = (prior_version or 0) + 1

        ingestion = DocumentIngestion(
            school_id=school_id,
            pack_id=pack_id,
            file_id=file_id,
            doc_type=doc_type,
            status=IngestStatus.PENDING,
            version=version,
            source_name=record.original_name,
            ingested_by=ingested_by,
        )
        self.db.add(ingestion)
        await self.db.flush()

        try:
            file_data = read_file_bytes_bounded(
                record.storage_path,
                size_bytes=record.size_bytes,
                max_bytes=max_upload_bytes(FileCategory.DOCUMENT),
            )
            raw_text = extract_text_from_upload(
                file_data=file_data, content_type=record.content_type
            )
            chunks = sanitize_chunks(chunk_text(raw_text))
            if not chunks:
                raise DocumentIntelligenceError(
                    "No extractable text in document — check OCR or upload a text-based PDF"
                )

            indexed = await self.rag.index_document_chunks(
                pack,
                file_id=file_id,
                doc_type=doc_type.value,
                source_name=record.original_name,
                chunks=chunks,
            )
            ingestion.chunks_indexed = indexed
            ingestion.status = IngestStatus.COMPLETED
            from app.modules.curriculum.services.content_review_service import (
                ContentReviewService,
            )

            await ContentReviewService(self.db).enqueue_document_ingest(
                school_id=school_id, ingestion=ingestion
            )
            logger.info(
                "document_ingested",
                school_id=str(school_id),
                pack_id=str(pack_id),
                file_id=str(file_id),
                chunks=indexed,
                version=version,
            )
        except DocumentIntelligenceError:
            ingestion.status = IngestStatus.FAILED
            ingestion.error_message = "Ingestion failed"
            raise
        except Exception as exc:
            ingestion.status = IngestStatus.FAILED
            ingestion.error_message = "Ingestion failed"
            logger.warning(
                "document_ingest_failed",
                school_id=str(school_id),
                pack_id=str(pack_id),
                file_id=str(file_id),
                exc_info=True,
            )
            raise DocumentIntelligenceError("Document ingestion failed") from exc

        return ingestion

    async def get_ingest_status(
        self, *, school_id: uuid.UUID, pack_id: uuid.UUID
    ) -> dict:
        await self.packs.get_pack(school_id, pack_id)

        from app.db.models.curriculum_pack import CurriculumChapter, CurriculumTopic

        chapters = (
            await self.db.execute(
                select(CurriculumChapter.id).where(
                    CurriculumChapter.pack_id == pack_id,
                    CurriculumChapter.school_id == school_id,
                )
            )
        ).scalars().all()
        indexed_topic_count = 0
        if chapters:
            indexed_topic_count = (
                await self.db.scalar(
                    select(func.count()).select_from(CurriculumTopic).where(
                        CurriculumTopic.chapter_id.in_(list(chapters))
                    )
                )
            ) or 0

        doc_chunks_db = (
            await self.db.scalar(
                select(func.coalesce(func.sum(DocumentIngestion.chunks_indexed), 0)).where(
                    DocumentIngestion.school_id == school_id,
                    DocumentIngestion.pack_id == pack_id,
                    DocumentIngestion.status == IngestStatus.COMPLETED,
                )
            )
        ) or 0

        last_ingested_at = await self.db.scalar(
            select(func.max(DocumentIngestion.updated_at)).where(
                DocumentIngestion.school_id == school_id,
                DocumentIngestion.pack_id == pack_id,
                DocumentIngestion.status == IngestStatus.COMPLETED,
            )
        )

        recent = (
            await self.db.execute(
                select(DocumentIngestion)
                .where(
                    DocumentIngestion.school_id == school_id,
                    DocumentIngestion.pack_id == pack_id,
                )
                .order_by(DocumentIngestion.created_at.desc())
                .limit(10)
            )
        ).scalars().all()

        indexed_document_chunks = doc_chunks_db
        if self.store is not None:
            try:
                vector_count = await self.rag.count_document_chunks(
                    school_id=school_id, pack_id=pack_id
                )
                if vector_count:
                    indexed_document_chunks = vector_count
            except Exception:  # noqa: BLE001
                logger.warning(
                    "document_chunk_count_failed",
                    school_id=str(school_id),
                    pack_id=str(pack_id),
                    exc_info=True,
                )

        return {
            "indexed_topic_count": indexed_topic_count,
            "indexed_document_chunks": int(indexed_document_chunks),
            "last_ingested_at": last_ingested_at,
            "ingestions": recent,
        }

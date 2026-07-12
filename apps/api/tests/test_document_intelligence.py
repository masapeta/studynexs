"""Document Intelligence — OCR → chunk → embed → index pipeline (Batch 16).

Uses stub embedder + in-memory vector store; OCR is monkeypatched for deterministic text.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from app.db.models.academic import AcademicYear, Class, Subject
from app.db.models.curriculum_pack import (
    CurriculumChapter,
    CurriculumPack,
    CurriculumTopic,
    PackStatus,
)
from app.db.models.document_ingestion import DocumentType, IngestStatus
from app.db.models.file import FileCategory
from app.db.models.school import School
from app.db.models.user import User, UserRole
from app.modules.ai.embeddings import EmbeddingService
from app.modules.ai.embeddings.stub_provider import StubEmbeddingProvider
from app.modules.ai.rag import RagService
from app.modules.ai.services.document_intelligence_service import (
    DocumentIntelligenceError,
    DocumentIntelligenceService,
    chunk_text,
    sanitize_chunks,
)
from app.modules.ai.vectorstore.memory_store import InMemoryVectorStore
from app.modules.files.services.file_service import FileService

_OCR = "app.modules.ai.services.document_intelligence_service.extract_text_from_upload"


async def _seed(db, *, pack_status=PackStatus.APPROVED):
    school = School(
        name="T",
        code="T",
        tenant_slug="t",
        board="SSC",
        contact_email="a@t.com",
        contact_phone="+910000000000",
        is_active=True,
    )
    db.add(school)
    await db.flush()
    ay = AcademicYear(
        school_id=school.id,
        year_label="2026-2027",
        start_date=date(2026, 6, 1),
        end_date=date(2027, 5, 31),
        is_active=True,
    )
    db.add(ay)
    await db.flush()
    cls = Class(school_id=school.id, grade="10", section="A", academic_year_id=ay.id)
    teacher = User(
        school_id=school.id,
        mobile="+910000000001",
        full_name="Teacher",
        role=UserRole.TEACHER,
        is_active=True,
    )
    db.add_all([cls, teacher])
    await db.flush()
    maths = Subject(school_id=school.id, name="Maths", class_id=cls.id)
    db.add(maths)
    await db.flush()

    pack = CurriculumPack(
        school_id=school.id,
        class_id=cls.id,
        subject_id=maths.id,
        academic_year_id=ay.id,
        board="SSC",
        created_by=teacher.id,
        status=pack_status,
        approved_by=teacher.id if pack_status == PackStatus.APPROVED else None,
        approved_at=datetime.now(timezone.utc) if pack_status == PackStatus.APPROVED else None,
    )
    db.add(pack)
    await db.flush()
    ch = CurriculumChapter(
        school_id=school.id, pack_id=pack.id, number="1", title="Algebra", order_index=0
    )
    db.add(ch)
    await db.flush()
    db.add(
        CurriculumTopic(
            school_id=school.id,
            chapter_id=ch.id,
            title="Quadratic Equations",
            order_index=0,
            concepts=["factorisation"],
        )
    )
    await db.flush()
    return school, pack, teacher


def _svc(db) -> DocumentIntelligenceService:
    store = InMemoryVectorStore()
    embedder = EmbeddingService(provider=StubEmbeddingProvider())
    return DocumentIntelligenceService(db, embedder=embedder, store=store)


def test_chunk_text_splits_paragraphs():
    text = "Para one about quadratics.\n\n" + ("Para two " * 40)
    chunks = chunk_text(text, max_chars=200, min_chars=30)
    assert len(chunks) >= 2
    assert all(len(c) >= 30 for c in chunks)


def test_sanitize_chunks_strips_control_chars():
    raw = ["Hello\x00 world " * 10]
    out = sanitize_chunks(raw)
    assert out and "\x00" not in out[0]


@pytest.mark.asyncio
async def test_ingest_document_indexes_chunks(db_session, monkeypatch):
    school, pack, teacher = await _seed(db_session)
    svc = _svc(db_session)
    files = FileService(db_session)

    sample_text = (
        "Quadratic equations worksheet.\n\n"
        "Solve x squared plus five x plus six equals zero using factorisation.\n\n"
        "Practice problems for class ten students."
    )

    def _fake_ocr(**_kwargs):
        return sample_text

    monkeypatch.setattr(_OCR, _fake_ocr)

    uploaded = await files.upload(
        school.id,
        b"%PDF-fake",
        "worksheet.pdf",
        "application/pdf",
        FileCategory.DOCUMENT,
        teacher.id,
    )

    result = await svc.ingest_uploaded_file(
        school_id=school.id,
        pack_id=pack.id,
        file_id=uploaded.id,
        doc_type=DocumentType.WORKSHEET,
        ingested_by=teacher.id,
    )

    assert result.status == IngestStatus.COMPLETED
    assert result.chunks_indexed >= 1

    rag = RagService(
        db_session,
        embedder=svc.embedder,
        store=svc.store,  # type: ignore[arg-type]
    )
    chunks = await rag.retrieve(
        "factorisation quadratic",
        school_id=school.id,
        pack_id=pack.id,
        top_k=5,
    )
    assert chunks
    assert any("quadratic" in c.text.lower() for c in chunks)


@pytest.mark.asyncio
async def test_ingest_rejects_draft_pack(db_session, monkeypatch):
    school, pack, teacher = await _seed(db_session, pack_status=PackStatus.DRAFT)
    svc = _svc(db_session)
    files = FileService(db_session)
    monkeypatch.setattr(_OCR, lambda **_k: "Some text " * 20)

    uploaded = await files.upload(
        school.id,
        b"%PDF-fake",
        "notes.pdf",
        "application/pdf",
        FileCategory.DOCUMENT,
        teacher.id,
    )

    with pytest.raises(DocumentIntelligenceError, match="approved"):
        await svc.ingest_uploaded_file(
            school_id=school.id,
            pack_id=pack.id,
            file_id=uploaded.id,
            doc_type=DocumentType.NOTES,
            ingested_by=teacher.id,
        )


@pytest.mark.asyncio
async def test_ingest_status_reports_counts(db_session, monkeypatch):
    school, pack, teacher = await _seed(db_session)
    svc = _svc(db_session)
    monkeypatch.setattr(_OCR, lambda **_k: "Worksheet content " * 30)

    files = FileService(db_session)
    uploaded = await files.upload(
        school.id,
        b"%PDF-fake",
        "sheet.pdf",
        "application/pdf",
        FileCategory.DOCUMENT,
        teacher.id,
    )
    await svc.ingest_uploaded_file(
        school_id=school.id,
        pack_id=pack.id,
        file_id=uploaded.id,
        doc_type=DocumentType.WORKSHEET,
        ingested_by=teacher.id,
    )

    status = await svc.get_ingest_status(school_id=school.id, pack_id=pack.id)
    assert status["indexed_topic_count"] == 1
    assert status["indexed_document_chunks"] >= 1
    assert status["last_ingested_at"] is not None
    assert len(status["ingestions"]) == 1


@pytest.mark.asyncio
async def test_reingest_increments_version(db_session, monkeypatch):
    school, pack, teacher = await _seed(db_session)
    svc = _svc(db_session)
    monkeypatch.setattr(_OCR, lambda **_k: "Updated notes content " * 25)

    files = FileService(db_session)
    uploaded = await files.upload(
        school.id,
        b"%PDF-fake",
        "notes.pdf",
        "application/pdf",
        FileCategory.DOCUMENT,
        teacher.id,
    )

    first = await svc.ingest_uploaded_file(
        school_id=school.id,
        pack_id=pack.id,
        file_id=uploaded.id,
        doc_type=DocumentType.NOTES,
        ingested_by=teacher.id,
    )
    second = await svc.ingest_uploaded_file(
        school_id=school.id,
        pack_id=pack.id,
        file_id=uploaded.id,
        doc_type=DocumentType.NOTES,
        ingested_by=teacher.id,
    )
    assert first.version == 1
    assert second.version == 2
    assert second.status == IngestStatus.COMPLETED

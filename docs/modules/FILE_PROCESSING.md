# File Processing

> Module dashboard · Master: [`../PLATFORM_STATUS.md`](../PLATFORM_STATUS.md) · Canonical: [`/CLAUDE.md`](../../CLAUDE.md) §38.1

## Status

**✅ Complete** (Batch 16 — Document Intelligence MVP)

## Owner

Shared document pipeline (one path for all school documents)

## Pipeline

OCR → parse → chunk → embed → metadata → index → version

## Implementation

| Layer | Path |
|-------|------|
| Shared OCR | `apps/api/app/modules/files/services/document_ocr.py` |
| Orchestrator | `apps/api/app/modules/ai/services/document_intelligence_service.py` |
| RAG extension | `RagService.index_document_chunks()` |
| Audit | `document_ingestions` table (migration `x4e5f6a7b8c9`) |
| API | `POST /api/v1/curriculum/packs/{pack_id}/ingest-document`, `GET .../ingest-status` |
| Admin UI | `apps/admin-web/.../teaching/document-ingest/page.tsx` |
| Tests | `apps/api/tests/test_document_intelligence.py` (6) |

## Fragments unified

- Admissions OCR now delegates to shared `document_ocr.py`
- Answer-sheet vision remains eval-specific (not merged into curriculum ingest)

## Rule

Never re-implement per-feature OCR/embed pipelines.

## Used by

Curriculum pack grounding (RAG) · Knowledge Graph (Batch 17, planned)

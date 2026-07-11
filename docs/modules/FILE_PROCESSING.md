# File Processing

> Module dashboard · Master: [`../PLATFORM_STATUS.md`](../PLATFORM_STATUS.md) · Canonical: [`/CLAUDE.md`](../../CLAUDE.md) §38.1

## Status

**🔴 Planned** (Batch 16 — Document Intelligence)

## Owner

Shared document pipeline (one path for all school documents)

## Target pipeline

OCR → parse → chunk → embed → metadata → index → version

## Current fragments

- Admissions document OCR (`pytesseract` in school_ops)
- File upload service (`apps/api/app/modules/files/`)
- Answer-sheet images (vision path — see OCR_PIPELINE)

## Rule

Never re-implement per-feature OCR/embed pipelines.

## Used by (planned)

Curriculum ingestion · RAG · Knowledge Graph

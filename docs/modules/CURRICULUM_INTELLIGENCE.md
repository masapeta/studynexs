# Curriculum Intelligence

> Module dashboard · Master: [`../PLATFORM_STATUS.md`](../PLATFORM_STATUS.md) · Canonical: [`/CLAUDE.md`](../../CLAUDE.md) §38–§39

## Status

**🟡 In progress** (~55%)

## Owner

Pillar 1 — source of truth for academic AI

## Features

| Feature | State |
|---------|-------|
| CurriculumPack model + versioning | ✅ |
| HOD approval → immutable approved pack | ✅ |
| RAG index on approved pack | ✅ |
| Grounded QP generation | ✅ |
| Document Intelligence (OCR→chunk→embed pipeline) | ✅ Batch 16 |
| Knowledge Graph spine tables | ⬜ Batch 17 |
| Curriculum management UI | ⬜ |

## Files

`apps/api/app/modules/curriculum/` · `apps/api/app/modules/ai/rag/`

## Rule

All academic AI runs against an **approved** pack — never free-text board assumptions in code.

## Used by

RAG · Assessment Intelligence · Teacher Copilot · Document Intelligence

## Tests

`tests/test_curriculum_pack.py` · `tests/test_document_intelligence.py`

## Next batch

Knowledge Graph schema (Batch 17)

# Curriculum Intelligence

> Module dashboard · Master: [`../PLATFORM_STATUS.md`](../PLATFORM_STATUS.md) · Canonical: [`/CLAUDE.md`](../../CLAUDE.md) §38–§39

## Status

**🟡 In progress** (~40%)

## Owner

Pillar 1 — source of truth for academic AI

## Features

| Feature | State |
|---------|-------|
| CurriculumPack model + versioning | ✅ |
| HOD approval → immutable approved pack | ✅ |
| RAG index on approved pack | ✅ |
| Grounded QP generation | ✅ |
| Document Intelligence (OCR→chunk→embed pipeline) | ⬜ |
| Knowledge Graph spine tables | ⬜ |
| Curriculum management UI | ⬜ |

## Files

`apps/api/app/modules/curriculum/` · `apps/api/app/modules/ai/rag/`

## Rule

All academic AI runs against an **approved** pack — never free-text board assumptions in code.

## Used by

RAG · Assessment Intelligence · Teacher Copilot (planned)

## Tests

`tests/test_curriculum_pack.py`

## Next batch

Document Intelligence ingestion (Batch 16)

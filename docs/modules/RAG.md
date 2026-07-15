# RAG

> Module dashboard · Master: [`../PLATFORM_STATUS.md`](../PLATFORM_STATUS.md)

## Status

**✅ Complete (hybrid + re-rank MVP)** — Batch 24 · Verified: **tests passing**

## Depends on

| | Modules |
|---|---------|
| **Satisfied** | Embeddings · Vector Store · Knowledge Graph |
| **Pending** | — |

## Owner

`app/modules/ai/rag/` · grounding seams in `assessment_grounding.py`

## Features

| Feature | State |
|---------|-------|
| `index_pack` (chapter → topic chunks) | ✅ |
| `retrieve` (tenant + pack scoped) | ✅ |
| `build_context` with numbered citations | ✅ |
| `ground_for_pack` (QP generation) | ✅ |
| `ground_for_evaluation` (marking, best-effort) | ✅ |
| Hybrid search (vector + graph expansion) | ✅ Batch 24 |
| Re-ranking (concept/card/weak boosts) | ✅ Batch 24 |
| `GET .../packs/{id}/rag/search` API | ✅ Batch 24 |
| Metadata filtering beyond pack/topic | ⬜ |

## Files

`apps/api/app/modules/ai/rag/service.py` · `hybrid.py` · `assessment_grounding.py` · `endpoints/rag.py`

## Grounding unit

Curriculum **topic** (structured, copyright-safe) — not raw textbook prose.

## Used by

Assessment Intelligence · Curriculum Intelligence · Teacher Copilot · Copilot debug API

## Tests

`tests/test_rag.py` · `tests/test_rag_hybrid.py` (3) · `tests/test_assessment_grounding.py`

## Batch

9–12 (foundation) · 14 (eval grounding) · **24 (hybrid + re-rank)**

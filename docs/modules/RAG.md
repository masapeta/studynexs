# RAG

> Module dashboard · Master: [`../PLATFORM_STATUS.md`](../PLATFORM_STATUS.md)

## Status

**🟡 In progress** — core retrieval complete; advanced retrieval pending · Verified: **integration pending**

## Depends on

| | Modules |
|---|---------|
| **Satisfied** | Embeddings · Vector Store |
| **Pending** | — |

## Owner

`app/modules/ai/rag/service.py` · grounding seams in `assessment_grounding.py`

## Features

| Feature | State |
|---------|-------|
| `index_pack` (chapter → topic chunks) | ✅ |
| `retrieve` (tenant + pack scoped) | ✅ |
| `build_context` with numbered citations | ✅ |
| `ground_for_pack` (QP generation) | ✅ |
| `ground_for_evaluation` (marking, best-effort) | ✅ |
| Metadata filtering beyond pack/topic | ⬜ |
| Hybrid search | ⬜ |
| Re-ranking | ⬜ |

## Files

`apps/api/app/modules/ai/rag/` · `app/modules/ai/services/assessment_grounding.py`

## Grounding unit

Curriculum **topic** (structured, copyright-safe) — not raw textbook prose.

## Used by

Assessment Intelligence · Curriculum Intelligence · Teacher Copilot (planned)

## Tests

`tests/test_rag.py` · `tests/test_assessment_grounding.py`

## Batch

9–12 (foundation) · 14 (eval grounding)

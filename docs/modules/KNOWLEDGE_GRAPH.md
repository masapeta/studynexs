# Knowledge Graph

> Module dashboard · Master: [`../PLATFORM_STATUS.md`](../PLATFORM_STATUS.md) · Detail: [`../KNOWLEDGE_GRAPH.md`](../KNOWLEDGE_GRAPH.md)

## Status

**✅ Complete (spine + question links MVP)** — Batch 19

## Owner

Shared spine — Pack → Chapter → Topic → Concept

## Features

| Feature | State |
|---------|-------|
| Architecture documented | ✅ |
| `curriculum_concepts` + `kg_edges` tables | ✅ Batch 17 |
| Spine build on pack approve | ✅ |
| `GET /packs/{id}/graph` read API | ✅ |
| `ConceptCard` first-class model | ✅ Batch 18 |
| Question → Concept links | ✅ Batch 19 |
| Graph queries for copilots | ⬜ |

## Implementation

| Layer | Path |
|-------|------|
| Models | `apps/api/app/db/models/knowledge_graph.py` |
| Service | `apps/api/app/modules/knowledge_graph/services/graph_service.py` |
| Question links | `apps/api/app/modules/knowledge_graph/services/question_concept_link_service.py` |
| API | `GET /api/v1/curriculum/packs/{pack_id}/graph` |
| Bank concepts API | `GET /api/v1/ai/question-bank/items/{item_id}/concepts` |
| Hook | `PackService.approve_pack` → `build_spine_from_pack`; `ingest_from_paper` → TESTS edges |
| Tests | `apps/api/tests/test_knowledge_graph.py` (6) · `test_question_concept_links.py` (6) |

## Used by

Curriculum Intelligence · Teacher Copilot (future concept queries) · Adaptive learning (planned)

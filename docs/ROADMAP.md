# StudyNexs — Roadmap

> Milestones and sequencing. **Canonical policy:** [`/CLAUDE.md`](../CLAUDE.md) §87–§88. **Live
> state:** [`STATUS.md`](./STATUS.md) and [`AGENT_HANDOVER.md`](./AGENT_HANDOVER.md). **Product
> detail:** [`PRODUCT.md`](./PRODUCT.md). This file is the engineering-facing milestone view; it
> never overrides the constitution.
>
> Rule: **one thin, real, production-grade slice at a time** (`DECISION_LOG` D3). Build platform
> capabilities before isolated features; don't front-run later layers with speculative complexity.

## The four intelligence pillars (progress — engineering estimate)

| Pillar | Progress | State |
|---|---|---|
| Curriculum Intelligence | ~55% | CurriculumPack + RAG + document ingest ✅; Knowledge Graph pending → [`CURRICULUM_INTELLIGENCE.md`](./CURRICULUM_INTELLIGENCE.md) |
| Assessment Intelligence | ~60% | Grounded+cited QP ✅; rubric-per-criterion eval ✅; pack-grounded marking + eval UI rubric display ✅ → [`ASSESSMENT_INTELLIGENCE.md`](./ASSESSMENT_INTELLIGENCE.md) |
| Learning Intelligence | ~15% | mastery compute + template tutor; adaptive + analytics pending |
| School Operations Intelligence | ~60% | students/staff/fees/attendance/exams/finance built |
| Shared AI Platform | ~75% | gateway + metering + credits + embeddings + vector store + RAG + grounding seam live → [`AI_ARCHITECTURE.md`](./AI_ARCHITECTURE.md) |
| Knowledge Graph | ~10% | modeled; no tables yet → [`KNOWLEDGE_GRAPH.md`](./KNOWLEDGE_GRAPH.md) |
| Flutter mobile | 0% | not started → [`MOBILE_ARCHITECTURE.md`](./MOBILE_ARCHITECTURE.md) |

## Horizons (from `CLAUDE.md` §87)

| Horizon | Focus | Status |
|---|---|---|
| **Now** | Pilot-ready SMS core + Teacher-AI question papers (HITL) + grounded eval assist | 🟡 in progress |
| **Next** | Knowledge Graph schema · Concept Cards | 🟡 Batch 16 document ingest shipped |
| **Then** | AI Tutor (mistake-recovery) → voice; Concept Cards + Content Review Queue | 🔧 template tutor shipped |
| **Later** | Parent/Student copilots, adaptive learning, learning + behaviour analytics | ⬜ |
| **Platform** | Integrations, workflow automation, tool-using agents on the gateway | ⬜ |
| **Future** | Marketplace · plugins · MCP · agent-to-agent (strict tenant/RBAC/metering/audit) | 🔭 |

## Immediate engineering sequence (updated 2026-07-11)

1. ~~**Wire `RagService` into question-paper generation**~~ — ✅ Batch 12 (`assessment_grounding.ground_for_pack`).
2. ~~**Rubric-per-criterion + LLM subjective evaluation**~~ — ✅ Batch 13 (`evaluation_engine` + `answer_sheet_eval_service` wiring).
3. ~~**Pack-grounded evaluation marking**~~ — ✅ Batch 14 (`ground_for_evaluation` + eval UI rubric display).
4. **AI Teacher Copilot enhancements** — ✅ Batch 15 (`teacher_copilot_service`, grounded lesson plans, QP review, feedback draft).
5. ~~**Document Intelligence ingestion**~~ — ✅ Batch 16 (`document_intelligence_service`, pack document ingest API, RAG document chunks).
6. **`ConceptCard` first-class table** — tutor grounding + Content Review Queue.
7. **Knowledge Graph schema** — curriculum spine first (`Curriculum→Subject→Chapter→Topic→Concept`).
8. **Curriculum management UI.**
9. **Flutter mobile foundation** — once shared API/RBAC/design contracts are stable.
10. **Incremental** — lint → zero (then flip CI blocking); Azure Blob; real notification delivery; backups/DR; CD.

## Scalability roadmap (introduce when metrics justify — `CLAUDE.md` §88)

Shared-DB multi-tenant (`school_id` everywhere) → read replicas → partition/shard hot tables → service
extraction at a measured need → more Arq workers → semantic caching + smaller-model routing → multi-region
for residency. Never preemptively.

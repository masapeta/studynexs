# StudyNexs — Roadmap

> Milestones and sequencing. **Canonical policy:** [`/CLAUDE.md`](../CLAUDE.md) §87–§88. **Live
> state:** [`STATUS.md`](./STATUS.md) and [`AGENT_HANDOVER.md`](./AGENT_HANDOVER.md) §8. **Product
> detail:** [`PRODUCT.md`](./PRODUCT.md). This file is the engineering-facing milestone view; it
> never overrides the constitution.
>
> Rule: **one thin, real, production-grade slice at a time** (`DECISION_LOG` D3). Build platform
> capabilities before isolated features; don't front-run later layers with speculative complexity.

## The four intelligence pillars (progress — engineering estimate)

| Pillar | Progress | State |
|---|---|---|
| Curriculum Intelligence | ~40% | CurriculumPack model + versioning + RAG retrieval exist; ingestion + Knowledge Graph pending → [`CURRICULUM_INTELLIGENCE.md`](./CURRICULUM_INTELLIGENCE.md) |
| Assessment Intelligence | ~30% | QP generation + answer-sheet eval + HITL exist; not pack-grounded; rubric-per-criterion + LLM subjective pending → [`ASSESSMENT_INTELLIGENCE.md`](./ASSESSMENT_INTELLIGENCE.md) |
| Learning Intelligence | ~15% | mastery compute + template tutor; adaptive + analytics pending |
| School Operations Intelligence | ~60% | students/staff/fees/attendance/exams/finance built |
| Shared AI Platform | ~60% | gateway + metering + credits + embeddings + vector store + RAG foundation → [`AI_ARCHITECTURE.md`](./AI_ARCHITECTURE.md) |
| Knowledge Graph | ~10% | modeled; no tables yet → [`KNOWLEDGE_GRAPH.md`](./KNOWLEDGE_GRAPH.md) |
| Flutter mobile | 0% | not started → [`MOBILE_ARCHITECTURE.md`](./MOBILE_ARCHITECTURE.md) |

## Horizons (from `CLAUDE.md` §87)

| Horizon | Focus | Status |
|---|---|---|
| **Now** | Pilot-ready SMS core + Teacher-AI question papers (HITL) | 🟡 in progress |
| **Next** | CurriculumPack grounding + answer-sheet evaluation + mastery; **ground QP generation in RAG** | 🟡 foundation built, wiring pending |
| **Then** | AI Tutor (mistake-recovery) → voice; Concept Cards + Content Review Queue | 🔧 template tutor shipped |
| **Later** | Parent/Student copilots, adaptive learning, learning + behaviour analytics | ⬜ |
| **Platform** | Integrations, workflow automation, tool-using agents on the gateway | ⬜ |
| **Future** | Marketplace · plugins · MCP · agent-to-agent (strict tenant/RBAC/metering/audit) | 🔭 |

## Immediate engineering sequence (owner-revised 2026-07-10)

1. **Wire `RagService` into question-paper generation** — grounded, cited Assessment Intelligence; exercises the whole shared platform end-to-end. *(next batch)*
2. **Document Intelligence ingestion** — one OCR/parse/chunk/embed/index/version pipeline (`CLAUDE.md` §38.1) feeding RAG + the graph.
3. **`ConceptCard` first-class table** — tutor grounding + Content Review Queue.
4. **Knowledge Graph schema** — curriculum spine first (`Curriculum→Subject→Chapter→Topic→Concept`).
5. **Curriculum management UI.**
6. **Assessment Intelligence hardening (§40)** — rubric-per-criterion scoring, LLM subjective eval, audited marks, shared engines.
7. **Flutter mobile foundation** — once shared API/RBAC/design contracts are stable.
8. **Incremental** — lint → zero (then flip CI blocking); STATUS/README refresh; Azure Blob; real notification delivery; backups/DR; CD.

## Scalability roadmap (introduce when metrics justify — `CLAUDE.md` §88)

Shared-DB multi-tenant (`school_id` everywhere) → read replicas → partition/shard hot tables → service
extraction at a measured need → more Arq workers → semantic caching + smaller-model routing → multi-region
for residency. Never preemptively.

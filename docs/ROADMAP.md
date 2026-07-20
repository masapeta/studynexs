# StudyNexs — Roadmap

> Milestones and sequencing. **Canonical policy:** [`/CLAUDE.md`](../CLAUDE.md) §87–§88. **Live
> state:** [`STATUS.md`](./STATUS.md) and [`AGENT_HANDOVER.md`](./AGENT_HANDOVER.md). **Product
> detail:** [`PRODUCT.md`](./PRODUCT.md). **Pilot execution:** [`BACKLOG.md`](./BACKLOG.md) Gate 1–3,
> [`TRACK_AB_EXECUTION.md`](./TRACK_AB_EXECUTION.md), [`pilot/GATE1_EXECUTION.md`](./pilot/GATE1_EXECUTION.md).
>
> Rule: **one thin, real, production-grade slice at a time** (`DECISION_LOG` D3).

---

## Business milestones (primary sequence)

Engineering batches build capability. **Business milestones** decide when customers can experience it.

```
Engineering Complete     ← Batches 1–28 shipped (architecture v2.6)
        ↓
Gate 1A — Demo Online    ← HTTPS, login, demo data, AI, smokes (IN PROGRESS)
        ↓
Gate 1B — Demo Reliable  ← fallbacks, UX, teacher/parent flows, reliability targets
        ↓
Gate 1 EXIT              ← principal demo + no critical issues → STOP polishing
        ↓
Pilot Ready              ← Gate 2
        ↓
Pilot Running → Pilot Validated → Production Ready (Gate 3)
```

**Current focus:** **Batch 29 — Infrastructure Readiness**, then **Gate 1A — Demo Online** (HTTPS deploy blocked on credentials). **Batch 30 (Learning Analytics) deferred** until Gate 1 exit.

Principal's sequence: **See → Trust → Pilot → Buy → Use → Analytics** — not Build → Build → Analytics.

---

## Intelligence pillars (progress — 2026-07-15)

| Pillar | Progress | State |
|---|---|---|
| Curriculum Intelligence | ~75% | Pack lifecycle, RAG, document ingest, ConceptCard, content review, curriculum UI, KG spine ✅ |
| Assessment Intelligence | ~70% | Grounded QP, rubric eval, pack-grounded marking, eval UI ✅ |
| Learning Intelligence | ~45% | Mastery engine, Student + Parent Copilot, template tutor + grounded ask ✅; analytics deferred |
| School Operations Intelligence | ~60% | Students, staff, fees, attendance, exams, finance built |
| Shared AI Platform | ~80% | Gateway, metering, credits, embeddings, vector store, RAG hybrid + re-rank ✅ |
| Knowledge Graph | ~60% | Spine, concept cards, question links, weak-concept edges, graph queries ✅ |
| Flutter mobile | 0% | PWA for pilot; native deferred → [`MOBILE_ARCHITECTURE.md`](./MOBILE_ARCHITECTURE.md) |

---

## Engineering batches completed (reference)

| Batches | Focus |
|---------|-------|
| 1–11 | Foundation, tenant isolation, AI platform |
| 12–14 | Grounded QP, rubric eval, pack-grounded marking |
| 15 | Teacher Copilot |
| 16 | Document Intelligence |
| 17–23 | Knowledge Graph, ConceptCard, content review, curriculum UI, weak concepts, graph queries |
| 24 | RAG hybrid + re-rank |
| 25–26 | Student Copilot API + UI |
| 27–28 | Parent Copilot API + UI |
| — | Engineering OS validation standard (docs commit `45ed42a`) |

**Deferred:** Batch 30 Learning Analytics — until Demo Ready exit.

**In progress:** Batch 29 Infrastructure Readiness — reserved API hosts, runtime tenant, Dockerfile `[rag]`, deployment docs (`URL_ARCHITECTURE.md`, `DEPLOYMENT_ARCHITECTURE.md`).

---

## Gate 1 — Demo Ready (active)

Split into **1A Demo Online** and **1B Demo Reliable**. Detail: [`pilot/GATE1_EXECUTION.md`](./pilot/GATE1_EXECUTION.md).

| Sub-gate | Success |
|----------|---------|
| **1A** | HTTPS URL sendable — login, demo data, AI works, smokes 100% |
| **1B** | Demo Reliability Targets met — fallbacks, polish, teacher/parent flows |
| **Exit** | Principal demo done, no critical issues → **stop**, move to Gate 2 |

**Reliability targets:** AI ≥95%, FCP <2s, QP <20s, fallback coverage 100%, critical errors 0, smokes 100%.

---

## Horizons (product — updated)

| Horizon | Focus | Status |
|---|---|---|
| **Now** | Gate 1A Demo Online — HTTPS deploy | 🟡 blocked on credentials |
| **Next** | Gate 1B Demo Reliable → Gate 1 exit (principal demo) | ⬜ |
| **Then** | Gate 2 controlled pilot | ⬜ after Gate 1 exit |
| **Later** | Batch 30 analytics (from pilot feedback) | ⬜ deferred |
| **Platform** | Integrations, workflow automation, tool-using agents | ⬜ |
| **Future** | Marketplace · plugins · MCP | 🔭 |

---

## Scalability roadmap (introduce when metrics justify — `CLAUDE.md` §88)

Shared-DB multi-tenant → read replicas → partition hot tables → service extraction → more Arq workers → semantic caching → multi-region. Never preemptively.

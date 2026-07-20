# Platform Status — Engineering Dashboard

> **Master dashboard** for StudyNexs platform engineering. Machine-readable data:
> [`docs/engineering/`](./engineering/) (`platform.json`, `modules.json`, `roadmap.json`) — powers
> **Dashboard → Platform → Engineering**. Canonical policy: [`/CLAUDE.md`](../CLAUDE.md). Session
> detail: [`AGENT_HANDOVER.md`](./AGENT_HANDOVER.md).

## Source of truth

This dashboard **summarizes** the current platform. It is a navigation aid, not an oracle.

**If documentation and implementation differ, the implementation is authoritative.** Verify with
code, tests, and runtime behavior — then update this dashboard and `docs/engineering/*.json`.

Documentation must be updated whenever implementation changes (end of every engineering batch).

---

## Architecture version

| Field | Value |
|-------|-------|
| **Architecture version** | **2.6** |
| **Last updated** | 2026-07-15 |
| **Last engineering batch** | 28 (Parent Copilot UI) |
| **Business milestone** | **Gate 1A — Demo Online** (after Batch 29) |
| **Current batch** | **29 — Infrastructure Readiness** (in progress) |
| **Branch** | `develop` |
| **Commit** | `45ed42a` (pushed) |

---

## Next milestone

| Field | Value |
|-------|-------|
| **Focus** | **Batch 29 — Infrastructure Readiness**, then **Gate 1A** |
| **1A success** | HTTPS · login · demo data · AI works · smokes 100% |
| **1B next** | Demo Reliable — targets in `GATE1_EXECUTION.md` |
| **Exit** | Principal demo + no critical issues → stop polishing |
| **Blocked** | HTTPS deploy — cloud credentials |
| **Detail** | [`pilot/GATE1_EXECUTION.md`](./pilot/GATE1_EXECUTION.md) |

---

## Snapshot

| Signal | Status | Verified |
|--------|--------|----------|
| Tests (`apps/api/tests/`) | 340 passed, 2 skipped, 0 errors | Verified 2026-07-15 (isolated full suite) |
| Parent Copilot | ✅ Batches 27–28 | Tests + build passing |
| Student Copilot | ✅ Batches 25–26 | Tests + build passing |
| RAG hybrid + re-rank | ✅ Batch 24 | Tests passing |
| Graph queries for copilots | ✅ Batch 23 | Tests passing |
| Student → weak Concept links | ✅ Batch 22 | Tests passing |
| Curriculum management UI | ✅ Batch 21 | Build passing |
| Content Review Queue | ✅ Batch 20 | Tests passing |
| Question → Concept links | ✅ Batch 19 | Tests passing |
| ConceptCard (tutor grounding) | ✅ Batch 18 | Tests passing |
| Knowledge Graph (spine + links) | ✅ Batches 17–23 | Tests passing |
| LLM gateway | ✅ live | Tests passing |
| Embeddings | ✅ OpenAI + stub | Tests passing |
| Vector DB | ✅ Qdrant | Tests passing |
| RAG (core) | ✅ index/retrieve/citations | Tests passing |
| Assessment Intelligence | ✅ Batch 14 | Tests passing |
| Teacher Copilot | ✅ Batch 15 | Tests passing |
| Document Intelligence | ✅ Batch 16 | Tests passing |

**Verified legend:** `tests_passing` · `integration_pending` · `partial` · `not_started`

---

## Capability matrix

| Capability | Status | Verified | Batch |
|------------|--------|----------|-------|
| Student Copilot | ✅ | Tests passing | 25–26 |
| Parent Copilot | ✅ | Tests passing | 27–28 |
| RAG hybrid search + re-ranking | ✅ | Tests passing | 24 |
| Graph queries for copilots | ✅ | Tests passing | 23 |
| Student → weak Concept links | ✅ | Tests passing | 22 |
| Curriculum management UI | ✅ | Build passing | 21 |
| Content Review Queue | ✅ | Tests passing | 20 |
| Question → Concept links | ✅ | Tests passing | 19 |
| ConceptCard | ✅ | Tests passing | 18 |
| Knowledge Graph spine | ✅ | Tests passing | 17 |
| Document Intelligence | ✅ | Tests passing | 16 |
| Teacher Copilot | ✅ | Tests passing | 15 |
| Pack-grounded evaluation | ✅ | Tests passing | 14 |
| Grounded QP generation | ✅ | Tests passing | 12 |
| RAG index / retrieve / citations | ✅ | Tests passing | 9–12 |
| Mastery engine | ✅ | Tests passing | pre-12 |
| Authorization / tenant isolation | ✅ | Tests passing | 1–6 |

Full matrix: [`engineering/platform.json`](./engineering/platform.json)

---

## Module index (status + verification + dependencies)

| Module | Status | Verified | Depends on (satisfied) | Pending |
|--------|--------|----------|------------------------|---------|
| RAG | ✅ | Tests passing | Embeddings, Vector Store, Knowledge Graph | — |
| Knowledge Graph | ✅ | Tests passing | Curriculum Intelligence | — |
| Curriculum Intelligence | ✅ | Tests passing | RAG, Embeddings, File Processing | — |
| Teacher Copilot | ✅ | Tests passing | Embeddings, RAG, Curriculum, AI Platform | — |
| Assessment Intelligence | ✅ | Tests passing | RAG, AI Platform | — |
| Student Copilot | ✅ | Tests passing | Mastery, RAG, Knowledge Graph, AI Platform | — |
| Parent Copilot | ✅ | Tests passing | Mastery, RAG, Knowledge Graph, Authorization | — |
| File Processing | ✅ | Tests passing | AI Platform, OCR Pipeline, RAG | — |
| Mastery Engine | ✅ | Tests passing | Authorization | — |
| AI Platform | ✅ | Tests passing | — | — |

Module detail: [`docs/modules/`](./modules/) · structured deps: [`engineering/modules.json`](./engineering/modules.json)

---

## Maintenance (every engineering batch)

Follow [`engineering/005-development-lifecycle.md`](./engineering/005-development-lifecycle.md). Validation standard: [`engineering/004-validation-and-testing.md`](./engineering/004-validation-and-testing.md).

1. Implement + validate per [`004-validation-and-testing.md`](./engineering/004-validation-and-testing.md)
2. Update `docs/engineering/platform.json`, `modules.json`, `roadmap.json`
3. Update this file + affected `docs/modules/*.md`
4. Update `STATUS.md`, `CHANGELOG.md`, `ROADMAP.md`, `AGENT_HANDOVER.md`
5. Bump `architecture_version` when platform contracts change materially

**Do not** rewrite core engineering standards (`docs/engineering/001`–`005`) unless repeated sessions prove a gap — grow module docs and update this dashboard instead. Policy: [`engineering/ONBOARDING.md`](./engineering/ONBOARDING.md).

Cursor rule: [`.cursor/rules/engineering-dashboard.mdc`](../.cursor/rules/engineering-dashboard.mdc)

In-app: **Dashboard → Platform → Engineering** (`/dashboard/platform/engineering`, admin only)

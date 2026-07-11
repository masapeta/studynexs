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
| **Architecture version** | **1.4** |
| **Last updated** | 2026-07-11 |
| **Last engineering batch** | 14 (pack-grounded eval + eval UI) |
| **Branch** | `develop` |
| **Commit** | `a2286bf` (refresh via API runtime or `git rev-parse`) |

---

## Next milestone

| Field | Value |
|-------|-------|
| **Next batch** | **15 — AI Teacher Copilot** |
| **Summary** | Grounded, cited assistance for lesson planning, QP review, and feedback drafting |
| **Estimated** | ~6 days |
| **Dependencies blocking** | None |
| **Dependencies satisfied** | Embeddings · RAG · Curriculum Intelligence · AI Platform |
| **Optional** | Knowledge Graph (enhances, not required for MVP) |

---

## Snapshot

| Signal | Status | Verified |
|--------|--------|----------|
| Tests (`apps/api/tests/`) | 292 passed, 1 skipped | Tests passing |
| LLM gateway | ✅ live | Tests passing |
| Embeddings | ✅ OpenAI + stub | Tests passing |
| Vector DB | ✅ Qdrant | Tests passing |
| RAG (core) | ✅ index/retrieve/citations | Tests passing |
| RAG (advanced) | 🟡 hybrid + re-rank pending | Integration pending |
| Assessment Intelligence | ✅ Batch 14 | Tests passing |
| Curriculum Intelligence | 🟡 pack + RAG | Tests passing (ingestion pending) |
| Teacher Copilot | 🟡 Batch 15 planned | Not started |
| Knowledge Graph | 🔴 planned | Not started |

**Verified legend:** `tests_passing` · `integration_pending` · `partial` · `not_started`

---

## Capability matrix

| Capability | Status | Verified | Batch |
|------------|--------|----------|-------|
| LLM provider abstraction | ✅ | Tests passing | 9 |
| Embeddings (OpenAI + stub) | ✅ | Tests passing | 9–11 |
| Vector store | ✅ | Tests passing | 9–11 |
| RAG index / retrieve / citations | ✅ | Tests passing | 9–12 |
| RAG hybrid search + re-ranking | 🟡 | Integration pending | 15+ |
| Grounded QP generation | ✅ | Tests passing | 12 |
| Rubric-per-criterion evaluation | ✅ | Tests passing | 13 |
| Pack-grounded evaluation marking | ✅ | Tests passing | 14 |
| Eval UI rubric breakdown | ✅ | Partial (no UI tests) | 14 |
| CurriculumPack + approval | ✅ | Tests passing | pre-12 |
| Teacher Copilot | 🟡 | Not started | 15 |
| Document Intelligence | 🔴 | Not started | 16 |
| Knowledge Graph | 🔴 | Not started | 17 |
| Mastery engine | ✅ | Tests passing | pre-12 |
| Authorization / tenant isolation | ✅ | Tests passing | 1–6 |

Full matrix: [`engineering/platform.json`](./engineering/platform.json)

---

## Module index (status + verification + dependencies)

| Module | Status | Verified | Depends on (satisfied) | Pending |
|--------|--------|----------|------------------------|---------|
| AI Platform | ✅ | Tests passing | — | — |
| Embeddings | ✅ | Tests passing | AI Platform | — |
| Vector Store | ✅ | Tests passing | AI Platform | — |
| RAG | 🟡 | Integration pending | Embeddings, Vector Store | — |
| Assessment Intelligence | ✅ | Tests passing | RAG, AI Platform | — |
| Curriculum Intelligence | 🟡 | Tests passing | RAG, Embeddings | File Processing |
| Teacher Copilot | 🟡 | Not started | Embeddings, RAG, Curriculum, AI Platform | Knowledge Graph |
| Student Copilot | 🔴 | Not started | Mastery, AI Platform | Knowledge Graph, RAG |
| Parent Copilot | 🔴 | Not started | Mastery, Authorization | Student Copilot |
| Knowledge Graph | 🔴 | Not started | Curriculum Intelligence | File Processing |
| File Processing | 🔴 | Not started | AI Platform | OCR Pipeline (unified) |
| OCR Pipeline | 🟡 | Partial | AI Platform | File Processing |
| Mastery Engine | ✅ | Tests passing | Authorization | — |
| Authorization | ✅ | Tests passing | — | — |

Module detail: [`docs/modules/`](./modules/) · structured deps: [`engineering/modules.json`](./engineering/modules.json)

---

## Maintenance (every engineering batch)

1. Implement + validate (tests are the verification source)
2. Update `docs/engineering/platform.json`, `modules.json`, `roadmap.json`
3. Update this file + affected `docs/modules/*.md`
4. Update `STATUS.md`, `CHANGELOG.md`, `ROADMAP.md`, `AGENT_HANDOVER.md`
5. Bump `architecture_version` when platform contracts change materially

Cursor rule: [`.cursor/rules/engineering-dashboard.mdc`](../.cursor/rules/engineering-dashboard.mdc)

In-app: **Dashboard → Platform → Engineering** (`/dashboard/platform/engineering`, admin only)

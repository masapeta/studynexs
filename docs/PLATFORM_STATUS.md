# Platform Status — Engineering Dashboard

> **Master dashboard** for StudyNexs platform engineering. Machine-readable data:
> [`docs/engineering/`](./engineering/) powers **Dashboard → Platform → Engineering**.
> Canonical execution plan: [`product/PRODUCT_EXECUTION_PLAN.md`](./product/PRODUCT_EXECUTION_PLAN.md).

**Last updated:** 2026-07-23

---

## Source of truth

This dashboard summarizes current platform state. It is a navigation aid, not an oracle.

If documentation and implementation differ, verify with code, tests, and runtime behavior, then update this dashboard and `docs/engineering/*.json`.

---

## Current product state

| Field | Value |
|---|---|
| Architecture version | 2.7 |
| Last accepted product batch | **Batch 1 — Curriculum Intelligence** |
| Release | **0.1 — Accepted / Frozen** |
| Commit | `63a5584` — `feat(curriculum): complete Batch 1 intelligence closure` |
| Current authorized batch | **Batch 2 — Academic Onboarding** |
| Batch 2 status | AUTHORIZED / active |
| Branch | `develop` |

---

## Batch 1 acceptance snapshot

| Signal | Status | Evidence |
|---|---:|---|
| Completion report | Accepted | [`product/BATCH_01_COMPLETION_REPORT.md`](./product/BATCH_01_COMPLETION_REPORT.md) |
| API readiness | PASS | DB + Redis healthy |
| Alembic | PASS | `a1b2c3d4e5f7 (head)` |
| API import | PASS | `import app.main` |
| Focused API tests | PASS | 39 passed |
| Web production build | PASS | `npm run build` |
| Browser onboarding review | PASS | tenant reference + single pack-detail GET + 0 disallowed console errors |
| Browser smoke | PASS | 20 checks + 0 disallowed console errors |
| Live curriculum-intelligence rehearsal | PASS | teacher draft → principal approval → KG/RAG → cited lesson plan + QP |
| Supporting-material document ingest | PASS | indexed 1 chunk, then self-cleaned |
| Learning loop smoke | PASS | 20 WORKS, 2 PARTIAL, 0 FAIL |

---

## Current milestone

| Field | Value |
|---|---|
| Focus | **Batch 2 — Academic Onboarding** |
| Goal | Curriculum-first onboarding that culminates in **Academic Intelligence Ready** |
| Must reuse | `CurriculumPack`, Document Intelligence, extraction service, approval workflow, KG, RAG |
| Must not build | Full textbook warehousing, parallel ingestion service, second curriculum engine, Batch 3 assessment automation |
| Blocked by | None — implementation authorized by ARM |
| Detail | [`product/CURRENT_BATCH.md`](./product/CURRENT_BATCH.md) |

---

## Capability matrix

| Capability | Status | Verified |
|---|---|---|
| Curriculum Intelligence | Accepted / Frozen | Batch 1 report + runtime evidence |
| Academic Onboarding | Authorized | Implementation active under Batch 2 |
| RAG | Complete | Tests + live pack citation evidence |
| Knowledge Graph | Complete | KG ready in live rehearsal |
| Document Intelligence | Complete for supporting-material ingest | Live ingest smoke |
| Teacher Copilot | Complete for grounded lesson-plan evidence | Live rehearsal |
| Assessment Intelligence | Existing foundation | Batch 3 deferred |
| Student Copilot / Tutor | Complete for concept-card-grounded reference loop | Learning-loop smoke |
| Parent Copilot | Complete for same-topic reference loop | Learning-loop smoke |
| Authorization / tenant isolation | Complete for Batch 1 scope | Tests + browser tenant tracker |

---

## Maintenance rule

At the end of every accepted product batch, update:

1. `docs/product/PRODUCT_EXECUTION_PLAN.md`
2. `docs/ROADMAP.md`
3. `docs/STATUS.md`
4. `docs/decisions/DECISION_LOG.md`
5. `docs/engineering/roadmap.json`
6. `docs/engineering/platform.json`
7. the batch completion report / release-history artifact

During an active batch, do not create intermediate governance documents unless ARM explicitly asks. Update governance again when the batch is complete.

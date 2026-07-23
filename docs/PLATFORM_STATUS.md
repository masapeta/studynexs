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
| Last accepted product batch | **Batch 2 — Academic Onboarding** |
| Release | **0.2 — Accepted / Frozen** |
| Commit | `469c0f8` — `feat(onboarding): complete Batch 2 academic onboarding proof` |
| Current authorized batch | **None** |
| Batch 3 status | Not authorized |
| Branch | `develop` |

---

## Batch 2 acceptance snapshot

| Signal | Status | Evidence |
|---|---:|---|
| Completion report | Accepted | [`product/BATCH_02_COMPLETION_REPORT.md`](./product/BATCH_02_COMPLETION_REPORT.md) |
| API readiness | PASS | DB + Redis healthy |
| Alembic | PASS | `a1b2c3d4e5f7 (head)` |
| API import | PASS | `import app.main` |
| Focused API tests | PASS | 15 onboarding + 17 tutor/parent/content-review tests |
| Web production build | PASS | `npm run build` |
| Runtime proof | PASS | Uploaded source → approved pack → KG/RAG → downstream AI loop |
| Evidence ledger | PASS | Tenant, pack, vector count, grounding, citation/source evidence |
| Answer-sheet vision path | PASS | Uploaded PNG + `answer_sheet_vision` LLM call |
| Same-pack downstream proof | PASS | Lesson plan, materials, QP, assessment, tutor, student, parent |

---

## Current milestone

| Field | Value |
|---|---|
| Focus | **No active implementation batch** |
| Latest milestone | **Release 0.2 — Batch 2 Academic Onboarding** |
| Status | Accepted / Frozen |
| Next batch | Not authorized |
| Blocked by | ARM must explicitly authorize the next execution batch |
| Detail | [`product/BATCH_02_COMPLETION_REPORT.md`](./product/BATCH_02_COMPLETION_REPORT.md) |

---

## Capability matrix

| Capability | Status | Verified |
|---|---|---|
| Curriculum Intelligence | Accepted / Frozen | Batch 1 report + runtime evidence |
| Academic Onboarding | Accepted / Frozen | Batch 2 report + runtime evidence ledger |
| RAG | Complete | Tests + live pack citation evidence |
| Knowledge Graph | Complete | KG ready in runtime proof |
| Document Intelligence | Complete for onboarding/source ingest and supporting-material ingest | Runtime proof + ingest smoke |
| Teacher Copilot | Complete for grounded lesson-plan evidence | Runtime proof |
| Assessment Intelligence | Existing foundation; deeper Batch 3 work deferred | Runtime proof covered approved QP → evaluation → marks/mastery |
| Student Copilot / Tutor | Complete for concept-card-grounded reference loop | Runtime proof |
| Parent Copilot | Complete for same-pack parent briefing/ask loop | Runtime proof |
| Authorization / tenant isolation | Complete for Batch 2 scope | Tests + same-pack tenant evidence |

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

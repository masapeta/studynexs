# StudyNexs — Current Status

> **Owner:** Avinash Reddy Masapeta (ARM)
> **As of:** 2026-07-23
> **Canonical execution plan:** [`product/PRODUCT_EXECUTION_PLAN.md`](./product/PRODUCT_EXECUTION_PLAN.md)

---

## Executive status

**Batch 1 — Curriculum Intelligence is accepted and frozen.**

The platform now has the required curriculum-intelligence foundation:

- curriculum ownership;
- approval governance;
- tenant-scoped `CurriculumPack`;
- KG/RAG grounding;
- same-pack grounding across multiple AI capabilities;
- teacher-owned workflow;
- runtime validation;
- documented limitations.

Batch 1 should not be modified except for production defects, security fixes, or critical regressions.

---

## Current execution state

| Area | Status |
|---|---|
| Current release | **Release 0.1 — Batch 1 Curriculum Intelligence** |
| Release status | **Accepted / Frozen** |
| Latest accepted commit | `63a5584` — `feat(curriculum): complete Batch 1 intelligence closure` |
| Completion report | [`product/BATCH_01_COMPLETION_REPORT.md`](./product/BATCH_01_COMPLETION_REPORT.md) |
| Current authorized release | **Release 0.2 — Batch 2 Academic Onboarding** |
| Batch 2 implementation | **Authorized / active** |

---

## Batch 1 validation evidence

| Gate | Result |
|---|---:|
| API readiness | PASS — DB + Redis healthy |
| Alembic current/head | PASS — `a1b2c3d4e5f7 (head)` |
| API import | PASS |
| Focused API tests | PASS — 39 passed |
| Web production build + TypeScript | PASS |
| Browser onboarding review E2E | PASS |
| Browser smoke E2E | PASS — 20 checks |
| Live curriculum-intelligence rehearsal | PASS |
| Supporting-material document ingest | PASS |
| Reference learning loop | PASS — 20 WORKS, 2 PARTIAL, 0 FAIL |

---

## Current authorized batch

**Batch 2 — Academic Onboarding**

Objective: deliver the curriculum-first onboarding experience that teaches StudyNexs a school's curriculum and culminates in **Academic Intelligence Ready**.

Batch 2 must reuse:

- `CurriculumPack`;
- Document Intelligence;
- existing extraction service;
- approval workflow;
- KG;
- RAG;
- existing downstream AI grounding.

Batch 2 must not implement:

- a second curriculum engine;
- parallel ingestion services;
- full textbook warehousing;
- complete OCR automation;
- Batch 3 assessment automation.

Implementation is authorized by ARM as of 2026-07-23.

---

## Known repository state

The Batch 1 commit is isolated. The working tree may still contain unrelated uncommitted dashboard/briefing/status/showcase artifacts from earlier sessions; those are not part of Batch 1 acceptance.

Global repo lint remains a known technical-debt area. Batch 1 validation used focused tests, web build, browser smokes, runtime smokes, and scoped fatal lint checks.

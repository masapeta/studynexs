# StudyNexs — Roadmap

> Milestones and sequencing. Current execution detail lives in
> [`product/PRODUCT_EXECUTION_PLAN.md`](./product/PRODUCT_EXECUTION_PLAN.md).

**Last updated:** 2026-07-23

---

## Product release history

| Release | Batch | Capability | Status |
|---|---:|---|---|
| **Release 0.1** | **Batch 1** | Curriculum Intelligence | **Accepted / Frozen** |
| **Release 0.2** | **Batch 2** | Academic Onboarding | **AUTHORIZED** |
| **Release 0.3** | Batch 3 | Assessment Intelligence | Deferred |
| **Release 1.0** | Pilot Ready | Principal-demo-to-pilot readiness | Future |

Release history artifact: [`product/RELEASE_HISTORY.md`](./product/RELEASE_HISTORY.md).

---

## Current product sequence

```text
Release 0.1 — Batch 1 Curriculum Intelligence
        ✓ Accepted / Frozen
        ↓
Release 0.2 — Batch 2 Academic Onboarding
        AUTHORIZED — implementation active
        ↓
Release 0.3 — Assessment Intelligence
        Deferred
        ↓
Release 1.0 — Pilot Ready
        Future
```

---

## Current focus

**Batch 2 — Academic Onboarding**

Purpose: create the first curriculum-first experience a school has with StudyNexs.

The onboarding journey must culminate in **Academic Intelligence Ready** by reusing:

- `CurriculumPack`
- Document Intelligence
- existing extraction service
- approval workflow
- Knowledge Graph
- RAG
- downstream AI grounding

Do not build a parallel curriculum engine or full textbook warehouse.

---

## Frozen foundation

**Batch 1 — Curriculum Intelligence** is accepted and frozen.

No further Batch 1 changes are authorized except production defects, security fixes, or critical regressions.

Accepted evidence:

- [`product/BATCH_01_COMPLETION_REPORT.md`](./product/BATCH_01_COMPLETION_REPORT.md)
- commit `63a5584` — `feat(curriculum): complete Batch 1 intelligence closure`

---

## Roadmap boundaries

### Now

Implement Batch 2 — Academic Onboarding.

### Next

Complete Batch 2 validation and produce the completion report after implementation is finished.

### Later

Batch 3 — Assessment Intelligence:

- exam creation from approved packs;
- answer-sheet upload/OCR/evaluation;
- teacher approval;
- marks/gradebook/mastery/report-card propagation.

### Future

Pilot-ready release:

- stable demo environment;
- principal demo journey;
- school onboarding;
- operational reliability;
- support/rollback/monitoring readiness.

---

## Scaling principle

Shared-DB multi-tenant architecture remains the active model. Introduce read replicas, partitioning, service extraction, additional workers, caching, and multi-region only when real usage metrics justify them.

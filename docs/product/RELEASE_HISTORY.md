# StudyNexs Release History

> Product execution releases. Each release maps to an accepted batch or future milestone.

**Last updated:** 2026-07-23

---

## Release table

| Release | Batch | Name | Status | Evidence |
|---|---:|---|---|---|
| **0.1** | **1** | Curriculum Intelligence | **Accepted / Frozen** | [`BATCH_01_COMPLETION_REPORT.md`](./BATCH_01_COMPLETION_REPORT.md) |
| **0.2** | **2** | Academic Onboarding | **AUTHORIZED** | [`CURRENT_BATCH.md`](./CURRENT_BATCH.md) |
| **0.3** | 3 | Assessment Intelligence | Deferred | Not authorized |
| **1.0** | Pilot Ready | Principal-demo-to-pilot readiness | Future | Not authorized |

---

## Release 0.1 — Batch 1 Curriculum Intelligence

**Status:** Accepted / Frozen
**Accepted date:** 2026-07-23
**Commit:** `63a5584` — `feat(curriculum): complete Batch 1 intelligence closure`

### Delivered

- Teacher-owned curriculum drafts.
- Class-incharge/admin approval governance.
- Tenant-scoped `CurriculumPack` lifecycle.
- KG + RAG indexing on approval.
- Same-pack grounding across lesson plans, question papers, tutor, and parent evidence paths.
- Runtime validation and acceptance report.

### Freeze rule

Do not modify Release 0.1 / Batch 1 except for:

- production defects;
- security fixes;
- critical regressions.

---

## Release 0.2 — Batch 2 Academic Onboarding

**Status:** AUTHORIZED, implementation active.

### Goal

Deliver the curriculum-first onboarding experience that teaches StudyNexs a school's curriculum and ends in **Academic Intelligence Ready**.

Completion must prove the newly approved pack is used downstream:

```text
Academic Intelligence Ready
↓
Generate Lesson Plan
↓
Generate Question Paper
↓
Grounding Verified
```

### Required reuse

- `CurriculumPack`
- Document Intelligence
- existing extraction service
- approval workflow
- KG
- RAG
- downstream AI grounding

### Explicit non-goals

- full textbook warehousing;
- second curriculum engine;
- parallel ingestion service;
- complete OCR automation;
- Batch 3 assessment automation.

---

## Release 0.3 — Assessment Intelligence

**Status:** Deferred.

Assessment generation, answer-sheet evaluation, marks, gradebook, mastery, report-card, and remediation loops should be planned only after Release 0.2 is accepted.

---

## Release 1.0 — Pilot Ready

**Status:** Future.

Release 1.0 represents the point where a school can pilot StudyNexs with a stable onboarding, teaching, assessment, parent, and student journey.

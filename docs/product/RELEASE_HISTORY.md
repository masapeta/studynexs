# StudyNexs Release History

> Product execution releases. Each release maps to an accepted batch or future milestone.

**Last updated:** 2026-07-23

---

## Release table

| Release | Batch | Name | Status | Evidence |
|---|---:|---|---|---|
| **0.1** | **1** | Curriculum Intelligence | **Accepted / Frozen** | [`BATCH_01_COMPLETION_REPORT.md`](./BATCH_01_COMPLETION_REPORT.md) |
| **0.2** | **2** | Academic Onboarding | **Accepted / Frozen** | [`BATCH_02_COMPLETION_REPORT.md`](./BATCH_02_COMPLETION_REPORT.md) |
| **0.3** | 3 | Assessment Intelligence | Deferred | Not authorized |
| **1.0** | Pilot Ready | Principal-demo-to-pilot readiness | Future | Not authorized |

---

## Release 0.1 â€” Batch 1 Curriculum Intelligence

**Status:** Accepted / Frozen
**Accepted date:** 2026-07-23
**Commit:** `63a5584` â€” `feat(curriculum): complete Batch 1 intelligence closure`

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

## Release 0.2 â€” Batch 2 Academic Onboarding

**Status:** Accepted / Frozen
**Accepted date:** 2026-07-23
**Commit:** `469c0f8` â€” `feat(onboarding): complete Batch 2 academic onboarding proof`

### Delivered

- Uploaded curriculum source intake.
- AI extraction into draft `CurriculumPack`.
- Teacher/HOD human review and approval governance.
- KG + RAG readiness gate.
- Grounded lesson plan and learning materials from the newly approved pack.
- Grounded question paper from the newly approved pack.
- Answer-sheet upload / vision path exercised.
- AI evaluation suggestions, teacher approval, marks, mastery, student tutor/copilot, and parent copilot verified through the same approved pack.
- Deterministic same-pack evidence ledger.

### Evidence

- [`BATCH_02_COMPLETION_REPORT.md`](./BATCH_02_COMPLETION_REPORT.md)
- Runtime proof pack: `1bdfffc6-933d-4780-9de4-b7d6c92201bb`
- Implementation commit: `469c0f8`

### Freeze rule

Do not modify Release 0.2 / Batch 2 except for:

- production defects;
- security fixes;
- critical regressions.

---

## Release 0.3 â€” Assessment Intelligence

**Status:** Deferred / Not authorized.

Batch 3 is not authorized. It should be planned only after ARM explicitly selects and authorizes the next execution batch.

---

## Release 1.0 â€” Pilot Ready

**Status:** Future.

Release 1.0 represents the point where a school can pilot StudyNexs with a stable onboarding, teaching, assessment, parent, and student journey.

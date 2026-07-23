# StudyNexs â€” Current Status

> **Owner:** Avinash Reddy Masapeta (ARM)
> **As of:** 2026-07-23
> **Canonical execution plan:** [`product/PRODUCT_EXECUTION_PLAN.md`](./product/PRODUCT_EXECUTION_PLAN.md)

---

## Executive status

**Release 0.2 / Batch 2 â€” Academic Onboarding is accepted and frozen.**

The platform now has the required academic-onboarding foundation:

- uploaded curriculum source intake;
- AI extraction into draft `CurriculumPack`;
- human review and approval governance;
- tenant-scoped `CurriculumPack`;
- KG/RAG readiness;
- Academic Intelligence Ready;
- deterministic same-pack evidence ledger;
- runtime proof across lesson plans, learning materials, question papers, assessment evaluation, mastery, student tutor/copilot, and parent copilot.

Batch 1 and Batch 2 should not be modified except for production defects, security fixes, or critical regressions.

---

## Current execution state

| Area | Status |
|---|---|
| Current release | **Release 0.2 â€” Batch 2 Academic Onboarding** |
| Release status | **Accepted / Frozen** |
| Latest accepted commit | `469c0f8` â€” `feat(onboarding): complete Batch 2 academic onboarding proof` |
| Completion report | [`product/BATCH_02_COMPLETION_REPORT.md`](./product/BATCH_02_COMPLETION_REPORT.md) |
| Previous release | **Release 0.1 â€” Batch 1 Curriculum Intelligence** |
| Previous release status | **Accepted / Frozen** |
| Current authorized release | **None** |
| Batch 3 implementation | **Not authorized** |

---

## Batch 2 validation evidence

| Gate | Result |
|---|---:|
| API readiness | PASS â€” DB + Redis healthy |
| Alembic current/head | PASS â€” `a1b2c3d4e5f7 (head)` |
| API import | PASS |
| Academic Onboarding regression | PASS â€” 15 passed |
| Tutor / Student Copilot / Parent Copilot / Content Review regression | PASS â€” 17 passed |
| Web production build + TypeScript | PASS |
| Runtime proof script lint + compile | PASS |
| Full runtime proof | PASS |
| Evidence ledger | PASS â€” every downstream capability proved tenant `reference`, same pack, vectors, grounding, and source/citation evidence |

Runtime proof artifacts:

| Artifact | ID |
|---|---|
| Curriculum source file | `42ebd493-756e-42db-a885-a350a55e9f58` |
| Approved CurriculumPack | `1bdfffc6-933d-4780-9de4-b7d6c92201bb` |
| Question paper | `b2c8e0bb-0a19-408d-9de1-f51640c29ad1` |
| Exam | `71c0fb96-ecc9-4e77-bb78-ca44ce059bb1` |
| Answer-sheet file | `a1c6a024-a148-41ca-bb1c-f3e03d566cad` |
| Evaluation | `17168b3b-9f1e-4291-b18a-03a2504ed752` |

---

## Current authorization state

No implementation batch is currently authorized.

Batch 3 must not begin until ARM explicitly authorizes the next execution batch.

---

## Known repository state

The Batch 2 implementation commit is isolated. The working tree may still contain unrelated uncommitted dashboard/briefing/status/showcase artifacts from earlier sessions; those are not part of Release 0.2 acceptance.

Global repo lint remains a known technical-debt area. Batch 2 validation used focused tests, web build, runtime proof, evidence ledger, and scoped lint/compile checks.

Known operational limitation: the local runtime proof queues answer-sheet evaluation, waits, and executes the existing evaluation service inline if the queued worker does not finish within the script timeout. Product behavior is validated; production async worker parity should be handled as a separate operational hardening task.

# StudyNexs — Current Status

> **Owner:** Avinash Reddy Masapeta (ARM)
> **As of:** 2026-07-23
> **Canonical execution plan:** [`product/PRODUCT_EXECUTION_PLAN.md`](./product/PRODUCT_EXECUTION_PLAN.md)

---

## Executive status

**Release 0.3 / Batch 3 — School Pilot Experience is accepted and frozen.**

The platform now has the validated first-pilot experience for the two decision-critical school users:

- Principal runtime proof;
- Teacher runtime proof;
- Principal browser walkthrough;
- Teacher browser walkthrough;
- tenant isolation verification;
- same-pack grounding verification for teacher-generated lesson plan and question paper;
- focused evidence recorded in the Batch 3 completion report.

Release 0.1, Release 0.2, and Release 0.3 should not be modified except for production defects, security fixes, or critical regressions.

---

## Current execution state

| Area | Status |
|---|---|
| Current release | **Release 0.3 — Batch 3 School Pilot Experience** |
| Release status | **Accepted / Frozen** |
| Latest accepted commit | `649d835` — `feat(pilot): complete Batch 3 principal teacher proof` |
| Completion report | [`product/BATCH_03_COMPLETION_REPORT.md`](./product/BATCH_03_COMPLETION_REPORT.md) |
| Previous release | **Release 0.2 — Batch 2 Academic Onboarding** |
| Previous release status | **Accepted / Frozen** |
| Current authorized release | **None** |
| Release 0.4 implementation | **Not authorized** |

---

## Batch 3 validation evidence

| Gate | Result |
|---|---:|
| API readiness | PASS — DB + Redis healthy |
| Principal runtime proof | PASS |
| Teacher runtime proof | PASS |
| Principal + Teacher browser walkthrough | PASS — 13 checks |
| Tenant tracking | PASS — tenant `reference` |
| Same-pack grounding | PASS — lesson plan + question paper use pack `1bdfffc6-933d-4780-9de4-b7d6c92201bb` |
| Admin web production build | PASS |
| Reference School smoke | PASS — 32 checks |
| Focused lint/compile checks | PASS |

Runtime proof artifacts:

| Artifact | ID |
|---|---|
| Approved CurriculumPack | `1bdfffc6-933d-4780-9de4-b7d6c92201bb` |
| Final proof lesson plan | `8e245b4e-a5cf-4cff-bfd3-69714cc6c2fc` |
| Final proof question paper | `2f3022d0-187c-4bce-98e1-53dbb0799238` |

---

## Current authorization state

No implementation batch is currently authorized.

Release 0.4 must not begin until ARM explicitly authorizes the next execution batch.

---

## Known repository state

The Batch 3 implementation commit is isolated. The working tree may still contain unrelated uncommitted dashboard/briefing/status/showcase artifacts from earlier sessions; those are not part of Release 0.3 acceptance.

Reference tenant AI credits were exhausted by repeated validation runs; the existing principal emergency override path was used and is now asserted by the Batch 3 proof. For a real pilot, preflight should ensure sufficient AI budget or active principal override.

Global repo lint remains a known technical-debt area. Batch 3 validation used focused tests, web build, browser walkthrough, runtime proof, and scoped lint/compile checks.

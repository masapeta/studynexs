# StudyNexs — Roadmap

> Milestones and sequencing. Current execution detail lives in
> [`product/PRODUCT_EXECUTION_PLAN.md`](./product/PRODUCT_EXECUTION_PLAN.md).

**Last updated:** 2026-07-23

---

## Product release history

| Release | Batch | Capability | Status |
|---|---:|---|---|
| **Release 0.1** | **Batch 1** | Curriculum Intelligence | **Accepted / Frozen** |
| **Release 0.2** | **Batch 2** | Academic Onboarding | **Accepted / Frozen** |
| **Release 0.3** | Batch 3 | Assessment Intelligence | Deferred / Not authorized |
| **Release 1.0** | Pilot Ready | Principal-demo-to-pilot readiness | Future |

Release history artifact: [`product/RELEASE_HISTORY.md`](./product/RELEASE_HISTORY.md).

---

## Product sequence

```text
Release 0.1 — Batch 1 Curriculum Intelligence
        ✓ Accepted / Frozen
        ↓
Release 0.2 — Batch 2 Academic Onboarding
        ✓ Accepted / Frozen
        ↓
Release 0.3 — Assessment Intelligence
        Deferred / Not authorized
        ↓
Release 1.0 — Pilot Ready
        Future
```

---

## Current focus

There is no active implementation batch.

Release 0.2 is frozen. Batch 3 must not begin until ARM explicitly authorizes the next execution batch.

---

## Frozen foundation

### Batch 2 — Academic Onboarding

Batch 2 is accepted and frozen.

Accepted evidence:

- [`product/BATCH_02_COMPLETION_REPORT.md`](./product/BATCH_02_COMPLETION_REPORT.md)
- commit `469c0f8` — `feat(onboarding): complete Batch 2 academic onboarding proof`

### Batch 1 — Curriculum Intelligence

Batch 1 is accepted and frozen.

Accepted evidence:

- [`product/BATCH_01_COMPLETION_REPORT.md`](./product/BATCH_01_COMPLETION_REPORT.md)
- commit `63a5584` — `feat(curriculum): complete Batch 1 intelligence closure`

No further Batch 1 or Batch 2 changes are authorized except production defects, security fixes, or critical regressions.

---

## Roadmap boundaries

### Now

Hold Release 0.2 frozen and review the next execution priority.

### Next

Batch 3 remains unauthorized until ARM explicitly selects the next batch.

### Later

Candidate future work:

- production async evaluation worker parity;
- Assessment Intelligence deepening;
- pilot readiness and deployment hardening;
- controlled Reference School demo polish.

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

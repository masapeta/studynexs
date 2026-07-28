# StudyNexs Product Execution Plan

> **Living document** — update this file when product execution batches are accepted or re-prioritized.
> **Constitutional priority:** [`PRODUCT_EXECUTION_CONSTITUTION.md`](./PRODUCT_EXECUTION_CONSTITUTION.md)

**Last updated:** 2026-07-28
**Current governance state:** Batch 1, Batch 2, and Batch 3 remain accepted and
frozen. Production Safety is accepted and publication-authorized. No
implementation gate is active; Operational Proof is planned and not authorized.

---

## 2026-07-28 stabilization execution override

This current decision supersedes earlier statements that there is no active
batch or that Teacher Evaluation UX-D is the next implementation target. It
does not alter or delete the accepted release history below.

Execution order:

1. Governance-source reconciliation and correction of the July 2026 technical
   audit.
2. **Production Safety Batch** — completed, certified, and publication
   authorized.
3. **Operational Proof** — planned; not authorized.
4. **AEI Activation/Trust** — planned; not authorized.
5. **Topic-ID/mastery spine unification design** — planned design gate; not
   authorized for implementation.
6. **Teacher Evaluation UX-D** — deferred until supported capabilities execute
   with runtime evidence; not authorized.

Later gates do not inherit authorization from the completed Production Safety
Batch. Each requires its own review and explicit ARM authorization.

---

## Release train

| Release | Batch | Capability | Status | Evidence |
|---|---:|---|---|---|
| **Release 0.1** | **Batch 1** | Curriculum Intelligence | **Accepted / Frozen** | [`BATCH_01_COMPLETION_REPORT.md`](./BATCH_01_COMPLETION_REPORT.md) |
| **Release 0.2** | **Batch 2** | Academic Onboarding | **Accepted / Frozen** | [`BATCH_02_COMPLETION_REPORT.md`](./BATCH_02_COMPLETION_REPORT.md) |
| **Release 0.3** | **Batch 3** | School Pilot Experience | **Accepted / Frozen** | [`BATCH_03_COMPLETION_REPORT.md`](./BATCH_03_COMPLETION_REPORT.md) |
| **Release 0.4** | Batch 4 | Student + Parent Pilot Experience | Deferred | Not authorized |
| **Release 0.5** | Batch 5 | Pilot Operations / Assessment Reliability | Future | Not authorized |
| **Release 1.0** | Pilot Ready | Principal-demo-to-pilot readiness | Future | Not authorized |

Batch 1, Batch 2, and Batch 3 are immutable except for production defects, security fixes, or critical regressions.

---

## Batch Authorization

Only one batch may have status **AUTHORIZED** at any time.

| Field | Value |
|---|---|
| **Release** | Stabilization program |
| **Batch** | Gate 1 |
| **Title** | Production Safety Batch |
| **Status** | **COMPLETED / CERTIFIED / PUBLICATION AUTHORIZED** |
| **Authorized by** | ARM |
| **Authorization date** | 2026-07-28 |
| **Implementation posture** | ARM accepted; commit, tag, and publication authorized |
| **Previous published product-facing slice** | AEI v1.0 Teacher Evaluation UX-C (**Published / Certified**) |
| **Next gate** | Operational Proof — Planned / Not Authorized |

All other batches must be one of: Planned, Frozen, Deferred, or Completed.

---

## Current phase

**Stabilization Gate 1 — Production Safety Batch (completed)**

### Status

**Accepted and certified. No implementation gate is currently active.**

Certification evidence:
[`PRODUCTION_SAFETY_BATCH_CERTIFICATION_REPORT.md`](./PRODUCTION_SAFETY_BATCH_CERTIFICATION_REPORT.md).
Operational Proof remains planned and not authorized; no later-gate
authorization is implied.

### Objective

Remove verified production-safety defects before further product-facing AEI
work:

- declare required runtime dependencies;
- reject unsafe localhost CORS origins in production;
- enforce tenant scope on notification reads;
- correct teacher-scope pagination and totals;
- preserve exact `Decimal` money handling;
- make PDF behavior truthful and fail safely when PDF rendering is unavailable.

### Required validation posture

- focused build, lint, and tests for every changed surface;
- adjacent regression coverage for authentication, tenancy, evaluation, fees,
  pagination, and document output as applicable;
- additive `/api/v1` compatibility;
- no weakening of boot, security, tenant, or human-authority guardrails;
- explicit evidence for every accepted audit finding closed by this batch.

### Hard constraints

- keep Release 0.1 through Release 0.3 and the certified AEI/EUI architecture
  frozen except for verified production defects, security fixes, or critical
  regressions;
- do not start Operational Proof, AEI Activation/Trust, topic-ID/mastery
  implementation, or UX-D under this authorization;
- do not broaden product claims while capability flags remain unproven in the
  authorized runtime environment.

---

## Historical accepted execution baseline

**Release 0.3 / Batch 3 — School Pilot Experience remains Accepted / Frozen.**

### Objective completed

Batch 3 validated the smallest pilot-success slice: the existing Principal and Teacher journeys complete successfully without engineering assistance during the walkthrough.

### Product story

```text
Principal login
↓
Dashboard + curriculum readiness
↓
Academic Intelligence Ready
↓
Teacher login
↓
Assigned class/subject scope
↓
Approved CurriculumPack
↓
Grounded lesson plan
↓
Grounded question paper
↓
Principal + Teacher walkthrough PASS
```

### Primary personas

- School Principal
- Subject Teacher

### Architecture reuse requirements

Batch 3 reused the existing platform foundation:

- tenant resolution and `X-Tenant-Slug`;
- auth and RBAC;
- `CurriculumPack`;
- Knowledge Graph readiness;
- RAG retrieval and grounding;
- LLM gateway and AI credits;
- lesson-plan generation;
- question-paper generation;
- existing browser/API validation harness patterns.

### Historical freeze constraints

Do **not** modify frozen releases except for:

- production defects;
- security fixes;
- critical regressions.

The former Release 0.4 sequence is superseded as the immediate execution target
by the 2026-07-28 stabilization execution override above.

---

## Accepted batches

**Batch 3 — School Pilot Experience**

### Status

**Accepted / Frozen**

### Delivered capability

StudyNexs now has a validated Principal + Teacher pilot experience:

- Principal runtime proof;
- Teacher runtime proof;
- Principal browser walkthrough;
- Teacher browser walkthrough;
- tenant isolation verification;
- same-pack grounding verification for teacher lesson plan and question paper;
- focused Batch 3 validation harnesses.

### Acceptance evidence

See [`BATCH_03_COMPLETION_REPORT.md`](./BATCH_03_COMPLETION_REPORT.md).

### Commit

`649d835` — `feat(pilot): complete Batch 3 principal teacher proof`

### Freeze rule

Do not modify Batch 3 architecture or implementation except for:

- production defects;
- security fixes;
- critical regressions.

---

**Batch 2 — Academic Onboarding**

### Status

**Accepted / Frozen**

### Delivered capability

StudyNexs now has a curriculum-first onboarding loop:

- uploaded curriculum source intake;
- AI extraction into draft `CurriculumPack`;
- teacher/HOD human review;
- class-incharge/admin approval governance;
- KG + RAG readiness;
- deterministic same-pack evidence ledger;
- downstream proof across lesson plans, learning materials, question papers, assessment evaluation, mastery, student tutor/copilot, and parent copilot.

### Acceptance evidence

See [`BATCH_02_COMPLETION_REPORT.md`](./BATCH_02_COMPLETION_REPORT.md).

### Commit

`469c0f8` — `feat(onboarding): complete Batch 2 academic onboarding proof`

### Freeze rule

Do not modify Batch 2 architecture or implementation except for:

- production defects;
- security fixes;
- critical regressions.

---

**Batch 1 — Curriculum Intelligence**

### Status

**Accepted / Frozen**

### Delivered capability

StudyNexs now has an institutional curriculum memory foundation:

- teacher-owned curriculum drafts;
- class-incharge/admin approval governance;
- tenant-scoped `CurriculumPack` lifecycle;
- KG + RAG indexing on approval;
- same-pack grounding across lesson plans, question papers, tutor, and parent evidence paths.

### Acceptance evidence

See [`BATCH_01_COMPLETION_REPORT.md`](./BATCH_01_COMPLETION_REPORT.md).

### Commit

`63a5584` — `feat(curriculum): complete Batch 1 intelligence closure`

### Freeze rule

Do not modify Batch 1 architecture or implementation except for:

- production defects;
- security fixes;
- critical regressions.

---

## Deferred backlog

- Release 0.4 — Student + Parent Pilot Experience.
- Production async answer-sheet evaluation worker hardening.
- Pilot operations and deployment readiness.
- Full textbook PDF warehousing.
- Full textbook-to-`CurriculumPack` automation across arbitrary book layouts.
- Advanced report cards.
- Rich student practice engine.
- Public/prospect full learner loop.

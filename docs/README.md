# StudyNexs Documentation — Governance Hierarchy

> **Status:** Active · Product Execution Phase effective 2026-07-17  
> **Principle:** Higher documents constrain lower ones. Lower documents cannot contradict higher documents.

```
Architecture Constitution
        ↓
Engineering Governance
        ↓
Platform Design System v1
        ↓
Product Execution Constitution
        ↓
Product Execution Plan          ← changes every few weeks
        ↓
Implementation
        ↓
Capability Evidence
```

---

## Constitutional documents (frozen)

| Document | Answers | Path |
|----------|---------|------|
| **Architecture Constitution** | What are we building? | [`architecture/ARCHITECTURE_CONSTITUTION.md`](./architecture/ARCHITECTURE_CONSTITUTION.md) |
| **Engineering Governance** | How do we engineer it? | [`engineering/ENGINEERING_GOVERNANCE.md`](./engineering/ENGINEERING_GOVERNANCE.md) |
| **Platform Design System v1** | How should it feel? | [`design/PLATFORM_DESIGN_SYSTEM_V1.md`](./design/PLATFORM_DESIGN_SYSTEM_V1.md) |
| **Product Execution Constitution** | How do we prioritize engineering effort? | [`product/PRODUCT_EXECUTION_CONSTITUTION.md`](./product/PRODUCT_EXECUTION_CONSTITUTION.md) |
| **Review Standards** | How is quality evaluated? | [`reviews/REVIEW_STANDARDS.md`](./reviews/REVIEW_STANDARDS.md) |
| **Decision Log** | Why were important decisions made? | [`decisions/DECISION_LOG.md`](./decisions/DECISION_LOG.md) |

---

## Operational document (living)

| Document | Answers | Path |
|----------|---------|------|
| **Product Execution Plan** | What is the team building now? | [`product/PRODUCT_EXECUTION_PLAN.md`](./product/PRODUCT_EXECUTION_PLAN.md) |
| **Current Batch** | What must the active coding session execute? | [`product/CURRENT_BATCH.md`](./product/CURRENT_BATCH.md) |

The **Product Execution Plan** and **Current Batch** are the authoritative
sources for active execution scope. `STATUS.md` is the project anchor and must
reflect, but must not override, those operational documents.

When a batch completes, update the Product Execution Plan and Current Batch,
then update capability evidence, the Decision Log, and Master Status as
required by the accepted release workflow.

---

## Supporting references (not constitutional)

| Area | Examples |
|------|----------|
| Platform foundation history | [`ui-audit/`](./ui-audit/) — Phase 0–3C audit trail |
| Deployment | [`DEPLOYMENT_ARCHITECTURE.md`](./DEPLOYMENT_ARCHITECTURE.md) |
| Agent session | [`AGENT_HANDOVER.md`](./AGENT_HANDOVER.md), [`STATUS.md`](./STATUS.md) |
| Full engineering charter | [`/CLAUDE.md`](../CLAUDE.md) — operational superset |

---

## Current execution target

**Release 0.1 through Release 0.3 remain accepted and frozen historical
baselines.**

**Latest accepted gate:** **Stabilization Gate 1 — Production Safety Batch** ·
[`product/CURRENT_BATCH.md`](./product/CURRENT_BATCH.md)

ARM accepted the implementation and authorized publication. Certification is
recorded in
[`product/PRODUCTION_SAFETY_BATCH_CERTIFICATION_REPORT.md`](./product/PRODUCTION_SAFETY_BATCH_CERTIFICATION_REPORT.md).

No implementation gate is active. Operational Proof is next in sequence and
remains planned / not authorized.

The ordered gates after Production Safety are Operational Proof, AEI
Activation/Trust, topic-ID/mastery spine design, and then Teacher Evaluation
UX-D. Those later gates are planning order only and are not implementation
authorization.

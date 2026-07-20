# Gate 2 Pilot Decisions Log

> **Purpose:** Record **decisions** made during the pilot — not raw feedback.  
> **Structured log:** [`../PILOT_DECISION_LOG.md`](../PILOT_DECISION_LOG.md) (Date · Source · Observation · Evidence · Decision · Batch)  
> **Baseline:** `v0.1.0-batch1` · tenant `naagarjuna`  
> **Feedback (raw):** use [GATE2_FEEDBACK_COLLECTION_TEMPLATE.md](./GATE2_FEEDBACK_COLLECTION_TEMPLATE.md)  
> **Why separate:** Feedback informs; decisions commit the team to a direction and shape the roadmap.

---

## How to use

1. After each school sync, HOD meeting, or internal triage, log **decisions** here — not every comment.
2. One row per decision. Link to feedback form or daily log if helpful.
3. Tag **Action** as: `Pilot ops` · `Batch 2 candidate` · `Won't do` · `Defer` · `Fix now` · `Process`
4. Review weekly with product owner; carry Batch 2 candidates to [PRODUCT_EXECUTION_PLAN.md](../../product/PRODUCT_EXECUTION_PLAN.md) only after Gate 2 exit.

---

## Decision register

| Date | Decision | Reason | Action | Owner | Status |
|------|----------|--------|--------|-------|--------|
| 2026-07-20 | Use placeholder SSC Class 10 Maths seed pack until HOD supplies official syllabus | T-0 preflight; approved pack in DB (14 chapters) | Pilot ops — HOD validates Day 1 | PO | Open |
| | | | | | |
| | | | | | |
| | | | | | |

---

## Template (copy for new entries)

```markdown
### YYYY-MM-DD — [Short title]

**Decision:** What we decided (one sentence).

**Reason:** Evidence from school session, feedback, or ops (cite daily log / feedback form if applicable).

**Alternatives considered:** (optional)

**Action:** Pilot ops | Batch 2 candidate | Won't do | Defer | Fix now | Process

**Owner:** 

**Status:** Open | In progress | Done | Superseded

**Follow-up date:** 
```

---

## Decision categories

| Category | Use when |
|----------|----------|
| **Scope** | In/out of pilot wedge (class, subject, feature) |
| **Product** | UX, workflow, or capability direction |
| **Technical** | Env, deploy, tooling choices during pilot |
| **Commercial** | Pricing, timeline, expansion |
| **Compliance** | DPDP, consent, data handling |
| **Process** | Cadence, roles, communication with school |

---

## Rules

- Do **not** duplicate open defects here — use [PILOT_FEEDBACK_LOG.md](../../product/PILOT_FEEDBACK_LOG.md) for bugs/env issues.
- Do **not** treat unresolved debates as decisions — mark as `Open` only after explicit agreement (PO + HOD or PO + team).
- **Superseded** decisions stay in the table (strike-through or note in Status) for audit trail.
- At Gate 2 exit, summarize decisions in [GATE2_EXIT_REVIEW_TEMPLATE.md](./GATE2_EXIT_REVIEW_TEMPLATE.md) §6.

---

## Weekly decision review (standing)

| Week | Reviewer | New decisions | Batch 2 promoted | Closed |
|------|----------|---------------|------------------|--------|
| | | | | |

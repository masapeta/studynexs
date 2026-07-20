# Gate 2 GO — Naagarjuna Talent School Pilot

> **Declared:** 2026-07-20  
> **Authority:** Product Owner — Final Release Authorization (post-P6)  
> **Baseline:** `v0.1.0-batch1` on `studynexs-dev` `develop`  
> **Status:** **GO — pilot authorized**

---

## Declaration

**Gate 2 is GO.** The Naagarjuna Talent School pilot (Class 10 Mathematics, Telangana SSC) is authorized to begin on the Batch 1 baseline.

| Item | Value |
|------|-------|
| Canonical repository | `studynexs-dev` |
| Release tag | `v0.1.0-batch1` |
| Tenant slug | `naagarjuna` |
| Pilot wedge | Class 10 · Maths · Telangana SSC |

---

## Validated capabilities (Batch 1)

- Approval pipeline (`approve_pack()`)
- Curriculum grounding facade (`ground_approved_pack()`)
- Knowledge Graph integration
- Hybrid RAG integration
- Learning Outcomes · Audit Trail
- Question Papers · Lesson Plans (template default)
- Curriculum UI extensions
- Smoke 12/12 · Playwright 11/11

---

## Operating constraints

- **Primary objective:** Learn from the pilot — not build new features.
- **No new features** until pilot completes — critical production defects only (PO-approved).
- **Triage all feedback** into three buckets — log in [`PILOT_DECISION_LOG.md`](./PILOT_DECISION_LOG.md) with **Priority** (P0–P3), **Owner**, and **Status**:
  - **Critical defect** → Batch 1 patch (code allowed)
  - **Operational improvement** → docs / runbooks / config (no architecture change)
  - **Product opportunity** → Batch 2 backlog (do not implement now)
- **Architecture frozen** — see [`BATCH1_BASELINE_CERTIFICATE.md`](../../BATCH1_BASELINE_CERTIFICATE.md).
- **Execution:** [`gate2/GATE2_PILOT_EXECUTION_PLAN.md`](./gate2/GATE2_PILOT_EXECUTION_PLAN.md)

---

## Pre-session checklist

1. [`GATE2_PREFLIGHT_CHECKLIST.md`](./gate2/GATE2_PREFLIGHT_CHECKLIST.md)
2. `python scripts/smoke_pilot_readiness.py` → 12/12
3. Admin web with `naagarjuna` tenant on `localhost:8000`

---

*Pilot operations begin upon this declaration.*

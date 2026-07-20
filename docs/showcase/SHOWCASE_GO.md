# Showcase Environment GO

> **Declared:** 2026-07-20  
> **Authority:** Product Owner — Final Release Authorization (post-P6)  
> **Baseline:** `v0.1.0-batch1` on `studynexs-dev`  
> **Status:** **GO — Showcase (Reference School) authorized**

---

## Declaration

The **StudyNexs Reference School** (Showcase) demonstration environment is authorized to operate on the Batch 1 software baseline.

This is **not** a customer tenant and **not** a customer pilot. It is the permanent internal environment for sales demonstrations and platform validation with representative sample data.

| Item | Value |
|------|-------|
| Formal name | StudyNexs Reference School |
| Shorthand | Showcase |
| Canonical repository | `studynexs-dev` |
| Release tag | `v0.1.0-batch1` |
| Tenant slug (current) | `naagarjuna` — Phase B target: `showcase` |
| Demo wedge (initial) | Class 10 · Maths · Telangana SSC |

See [`customer-journey/README.md`](../customer-journey/README.md) — Showcase is a **customer journey** phase, not an engineering release stage.

---

## Validated capabilities (Batch 1)

- Approval pipeline (`approve_pack()`)
- Curriculum grounding facade (`ground_approved_pack()`)
- Knowledge Graph · Hybrid RAG integration
- Learning Outcomes · Audit Trail
- Question Papers · Lesson Plans (template default)
- Curriculum UI extensions
- Smoke 12/12 · Playwright 11/11

---

## Operating constraints

- **Purpose:** Demonstrate platform to prospective schools — representative data only.
- **No customer-specific content** in Showcase docs — use [`discovery/schools/`](../discovery/schools/).
- **Software changes:** Critical production defects only on `v0.1.0-batch1` (PO-approved).
- **Ops decisions:** [`SHOWCASE_DECISION_LOG.md`](./SHOWCASE_DECISION_LOG.md)
- **Demo script:** [`SHOWCASE_DEMO_SCRIPT.md`](./SHOWCASE_DEMO_SCRIPT.md)
- **Architecture frozen** — [`BATCH1_BASELINE_CERTIFICATE.md`](../../BATCH1_BASELINE_CERTIFICATE.md)

---

## Pre-demo checklist

1. [`SHOWCASE_ENVIRONMENT_VALIDATION.md`](./SHOWCASE_ENVIRONMENT_VALIDATION.md)
2. `python scripts/smoke_pilot_readiness.py` → 12/12
3. Admin web with showcase tenant slug on `localhost:8000`

---

*Customer Pilot for signed schools is governed separately under [`customer-pilot/`](../customer-pilot/).*

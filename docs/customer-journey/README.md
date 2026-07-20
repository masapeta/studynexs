# StudyNexs Customer Journey

> **Status:** Active product model (2026-07-20)  
> **Owner:** Product  
> **Independent of:** [Engineering release lifecycle](../engineering/ENGINEERING_GOVERNANCE.md#release-lifecycle-permanent-model)

---

## Two independent models

| Model | Question it answers | Document |
|-------|---------------------|----------|
| **Engineering release lifecycle** | How do we **build and release** software? | [`ENGINEERING_GOVERNANCE.md`](../engineering/ENGINEERING_GOVERNANCE.md) |
| **Customer journey** | How does a **school adopt** StudyNexs? | This document |

Do not mix these models. Release tags (e.g. `v0.1.0-batch1`) describe **software baselines**. Customer journey phases describe **go-to-market and adoption**.

---

## Customer lifecycle

```
Discovery
    ↓
Showcase (Reference School)
    ↓
Customer Decision
    ↓
Customer Onboarding
    ↓
Customer Pilot
    ↓
Go Live
    ↓
Expansion
```

| Phase | Purpose | Documentation |
|-------|---------|---------------|
| **Discovery** | Qualify prospect; capture requirements and meeting outcomes | [`discovery/`](../discovery/) |
| **Showcase** | Permanent internal **Reference School** — sales demonstrations with representative sample data | [`showcase/`](../showcase/) |
| **Customer Decision** | Contract / commitment to proceed | CRM / commercial (outside repo) |
| **Customer Onboarding** | Dedicated tenant, real curriculum & ops data import, staff setup | [`onboarding/`](../onboarding/) |
| **Customer Pilot** | Bounded real-world validation on **customer's own data** | [`customer-pilot/`](../customer-pilot/) |
| **Go Live** | Production rollout for signed school | TBD |
| **Expansion** | Additional classes, subjects, modules | TBD |

---

## Showcase vs Customer Pilot

| | **Showcase (Reference School)** | **Customer Pilot** |
|---|--------------------------------|-------------------|
| **Audience** | Prospective schools, investors, internal training | Signed customer only |
| **Tenant** | Permanent demonstration tenant (slug: `showcase` — Phase B) | Dedicated customer tenant |
| **Data** | Representative sample (Board, Grade, Subject, synthetic users) | Real curriculum, teachers, students |
| **Display name** | StudyNexs Reference School | Customer's school name |
| **Customer-specific info** | ❌ Never | ✅ In [`discovery/schools/`](../discovery/schools/) + customer tenant |
| **Begins when** | Software baseline tagged & env validated | Contract signed · tenant created · data imported · teachers trained |

---

## Architecture rule

No business logic depends on a school name. All environments are **tenant-driven**. The Intelligence Layer operates on Board · Grade · Subject · Curriculum Pack · Learning Outcomes · Knowledge Graph · Policies — not on a specific school's identity.

---

## Naming

| Context | Term |
|---------|------|
| Formal documentation | **Reference School** |
| Engineering / ops shorthand | **Showcase** |
| Avoid in formal docs | "Demo School", "Pilot School" (ambiguous) |

---

## Related

| Document | Role |
|----------|------|
| [`showcase/SHOWCASE_GO.md`](../showcase/SHOWCASE_GO.md) | Showcase environment authorized to operate |
| [`showcase/SHOWCASE_DECISION_LOG.md`](../showcase/SHOWCASE_DECISION_LOG.md) | Showcase ops decisions |
| [`customer-pilot/README.md`](../customer-pilot/README.md) | Post-signing pilot prerequisites |
| [`SHOWCASE_DOCUMENTATION_REFACTORING_PLAN.md`](../SHOWCASE_DOCUMENTATION_REFACTORING_PLAN.md) | Phase A/B plan (PO-approved) |

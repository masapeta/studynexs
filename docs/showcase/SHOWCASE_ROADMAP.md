# Showcase Roadmap — StudyNexs Reference School

> **Asset:** StudyNexs Reference School (Showcase)  
> **Status:** Living roadmap — not a release milestone  
> **Purpose:** Define what the Reference School should eventually demonstrate  
> **Rule:** New platform capabilities should appear here **before** customer tenant rollout

---

## Product intent

The Reference School is a **permanent product asset** — a continuously evolving **golden tenant** — not a throwaway demo database.

| Property | Reference School | Customer tenant |
|----------|------------------|-----------------|
| Purpose | Demonstrate full platform to prospects | Operate a signed school |
| Data | Representative sample (Board-aligned) | Real school data |
| Lifecycle | Maintained with every major capability | Onboarded per contract |
| Identity | StudyNexs Reference School | Customer's school name |

Every new capability engineering ships should be **demonstrable in the Reference School** before it is offered to customer pilots or go-live deployments.

---

## Current baseline (v0.1.0-batch1)

Validated on tag `v0.1.0-batch1` · tenant slug `naagarjuna` (Phase B → `showcase`).

| Area | Capability | Status |
|------|------------|--------|
| Academic | Curriculum pack CRUD + approve | ✅ Demonstrated |
| Academic | Learning outcomes | ✅ Demonstrated |
| Academic | Grounded question papers | ✅ Demonstrated |
| Academic | Template lesson plans + grounding | ✅ Demonstrated |
| Academic | Audit trail | ✅ Demonstrated |
| AI | Hybrid RAG + Knowledge Graph spine | ✅ Demonstrated |
| AI | Teacher Copilot routing (optional) | ✅ Smoke validated |
| Admin | Principal dashboard (visibility) | ✅ Partial |
| Operations | Smoke 12/12 · Playwright 11/11 | ✅ Evidence on file |

**Initial wedge:** Class 10 · Mathematics · Telangana SSC.

---

## Target demonstration scope

The Reference School should eventually represent a **complete school platform** — Classes 6–10, full operations, and all Intelligence Layer capabilities.

### Reference School structure (target)

```
StudyNexs Reference School
├── Board ........................ Telangana SSC (expandable)
├── Grades ....................... 6 – 10
├── Teachers ..................... representative staff roster
├── Students ..................... representative cohorts per grade
├── Parents ...................... linked guardian accounts
├── Timetable .................... sample schedules
├── Exams ........................ exam cycles + eval workflows
├── Attendance ................... daily attendance patterns
├── Fee Records .................. sample fee structures (no live payments)
├── Curriculum Packs ............. approved packs per grade/subject
├── AI Tutor ..................... student-facing demo flows
├── Analytics .................... principal / HOD intelligence views
└── School Operations ............ notices, events, transport (as built)
```

---

## Capability roadmap by domain

Track **Demonstrated** · **Partial** · **Planned** · **N/A** during showcase reviews.

### Academic

| Capability | Target | Notes |
|------------|--------|-------|
| Curriculum Intelligence | ✅ → expand | Multi-grade packs; Board-driven content |
| Assessment Intelligence | Partial | QP grounded; eval assist on sample sheets |
| AI Tutor | Planned | Student copilot on flagged mistakes |
| Lesson Plans | ✅ | Template + grounding default |
| Question Papers | ✅ | HITL approve workflow |
| Gradebook / Report cards | Planned | Sample academic records |
| Mastery / weak topics | Partial | Demo views from sample eval data |

### Administration

| Capability | Target | Notes |
|------------|--------|-------|
| Admissions | Planned | Enquiry → admission sample funnel |
| Attendance | Planned | Class-level daily marks |
| Fees | Planned | Structure + receipts (Decimal, demo only) |
| Transport | Planned | Routes + assignments (when module ready) |
| Library | Planned | Catalog + issue demo |
| Staff / HR | Partial | Existing staff models; showcase roster |

### AI

| Capability | Target | Notes |
|------------|--------|-------|
| Teacher Copilot | Partial | Optional; template default for LP |
| Parent Copilot | Planned | Batch 27–28 capability in golden tenant |
| Student Copilot | Planned | Tutor page integration |
| Principal Dashboard | Partial | Morning briefing / school day |
| School Intelligence | Planned | Cross-module insights (policy-driven) |

### Operations

| Capability | Target | Notes |
|------------|--------|-------|
| Reports | Planned | Standard school reports on sample data |
| Notifications | Planned | Notices, audience targeting |
| Workflows | Planned | Approval chains visible in demo |
| Analytics | Partial | Dashboard widgets on representative data |

---

## Quality standards (golden tenant)

Before marking a capability **Demonstrated** in the Reference School:

| Standard | Requirement |
|----------|-------------|
| **Smoke** | Relevant check passes or dedicated showcase smoke added |
| **Data** | Representative, Board-aligned sample — no customer PII |
| **Demo script** | Step documented in [`SHOWCASE_DEMO_SCRIPT.md`](./SHOWCASE_DEMO_SCRIPT.md) or addendum |
| **Provenance** | AI outputs show grounding / HITL where applicable |
| **Tenant isolation** | No hardcoded school names in logic — slug-driven only |
| **Decision log** | Material gaps logged in [`SHOWCASE_DECISION_LOG.md`](./SHOWCASE_DECISION_LOG.md) |

---

## Phase B — tenant identity (pending PO approval)

| Field | Current | Proposed |
|-------|---------|----------|
| Tenant slug | `naagarjuna` | `showcase` |
| Display name | (seed-defined) | **StudyNexs Reference School** |
| Seed scripts | `seed_pilot_naagarjuna*.py` | `seed_showcase_reference_school*.py` |

Phase B renames identifiers only — the **product asset** is the Reference School itself, not the slug string.

---

## Review cadence

| When | Activity |
|------|----------|
| After each product batch | Update status column; add rows for new capabilities |
| Before major sales demo | Verify [`SHOWCASE_ENVIRONMENT_VALIDATION.md`](./SHOWCASE_ENVIRONMENT_VALIDATION.md) |
| Quarterly | PO + Engineering review — prioritize gaps for next batches |

---

## Related

| Document | Role |
|----------|------|
| [`README.md`](./README.md) | Showcase ops index |
| [`SHOWCASE_GO.md`](./SHOWCASE_GO.md) | Environment authorized |
| [`reference-school/`](./reference-school/) | Validation evidence |
| [`../customer-journey/README.md`](../customer-journey/README.md) | Where Showcase fits in adoption |
| [`../product/PRODUCT_EXECUTION_PLAN.md`](../product/PRODUCT_EXECUTION_PLAN.md) | Batch delivery schedule |

---

*Living document — update as the Reference School grows toward full platform demonstration.*

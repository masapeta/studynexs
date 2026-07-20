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

Before marking a capability **Demonstrated** in the Reference School — and before considering a feature **complete** per [Reference School Acceptance Rule](../engineering/ENGINEERING_GOVERNANCE.md#reference-school-acceptance-rule):

| Standard | Requirement |
|----------|-------------|
| **Automated validation** | Build, lint, tests pass; smoke updated if applicable |
| **Documentation** | Capability documented per batch scope |
| **Reference School demo** | Successfully demonstrated; demo script step added or updated |
| **Data** | Representative, Board-aligned sample — no customer PII |
| **Provenance** | AI outputs show grounding / HITL where applicable |
| **Isolation** | No hardcoded school names in logic — tenant-driven only |
| **Decision log** | Material gaps in [`SHOWCASE_DECISION_LOG.md`](./SHOWCASE_DECISION_LOG.md) |

### QA acceptance path

```
Feature → Reference School → Smoke → Demo Script → Acceptance
```

Sales, marketing, QA, product, and engineering all use this **one** environment.

---

## Future reference assets (vision)

As StudyNexs expands beyond K–12, the platform may host additional **reference environments** — same platform, different domain content:

```
Reference Assets (future)
├── Reference School .............. K–12 (current — StudyNexs Reference School)
├── Reference College ............. TBD
├── Reference University .......... TBD
├── Reference Coaching Institute .. TBD
└── Reference Training Center ..... TBD
```

Each is a maintained product asset, not a customer tenant. Customer tenants remain separate under onboarding and go-live.

---

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

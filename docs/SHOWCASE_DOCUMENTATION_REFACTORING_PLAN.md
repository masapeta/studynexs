# Showcase vs Customer Pilot — Documentation Refactoring Plan

> **Status:** ✅ **Phase A approved and executed** (2026-07-20)  
> **PO direction:** Customer journey and engineering release lifecycle are **independent models**

---

## 1. Product direction (accepted for planning)

StudyNexs now distinguishes **three phases** in the customer journey:

```
Showcase (sales / demo)          →  permanent Reference School, sample data, all prospects
        ↓
Customer onboarding              →  dedicated tenant, real curriculum & ops data import
        ↓
Customer pilot                   →  real teachers, students, validation on their data
```

| Phase | Environment | Data | Audience |
|-------|-------------|------|----------|
| **Showcase** | Internal demonstration tenant | Representative sample (Classes 6–10, Telangana SSC, synthetic users) | Prospective schools, investors, internal training |
| **Customer onboarding** | New dedicated tenant per signed school | Real school curriculum and operational data | Implementation team + school IT |
| **Customer pilot** | Same dedicated tenant | Real teachers, students, exams | HOD, teachers, PO — bounded wedge |

### Architecture rule (unchanged — documentation must reflect)

- **No business logic may depend on a school name.**
- Intelligence layer operates on: Board · Grade · Subject · Curriculum Pack · Learning Outcomes · Knowledge Graph · Policies.
- All environments are **tenant-driven** (`school_id` / tenant slug) — never hardcoded school identity in code paths.

### Terminology mapping

| Retire in active docs | Replace with |
|------------------------|--------------|
| Naagarjuna Talent School Pilot | **Showcase School** / **Reference School** / **StudyNexs Demonstration Environment** |
| Naagarjuna tenant (as product concept) | **Showcase tenant** |
| Pilot school (when meaning demo) | **Reference School** or **Demo School** |
| Gate 2 GO (Naagarjuna) | **Showcase Environment GO** (historical Gate 2 validation → showcase readiness) |
| Pilot (when meaning sales demo) | **Showcase** or **Demonstration** |
| Pilot (when meaning post-signing validation) | **Customer Pilot** |

**Note:** The database tenant slug `naagarjuna` and seed script filenames are **implementation details** today. Doc refactor is Phase A; slug/script rename is Phase B (separate PO approval, see §6).

---

## 2. Current state assessment

The existing **Gate 2 / Pilot** documentation conflates two distinct programs:

1. **What P5–P6 actually validated** — smoke, Playwright, T-0 evidence, demo script, seed data → this is **Showcase readiness**, not a live customer pilot.
2. **What Gate 2 templates describe** — 8-week HOD/teacher program, school inputs, feedback forms, exit review → this is a **Customer Pilot playbook** for post-signing schools.

The release tag `v0.1.0-batch1` remains valid as the **software baseline** for both showcase and future customer pilots. This plan does **not** propose a new release tag.

---

## 3. Document classification

### 3A. Showcase / demonstration (rename & refactor)

These documents describe the **permanent internal demo environment** or record its validation evidence.

| Current path | Classification | Proposed action |
|--------------|----------------|-----------------|
| [`GATE2_GO.md`](./GATE2_GO.md) | Showcase authorization (mislabeled as Naagarjuna pilot) | **Rename** → `showcase/SHOWCASE_GO.md`; rewrite for Reference School; add historical note |
| [`PILOT_DECISION_LOG.md`](./PILOT_DECISION_LOG.md) | Showcase ops decision log (learn-first → **showcase ops** learn-from-demo) | **Move/refactor** → `showcase/SHOWCASE_DECISION_LOG.md`; triage buckets remain; remove school name |
| [`naagarjuna-talent-school/`](./naagarjuna-talent-school/) | T-0 validation evidence for demo tenant | **Rename** → `showcase/reference-school/t0-evidence/`; update README |
| [`gate2/GATE2_DEMO_SCRIPT.md`](./gate2/GATE2_DEMO_SCRIPT.md) | Sales demo script (HOD + teacher walkthrough) | **Move** → `showcase/SHOWCASE_DEMO_SCRIPT.md`; neutral narrative |
| [`gate2/GATE2_ENVIRONMENT_VALIDATION.md`](./gate2/GATE2_ENVIRONMENT_VALIDATION.md) | Demo stack validation (smoke, docker, API) | **Move** → `showcase/SHOWCASE_ENVIRONMENT_VALIDATION.md` |
| [`gate2/GATE2_READINESS_AUDIT.md`](./gate2/GATE2_READINESS_AUDIT.md) | T-0 readiness (pre-showcase) | **Move** → `showcase/SHOWCASE_READINESS_AUDIT.md` + archival banner |
| [`gate2/README.md`](./gate2/README.md) (partial) | Mixed index | **Split** — showcase ops section → `showcase/README.md` |
| [`product/batch1-ui-demo/`](../product/batch1-ui-demo/) | Playwright evidence | **Keep path**; add README clarifying showcase validation artifact |
| [`GATE1_EXECUTION.md`](./GATE1_EXECUTION.md) | Demo Online / Demo Reliable | **Cross-link** from `showcase/README.md`; already aligned with demo intent |
| [`HANDS_ON_RUNBOOK.md`](./HANDS_ON_RUNBOOK.md) | Gate 1 hands-on (tenant `test`) | **Cross-link** from showcase; note legacy `test` vs future unified showcase tenant |

### 3B. Customer pilot (keep, generalize, relocate)

These are **reusable templates** for real schools **after signing**. Remove Naagarjuna-specific framing; keep structure.

| Current path | Classification | Proposed action |
|--------------|----------------|-----------------|
| [`gate2/GATE2_PILOT_EXECUTION_PLAN.md`](./gate2/GATE2_PILOT_EXECUTION_PLAN.md) | 8-week customer pilot program | **Move** → `customer-pilot/CUSTOMER_PILOT_EXECUTION_PLAN.md`; generic roles & timeline |
| [`gate2/GATE2_PREFLIGHT_CHECKLIST.md`](./gate2/GATE2_PREFLIGHT_CHECKLIST.md) | Pre-pilot go/no-go (school inputs, HOD sign-off) | **Move** → `customer-pilot/CUSTOMER_PILOT_PREFLIGHT_CHECKLIST.md`; split showcase preflight out |
| [`gate2/GATE2_SUCCESS_CRITERIA.md`](./gate2/GATE2_SUCCESS_CRITERIA.md) | Customer pilot exit criteria | **Move** → `customer-pilot/CUSTOMER_PILOT_SUCCESS_CRITERIA.md` |
| [`gate2/GATE2_FEEDBACK_COLLECTION_TEMPLATE.md`](./gate2/GATE2_FEEDBACK_COLLECTION_TEMPLATE.md) | HOD/teacher feedback | **Move** → `customer-pilot/templates/FEEDBACK_COLLECTION.md` |
| [`gate2/GATE2_DAILY_PILOT_LOG_TEMPLATE.md`](./gate2/GATE2_DAILY_PILOT_LOG_TEMPLATE.md) | Daily ops during customer pilot | **Move** → `customer-pilot/templates/DAILY_PILOT_LOG.md` |
| [`gate2/GATE2_PILOT_SESSION_REPORT_TEMPLATE.md`](./gate2/GATE2_PILOT_SESSION_REPORT_TEMPLATE.md) | Post-session report | **Move** → `customer-pilot/templates/SESSION_REPORT.md` |
| [`gate2/GATE2_EXIT_REVIEW_TEMPLATE.md`](./gate2/GATE2_EXIT_REVIEW_TEMPLATE.md) | Pilot exit decision | **Move** → `customer-pilot/templates/EXIT_REVIEW.md` |
| [`gate2/GATE2_FINAL_REPORT.md`](./gate2/GATE2_FINAL_REPORT.md) | Pilot close-out report | **Move** → `customer-pilot/templates/FINAL_REPORT.md` |
| [`gate2/PILOT_DECISIONS.md`](./gate2/PILOT_DECISIONS.md) | Narrative decision register (customer pilot) | **Move** → `customer-pilot/CUSTOMER_PILOT_DECISIONS.md` |
| [`gate2/GATE2_RISK_REGISTER.md`](./gate2/GATE2_RISK_REGISTER.md) | Risk register | **Move** → `customer-pilot/CUSTOMER_PILOT_RISK_REGISTER.md` |
| [`gate2/GATE2_ROLLBACK_PLAN.md`](./gate2/GATE2_ROLLBACK_PLAN.md) | Rollback | **Move** → `customer-pilot/CUSTOMER_PILOT_ROLLBACK_PLAN.md` |
| [`gate2/RELEASE_ENGINEERING_REVIEW.md`](./gate2/RELEASE_ENGINEERING_REVIEW.md) | Release review | **Keep** under `customer-pilot/` or `docs/release/` |
| [`PILOT_OUTCOME_SHEET.md`](./PILOT_OUTCOME_SHEET.md) | Discovery meeting outcome | **Move** → `discovery/PILOT_OUTCOME_SHEET.md` (pre-signing, not pilot) |
| [`PILOT_DISCOVERY.md`](../PILOT_DISCOVERY.md) | Sales discovery questions | **Move** → `discovery/PILOT_DISCOVERY.md` |
| [`CLASS_10_MATHS_EXAM_LOOP.md`](./CLASS_10_MATHS_EXAM_LOOP.md) | Eval positioning for demos/pilots | **Keep**; neutralize school refs; tag as shared reference |
| School outcome folders (`delhi-public-school/`, etc.) | Pre-signing discovery records | **Move** → `discovery/schools/<slug>/` |

### 3C. Historical / release artifacts (annotate only)

Do **not** rewrite history. Add a one-line banner: *"Historical record — pre-showcase/customer-pilot terminology split (2026-07-20)."*

| Path | Action |
|------|--------|
| [`P3_IMPLEMENTATION_REPORT.md`](../P3_IMPLEMENTATION_REPORT.md) | Banner only |
| [`P4_IMPLEMENTATION_REPORT.md`](../P4_IMPLEMENTATION_REPORT.md) | Banner only |
| [`P5_IMPLEMENTATION_REPORT.md`](../P5_IMPLEMENTATION_REPORT.md) | Banner only |
| [`P6_IMPLEMENTATION_REPORT.md`](../P6_IMPLEMENTATION_REPORT.md) | Banner only |
| [`BATCH1_BASELINE_CERTIFICATE.md`](../BATCH1_BASELINE_CERTIFICATE.md) | Banner + § note: validated software applies to showcase & customer pilot |
| [`RELEASE_NOTES_v0.1.0-batch1.md`](../RELEASE_NOTES_v0.1.0-batch1.md) | Banner only |
| [`RELEASE_CHECKLIST_v0.1.0-batch1.md`](./RELEASE_CHECKLIST_v0.1.0-batch1.md) | Banner only |
| [`BATCH1_RECONCILIATION_PLAN.md`](../BATCH1_RECONCILIATION_PLAN.md) | Banner only |

### 3D. Root / engineering docs (light touch)

| Path | Action |
|------|--------|
| [`ENGINEERING_GOVERNANCE.md`](../engineering/ENGINEERING_GOVERNANCE.md) | Extend release lifecycle: Showcase → Onboarding → Customer Pilot → Production |
| [`CANONICAL_REPOSITORY.md`](../CANONICAL_REPOSITORY.md) | No change |
| [`README.md`](../README.md) | Link to `docs/showcase/README.md` |
| [`BACKLOG.md`](../BACKLOG.md), [`PRODUCT.md`](../PRODUCT.md) | Separate pass — PO review after doc structure lands |

---

## 4. Proposed documentation structure

```
docs/
├── showcase/                              # NEW — permanent demonstration environment
│   ├── README.md                          # What showcase is; not a customer tenant
│   ├── SHOWCASE_GO.md                     # Authorization to operate demo environment
│   ├── SHOWCASE_DECISION_LOG.md           # Ops decisions (Priority, Owner, Status)
│   ├── SHOWCASE_DEMO_SCRIPT.md            # Sales walkthrough (from GATE2_DEMO_SCRIPT)
│   ├── SHOWCASE_ENVIRONMENT_VALIDATION.md # Stack/smoke/Playwright pre-demo checks
│   ├── SHOWCASE_READINESS_AUDIT.md        # Readiness audit (from GATE2_READINESS_AUDIT)
│   ├── SHOWCASE_DATA_ROADMAP.md           # NEW — Classes 6–10, SSC, sample users (future content)
│   └── reference-school/
│       ├── README.md                      # Seed scripts, accounts, tenant slug note
│       └── t0-evidence/                   # smoke-results, workflow-results, checklist
│
├── customer-pilot/                        # NEW — post-signing validation only
│   ├── README.md                          # When to use; requires dedicated tenant
│   ├── CUSTOMER_PILOT_EXECUTION_PLAN.md
│   ├── CUSTOMER_PILOT_PREFLIGHT_CHECKLIST.md
│   ├── CUSTOMER_PILOT_SUCCESS_CRITERIA.md
│   ├── CUSTOMER_PILOT_DECISIONS.md
│   ├── CUSTOMER_PILOT_RISK_REGISTER.md
│   ├── CUSTOMER_PILOT_ROLLBACK_PLAN.md
│   └── templates/
│       ├── FEEDBACK_COLLECTION.md
│       ├── DAILY_PILOT_LOG.md
│       ├── SESSION_REPORT.md
│       ├── EXIT_REVIEW.md
│       └── FINAL_REPORT.md
│
├── onboarding/                            # NEW — placeholder for Phase 2 docs
│   └── README.md                          # Tenant creation, data import (TBD)
│
├── discovery/                             # Pre-signing sales discovery
│   ├── PILOT_DISCOVERY.md
│   ├── PILOT_OUTCOME_SHEET.md
│   └── schools/                           # Per-prospect outcome records
│
└── pilot/                                 # TRANSITION — deprecate after migration
    ├── gate2/                             # Redirect stubs → new paths (30-day)
    └── (legacy files with DEPRECATED banners)
```

---

## 5. Refactoring phases (documentation only)

### Phase A — Structure & terminology (PO approval required)

**Effort:** ~1 session · **Risk:** Low · **No code changes**

1. Create `docs/showcase/`, `docs/customer-pilot/`, `docs/onboarding/`, `docs/discovery/` skeletons.
2. Move/rename documents per §3 tables.
3. Replace school-specific terminology in **active** showcase and customer-pilot docs.
4. Add `DEPRECATED` redirect stubs in old `docs/pilot/gate2/` paths (link to new locations).
5. Update cross-links in `GATE2_GO` successors, `ENGINEERING_GOVERNANCE`, `showcase/README.md`.
6. Add historical banners to P3–P6 / release artifacts (§3C).
7. Single governance commit: `docs(governance): split showcase and customer pilot documentation`

### Phase B — Implementation alignment (separate PO approval)

**Not in scope for Phase A.** Document only; execute after showcase data roadmap approved.

| Item | Current | Proposed | Rationale |
|------|---------|----------|-------------|
| Tenant slug | `naagarjuna` | `showcase` or `studynexs-reference` | No school name in identifiers |
| `seed_pilot_naagarjuna.py` | School-named script | `seed_showcase_reference_school.py` | Tenant-driven seeding |
| `smoke_pilot_readiness.py` | Default `naagarjuna` | Default showcase slug via env | No hardcoded school |
| `.env.local` example | `NEXT_PUBLIC_TENANT_SLUG=naagarjuna` | `showcase` | Demo env standard |
| School display name in seed | "Naagarjuna Talent School" | "StudyNexs Reference School" | Neutral branding |

**Architecture validation:** grep for `naagarjuna` in `apps/` — must be scripts/config only, not business logic (confirm during Phase B).

### Phase C — Showcase data expansion (product backlog)

Populate showcase tenant with representative content (Classes 6–10, full SSC wedge, sample teachers/students/parents, textbooks, QPs, LPs, evals, tutor, dashboards). Tracked in `SHOWCASE_DATA_ROADMAP.md` — **not** Batch 1 scope.

---

## 6. Governance updates

### Release lifecycle (extend `ENGINEERING_GOVERNANCE.md`)

```
Development → Architecture Review → Implementation → Operational Validation
    → Release Governance → Release Candidate → Tag
    → Showcase (demo) → Customer Onboarding → Customer Pilot → Production
```

| Stage | Doc home | Decision log |
|-------|----------|--------------|
| Showcase | `docs/showcase/` | `SHOWCASE_DECISION_LOG.md` |
| Customer onboarding | `docs/onboarding/` | TBD |
| Customer pilot | `docs/customer-pilot/` | `CUSTOMER_PILOT_DECISIONS.md` + templates |

### What changes for engineering **now** (post Phase A)

- **`develop` freeze** continues for `v0.1.0-batch1` software baseline.
- **Primary objective** shifts from "Naagarjuna pilot" to **operating and enriching the Showcase environment**.
- **Customer pilot docs** exist but are **inactive** until a school signs.
- Decision log triage buckets unchanged; log moves to showcase ops.

---

## 7. Explicit non-goals

- ❌ No API, schema, or UI changes in Phase A
- ❌ No new release tag
- ❌ No rewrite of P3–P6 historical reports (banner only)
- ❌ No deletion of `docs/pilot/gate2/` until redirect stubs verified
- ❌ No customer pilot execution until onboarding complete for a signed school

---

## 8. Open decisions for Product Owner

| # | Question | Recommendation |
|---|----------|----------------|
| D1 | Canonical name: **Showcase School** vs **Reference School** vs **Demo School**? | **Reference School** in formal docs; **Showcase** in ops/engineering shorthand |
| D2 | Target tenant slug for Phase B? | `showcase` (short, neutral) |
| D3 | Keep `gate2/` folder name as deprecated alias? | Yes — 30-day redirect stubs, then remove |
| D4 | Is Gate 1 (`test` tenant) merged into unified showcase tenant? | Decide in Phase C; document both until merged |
| D5 | Naagarjuna as a future **customer** prospect — retain in `discovery/schools/`? | Yes — if real prospect; separate from showcase |

---

## 9. Success criteria for Phase A approval

- [ ] PO approves terminology (`Reference School` / `Showcase`)
- [ ] PO approves proposed folder structure (§4)
- [ ] PO approves Phase A vs B boundary (docs only vs slug/script rename)
- [ ] Engineering executes Phase A in single governance commit
- [ ] No broken doc links (CI or manual link check)
- [ ] `SHOWCASE_GO.md` replaces misleading "Naagarjuna pilot authorized" framing

---

## 10. Recommendation

**Approve Phase A** to align documentation with the three-phase customer journey before investing in showcase data expansion (Phase C).

The conflation of **validation evidence** (what P5–P6 produced) with **customer pilot operations** (8-week Gate 2 plan) is the root documentation debt. Splitting now prevents sales demos from being run under "pilot" language and preserves customer pilot templates for post-signing use.

**Awaiting Product Owner approval before any file moves or renames.**

---

*Prepared by Engineering — documentation refactoring plan only.*

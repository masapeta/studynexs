# Pilot Decision Log — Naagarjuna Talent School

> **Phase:** Gate 2 live pilot · **Baseline:** `v0.1.0-batch1` @ `649967a`  
> **Tenant:** `naagarjuna` · **Wedge:** Class 10 Mathematics · Telangana SSC  
> **Primary objective:** **Learn from the pilot** — not build new features.

---

## Purpose

Record significant pilot feedback with a clear **decision**, **priority**, and **batch assignment**. This log is the audit trail for why product and engineering choices were made — preventing anecdotal feedback from becoming unplanned development.

| Document | Role |
|----------|------|
| **This log** | Structured feedback → decision → batch (table below) |
| [`gate2/PILOT_DECISIONS.md`](./gate2/PILOT_DECISIONS.md) | Narrative decision register (scope, product, process) |
| [`gate2/GATE2_DAILY_PILOT_LOG_TEMPLATE.md`](./gate2/GATE2_DAILY_PILOT_LOG_TEMPLATE.md) | Daily operator notes |
| [`gate2/GATE2_FEEDBACK_COLLECTION_TEMPLATE.md`](./gate2/GATE2_FEEDBACK_COLLECTION_TEMPLATE.md) | Structured HOD/teacher feedback forms |

---

## Triage buckets (mandatory)

Every observation must be classified before action:

| Bucket | Definition | Action during Batch 1 pilot |
|--------|------------|----------------------------|
| **Critical defect** | Prevents or significantly disrupts pilot operation | **Only** code changes allowed — PO-approved patch on `v0.1.0-batch1` |
| **Operational improvement** | Docs, training, runbooks, deployment, configuration | Update ops docs / procedures — no core architecture change |
| **Product opportunity** | Useful idea or requested capability | Log here → **Batch 2 backlog** — do not implement now |

**Architecture is frozen** during the pilot. See [`GATE2_GO.md`](./GATE2_GO.md) and [`../BATCH1_BASELINE_CERTIFICATE.md`](../BATCH1_BASELINE_CERTIFICATE.md).

---

## Priority (required)

| Priority | Meaning | Typical use |
|----------|---------|-------------|
| **P0** | Immediate — pilot blocker | Critical defect; same-day or next-session response |
| **P1** | High | Significant pilot friction; address during pilot (ops or patch) |
| **P2** | Medium | Valuable improvement; Batch 2 candidate with clear demand signal |
| **P3** | Future | Nice-to-have; backlog without near-term commitment |

Priority prevents the Batch 2 backlog from becoming a flat list of ideas. At pilot exit, sort by P0→P3 for roadmap planning.

---

## Status values

| Status | Meaning |
|--------|---------|
| **Open** | Logged; not yet triaged or owned |
| **Accepted** | Decision approved; work authorized per batch rules |
| **Deferred** | Valid but not now — revisit at exit review |
| **Completed** | Action done (patch shipped, doc updated, etc.) |
| **Rejected** | Will not pursue (with reason in Decision column) |

---

## Decision log

| Date | Source | Observation | Evidence | Decision | Batch | Priority | Owner | Status |
|------|--------|-------------|----------|----------|-------|----------|-------|--------|
| 2026-07-20 | PO / Engineering | Batch 1 baseline released; Gate 2 GO declared | [`GATE2_GO.md`](./GATE2_GO.md), tag `v0.1.0-batch1` | Pilot authorized; learn-first operating mode | Pilot ops | P0 | PO | Completed |
| 2026-07-20 | PO | Use placeholder SSC Class 10 Maths seed until HOD supplies official syllabus | T-0 preflight, [`PILOT_DECISIONS.md`](./gate2/PILOT_DECISIONS.md) | HOD validates pack Day 1; no schema change | Pilot ops | P1 | PO | Open |
| | | | | | | | | |

---

## How to add an entry

1. Capture **observation** from school session, feedback form, or ops.
2. Link **evidence** (daily log date, screenshot, log excerpt — no PII in repo).
3. Classify **bucket** (critical / operational / product).
4. Record **decision** in one sentence.
5. Assign **batch**: `Batch 1 patch` · `Pilot ops` · `Batch 2` · `Won't do` · `Defer`.
6. Set **priority**: P0 · P1 · P2 · P3.
7. Assign **owner** and **status** (default: Open until weekly review).

### Example rows (illustrative — remove when real entries accumulate)

| Date | Source | Observation | Evidence | Decision | Batch | Priority | Owner | Status |
|------|--------|-------------|----------|----------|-------|----------|-------|--------|
| 2026-07-22 | HOD | QP approval flow felt slow | Session notes W1D2 | Improve approval UX | Batch 2 | P2 | PO | Accepted |
| 2026-07-23 | Teacher | Wanted manual difficulty override | Feedback form T-01 | Accepted for roadmap | Batch 2 | P2 | PO | Accepted |
| 2026-07-24 | Pilot ops | API timeout during QP generation | API logs, incident #001 | Patch timeout handling | Batch 1 patch | P0 | Engineering | Open |

---

## Weekly review (standing)

| Week | Reviewer | New entries | P0 open | Promoted to Batch 2 | Completed |
|------|----------|-------------|---------|---------------------|-----------|
| W1 | | | | | |

At Gate 2 exit, export P1–P3 **Accepted** items as prioritized Batch 2 input; summarize in [`gate2/GATE2_EXIT_REVIEW_TEMPLATE.md`](./gate2/GATE2_EXIT_REVIEW_TEMPLATE.md).

---

## Rules

- **No code** for Product opportunity items during the pilot (unless reclassified as Critical defect).
- **No architecture redesign** under any bucket without explicit PO authorization post-pilot.
- Critical defects require evidence before fix; tag patches from `v0.1.0-batch1` when released.
- Superseded decisions stay in the table with a note — do not delete rows.
- After this log was established, `develop` accepts only **critical production defect patches** or **pilot-generated documentation updates**.

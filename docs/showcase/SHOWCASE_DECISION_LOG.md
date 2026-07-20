# Showcase Decision Log — Reference School Operations

> **Environment:** StudyNexs Reference School (Showcase)  
> **Baseline:** `v0.1.0-batch1` @ `649967a`  
> **Tenant slug (current):** `naagarjuna` — Phase B target: `showcase`  
> **Purpose:** Record ops decisions for the **demonstration environment** — not customer pilot feedback

---

## Purpose

Record significant Showcase observations with **decision**, **priority**, **owner**, and **status**. Customer-specific prospect notes belong in [`discovery/schools/`](../discovery/schools/). Signed-school pilot decisions belong in [`customer-pilot/`](../customer-pilot/).

| Document | Role |
|----------|------|
| **This log** | Showcase ops — structured table |
| [`customer-pilot/CUSTOMER_PILOT_DECISIONS.md`](../customer-pilot/CUSTOMER_PILOT_DECISIONS.md) | Post-signing customer pilot |
| [`discovery/`](../discovery/) | Pre-signing prospect records |

---

## Triage buckets

| Bucket | Definition | Action on Showcase baseline |
|--------|------------|----------------------------|
| **Critical defect** | Blocks sales demo or platform validation | PO-approved patch on `v0.1.0-batch1` |
| **Operational improvement** | Docs, demo script, runbooks, config | Update showcase ops docs |
| **Product opportunity** | Feature idea from demo feedback | Batch 2 backlog — do not implement now |

---

## Priority

| Priority | Meaning |
|----------|---------|
| **P0** | Immediate — demo blocker |
| **P1** | High — significant demo friction |
| **P2** | Medium — Batch 2 candidate |
| **P3** | Future — backlog |

## Status

Open · Accepted · Deferred · Completed · Rejected

---

## Decision log

| Date | Source | Observation | Evidence | Decision | Batch | Priority | Owner | Status |
|------|--------|-------------|----------|----------|-------|----------|-------|--------|
| 2026-07-20 | PO / Engineering | Batch 1 baseline released; Showcase GO | [`SHOWCASE_GO.md`](./SHOWCASE_GO.md), tag `v0.1.0-batch1` | Reference School authorized for sales demos | Showcase ops | P0 | PO | Completed |
| 2026-07-20 | PO | Doc split: Showcase vs Customer Pilot vs Discovery | Phase A refactor | Separate customer journey from release lifecycle | Showcase ops | P1 | PO | Completed |
| | | | | | | | | |

---

## Rules

- No customer-specific school data in this log — use `discovery/schools/<slug>/`.
- No Customer Pilot execution until contract + onboarding complete.
- Architecture frozen per [`BATCH1_BASELINE_CERTIFICATE.md`](../../BATCH1_BASELINE_CERTIFICATE.md).

# Gate 2 Pre-flight Checklist

> **Baseline:** `v0.1.0-batch1` · tenant `naagarjuna` · Class 10 Maths wedge  
> **Use:** Complete **T-7 through T-0** (pilot day). All items must be ✅ or explicitly waived with owner sign-off.

---

## Sign-off block

| Role | Name | Date | Signature / OK |
|------|------|------|----------------|
| Product owner | | | |
| Pilot lead (ops) | | | |
| Engineering on-call | | | |
| School HOD contact | | | |

**Go / No-go decision:** ☐ Go  ☐ No-go  ☐ Go with conditions (list below)

**Conditions / waivers:**

---

## A. Baseline & change control

| # | Check | Owner | T-7 | T-1 | T-0 |
|---|-------|-------|-----|-----|-----|
| A1 | Deployed commit matches tag **`v0.1.0-batch1`** (`git describe --tags`) | Eng | ☐ | ☐ | ☐ |
| A2 | No unapproved feature work on pilot branch during active pilot | PO | ☐ | ☐ | ☐ |
| A3 | [PILOT_FEEDBACK_LOG.md](../../product/PILOT_FEEDBACK_LOG.md) ready for issue intake | Eng | ☐ | ☐ | ☐ |
| A4 | Rollback plan reviewed ([GATE2_ROLLBACK_PLAN.md](./GATE2_ROLLBACK_PLAN.md)) | Eng | ☐ | ☐ | ☐ |
| A5 | Daily log + feedback templates printed or bookmarked | Ops | ☐ | ☐ | ☐ |

---

## B. School inputs (pack checklist)

| # | Check | Owner | Status |
|---|-------|-------|--------|
| B1 | Class 10 Maths syllabus / chapter list received | HOD | ☐ Received ☐ Placeholder seed ☐ Waived |
| B2 | One sample board-style paper + marking scheme | HOD | ☐ ☐ ☐ |
| B3 | Blueprint / weightage table (if separate) | HOD | ☐ ☐ ☐ |
| B4 | Exam in-charge + Maths teacher contacts confirmed | PO | ☐ |
| B5 | 10 redacted answer sheets committed for eval tuning | HOD | ☐ ☐ Waived (manual eval only) |
| B6 | Parent/student consent approach documented | PO | ☐ |
| B7 | No full textbook PDFs stored — structured maps only | Legal/PO | ☐ |

---

## C. Environment (see [GATE2_ENVIRONMENT_VALIDATION.md](./GATE2_ENVIRONMENT_VALIDATION.md))

| # | Check | Owner | T-1 | T-0 |
|---|-------|-------|-----|-----|
| C1 | PostgreSQL up; Batch 1 schema applied | Eng | ☐ | ☐ |
| C2 | Redis up | Eng | ☐ | ☐ |
| C3 | Qdrant up; collections reachable from API | Eng | ☐ | ☐ |
| C4 | API image includes **`[rag]`** (`qdrant_client` import OK) | Eng | ☐ | ☐ |
| C5 | LLM gateway keys configured; credits sufficient for pilot week | Eng | ☐ | ☐ |
| C6 | `smoke_pilot_readiness.py` exits 0 | Eng | ☐ | ☐ |
| C7 | Admin UI 11-step workflow re-run OR spot-check on pilot env | Eng | ☐ | ☐ |
| C8 | API URL = `http://localhost:8000` (not ghost on `127.0.0.1:8000`) | Eng | ☐ | ☐ |
| C9 | Admin web on allowed port (3003) with `NEXT_PUBLIC_TENANT_SLUG=naagarjuna` | Eng | ☐ | ☐ |
| C10 | CORS allows admin-web origin | Eng | ☐ | ☐ |

---

## D. Accounts & access

| # | Check | Owner | Status |
|---|-------|-------|--------|
| D1 | `seed_pilot_naagarjuna.py` run (idempotent) | Eng | ☐ |
| D2 | `seed_pilot_naagarjuna_curriculum.py` run or pack entered via UI | Eng/HOD | ☐ |
| D3 | Login verified: `principal`, `maths_teacher`, `incharge` | Eng | ☐ |
| D4 | Demo passwords communicated securely (not in public channels) | Ops | ☐ |
| D5 | School Wi‑Fi / device plan for teacher laptops | Ops | ☐ |

| Portal | Username | Password | Role |
|--------|----------|----------|------|
| Staff | `principal` | `Demo@1234` | Principal / dashboard |
| Teacher | `maths_teacher` | `Demo@1234` | QP, eval, tutor wedge |
| Teacher | `incharge` | `Demo@1234` | Approve papers & marks |
| Parent | `parent_demo` | `Demo@1234` | Read-only progress |
| Student | `student_demo` | `Demo@1234` | Tutor demo |

---

## E. Expectations & messaging

| # | Check | Owner | Status |
|---|-------|-------|--------|
| E1 | HOD briefed: manual pack entry (no PDF ingestion) | PO | ☐ |
| E2 | Teachers briefed: lesson plans are template-first; provenance is real | PO | ☐ |
| E3 | Eval limits reviewed ([CLASS_10_MATHS_EXAM_LOOP.md](../CLASS_10_MATHS_EXAM_LOOP.md)) | PO | ☐ |
| E4 | AI is HITL — nothing published without teacher approve | PO | ☐ |
| E5 | Tutor not pack-grounded (Batch 2) — set expectations | PO | ☐ |
| E6 | Backup QP pre-approved if live generation slow ([BACKLOG DEMO-03](../../BACKLOG.md)) | Eng | ☐ |

---

## F. Support & incident readiness

| # | Check | Owner | Status |
|---|-------|-------|--------|
| F1 | On-call engineer identified + contact shared with ops | Eng | ☐ |
| F2 | Escalation path: Sev-1 (tenant leak, data loss) → immediate rollback | Eng | ☐ |
| F3 | Rollback artifacts: DB snapshot / compose down procedure tested | Eng | ☐ |
| F4 | [GATE2_RISK_REGISTER.md](./GATE2_RISK_REGISTER.md) reviewed; owners assigned | PO | ☐ |
| F5 | School IT contact for network/firewall issues | Ops | ☐ |

---

## G. Demo dry run

| # | Check | Owner | Status |
|---|-------|-------|--------|
| G1 | Full HOD workflow dry-run ([GATE2_DEMO_SCRIPT.md](./GATE2_DEMO_SCRIPT.md) § HOD) | Pilot lead | ☐ |
| G2 | Full Teacher workflow dry-run (§ Teacher) | Pilot lead | ☐ |
| G3 | Timing recorded; slow steps noted (QP gen ~90s) | Pilot lead | ☐ |
| G4 | Screenshots / screen share tested on school projector if applicable | Ops | ☐ |

---

## No-go triggers (any one = stop)

- Cross-tenant data visible in UI or API
- Login or core academic APIs return 5xx for all pilot accounts
- Pack approve fails (RAG index) without workaround
- LLM gateway unavailable with no pre-approved backup QP
- School has not accepted HITL + eval limit positioning in writing or meeting notes

---

## Post-check actions

1. File completed checklist in pilot folder: `docs/pilot/naagarjuna-talent-school/preflight-YYYY-MM-DD.md`
2. Open Day 1 entry in [GATE2_DAILY_PILOT_LOG_TEMPLATE.md](./GATE2_DAILY_PILOT_LOG_TEMPLATE.md)
3. Proceed per [GATE2_PILOT_EXECUTION_PLAN.md](./GATE2_PILOT_EXECUTION_PLAN.md)

# Gate 2 Pilot Execution Plan

> **Baseline:** `v0.1.0-batch1`  
> **School:** Naagarjuna Talent School (design partner)  
> **Duration:** 8 weeks (adjustable); **intensive phase:** Weeks 1–2  
> **Wedge:** Class 10 Mathematics — curriculum pack → grounded QP → exam eval → weak topics → tutor

---

## 1. Objectives

| Objective | Success signal |
|-----------|----------------|
| Validate Batch 1 Curriculum Intelligence in a real school context | HOD approves at least one pack from school syllabus |
| Prove teacher HITL workflow end-to-end | QP + marks approved by teacher; zero auto-publish |
| Collect eval accuracy signal on ~10 answer sheets | Teacher agrees AI assists ≥70% objective/short Qs |
| Measure teacher confidence and time saved | Feedback scores + daily log themes |
| Produce Gate 2 exit decision | [GATE2_EXIT_REVIEW_TEMPLATE.md](./GATE2_EXIT_REVIEW_TEMPLATE.md) completed |

---

## 2. Scope

### In scope

- Tenant `naagarjuna` — Class 10 Maths only
- Curriculum pack: create/edit/approve (manual entry)
- Grounded lesson plan (provenance demo)
- Grounded AI question paper → teacher edit → approve
- Answer sheet upload → vision eval → teacher override → approve
- Weak-topic / topic mastery views
- AI tutor for flagged mistakes (opt-in students)
- Principal dashboard snapshot (visibility, not wedge)
- Parent demo account (read-only, opt-in narrative)

### Out of scope (explicit no)

- Full-school ERP go-live
- Batch 2 features (pack-aligned eval, pack-grounded tutor, PDF ingestion)
- Online fee collection (Razorpay)
- WhatsApp mass messaging
- Flutter native apps
- Other classes/subjects unless PO authorizes expansion

---

## 3. Roles & RACI

| Activity | Product owner | Pilot lead | Eng on-call | HOD | Maths teacher | School IT |
|----------|---------------|------------|-------------|-----|---------------|-----------|
| Go/no-go preflight | A | R | C | I | I | I |
| Pack data entry | C | C | I | A/R | R | — |
| Daily smoke / env | I | R | A | — | — | C |
| Teacher training | A | R | C | C | R | — |
| Issue triage | A | R | R | I | I | C |
| Rollback decision | A | R | R | I | I | — |
| Exit review | A | R | C | R | R | — |

*R = Responsible, A = Accountable, C = Consulted, I = Informed*

---

## 4. Timeline

### Phase 0 — Pre-flight (T-7 to T-0)

- Complete [GATE2_PREFLIGHT_CHECKLIST.md](./GATE2_PREFLIGHT_CHECKLIST.md)
- Run [GATE2_ENVIRONMENT_VALIDATION.md](./GATE2_ENVIRONMENT_VALIDATION.md)
- Dry-run [GATE2_DEMO_SCRIPT.md](./GATE2_DEMO_SCRIPT.md)
- Collect school pack inputs (or approve placeholder seed)

### Phase 1 — Kickoff (Week 1)

| Day | Activity | Deliverable |
|-----|----------|-------------|
| D1 | Kickoff meeting + HOD workflow (pack approve) | Pack draft started |
| D2 | Teacher workshop: QP generation + HITL | 1 QP approved |
| D3 | Teacher workshop: eval + limits briefing | 2–3 sheets trialed |
| D4 | Weak topics + tutor demo | Teacher feedback form |
| D5 | Week 1 retrospective + log | Daily logs filed |

### Phase 2 — Steady operation (Weeks 2–4)

- Weekly cadence: 1 class test cycle (QP → exam → eval → report)
- Daily: smoke check + [daily log](./GATE2_DAILY_PILOT_LOG_TEMPLATE.md)
- Bi-weekly: PO + HOD sync (30 min)
- Log all issues in [PILOT_FEEDBACK_LOG.md](../../product/PILOT_FEEDBACK_LOG.md)

### Phase 3 — Validation (Weeks 5–6)

- Complete 10-sheet eval set (if collected)
- Compare weak-topic report vs teacher judgment
- Mid-pilot feedback collection ([template](./GATE2_FEEDBACK_COLLECTION_TEMPLATE.md))

### Phase 4 — Exit (Weeks 7–8)

- Final feedback from HOD + teachers
- Complete [GATE2_EXIT_REVIEW_TEMPLATE.md](./GATE2_EXIT_REVIEW_TEMPLATE.md)
- Decision: extend / expand subject / pause / commercial next step

---

## 5. Weekly cadence (standing)

| When | What | Owner |
|------|------|-------|
| Daily 08:00 | `smoke_pilot_readiness.py` + quick UI login | Eng on-call |
| Daily EOD | Daily pilot log entry | Pilot lead |
| Monday | Review risk register; update mitigations | PO |
| Wednesday | Check LLM usage/credits | Eng |
| Friday | Weekly summary to PO; feedback themes | Pilot lead |

---

## 6. Communication plan

| Audience | Channel | Frequency |
|----------|---------|-----------|
| School HOD | WhatsApp / phone (designated contact) | As needed; weekly summary |
| Teachers | In-person + written one-pager on eval limits | Week 1; reminders as needed |
| Internal team | Shared doc + feedback log | Daily during Week 1; weekly after |
| Escalation | Phone → on-call engineer | Sev-1/2 only |

**Messaging anchors:**

- AI **suggests**; teachers **approve**
- Pilot is Class 10 Maths only
- Demo data vs live school data clearly labeled in UI where applicable

---

## 7. Data handling (DPDP)

- Minimize PII in pilot logs — use roll numbers / redacted sheets only
- No student names in GitHub issues or public channels
- Answer sheets stored per school agreement; retention period documented with HOD
- No logging of credentials or tokens

---

## 8. Dependencies

| Dependency | Fallback |
|------------|----------|
| OpenAI / LLM provider | Pre-approved backup QP; template lesson plan |
| Qdrant | Block pack approve until restored; use last approved pack |
| School network | Mobile hotspot kit; offline talking points |
| Teacher availability | Record Loom/async for missed sessions |

---

## 9. Artifacts produced during pilot

| Artifact | Location |
|----------|----------|
| Pre-flight checklist copy | `docs/pilot/naagarjuna-talent-school/preflight-*.md` |
| Daily logs | `docs/pilot/naagarjuna-talent-school/daily-log-*.md` |
| Feedback forms | `docs/pilot/naagarjuna-talent-school/feedback-*.md` |
| Issue triage | [PILOT_FEEDBACK_LOG.md](../../product/PILOT_FEEDBACK_LOG.md) |
| Exit review | `docs/pilot/naagarjuna-talent-school/exit-review-*.md` |

---

## 10. Authorization gates

| Gate | Approver | Criteria |
|------|----------|----------|
| Pilot start | PO | Pre-flight ✅ |
| Code change during pilot | PO + Eng | Defect with evidence; logged in feedback log |
| Scope expansion (class/subject) | PO | Exit review or mid-pilot amendment |
| Batch 2 work | PO | Explicit written authorization only |

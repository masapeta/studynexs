# Phase 1 Exit Checklist

> Owner: Avinash Reddy Masapeta (ARM)  
> **Purpose:** Single gate for “Phase 1 complete → start Phase 1.5.”  
> Living status: [STATUS.md](./STATUS.md) · Execution: [TRACK_AB_EXECUTION.md](./TRACK_AB_EXECUTION.md) · Vision: [PRODUCT.md](./PRODUCT.md)

---

## What Phase 1 is

**Pilot-ready SMS on `admin-web` + teacher AI wedge** — not full ERP, not CurriculumPack, not mobile.

| Pillar | Deliverable |
|--------|-------------|
| **7A** | Question papers — generate, edit, HITL approve, export |
| **7B** | Assisted grading — AI suggests, teacher approves → `exam_marks` |
| **7C** | Student summary — AI report-card narrative from marks + attendance |
| **Cross-cutting** | Metering, HITL, tenant isolation; no parent-facing AI without approval |
| **SMS** | Admin UI covers the **pilot school’s forced top-3** only |

**Out of Phase 1:** CurriculumPack, Mistake Recovery Tutor, Flutter, parent/student portals, platform-web, full finance/Razorpay (unless in pilot top-3), library/events UI, §7.6 premium features.

---

## Already built (don’t rebuild)

Use this section to avoid scope creep.

- [x] Phase 0 — LLM gateway, auth, tenant, AI metering, jobs infra
- [x] AI question papers — generate, edit, approve, export (HTML print)
- [x] AI credits + principal usage visibility
- [x] Report cards — AI draft, HITL approve, export
- [x] Mastery — compute, heatmap, flags, digest narratives
- [x] Exams API + marks UI + question schema editor
- [x] Question bank ingest on approve + `generate-from-bank`
- [x] Answer-sheet eval v1 — upload/OCR, async job, HITL approve, corrections, misconception library (basic)
- [x] Demo seed (SSC school) + admin-web pages wired

---

## Track A — Business validation

**Done when all checked OR you have a clear POLITE NO.**

### A1 — Pilot discovery meeting

- [ ] Demo URL or local stack ready (`api` + `admin-web`)
- [ ] Live QP generation on screen (Class 10 Maths or pilot subject)
- [ ] Approve → export/print flow shown
- [ ] [PILOT_DISCOVERY.md](./PILOT_DISCOVERY.md) questions asked
- [ ] [Pilot Outcome Sheet](./pilot/PILOT_OUTCOME_SHEET.md) filled → `docs/pilot/<school-slug>/`
- [ ] **Forced top-3** features captured
- [ ] Price reaction recorded
- [ ] Exam in-charge + 1 teacher contact captured
- [ ] Verdict: **REAL INTEREST** or **POLITE NO**

### A2 — Pack inputs (one class × subject)

| # | Input | Received |
|---|--------|----------|
| 1 | Board (SSC / CBSE / State) | ☐ |
| 2 | Class & subject | ☐ |
| 3 | Textbook name, publisher, edition | ☐ |
| 4 | Term syllabus (chapters this term) | ☐ |
| 5 | TOC / index | ☐ |
| 6 | Exam blueprint (if used) | ☐ |
| 7 | One previous question paper | ☐ |
| 8 | Sample marking notes (optional) | ☐ |
| 9 | HOD / exam in-charge contact | ☐ |

Store references in `docs/pilot/<school-slug>/` (no full copyrighted books in git).

### A3 — Blueprint verification

Requires A2 item 7 (real sample paper).

- [ ] Section names and counts match
- [ ] Marks per section match school total
- [ ] Internal choice rules match (“answer any N of M”)
- [ ] Question types match (VSA / SA / LA / MCQ)
- [ ] StudyNexs paper generated side-by-side with sample
- [ ] Gaps documented in `docs/pilot/<school>/blueprint-gap-notes.md`
- [ ] Critical gaps fixed in `question_paper_service` before promising school

---

## Track B — Engineering hardening

### B1 — Question paper (wedge)

- [ ] A3 complete or gaps accepted with school
- [ ] Teacher can edit all sections before approve
- [ ] Approved paper persists and re-opens correctly
- [ ] User-friendly errors on AI failure / credit limits
- [ ] Rate limits tested (won’t blow pilot budget in demo)
- [ ] Export limitation documented (HTML print-to-PDF; not WeasyPrint yet)

### B2 — Pilot-blocker UIs (**only items in forced top-3**)

Fill after A1. Default exam-wedge candidates:

| Priority | Item | Needed? | Done? |
|----------|------|---------|-------|
| P0 | AI Papers — approve/export harden | Almost always | ☐ |
| P0 | Exams + marks / eval flow polish | If marks in system | ☐ |
| P0 | Report cards E2E | If in top-3 | ☐ |
| P1 | Settings (profile, academic year) | If term rollover | ☐ |
| P1 | Notices — wire “New Notice” | If comms in top-3 | ☐ |
| P1 | Finance — fee payment UI | **Only if fees in top-3** | ☐ |
| P2 | Timetable polish | Only if in top-3 | ☐ |
| Skip | Library / events placeholders | Unless named | — |

### B3 — Tests

```powershell
cd apps\api
pytest tests/ -q
pytest tests_security/ -q
cd ..\admin-web
node e2e-smoke.cjs
```

- [ ] Backend tests pass (record count in STATUS.md when updating)
- [ ] `test_question_bank*.py` + `test_answer_sheet_eval.py` pass
- [ ] e2e-smoke passes or blockers documented

### B4 — AI unit economics

| Task | Provider A | Provider B | Provider C |
|------|------------|------------|------------|
| 1× QP generate (pilot class/subject) | | | |
| 1× report card remark | | | |
| 1× answer-sheet eval (with image if used) | | | |

- [ ] Default provider chosen for pilot
- [ ] Rough ₹/student/month at expected usage documented
- [ ] Result noted in [DECISION_LOG.md](./DECISION_LOG.md)

### B5 — Demo stability

- [ ] `python scripts/smoke_demo_readiness.py` passes
- [ ] No secrets in git; `.env` local only
- [ ] Demo commit hash noted on Pilot Outcome Sheet
- [ ] [STATUS.md](./STATUS.md) snapshot updated (eval, bank, etc.)

### B6 — Exam eval ops (if eval in pilot scope)

- [ ] `alembic upgrade head` through `l2f8g4b6c0d` on demo DB
- [ ] Arq worker documented: `arq app.core.jobs.worker.WorkerSettings`
- [ ] `GEMINI_API_KEY` or `OPENAI_API_KEY` set for vision OCR
- [ ] One real handwritten sheet trial (or documented fallback: manual answers only)

---

## Compliance (if real student data)

Skip for synthetic demo-only pilot; **required** before production student PII.

- [ ] Privacy notice drafted
- [ ] Parental consent process defined
- [ ] Retention policy documented
- [ ] DPDP purpose tags reviewed for pilot AI features

Password login OK for pilot; **MSG91 OTP** only if shipping OTP-first production login.

---

## Phase 1 exit gate → Phase 1.5

**Do not start CurriculumPack (8-week plan) until all are true:**

- [ ] A1: REAL INTEREST + top-3 + price + contact
- [ ] A2: inputs 1–7 for one subject
- [ ] A3: blueprint verified or gaps fixed
- [ ] B1: QP demo-ready for that subject
- [ ] B2: top-3 features work in UI
- [ ] B3: tests green
- [ ] B4: provider + unit economics
- [ ] Compliance minimal (if real student data)

When complete:

1. Update [STATUS.md](./STATUS.md) — mark Phase 1 ✅, date snapshot  
2. Log pilot name, top-3, pricing in [DECISION_LOG.md](./DECISION_LOG.md)  
3. Begin [Phase 1.5 Week 1](./STATUS.md#8-week-build-plan-phase-15) — `CurriculumPack` data model  

---

## Explicitly deferred (not Phase 1 blockers)

| Item | When |
|------|------|
| Fee UI + Razorpay | Pilot top-3 or Phase 2b |
| Library / Events UI | Only if school asks |
| teacher / parent / student / platform portals | Phase 2+ |
| Flutter apps | Phase 2 |
| WhatsApp / SMS / email delivery | Pilot one use-case max, else Phase 2 |
| CurriculumPack + RAG | Phase 1.5 |
| Blueprint intelligence, remedial packs, inspection/PTA | After pilot proves exam wedge |
| WeasyPrint PDF, Azure Blob, CI/CD | Production hardening parallel track |

---

## Related

| Doc | Use |
|-----|-----|
| [TRACK_AB_EXECUTION.md](./TRACK_AB_EXECUTION.md) | Week-by-week calendar |
| [PILOT_DISCOVERY.md](./PILOT_DISCOVERY.md) | Meeting script |
| [PRICING.md](./PRICING.md) | Tiers and pilot packaging |

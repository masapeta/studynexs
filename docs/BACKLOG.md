# StudyNexs — Enhancement Backlog

> Owner: Avinash Reddy Masapeta (ARM) · **Living inbox** for product enhancements discussed in chat, pilot meetings, and reviews.  
> **Not** a substitute for [PRODUCT.md](./PRODUCT.md) (vision) or [STATUS.md](./STATUS.md) (build truth).  
> **Companions:** [DECISION_LOG.md](./DECISION_LOG.md) · [TRACK_AB_EXECUTION.md](./TRACK_AB_EXECUTION.md) · [PILOT_DISCOVERY.md](./PILOT_DISCOVERY.md)

---

## Three gates (execution order)

**Rule:** Do not boil the ocean. Finish the gate you're in before pulling work from the next.

| Gate | Goal | Real data? | When |
|------|------|------------|------|
| **Gate 1 — Demo polish** | Confidence + hands-on walkthrough | **No** — synthetic demo school only | Before today's demo / school walkthrough |
| **Gate 2 — Controlled pilot** | School uses product narrowly; you improve weekly | **Yes** — one class/subject wedge + opt-in parents | After signed pilot scope + consent |
| **Gate 3 — Parent/student production** | Enterprise hardening at scale | **Yes** — full rollout | After Gate 2 proves value |

### Gate 2 engineering priority (solo builder)

1. Async AI workers (QP, report cards, answer-sheet eval)
2. Cloud file storage + upload scanning/quarantine
3. CI/CD pipeline
4. Consent + parent onboarding workflow
5. Real notification delivery (SMS/email; WhatsApp later)
6. Production observability
7. Tenant hardening (subdomain-first, security tests in prod mode)
8. AI quality / eval harness

---

## Gate 1 — Before demo / walkthrough (presentation only)

Focus: **confidence and clarity**. No production infra, no real PII.

| ID | Task | Status | Notes |
|----|------|--------|-------|
| G1-01 | Visible **“Demo data”** banner in UI (not live parent/student data) | ✅ | `DemoDataBanner`; tenant `test` / `demo`, `development`, or `NEXT_PUBLIC_DEMO_MODE=true` |
| G1-02 | Pre-seed **one clean E2E journey**: principal → teacher → QP → marks/eval → report card → parent view | ⬜ | See seed scripts + DEMO-03 below |
| G1-03 | **AI fallback** on heavy screens (timeout → show pre-approved draft or stub message) | ⬜ | Partial: report card has stub fallback; QP needs backup paper |
| G1-04 | **Hide or label** incomplete modules (payments, full notifications, parent rollout at scale) | ⬜ | Roadmap page or “Preview” badges |
| G1-05 | **“Not live yet”** talking points: privacy, consent, storage, parent onboarding | ⬜ | Verbal + optional 1-pager; see G1-06 |
| G1-06 | Hands-on **cheat sheet** + optional `docs/pilot/HANDS_ON_RUNBOOK.md` | ✅ | [HANDS_ON_RUNBOOK.md](./pilot/HANDS_ON_RUNBOOK.md) |
| G1-07 | Deploy **HTTPS URL** (not localhost) | ⬜ | DEMO-02 |
| G1-08 | Run `smoke_demo_readiness.py` + `e2e-smoke.cjs` | 🟡 | DEMO-04; Playwright in package.json |
| G1-09 | **Own Gemini key** or pre-approved QP backup | ⬜ | DEMO-05, DEMO-03 |

**Explicitly out of Gate 1:** Azure Blob, CI/CD, consent product, async workers, malware scan, subdomain tenant routing.

---

## Gate 2 — Before first controlled school pilot

School runs **real** workflows on a **bounded** scope (one class × subject; opt-in parents). Engineering time goes here after demo + signed pilot sheet.

| ID | Task | Status | Notes |
|----|------|--------|-------|
| G2-01 | **Async AI jobs** (Arq): QP, report cards, answer-sheet vision/eval | ⬜ | PROD-06; return job id |
| G2-02 | **Job status UI**: queued → running → failed/retry → complete | ⬜ | Frontend polling |
| G2-03 | **Azure Blob** (or S3-compatible) for uploads | ⬜ | PROD-01 |
| G2-04 | **Malware scan / quarantine** on admission + answer-sheet uploads | ⬜ | ClamAV or cloud scanner |
| G2-05 | **CI/CD**: pytest, tests_security, frontend build, migration smoke | ⬜ | PROD-05 |
| G2-06 | **Consent workflow** before parent/student accounts enabled | ⬜ | PROD-07, DEMO-06 |
| G2-07 | **Notification providers**: SMS + email (WhatsApp/push later) | ⬜ | COMMS-01 |
| G2-08 | **Observability**: API latency, errors, AI failures, queue depth, upload failures | ⬜ | OTEL partial today |
| G2-09 | **Production-mode security tests** (not only `ENVIRONMENT=testing`) | ⬜ | tests_security in CI |
| G2-10 | Pilot **tenant** + white-glove onboarding (one class CSV) | ⬜ | Separate from `test` demo school |
| G2-11 | **Weekly feedback** loop → BACKLOG | ⬜ | Process, not code |
| G2-12 | **CurriculumPack** + school syllabus inputs for pilot subject | 🟡 | EXAM-01 |

**Explicitly out of Gate 2 (unless school top-3):** Full-school rollout, Flutter apps, Razorpay live, PostgreSQL RLS, load tests.

---

## Gate 3 — Before real parent/student production at scale

Serious hardening. After Gate 2 success.

| ID | Task | Status | Notes |
|----|------|--------|-------|
| G3-01 | **Subdomain-first tenant** routing; don't trust public `X-Tenant-Slug` alone | ⬜ | Cross-check JWT school_id |
| G3-02 | **Backup/restore runbook** with tested recovery | ⬜ | |
| G3-03 | **Key Vault** (or equivalent) for all secrets | ⬜ | PROD-02 decided pattern |
| G3-04 | **Audit logs** for sensitive actions (login, file access, reports, parent invite, marks approve) | 🟡 | Audit exists; expand coverage |
| G3-05 | **Retention / deletion / export** workflows (DPDP) | ⬜ | PROD-07 |
| G3-06 | **Role-boundary review** (teacher, incharge, parent, student) | 🟡 | Partial; test_authorization.py |
| G3-07 | **HITL enforced** on all consequential AI outputs | 🟡 | QP/report approve flows exist |
| G3-08 | **AI eval harness**: golden papers, grading samples, prompt-injection tests | 🟡 | test_ai_hardening partial |
| G3-09 | **Load tests** around exam-week workflows | ⬜ | locustfile exists |
| G3-10 | **Security headers + CSP** (Next.js + Nginx) | ⬜ | |
| G3-11 | **Razorpay webhook** signature verification | ⬜ | PROD-08 |
| G3-12 | Aadhaar: **don't store** or encrypt at rest | ⬜ | PROD-10 |

---

## How to use this file

1. **Capture** — When a new idea comes up (chat, school call, review), add a row below with `source` and `status: proposed`.
2. **Decide** — If it's a real commitment, log the *why* in [DECISION_LOG.md](./DECISION_LOG.md) and update `status: decided`.
3. **Build** — Move to [STATUS.md](./STATUS.md) when work starts; mark `done` here when shipped.
4. **Pilot-only** — If a school names it in forced top-3, also note in `docs/pilot/<school>/outcome-*.md`.

### Status values

| Status | Meaning |
|--------|---------|
| `proposed` | Discussed, not committed |
| `decided` | Agreed in DECISION_LOG or pilot sheet |
| `in_progress` | Active engineering |
| `done` | Shipped (link commit or STATUS) |
| `deferred` | Valid but explicitly not now |
| `rejected` | We chose not to do it (note why) |

### Priority (for solo builder)

| P | When |
|---|------|
| **P0** | Blocks pilot demo or signed deal |
| **P1** | First 8 weeks after pilot signs |
| **P2** | Phase 2+ |
| **P3** | Vision / nice-to-have |

---

## Pilot & demo (from discussions 2026-06)

| ID | Enhancement | Priority | Status | Phase | Source | Notes |
|----|-------------|----------|--------|-------|--------|-------|
| DEMO-01 | **55-min full platform demo runbook** (admin → teacher → parent phone → student tutor) | P0 | proposed | Pre-pilot | Chat 2026-06 | Script exists in chat; promote to `docs/pilot/DEMO_RUNBOOK.md` or extend PILOT_DISCOVERY |
| DEMO-02 | Deploy **HTTPS demo URL** (not localhost) for school meeting | P0 | proposed | Pre-pilot | Chat 2026-06 | Blocker for credible pilot |
| DEMO-03 | **Pre-approve one Class 10 Maths QP** before live meeting (backup if API slow) | P0 | proposed | Pre-pilot | Chat 2026-06 | |
| DEMO-04 | Run full **seed stack** + `smoke_demo_readiness.py` + `e2e-smoke.cjs` before demo | P0 | in_progress | Pre-pilot | Chat 2026-06 | Playwright added to `package.json` |
| DEMO-05 | **Own Gemini API key** for demo (reduce dependency on borrowed OpenAI key) | P0 | proposed | Pre-pilot | Chat 2026-06 | Friend's key; can't rotate yet |
| DEMO-06 | Parent onboarding **consent one-pager** (post-meeting, before real parents) | P1 | proposed | Pilot week 1 | Chat 2026-06 | DPDP; synthetic demo skips this |
| DEMO-07 | Position **PWA / mobile web** as parent app for pilot; Flutter Phase 2 | P0 | decided | P2 | DECISION_LOG D4 | See DECISION_LOG |

---

## Product — learning & absence

| ID | Enhancement | Priority | Status | Phase | Source | Notes |
|----|-------------|----------|--------|-------|--------|-------|
| LEARN-01 | **Catch-up Pack** for absent students (attendance + lesson plan → tutor + practice) | P1 | proposed | 1.5–2 | Chat 2026-06 | PRODUCT §9 Layer 6; needs lesson plan + coverage |
| LEARN-02 | Link absence to **what was taught** (syllabus week / lesson plan per date) | P1 | proposed | A-OS | Chat 2026-06 | Prerequisite for LEARN-01 |
| LEARN-03 | Parent message: *"Catch-up assigned"* (in-app first; WhatsApp later) | P2 | proposed | Phase 2 | Chat 2026-06 | Notifications stubbed today |

---

## Product — approval memory & “self-improving” AI

| ID | Enhancement | Priority | Status | Phase | Source | Notes |
|----|-------------|----------|--------|-------|--------|-------|
| MEM-01 | **Structured QP rejection reason codes** (too hard, off syllabus, wrong key, …) | P1 | proposed | 1.5 | PRODUCT §7.5.6 | Free-text `rejection_reason` exists today |
| MEM-02 | **`ApprovalMemoryEvent` model** + inject last N events into QP generation prompt | P1 | proposed | 1.5 | Chat 2026-06 | Rules + prompt, not autonomous agent |
| MEM-03 | **TeacherStyleProfile** from approved/edited report remarks | P2 | proposed | B-OS | PRODUCT §7.6.3 | |
| MEM-04 | Student doubts → **Content Review Queue** → Concept Card draft → HOD approve | P1 | proposed | 1.5 | DECISION_LOG tutor MVP | Not open-ended tutor chat |
| MEM-05 | Reject **autonomous self-modifying agent**; use workflows + HITL only | — | decided | — | Chat 2026-06 | See PRODUCT §23, DECISION_LOG |

---

## UX & portals

| ID | Enhancement | Priority | Status | Phase | Source | Notes |
|----|-------------|----------|--------|-------|--------|-------|
| UX-01 | Global search suggestions **overlay** (not push page down) | P2 | done | — | Chat 2026-06 | `sn-page-density.css` absolute positioning |
| UX-02 | **Flutter** parent + student native apps | P2 | deferred | Phase 2 | DECISION_LOG D4 | PWA for pilot |
| UX-03 | Wire **New Notice** button to API | P2 | proposed | B2 | STATUS.md | If comms in school top-3 |
| UX-04 | Marketing nav / Noustriks site polish | P3 | done | — | Prior chat | |

---

## Production & security hardening

| ID | Enhancement | Priority | Status | Phase | Source | Notes |
|----|-------------|----------|--------|-------|--------|-------|
| PROD-01 | **Azure Blob** for file uploads (replace local disk) | P1 | proposed | Prod | PRR / STATUS | Blocks horizontal scale |
| PROD-02 | Secrets via **runtime env / Key Vault** — never in Docker image | P0 | decided | Prod | Chat 2026-06 | `.dockerignore` + whitelist Dockerfile since `bb26031` |
| PROD-03 | Prune old Docker build cache if pre-Jun-10 images built | P1 | proposed | Ops | Chat 2026-06 | Current `api:dev` image verified clean |
| PROD-04 | **Rotate / own** production AI keys (not friend's OpenAI) | P1 | proposed | Prod | Chat 2026-06 | Gemini own-account interim |
| PROD-05 | **CI/CD** GitHub Actions (pytest + tests_security + smoke) | P1 | proposed | Prod | PRR | No `.github/workflows` yet |
| PROD-06 | Move heavy **AI generation to Arq** (return job id) | P1 | proposed | Prod | STATUS / CODE_REVIEW | Sync LLM holds DB connection |
| PROD-07 | **DPDP pack** — privacy notice, consent, retention before real PII | P0 | proposed | Pilot→prod | PHASE_1_EXIT | Skip for synthetic demo only |
| PROD-08 | **Razorpay webhook** with signature verification (when payments go live) | P1 | proposed | Phase 2 | PRR | No webhook route in repo yet |
| PROD-09 | PRR reconciliation doc (fixed vs stale findings) | P2 | proposed | Docs | Chat 2026-06 | Many Critical items already fixed |
| PROD-10 | Aadhaar: **don't store** or column-level encryption | P1 | proposed | Prod | PRR | Plaintext on admissions/staff tables today |

---

## Curriculum & exam loop (from PRODUCT / STATUS)

| ID | Enhancement | Priority | Status | Phase | Source | Notes |
|----|-------------|----------|--------|-------|--------|-------|
| EXAM-01 | **CurriculumPack** entity stack + wire QP to pack | P1 | in_progress | 1.5 | STATUS 8-week | Migration exists; not end-to-end |
| EXAM-02 | Paper **quality checker** post-generation | P2 | proposed | 1.5 | PRODUCT §7.5.3 | |
| EXAM-03 | **Similarity checker** (duplicate questions) | P2 | proposed | 1.5 | PRODUCT §7.5.2 | |
| EXAM-04 | **Concept Cards** + upgrade tutor from templates | P1 | proposed | 1.5 | DECISION_LOG | |
| EXAM-05 | **AI lesson plans** (LLM, pack-grounded) | P1 | proposed | A-OS | PRODUCT §23.4 | Template-only today |

---

## Notifications & comms

| ID | Enhancement | Priority | Status | Phase | Source | Notes |
|----|-------------|----------|--------|-------|--------|-------|
| COMMS-01 | WhatsApp / SMS / email delivery (not stub) | P2 | proposed | Phase 2 | STATUS | Outbox handlers log only |
| COMMS-02 | Fee reminders via WhatsApp | P2 | proposed | FC Phase 1 | PRODUCT §14 | Only if pilot retention needs |

---

## Open questions (move to DECISION_LOG §6 when decided)

| Question | Status |
|----------|--------|
| Real pilot school name + forced top-3 after this week's meeting | ⏸ pending meeting |
| Rupee pricing locked | ⏸ |
| SSC blueprint verified against school's sample paper | ⏸ need A2 inputs |
| Pilot: one class only vs whole school for parent app | ⏸ |

---

## Changelog (this file)

| Date | Change |
|------|--------|
| 2026-06-30 | **Three gates** framework (demo / controlled pilot / production) + Gate 1–3 checklists |
| 2026-06-30 | Initial backlog seeded from Cursor chat (demo, catch-up, approval memory, security, PRR) |

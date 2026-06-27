# StudyNexs / Academix Platform — War Room Review (Full Record)

> **Type:** Business, product, architecture, engineering, security, compliance, operations, and investment-grade due diligence  
> **Date of review:** 2026-06 (conversation + repo evidence)  
> **Evidence base:** `docs/PRODUCT.md`, `docs/STATUS.md`, `CODE_REVIEW*.md`, pilot sheets, codebase inspection, marketing pages  
> **Stress test:** “Going live tomorrow to millions of users”  
> **Actual stated stage:** Pilot / design-partner; solo builder on `phase-0-foundation`  

**Disclaimer:** Findings are evidence-based where cited; items marked **UNKNOWN** need validation. This is not legal, financial, or security certification.

---

## Table of contents

1. [Executive summary](#1-executive-summary)
2. [Verdict matrix](#2-verdict-matrix)
3. [Panel findings by domain](#3-panel-findings-by-domain)
4. [What is real vs claimed](#4-what-is-real-vs-claimed)
5. [Marketing overclaims (detailed)](#5-marketing-overclaims-detailed)
6. [Security & engineering findings](#6-security--engineering-findings)
7. [AI platform assessment](#7-ai-platform-assessment)
8. [Compliance & DPDP](#8-compliance--dpdp)
9. [Operations & reliability](#9-operations--reliability)
10. [Go-to-market & pilot evidence](#10-go-to-market--pilot-evidence)
11. [Competitive & strategic position](#11-competitive--strategic-position)
12. [Investment readiness](#12-investment-readiness)
13. [Blocker register (prioritized)](#13-blocker-register-prioritized)
14. [Ship conditions (pilot)](#14-ship-conditions-pilot)
15. [Post-war-room work completed](#15-post-war-room-work-completed)
16. [Evidence log & unknowns](#16-evidence-log--unknowns)
17. [Review cadence](#17-review-cadence)

---

## 1. Executive summary

**StudyNexs** is an India-first K–12 **school operating system** with a credible **AI wedge** (question papers, report-card remarks, mastery narratives, answer-sheet vision) on a **multi-tenant FastAPI + PostgreSQL** backend and a **single Next.js app** (`admin-web`) that also hosts teacher/parent/student route shells.

### What is genuinely strong

- **Architecture maturity for stage:** modular monolith, `TenantScope`, object-level authz, JWT + refresh rotation, outbox pattern, Arq jobs, audit logging, production config guardrails.
- **AI wedge proven in demo:** question paper + report card generation end-to-end; credit metering; human-in-the-loop approve flows.
- **Exam loop vision is coherent:** CurriculumPack → QP → rubric → answer-sheet eval → mastery → tutor — not a random feature list.
- **Honest internal docs:** `STATUS.md` separates vision from repo truth (rare for early startups).
- **Test coverage exists:** ~105+ backend tests; security tests in separate suite.

### What is dangerous if ignored

- **Marketing promises exceed pilot reality** — schools will feel bait-and-switched.
- **Production notification + OTP + payments not wired** — core “parent comms” and monetization paths are stubbed.
- **No CI/CD** — regressions ship silently.
- **Real student PII before DPDP pack** — legal exposure.
- **Solo builder vs 8-week Phase 1.5 plan** — scope death without ruthless cuts.

### One-line verdict

| Audience | Verdict |
|----------|---------|
| **Mass market launch tomorrow** | **CONCERNING** — do not |
| **Single design-partner pilot (1 school, password login, scoped demo)** | **SHIP WITH CONDITIONS** |
| **Investor Series A narrative today** | **NOT READY** — pilot + revenue + compliance gaps |

---

## 2. Verdict matrix

| Dimension | Grade | Summary |
|-----------|-------|---------|
| **Product vision** | A | Clear category, exam loop, memory moat story |
| **Build vs vision gap** | C+ | Many modules API-only; 4/5 portals missing |
| **Security architecture** | B− | Good bones; historical criticals mostly fixed; edge cases remain |
| **Production readiness** | D+ | OTP, payments, notifications, CI/CD, blob storage |
| **AI product quality** | B (demo) | Works; needs pilot validation on tone/accuracy/cost |
| **Compliance (DPDP)** | D | Principles documented; product enforcement incomplete |
| **GTM / pilot traction** | C | Warm interest; no signed paid pilot captured in docs |
| **Marketing integrity** | D | Site overstates portal depth and feature completeness |
| **Team / execution risk** | High | Solo builder; binding constraint per STATUS.md |
| **Investor readiness** | D+ | Needs revenue, legal pack, metrics |

---

## 3. Panel findings by domain

### 3.1 Business & GTM panel

| Finding | Evidence | Severity |
|---------|----------|----------|
| No signed paid pilot in repo | `docs/STATUS.md` — “interested; no signed deal” | High |
| Pricing not validated | `docs/PRICING.md` — “rupee prices not locked” | Medium |
| Razorpay subscriptions planned, not built | STATUS, PRICING | High (pre-monetization) |
| 7 schools explored in pilot research; pick **one** design partner | Pilot conversation summary | Medium |
| Exam wedge validated in ~4/7 schools | Pilot outcome pattern | Positive |
| Finance Command Center is deal-expander, not wedge | PRODUCT.md §14 | Info — scope discipline |

**Assumption (explicit):** Willingness-to-pay not measured with signed order forms.

---

### 3.2 Product panel

| Finding | Evidence | Severity |
|---------|----------|----------|
| Only **admin-web** exists; teacher/parent/student/platform portals planned | STATUS.md, README | High for GTM claims |
| Hero workflow (exam loop) partially built | QP ✅, report cards ✅, eval 🟡, tutor template | Medium |
| CurriculumPack entity stack not complete | STATUS Phase 1.5 backlog | Expected |
| Library/events pages were placeholders; some UI improved since | STATUS vs recent commits | Improving |
| Human-in-the-loop approve model is real differentiator | QP + report card + mastery flows | Positive |

---

### 3.3 Engineering panel

| Finding | Evidence | Severity |
|---------|----------|----------|
| No `.github/workflows` CI | STATUS.md | High |
| AI generation still synchronous on request thread | STATUS.md (Arq exists but unused for AI) | Medium |
| Azure Blob configured but local disk only | STATUS.md | Medium |
| PDF export = HTML print fallback | STATUS.md | Low–Medium |
| Qdrant in docker but no app usage | STATUS.md | Expected (Phase 1.5) |
| Middleware skipped in main pytest (security tests separate) | STATUS.md | Low (documented) |

---

### 3.4 Security panel

See [§6](#6-security--engineering-findings) for full register. Headlines:

| Item | Status at review |
|------|------------------|
| Live API key in `.env` on disk | **CRITICAL** if not rotated (CODE_REVIEW C1) |
| Fee payment idempotency race | **Fixed** per later STATUS (unique constraints) |
| IP rate-limit spoofing via X-Forwarded-For | **Open** — nginx mitigates if sole ingress |
| Admin can create super_admin | **Fixed** per authorization hardening |
| Outbox worker `[-500]` bug | **Fixed** in pass-2 |
| Tenant isolation tests skip binding in test env | **Gap** — CODE_REVIEW_PASS2 |

---

### 3.5 AI / ML panel

| Finding | Evidence | Severity |
|---------|----------|----------|
| Provider-agnostic gateway | `apps/api/app/modules/ai/gateway/` | Positive |
| Credit metering + monthly caps | `ai_credits.py`, `usage_caps.py` | Positive |
| Ollama gemma4 fallback for text + vision | invoke.py, answer_sheet_vision.py | Positive (post-review) |
| OpenTelemetry + Grafana stack | `infra/observability/` | Positive (post-review) |
| AI runs sync — pool exhaustion under load | CODE_REVIEW M1 | Medium |
| Stub provider blocked in production | config.py | Positive |
| Content copyright risk if textbooks ingested | PRODUCT.md §4, §10 | High if violated |

---

### 3.6 Compliance & legal panel

| Finding | Evidence | Severity |
|---------|----------|----------|
| DPDP principles documented (purpose limitation, minimization, consent) | PRODUCT.md §14, conversation | Positive (doc only) |
| Consent records not in product | STATUS backlog item 4 | **Blocker** for real PII |
| Privacy policy / retention policy | Not in repo as user-facing artifact | **Blocker** |
| Minors’ data — school as fiduciary | Architecture intent | Needs DPA |
| Audit log improved but login events gap | CODE_REVIEW M9 | Medium |

---

### 3.7 Operations panel

| Finding | Evidence | Severity |
|---------|----------|----------|
| Docker compose dev stack works | `infra/docker/` | Positive |
| Observability overlay (Prometheus/Grafana/Tempo) | `docker-compose.observability.yml` | Positive (post-review) |
| Outbox handlers = `logger.info` only | CODE_REVIEW_PASS2, STATUS | **High** for “notify parents” |
| MSG91 OTP not wired | STATUS.md | **Blocker** for OTP-first prod login |
| No on-call / incident runbook in repo | UNKNOWN | Medium |

---

### 3.8 Customer success panel

| Risk | Mitigation |
|------|------------|
| School expects full ERP day one | Pilot scoping doc — forced top-3 features only |
| Teachers distrust AI marks/remarks | HITL approve — **keep mandatory** |
| Parents never get SMS/WhatsApp | Set expectation: in-app only until Phase 2 |
| Data migration from Excel/WhatsApp | White-glove onboarding; no self-serve importer |

---

## 4. What is real vs claimed

| Claim (marketing / vision) | Repo truth (STATUS + code) | Gap |
|----------------------------|---------------------------|-----|
| “AI-native school OS” | SMS modules + AI wedge in admin-web | Partial — OS breadth API-heavy |
| “Parent portal” | Route shell in admin-web | **Large** |
| “Student portal” | Route shell in admin-web | **Large** |
| “Answer sheet AI evaluation” | Built v1 — vision OCR + async job + HITL | Demo-ready; pilot validate |
| “WhatsApp / SMS alerts” | Handlers stubbed | **Total** |
| “Online fee payment” | API fields; no Razorpay flow | **Total** |
| “OTP login” | Dev logs OTP | **Prod blocker** |
| “5 portals” | 1 portal (README corrected) | Fixed in README |
| “Institutional memory” | Designed in PRODUCT.md; UI not built | Future |
| “CurriculumPack source of truth” | Models/plan started | Phase 1.5 |

---

## 5. Marketing overclaims (detailed)

**Definition:** Public copy promises more than a school experiences after login — creates trust debt and sales friction.

### 5.1 Examples

| Marketing surface | Says / implies | Reality |
|-------------------|----------------|---------|
| **Pricing / platform pages** | Parent & student portals included in pilot tier | Thin shells; not standalone apps |
| **Feature lists** | Full exam intelligence, tutor, notifications | Tutor = templates; notifications in-app only |
| **“AI evaluation”** | Production-grade grading | HITL required; vision depends on LLM keys |
| **Finance / fee collection** | End-to-end digital fees | Read-only finance UI; no Razorpay UI |
| **Multi-portal SaaS** | Complete portal suite | admin-web only |

### 5.2 Why it matters

- Principals share website with management — **overclaim kills renewal**.
- DPDP: marketing must match **actual data processing purposes**.
- Investors doing diligence will compare site to `STATUS.md` — inconsistency = credibility hit.

### 5.3 Remediation

1. Add **“Pilot scope”** banner on marketing: lists what’s live in current pilot build.
2. Align pricing page bullets with `docs/STATUS.md` ✅/🟡/⬜.
3. Replace “coming soon” with honest **roadmap dates** only when committed.
4. Single source of truth: link marketing to `STATUS.md` internally before each release.

---

## 6. Security & engineering findings

Consolidated from `CODE_REVIEW.md`, `CODE_REVIEW_PASS2.md`, `CODE_REVIEW_FIXES.md`, `CODE_REVIEW_FIXES_RACES.md`.

### 6.1 Critical (historical)

| ID | Issue | Action |
|----|-------|--------|
| C1 | OpenAI key in `apps/api/.env` on disk | **Rotate key**; secrets manager at deploy; gitleaks |

### 6.2 High (status varies)

| ID | Issue | Fix status |
|----|-------|------------|
| H1 | Fee payment idempotency race | **Fixed** (unique constraints) per STATUS |
| H2 | Spoofable `X-Forwarded-For` for app rate limits | **Open** — use `X-Real-IP` / trusted hops |
| H3 | Outbox worker traceback slice bug | **Fixed** |
| H4 | Admin creates super_admin | **Fixed** (role guards) |

### 6.3 Medium (selected open items)

| ID | Issue |
|----|-------|
| M1 | AI sync on request thread — pool exhaustion |
| M2 | N+1 + race on attendance/marks bulk |
| M6 | Redis fail-mode inconsistent; rate limit non-atomic |
| M8 | Single refresh JTI — multi-device logout |
| M9 | Audit sync on every mutation; login not audited |
| M10 | Login limiter per-username enables spray |

### 6.4 Testing gaps (PASS2)

- `validate_tenant_school_match` early-return in tests → **cross-tenant token replay untested**
- Isolation tests cover subset of modules only

---

## 7. AI platform assessment

### 7.1 Shipped AI features

| Feature | Status | Metered | HITL |
|---------|--------|---------|------|
| Question paper generate | ✅ | ✅ credits | Approve required |
| QP from bank (gap fill) | ✅ | ✅ | Approve |
| Report card remark | ✅ | ✅ | Approve |
| Mastery narrative | ✅ | ✅ | Approve flag |
| Answer sheet vision OCR | 🟡 | Partial | Teacher approve eval |
| Lesson plans | Template (no LLM) | — | — |
| Tutor lessons | Template (no LLM) | — | — |
| Tutor TTS | Azure Speech | Logs only | — |

### 7.2 Provider strategy

| Provider | Role |
|----------|------|
| OpenAI (primary) | Text + vision primary |
| Ollama gemma4:cloud | Fallback text + vision handwriting |
| Gemini / Anthropic | Supported in gateway; config-dependent |

### 7.3 Cost & abuse controls (post-hardening)

- Monthly AI caps per school
- Rate limits on generate endpoints
- `AIUsage` telemetry: tokens, latency, fallback flag, cost USD
- OpenTelemetry + Grafana dashboards (`infra/observability/`)

### 7.4 AI risks for pilot

| Risk | Mitigation |
|------|------------|
| Hallucinated report card remarks | Teacher edit + approve |
| Wrong OCR on handwriting | HITL; confidence UX (future) |
| Runaway LLM spend | Credits + caps |
| Copyright in generated questions | Teacher approve; no publisher text in prompts |

---

## 8. Compliance & DPDP

India **Digital Personal Data Protection Act, 2023** applies to minors’ data in schools.

### 8.1 Principles (aligned with product design)

| Principle | Product implication |
|-----------|---------------------|
| **Purpose limitation** | Tag events: `exam_evaluation`, `question_generation`, `ai_tutor` |
| **Data minimization** | Collect only fields needed per module |
| **Consent** | School obtains parent consent; platform records purpose + version |
| **Retention** | Define per data class; implement deletion on school offboarding |
| **Data fiduciary** | School; StudyNexs = processor under DPA |

### 8.2 Gaps before real student data

- [ ] Privacy Policy (parent-readable)
- [ ] School DPA template
- [ ] Consent record model in DB
- [ ] Purpose tags on AI/student-touching events (STATUS item 14)
- [ ] Data export + deletion runbook
- [ ] Breach notification procedure

---

## 9. Operations & reliability

| Capability | Status |
|------------|--------|
| Health `/health`, `/ready` | ✅ |
| Metrics `/metrics` | ✅ |
| AI telemetry `/api/v1/ai/telemetry` | ✅ (admin) |
| Grafana/Prometheus/Tempo | ✅ (optional compose) |
| CI/CD pipeline | ❌ |
| Staged prod environment | UNKNOWN |
| Backup/restore runbook | UNKNOWN |
| Secret management (Key Vault) | ❌ (local .env) |

**SLO recommendation for pilot:** 99% during school hours; honest maintenance windows.

---

## 10. Go-to-market & pilot evidence

### 10.1 Pilot school research (7 schools summarized)

| Pattern | Finding |
|---------|---------|
| Exam pain in top-2 | ~4/7 schools — wedge validated |
| Best fit example | Krishnaveni Talent — SSC Class 10 Maths aligns with demo |
| Common blocker | Warm interest; weak contacts; no signed pilot |
| Recommendation | **One design partner** — not 7 parallel |

### 10.2 Track A → B execution (from docs)

| Track | Goal |
|-------|------|
| **A** | Buy-list: top-3 features + price + contacts (1–2 weeks) |
| **B** | Pilot-ready product scoped to buy-list only (2–4 weeks) |

**Artifacts:** `docs/TRACK_AB_EXECUTION.md`, `docs/pilot/PILOT_OUTCOME_SHEET.md`

### 10.3 Demo readiness

- Seed school: Sri Saraswathi (SSC) — 288 students
- Scripts: `smoke_demo_readiness.py`, `e2e-smoke.cjs`
- Commit version should be recorded on pilot outcome sheet

---

## 11. Competitive & strategic position

### 11.1 Positioning (defensible)

> Not “ChatGPT for schools.” Not textbook warehouse.  
> **School-approved curriculum intelligence → exam loop → memory.**

### 11.2 Moat layers (time-ordered)

1. **CurriculumPack** approved per school/year
2. **Question bank** from approved papers
3. **Rubrics + eval history** per question
4. **Weak-concept memory** across terms
5. **Cross-year concept mapping** (future)

### 11.3 Competitive risks

| Threat | Response |
|--------|----------|
| Horizontal ERP adds “AI button” | Depth on exam loop + HITL trust |
| Free ChatGPT used by teachers | Workflow + audit + school memory |
| Fedena / traditional ERP | Coordination + AI wedge, not feature parity race |

---

## 12. Investment readiness

### 12.1 What investors will ask

| Question | Current answer |
|----------|----------------|
| Revenue? | **UNKNOWN / none in repo** |
| LOIs / paid pilots? | Interest only |
| TAM/SAM? | India K–12 — large; needs segment focus |
| Defensibility? | CurriculumPack + memory story — early |
| Team? | Solo builder — **key risk** |
| Unit economics? | AI cost per paper ~₹0.13 cited in STATUS; needs benchmark |
| Legal / IP clean? | See [IP_PROTECTION_GUIDE.md](./IP_PROTECTION_GUIDE.md) |

### 12.2 Milestones before seed/Series A narrative

1. **1 signed paid pilot** (even ₹25k–₹1L)
2. **3 referenceable teachers** using QP weekly
3. **DPDP minimum viable compliance**
4. **CI + staging environment**
5. **Trademark filed + company IP assigned**

---

## 13. Blocker register (prioritized)

| # | Blocker | Owner | Type |
|---|---------|-------|------|
| B1 | No signed pilot contract | Founder/GTM | Business |
| B2 | Marketing overclaims vs product | Founder/Product | Trust |
| B3 | MSG91 OTP not wired (if OTP-first login) | Engineering | Prod |
| B4 | Razorpay not integrated (if fees required) | Engineering | Revenue |
| B5 | DPDP pack before real PII | Legal/Product | Compliance |
| B6 | No CI/CD | Engineering | Quality |
| B7 | External notifications stubbed | Engineering | Product promise |
| B8 | API keys in local `.env` — rotation | Engineering | Security |
| B9 | Solo builder vs Phase 1.5 scope | Founder | Execution |

---

## 14. Ship conditions (pilot)

**Allowed to ship to ONE design-partner school when ALL are true:**

### 14.1 Scope

- [ ] Written **top-3 feature list** signed by school (from Track A)
- [ ] Demo path rehearsed on **pinned commit**
- [ ] Marketing site shows **pilot scope** disclaimer OR school-only private demo URL

### 14.2 Auth & access

- [ ] **Password login** acceptable OR MSG91 OTP wired
- [ ] RBAC verified for school roles in scope
- [ ] Tenant isolation spot-checked (school A token cannot access school B)

### 14.3 Data & legal

- [ ] Pilot MSA + DPA signed (even lightweight)
- [ ] Privacy notice shared with parents if student PII entered
- [ ] Data retention period agreed (e.g. delete 90 days after pilot end if not converting)

### 14.4 AI & trust

- [ ] Teacher **approve** required before QP/report goes to print/PDF
- [ ] AI credit budget set for school; no unlimited spend
- [ ] Fallback provider tested (Ollama) if OpenAI fails

### 14.5 Operations

- [ ] Backup of Postgres before go-live
- [ ] Founder on-call WhatsApp for first 2 weeks
- [ ] Incident contact + rollback plan (docker image tag)

### 14.6 Explicitly out of scope for pilot (do not promise)

- Parent/student native apps
- WhatsApp fee reminders
- Razorpay online pay (unless built before go-live)
- Full CurriculumPack / RAG
- Finance Command Center Phase 2+

---

## 15. Post-war-room work completed

Items addressed after initial war room (repo evidence):

| Area | Work |
|------|------|
| AI hardening | Rate limits, credit caps, shared LLM error handler, production stub guard |
| Ollama fallback | `generate_llm` → gemma4:cloud for text features |
| Vision fallback | Answer sheet OCR → Ollama gemma4 on primary failure |
| AI telemetry | `AIUsage` columns, `/metrics`, `/ai/telemetry`, Grafana dashboard |
| OpenTelemetry | OTLP → collector → Prometheus/Tempo |
| UI fixes | Events, transport keys, staff profile modal, credits UI |
| Config | Absolute `.env` path loading |

**Still open:** Blockers B1–B9 above.

---

## 16. Evidence log & unknowns

### 16.1 Primary evidence files

| Path | Contents |
|------|----------|
| `docs/PRODUCT.md` | Full product bible |
| `docs/STATUS.md` | Build truth as-of 2026-06-17 |
| `docs/PRICING.md` | Tier structure; prices not locked |
| `CODE_REVIEW.md` | Security review 2026-06-01 |
| `CODE_REVIEW_PASS2.md` | Notifications stub, test gaps |
| `CODE_REVIEW_FIXES.md` | Fix verification |
| `docs/IP_PROTECTION_GUIDE.md` | IP playbook |
| `infra/observability/README.md` | Monitoring stack |

### 16.2 Explicit unknowns (do not invent)

| Item | Status |
|------|--------|
| Exact pilot contract status | **UNKNOWN** — verify with founder |
| Company incorporation date | **UNKNOWN** |
| Trademark filing status | **UNKNOWN** |
| Production hosting (Azure vs other) | Partial — Azure Bicep exists |
| Insurance (cyber liability) | **UNKNOWN** |
| Current school count if any live | Demo seed only in repo |

---

## 17. Review cadence

| When | Action |
|------|--------|
| **Before each pilot demo** | Re-read §14 ship conditions |
| **After each sprint** | Update `STATUS.md`; reconcile marketing |
| **Monthly** | Re-run blocker register; rotate secrets audit |
| **Before fundraising** | Full war room refresh + IP data room |
| **After security incident** | Append §6 with postmortem |

---

## Appendix A — War room panel roles (reference)

This review simulated independent experts:

| Panel | Focus |
|-------|-------|
| Business / GTM | Pilot, pricing, positioning |
| Product | Vision vs build, UX, workflows |
| Engineering | Architecture, debt, scalability |
| Security | OWASP, tenant isolation, secrets |
| AI/ML | Model risk, cost, HITL |
| Compliance | DPDP, minors, contracts |
| Operations | SRE, observability, incidents |
| Customer success | Onboarding, support, churn risk |
| Investment | Readiness, unit economics, team |

Each panel challenged prior conclusions; facts without repo evidence marked **UNKNOWN**.

---

## Appendix B — Quick reference verdicts

```
Mass launch tomorrow     →  NO  (CONCERNING)
Single-school pilot      →  YES WITH CONDITIONS (§14)
Investor round today     →  NOT READY
Continue building        →  YES — focus exam loop + one school
Fix marketing first      →  YES — before next outbound sales
```

---

*Document owner: ARM · Next review: before pilot go-live or fundraising.*  
*Related: [IP_PROTECTION_GUIDE.md](./IP_PROTECTION_GUIDE.md) · [STATUS.md](./STATUS.md)*

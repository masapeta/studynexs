# StudyNexs Product State Assessment

**Assessment date:** 2026-07-20  
**Repository assessed:** `D:\Projects\studynexs-platform\studynexs-dev`  
**Repository state:** `develop` at `2a9248f` — *Ship Reference School Demo v1 for principal walkthrough*  
**Scope:** Assessment only. No product code, configuration, existing documentation, data, or deployment state was changed.

---

## Executive verdict

StudyNexs is no longer an early prototype. It is a broad, modular school-operations product with a real AI assessment/curriculum wedge, an integrated web portal for staff, parents, and students, and a deliberately seeded **Reference School Demo v1**.

The strongest honest statement today is:

> **A locally rehearsed principal demonstration is available in the repository.** It can tell a connected story from school operations to approved curriculum, teacher assessment, human-reviewed AI suggestions, parent context, and student support — without depending on a live LLM.

It is **not yet proven as a shareable customer demonstration**. The deployment path is unresolved, the current UI journey could not be independently exercised in this assessment, and the local Reference School seed/smoke were not re-run. The next value is therefore validation and presentation reliability, not a new feature area.

### Evidence legend

| Label | Meaning |
|---|---|
| **Verified in code** | Route, service, model, UI, seed, or configuration was inspected in this repository. |
| **Reported, not re-run** | A repository report or historical status claims a completed run; this assessment did not reproduce it. |
| **Unverified runtime** | Requires a configured provider, a live seeded database, a browser walkthrough, or cloud credentials. |

### Assessment limits

- `GET http://localhost:8000/health` returned `healthy` during the assessment.
- Docker process inspection was denied by the local Docker credential-file permissions, so the running API could not be tied to the current seeded stack.
- Browser access to `http://localhost:3000` is explicitly blocked by the local browser policy. No UI flow was exercised.
- Full test, lint, build, seed, migration, and deployment commands were intentionally not run; this is an assessment-only pass and the report does not claim a fresh green build.

---

## 1. Repository status

### Canonical repository

`CANONICAL_REPOSITORY.md` identifies this repository as the sole development repository and marks `academix-platform` as a reference archive. The checked branch is `develop`; the current `HEAD` contains the Reference School Demo v1 commit from 2026-07-20.

The working tree was clean when inspected. Git emitted warnings because it could not read the user's global ignore file, but no repository changes were reported.

### What is actually present

| Area | Verified state |
|---|---|
| Backend | FastAPI modular monolith under `apps/api`, with 23 domain directories and 27 router mounts. |
| Web product | One Next.js 16.2.6 application in `apps/admin-web`, with 72 page routes across staff, parent, student, marketing, and compatibility redirects. |
| Data | PostgreSQL-oriented SQLAlchemy model modules, Alembic migrations, Redis, Qdrant adapters, local upload storage, and seeded demo scripts. |
| Automated checks | 72 API test files + 4 security-test files, containing 389 test functions. Web checks are Playwright-style scripts rather than a conventional unit-test suite. |
| Infrastructure | Local Docker Compose supplies Postgres, Redis, Qdrant, API, and Nginx. Azure WAF infrastructure and Cloudflare/OpenNext configuration both exist. |
| Reference tenant | `reference` / ARM International School seed, demo asset seed, persona logins, API smoke, and walkthrough documentation are in the current commit. |

### Repository state is ahead of several status documents

The code and current commit history are newer than the broad status documents. This is a documentation-freshness issue, not evidence that the capabilities are absent.

- `docs/STATUS.md` is dated 2026-07-12 and says later work is uncommitted; the current `develop` head contains commits through 2026-07-20.
- `docs/product/PRODUCT_EXECUTION_PLAN.md` is dated 2026-07-17 and still calls RAG indexing, learning outcomes, and approval audit upcoming or partial. The current source contains migrations, services, UI, and Demo v1 seed work beyond that plan.
- `CANONICAL_REPOSITORY.md` names migration head `f4a5b6c7d8e9`, while the repository contains later migrations through `z6a7b8c9d0e1`. The database's actual applied revision was not checked.

---

## 2. Current architecture

### Implemented architecture

```text
Next.js 16 web application
  ├─ staff dashboard and Teaching / Students / Finance hubs
  ├─ parent routes (/parent/*) and student routes (/student/*)
  └─ API client: bearer access token + refresh-cookie flow + tenant header
            │
            ▼
FastAPI modular monolith (/api/v1)
  ├─ auth, users, academic, attendance, examinations, fees, timetable
  ├─ curriculum, AI, tutor, mastery, portal, parent copilot, dashboard
  ├─ school operations, files, notifications, jobs, platform
  └─ service-layer data access with tenant-aware CurrentUser context
            │
            ▼
PostgreSQL + Redis + optional Qdrant + local file storage in development
```

### Architecture facts verified in source

- FastAPI mounts 27 routers under `/api/v1`; one curriculum domain contributes several focused routers. `analytics` and `knowledge_graph` directories exist but are not direct standalone router mounts.
- Tenant resolution supports a school subdomain or `X-Tenant-Slug`; authenticated requests validate the resolved tenant against the token user's `school_id`. The application model is application-enforced multi-tenancy, not database row-level security.
- Protected APIs derive authorization from `CurrentUser`, not a client-provided `school_id`. The model layer contains pervasive `school_id` fields (109 source matches).
- AI providers sit behind a gateway with OpenAI, Gemini, Anthropic, Ollama, and a development stub option. Embeddings, vector-store, RAG, metering, credits, input/output guards, and telemetry are separate components.
- The web client currently stores the access token in `sessionStorage` and uses the refresh token through an HttpOnly cookie. This conflicts with the root README wording that access tokens are “in-memory only.”
- The deliberate UI architecture is one unified web app. Dedicated `apps/teacher-web`, `apps/parent-web`, `apps/student-web`, and `apps/platform-web` directories do not exist. `/teacher` is a redirect to the staff dashboard.

### Delivery architecture is not yet coherent

The intended production route is ambiguous:

| Evidence | Implication |
|---|---|
| Root README describes GitHub Actions to Azure Container Apps. | Azure is still a stated deployment target. |
| `infra/azure` contains Azure Front Door/WAF guidance, not a complete app deployment definition. | The edge is partially represented; the application delivery path is not. |
| `apps/admin-web` has OpenNext/Cloudflare Worker configuration. | A second possible web-hosting route exists. |
| `sites/studynexs-web` is a separate static Cloudflare marketing site. | Marketing currently has two implementations. |
| CI runs on `phase-0-foundation` and `main`, not `develop`. | The declared canonical branch is not protected by the checked quality workflow. |

This is the primary obstacle to a shareable demo URL, not a missing school-operations module.

---

## 3. Feature status

### Implemented and exposed in the product

| Capability | Evidence | Honest status |
|---|---|---|
| Authentication, roles, tenant matching, rate limits | Auth endpoints, dependencies, tenant middleware, security tests | **Implemented** |
| Students, guardians, staff, classes, subjects | Academic/users APIs and dashboard pages | **Implemented** |
| Attendance, timetable, notices | APIs and web pages; Reference School seed covers them | **Implemented** |
| Offline fees, receipts, fee dashboards | Fee model/service/API and Finance hub | **Implemented** for staff-recorded/offline payments |
| Admissions, document uploads, events, library, transport, residential, payroll, expenses | School-ops/files APIs and UI pages | **Implemented** as operational modules; not proven in the demo path |
| CurriculumPack lifecycle | Pack/chapter/topic/outcome APIs, approval/audit, curriculum web page, migrations | **Implemented** |
| Curriculum grounding / RAG | RAG service, Qdrant adapter, approved-pack grounding, question-paper integration | **Implemented in code; provider/index runtime is unverified** |
| Lesson plans | CRUD, template generation, optional grounded Teacher Copilot generation, UI | **Implemented** |
| Question bank and AI question papers | QP service/API/UI, approval workflow, curriculum grounding, credits | **Implemented** |
| Exam marks and per-question schema | Exam APIs, mark grid, question editor, teaching pages | **Implemented** |
| Answer-sheet evaluation and corrections | Upload/evaluation routes, objective matching, rubric engine, suggestion/review UI | **Implemented**; live OCR/LLM quality remains configuration-dependent |
| Report cards, mastery, flags, narratives | Models/services/APIs and teaching/student pages | **Implemented** |
| Student tutor and parent copilot | Portal context, tutor recommendations, parent copilot APIs and routes | **Implemented**; live generative response depends on configured provider |
| In-app notifications | Notification API and staff/parent UI surfaces | **Implemented** as in-product notifications |

### Partial implementations and important constraints

| Area | What exists | What prevents a “complete” claim |
|---|---|---|
| Parent and student experiences | Functional routes inside `admin-web` | No dedicated portal app or Flutter mobile application; UI walkthrough not independently run. |
| Teacher portal | Teaching hub and role support | `/teacher` is only a redirect; no standalone teacher portal. |
| Principal intelligence | Morning briefing, dashboard widgets, mastery and queue signals | No distinct, mature school-learning analytics product/module. |
| Live AI | Gateway, metering, guardrails, RAG, fallback and seeded artifacts | Requires credentials and provider availability; development stub exists. |
| Answer-sheet vision | Vision/evaluation services and review workflow | Real OCR/vision path needs file handling and configured providers; Demo v1 avoids this dependency with a seeded suggested evaluation. |
| Document intelligence | Upload, PDF/image parsing, Tesseract-based code paths | No verified managed OCR/storage integration; not ready to promise broadly. |
| Notifications | In-app persistence and outbox patterns | SMS, email, and FCM delivery are explicit TODOs in `notification_service.py`. |
| File storage | Upload/download flow exists | Source writes locally and labels Azure Blob as future production behavior. |
| Marketing | Static Cloudflare site and Next marketing routes | Duplicate surfaces can diverge. |

### Explicitly not implemented / future vision

- Signature-verified Razorpay checkout, webhook, and online fee collection. Online claims are deliberately rejected by the fee API.
- External WhatsApp, SMS, email, and push delivery integrations.
- Dedicated native/mobile (Flutter) parent and student applications.
- Dedicated teacher and platform-operator applications.
- A first-class homework module.
- A standalone school/learning analytics module beyond current dashboard widgets and mastery views.
- A confirmed production hosting, DNS, secrets, data-residency, and operating model.

These are appropriately described as future or partial. They must not be demonstrated as current customer capabilities.

---

## 4. Reference School Demo readiness

### What Demo v1 has already assembled

The current commit adds and wires the right assets for a durable local demo:

- `seed_reference_school.py` orchestrates the ARM International School tenant.
- `seed_reference_school_curriculum.py` supplies an approved Class 10 Mathematics curriculum path.
- `seed_reference_school_demo_v1.py` adds an approved paper, one pending-approval paper, a linked unit test, a **suggested** AI evaluation, and a class-work notice.
- `smoke_reference_school.py` delegates to a 32-check HTTP readiness script.
- Principal, teacher, parent, and student credentials are centralized in `reference_school_config.py` and documented in the login card.
- A script, journey checklist, and readiness report give the demonstration a repeatable narrative.

The included readiness report says the seed and all 32 smoke checks passed on 2026-07-20. That is **reported, not re-run** in this assessment.

### What can honestly be shown to a principal tomorrow

Assuming the operator runs the documented seed and smoke successfully, the following is a credible local walkthrough:

1. **Principal:** a populated school dashboard, with attendance, fees, student population, and an approval queue.
2. **Curriculum:** an approved Class 10 Mathematics pack with visible academic structure and audit/grounding context.
3. **Teacher:** a curriculum-linked lesson plan, a pre-approved question paper, and a pending paper that preserves human approval.
4. **Assessment:** a Unit Test with pre-seeded AI *suggestions* that the teacher reviews rather than blindly accepts.
5. **Parent and student:** the same school day appears as a class-work notice, child context, and tutor recommendations.
6. **Close:** the principal sees a connected operating system, not isolated AI screens.

This supports the current product blueprint: lead with day-to-day school problems and teacher time saved; treat curriculum intelligence and knowledge graph language as the engine, not the opening.

### What must not be claimed in that demo

- A live, dependable OCR/LLM marking run unless the provider configuration has been checked that day.
- Online fee payment or a Razorpay integration.
- SMS, WhatsApp, email, or push delivery.
- Native mobile applications.
- A live shareable HTTPS demo URL.
- A finished analytics product, inspection-document pack, or homework workflow.
- A production-ready environment or a current green CI run.

### Readiness by layer

| Layer | Assessment |
|---|---|
| Demo narrative and seed artifacts | **Green in source** |
| Local API health | **Green once** (`/health`) |
| Seeded Reference School content | **Amber** — present in code and reported green; not rerun |
| Principal/teacher/parent/student browser journey | **Amber** — scripts exist; UI review was blocked by local browser policy |
| Live AI wow moment | **Amber** — optional, provider/key dependent |
| Shareable HTTPS customer demo | **Red** — deployment and credentials unresolved |
| Pilot/production readiness | **Red** — external integrations and release path are incomplete |

---

## 5. Shortest path to a compelling end-to-end Reference School demonstration

**Do not build a new product feature first.** The shortest path is to validate, rehearse, and make the existing Demo v1 reliably presentable.

### Step 1 — Establish a known-good local rehearsal (no feature work)

An authorized operator should run the existing documented preflight:

```powershell
cd D:\Projects\studynexs-platform\studynexs-dev\apps\api
docker compose -f ../../infra/docker/docker-compose.dev.yml up -d
python scripts/seed_reference_school.py
python scripts/smoke_reference_school.py
```

Then start the web application with `NEXT_PUBLIC_TENANT_SLUG=reference` and `NEXT_PUBLIC_API_URL=http://localhost:8000`, and walk the four personas using the existing Demo v1 script.

**Exit criterion:** each screen and transition works in a browser, there are no empty/error states on the scripted path, and the presentation finishes in 45 minutes or less.

### Step 2 — Fix only blockers found during the rehearsal

Examples of valid Demo v1 work: broken routes, empty reference data, confusing transitions, unactionable dashboard copy, missing loading/error states, or a failure in the scripted review path.

Examples of work to defer: a new homework module, new analytics product, real-time OCR sophistication, native apps, payment gateway, or new AI agents.

### Step 3 — Make the rehearsal shareable

This requires an owner decision, not an implementation guess: choose the production/demo hosting path (Azure/Container Apps versus Cloudflare/OpenNext or a documented split), supply the required cloud/DNS/secrets authority, and put the actual canonical branch under CI.

**Exit criterion:** a short-lived HTTPS environment runs the same seed/preflight and the four personas can complete the script without developer-machine dependencies.

### Recommended demonstration shape

Use the Product Blueprint's 45-minute keynote, with the current Demo v1 assets as evidence:

| Moment | Existing proof |
|---|---|
| School runs today | populated roster, attendance, fees, timetable, notices |
| Teacher saves time | curriculum-linked plan and paper, with approval controls |
| Teacher “wow” | suggested evaluation and misconception/weak-concept conversation, explicitly human-reviewed |
| Parents stay informed | child context, class-work notice, copilot entry point |
| Principal gains clarity | dashboard health and pending-approval signals |

---

## 6. Technical debt and delivery risks

| Priority | Finding | Why it matters |
|---|---|---|
| P0 | CI does not trigger on canonical `develop`. | Current feature work can avoid the configured build/test gate. |
| P0 | Hosting and release architecture is unresolved. | A local demo cannot become a credible shareable customer asset. |
| P0 | Status/plan/migration documents lag the current commit. | Product decisions may be made using stale claims about what is built. |
| P1 | Browser E2E scripts exist but are not shown in CI, and the web app has no conventional test files. | Portal regressions can reach a demo without a current browser proof. |
| P1 | Root documentation says access tokens are in memory; implementation persists them in `sessionStorage`. | Security documentation and actual XSS exposure assumptions diverge. |
| P1 | Static marketing and Next marketing are separate implementations. | Content, branding, and hosting may drift. |
| P1 | Azure WAF, Cloudflare worker, static site, and Azure/Container Apps documentation coexist without a selected target. | Operational ownership and secrets/data-flow review are unclear. |
| P2 | Notifications, online payments, and production Blob storage are schema/config placeholders or explicit TODOs. | They cannot support a pilot promise yet. |
| P2 | “Analytics” exists mainly as dashboard presentation; the backend `analytics` package is not an exposed module. | Avoid selling a finished intelligence command center. |
| P2 | Reference Demo v1 uses seeded results to reduce provider risk. | Correct for sales reliability, but live AI needs a separate acceptance/quality proof. |

---

## 7. Unused work and hidden value

The repository has valuable capability that should be selectively surfaced in a demo rather than rebuilt.

| Existing work | Current exposure | Recommendation |
|---|---|---|
| Report cards, mastery flags/digest, student topic detail | API and staff/student routes; not central to Demo v1 | Use one carefully prepared view only if it supports the teacher/principal “wow.” |
| Question bank, rubrics, corrections history | Built behind AI papers/evaluation flow | Position as teacher control and institutional continuity, not as separate modules. |
| Admissions, document capture, library, transport, residential, payroll, expenses | Pages and APIs exist; not part of Reference School story | Keep as optional proof of operational breadth for a prospect who asks. |
| Notifications and files | API/UI support exists | Present only as in-app workflow support; do not imply external delivery or cloud storage. |
| Knowledge graph and RAG | Used behind curriculum/grounding; not a principal-facing module | Keep backstage. Show trustworthy curriculum outcomes rather than technical internals. |
| Legacy dashboard URLs | Many are explicit redirects to hub routes | Treat as deliberate compatibility paths, not immediate dead code. |
| Static marketing site and Next marketing pages | Two separate customer-facing implementations | A genuine duplication risk; choose one only after the demo/release path is confirmed. |

---

## 8. Documentation-to-implementation mismatches

| Documented claim | Code/repository evidence | Assessment |
|---|---|---|
| README describes 16 models and 13 domain modules. | Source contains 23 module directories and substantially more model modules. | Documentation is materially stale. |
| Four additional portal applications are planned. | Parent/student routes run in `admin-web`; teacher route redirects; no dedicated app directories exist. | The unified web portal is more capable than the wording implies, but the separate-portal vision is still future. |
| `STATUS.md` says later implementation is uncommitted. | Current `develop` head includes Reference School Demo v1 and recent governance/product commits. | Status document is stale. |
| Execution plan says several Batch 1 slices are next/planned. | Current migrations/services/UI include later pack, learning-outcome, audit, grounding, and demo work. | Plan does not represent actual current capability. |
| Root README states access tokens are in-memory only. | `apps/admin-web/src/lib/api.ts` uses `sessionStorage`. | Security-documentation mismatch. |
| Azure Container Apps is the delivery path. | Cloudflare/OpenNext config and a separate static Cloudflare site also exist; Azure directory is WAF-centric. | A deployment decision is outstanding. |
| Batch 1 migration head is `f4a5b6c7d8e9`. | The migration chain contains later revisions through `z6a7b8c9d0e1`. | Migration documentation needs reconciliation; applied DB revision remains unverified. |
| Product Blueprint says it supersedes demo scripts and journey frameworks. | Showcase documents still prescribe Demo v1 journeys. | Resolve this as a presentation hierarchy: Blueprint = narrative, Demo v1 script = operational runbook. |

---

## 9. Recommended priorities for owner confirmation

No implementation should begin from this assessment alone. The recommended sequence is:

1. **Accept the existing Reference School Demo v1 scope** as the next product milestone: local, seeded, human-reviewed, and no live AI dependency required.
2. **Authorize a human rehearsal** of the actual browser flow and record only Demo v1 blockers.
3. **Choose the shareable demo hosting path** and provide the required cloud/DNS/secrets authority.
4. **Align CI with `develop`** and run the current API/web/browser validation against the same reference workflow.
5. **Reconcile the living status/plan documents** after the current product state is accepted, using this report as the fact base.
6. **Only after a successful principal demo**, prioritize the pilot gaps: verified payment flow, external communications, managed storage/OCR, and the next intelligence capability justified by customer feedback.

### Decisions required from the product owner

1. Is the immediate target **a local principal rehearsal** or a **shareable HTTPS demo**?
2. If shareable, which hosting architecture is authoritative for web and API?
3. Does “Build Demo v1” mean **validate and harden the current committed Demo v1**, rather than add a new feature set?

---

## Conclusion

The shortest route to a compelling customer moment is already visible in the codebase. StudyNexs should demonstrate a connected school day with a grounded, human-approved assessment loop — not add another module before proving that story.

The product has enough operational breadth and AI differentiation for a serious local demo. Its next risks are presentation reliability, proof in a real browser, deployment coherence, and keeping documentation aligned with what the code already does.

**Assessment complete. Stop here pending owner review and explicit priority confirmation.**

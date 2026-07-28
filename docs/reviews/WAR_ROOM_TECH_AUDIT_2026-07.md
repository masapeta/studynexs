# StudyNexs WAR ROOM — Complete Production Readiness Review

> [!IMPORTANT]
> **Current validation status: validated with corrections; non-authoritative audit record.**
> The original review inspected `develop` at `edfc564`. ARM validation was
> performed against current `develop` at
> `7edf842212cfb22bd78d2045ec3b9245c362ee97` on 2026-07-28. This validation
> section controls current prioritization. The original review, scores, roadmap,
> and Addenda A-C are retained below as historical analysis and must not be used
> to override this section. This document is neither a release certificate nor
> implementation authorization.

## Current validation control — ARM-reviewed repository state

### Validation verdict

The review is useful as an issue-discovery record, but its severity model and
several conclusions do not accurately describe the current repository or the
approved deployment topology. Findings below are classified as **accepted**,
**corrected**, or **omitted by the original review**. Any implementation batch
must re-prove the affected condition against its starting HEAD.

### Accepted findings

The following defects or readiness gaps were confirmed against the validation
HEAD and remain valid inputs to remediation planning:

- `cryptography` is imported directly but is not declared as a direct runtime
  dependency.
- WeasyPrint is not available in the declared runtime; PDF-labelled operations
  can fall back to HTML rather than producing a real PDF.
- Production CORS validation rejects only part of the shipped localhost and
  loopback origin set.
- Notification reads and updates rely on `user_id` without mandatory
  `school_id` predicates at the service query boundary.
- Teacher class scope is applied after pagination, which can return incorrect
  pages and totals.
- Money types and API aggregation paths still leak into `float`, contrary to
  the repository's `Decimal`-end-to-end invariant.
- CI does not run on direct pushes to the active `develop` branch.
- The repository does not yet contain the production Compose topology and
  runtime proof needed to demonstrate persistent uploads, private API exposure,
  migration safety, and a recoverable container deployment.
- Mastery and downstream learning intelligence still depend materially on
  normalized free-text topic matching rather than one canonical topic/concept
  identity spine.
- Frontend automated coverage, failure-state verification, accessibility proof,
  and browser certification remain below the constitution's production-ready
  bar.

### Corrected or rejected claims

| Original framing | Current validated position |
|---|---|
| **C1:** local uploads necessarily disappear on redeploy | Incorrect for the approved OCI single-VM topology when `/opt/studynexs/data` is mounted persistently. Local storage is conditionally acceptable at this stage. The unresolved risk is absence of a committed production Compose proof, verified persistent upload mount, off-VM upload backup, and restore evidence; local disk also remains a single point of failure and does not support horizontal scaling. |
| **H2 / Addendum B:** no backup scripts, no backup/restore runbook, and no rollback runbook exist | Incorrect. `apps/api/scripts/backup_postgres.py`, `apps/api/scripts/verify_postgres_backup.py`, and `docs/runbooks/production-operations.md` exist. The real gaps are an executed clean restore drill, off-VM retention, upload/Qdrant backup automation and recovery proof, and a production Compose/deployment proof. |
| **M20:** `.gitignore` omits uploads and test/lint caches | Incorrect. `.gitignore` already excludes `uploads/`, `.pytest_cache/`, and `.ruff_cache/`. No remediation item is required for this claim. |
| **H7 / AI-2:** EUI is dead code that should be activated, archived, or deleted | Rejected. EUI is an intentionally passive, certified, protected platform subsystem behind default-off governance flags. Its source-selection work was deliberately closed at Phase 7E and Phase 7F was deferred. Default-off is a rollout posture, not evidence that the subsystem is accidental or disposable. Activation requires a product need, runtime evidence, rollback proof, and separate ARM authorization. |
| **H8:** absence of route-level `loading.tsx` proves pages lack loading states | Overstated. Route-segment coverage is limited, but multiple pages implement component-level loading states. The valid gap is incomplete route isolation and insufficient page-by-page browser proof, not proof that all 74 pages have no loading behavior. |
| **M1:** anonymous refresh consumes the documented login rate-limit budget | Overstated. Anonymous refresh may create avoidable 401 responses and log noise, but it does not by itself prove consumption of the login endpoint's rate-limit bucket. Treat this as a measured UX/observability optimization unless runtime evidence elevates it. |
| **AI-1:** the repository does not have a knowledge graph | Incorrectly absolute. A knowledge graph and curriculum-concept relationships exist; the confirmed limitation is missing prerequisite semantics and continued free-text mastery bridging. |
| **AI-3:** answer understanding stops at 40 characters | Misleading. The 40-character constant bounds a short objective exact-match path. Longer responses use subjective evaluation paths, and deterministic Maths equivalence exists behind a controlled flag. Accuracy and activation still require proof, but the system does not simply stop understanding at character 41. |
| **Move #1:** a topic picker is "strictly better" and should be implemented immediately | Not established. Canonical topic identity is strategically important, but a picker requires approved-pack availability, ambiguity handling, mobile UX, tenant-safe migration, legacy fallback, and teacher workflow validation. It must be designed and authorized separately. |

### Material risks omitted by the original review

The original audit predates or underweights the following current readiness
risks:

1. **Certified AEI capabilities remain default-off.** Maths normalization,
   review-policy metadata, approved-evidence metadata, language/OCR assist, and
   visual/science assist are present but not yet proven under an approved
   production/staging enablement profile.
2. **Manual-review signalling is not workflow enforcement.** A suggestion marked
   `manual_review_required` can still be approved unchanged without a distinct
   acknowledgement. Override reasons are enforced only when marks change.
3. **Governance sources conflict.** `docs/product/PRODUCT_EXECUTION_PLAN.md`
   reports no active implementation batch and an older release train, while
   `docs/STATUS.md` records the later AEI/EUI milestones and UX-D as the next
   gate. These sources must be reconciled before further implementation.
4. **Production metrics authentication is incomplete.** `/metrics` requires
   `METRICS_TOKEN` in production, but the supplied Prometheus scrape
   configuration sends no bearer token or `X-Metrics-Token`; the documented
   stack therefore cannot prove an authenticated production scrape.
5. **Lint debt is larger than the report communicates.** Scoped validation
   surfaced 203 API lint findings and 125 frontend lint findings; the teacher
   evaluation page alone currently has 11 lint errors. These counts are a
   baseline, not permission to ignore touched-code quality.
6. **Browser evidence is missing for the recently published teacher evaluation
   UX A-C path.** A successful frontend build is not a browser, responsive,
   keyboard, error-state, or accessibility proof.
7. **The current Golden Harness is regression infrastructure, not an accuracy
   certificate.** Real, anonymized, teacher-marked sheets are still required to
   measure agreement, false acceptance, manual-review recall, and override
   behavior.

### ARM-approved remediation order

This order supersedes the original Top 100 roadmap and all later addendum
sequencing for current execution:

1. **Correct the governance-source conflict and revise this audit.**
2. **Production safety batch:** direct dependencies, CORS, notification tenancy,
   teacher pagination, `Decimal` handling, and truthful PDF behavior.
3. **Operational proof:** production Compose, persistent uploads, private API
   binding, off-VM backups, a real restore drill, CI on `develop`,
   migration/container smoke, and authenticated metrics scraping.
4. **AEI activation and trust batch:** an explicit staging flag profile,
   enforced manual-review acknowledgement, a real teacher-marked Golden set,
   and browser proof for teacher evaluation UX A-C.
5. **Design topic-ID/mastery spine unification separately** before Student or
   Parent Learning Intelligence consumes it.
6. **Resume UX-D only after supported capabilities execute and have runtime
   evidence.** UX-D remains paused; UI must not imply support that the runtime
   profile has not proven.

### Production Safety remediation status

Stabilization Gate 1 was independently reviewed and accepted on 2026-07-28.
The direct-dependency, production CORS, notification tenancy, teacher
pagination, Decimal arithmetic, and truthful PDF findings are closed by
[`../product/PRODUCTION_SAFETY_BATCH_CERTIFICATION_REPORT.md`](../product/PRODUCTION_SAFETY_BATCH_CERTIFICATION_REPORT.md).

This closure does not change the remaining order: Operational Proof is next and
not authorized; AEI Activation/Trust, topic-ID/mastery spine design, and UX-D
remain later gated work.

### Interpretation rule

The historical findings and addenda below remain useful for traceability and
future investigation. Their original severities, scores, solution proposals,
and sequencing are not current ARM decisions. Where they conflict with this
validation control, this section wins.

> **Type:** Full technical repository audit (architecture, backend, frontend, UI/UX, security, performance, accessibility, database, API, DevOps, QA)
> **Repository:** `studynexs-dev` · branch `develop` · HEAD `edfc564`
> **Audit date:** 2026-07-28
> **Rule of engagement:** review only — **no code was modified.** Implementation awaits explicit ARM approval.
> **Coverage:** all 25 backend modules, all 22 `core/` files, DB models + 45 migrations, all frontend libs/shells/largest pages, CI, Docker, nginx, observability, 747 API tests + 11 e2e harnesses, docs. ~40.5k Python LOC + ~24k TS LOC + ~11k CSS LOC inspected.

**Review board (perspectives applied):** Principal Software Architect · Staff Frontend Engineer · Staff Backend Engineer · UI/UX Design Lead · Product Designer · Performance Engineer · Security Architect · DevOps Engineer · QA Lead · Accessibility Specialist · Database Architect · AI/LLM Systems Architect.

---

## Table of contents

1. [Phase 1 — Repository Understanding](#phase-1--repository-understanding)
   - [Architecture Overview](#1-architecture-overview)
   - [Repository Map](#2-repository-map)
   - [Module Dependency Summary](#3-module-dependency-summary)
   - [Technology Stack](#4-technology-stack)
   - [Major Risks](#5-major-risks-headline)
   - [Technical Debt Overview](#6-technical-debt-overview)
2. [Phase 2 — WAR ROOM Findings](#phase-2--war-room-findings)
   - [Critical](#-critical)
   - [High](#-high)
   - [Medium](#-medium-selected--full-ledger-available)
   - [Low](#-low-representative)
   - [What is genuinely good](#what-is-genuinely-good-credit-where-due)
3. [Scores](#scores)
4. [Prioritized Roadmap — Top 100](#prioritized-roadmap--top-100)
5. [Executive Summary](#executive-summary)
6. [Addendum A — Academic Readiness Review (scope + charter)](#addendum--academic-readiness-review-scope--charter)
7. [Addendum B — Deployment-Context Revision (OCI single-VM pilot)](#addendum-b--deployment-context-revision-oci-single-vm-one-school-pilot)
8. [Addendum C — Academic Intelligence Layer Assessment](#addendum-c--academic-intelligence-layer-assessment-the-product-definition-review)

---

# PHASE 1 — REPOSITORY UNDERSTANDING

## 1. Architecture Overview

StudyNexs is a **multi-tenant, AI-first School Operating System** built as:

- **Backend:** FastAPI (Python 3.11, fully async) **modular monolith** — 25 domain modules under `apps/api/app/modules/`, each with `endpoints/ → services/ → schemas/` layering. Cross-cutting concerns (auth, tenancy, RBAC, rate-limiting, encryption, audit) live in `app/core/`.
- **Data:** PostgreSQL 16 (SQLAlchemy 2.0 async + asyncpg), Redis 7 (auth/OTP/blacklist/rate-limit/cache), Qdrant (RAG vector store, hard-filtered by `school_id`).
- **Frontend:** Next.js 16 + React 19 + Tailwind v4 single app (`apps/admin-web`) hosting **five surfaces**: marketing site, admin dashboard, teacher portal, parent portal, student portal. Almost entirely client-rendered ("SPA inside Next").
- **AI platform:** a genuinely well-executed provider-agnostic **LLM gateway** (`gateway/invoke.py`) with fallback chains, per-call metering, credit ledger (row-locked), prompt-injection input guard, output sanitizer, and RAG grounding against approved CurriculumPacks. All authoritative AI output is human-in-the-loop.
- **Async work:** Arq (Redis) job queue + an embedded outbox worker in the API lifespan.
- **Tenancy:** subdomain/`X-Tenant-Slug` resolution → `TenantMiddleware` → JWT `school_id` cross-checked against resolved tenant on every request. All queries derive `school_id` from `CurrentUser`.
- **Auth:** 15-min JWT access tokens, 30-day HttpOnly path-scoped refresh cookie, per-device session (`sid`) rotation via an atomic Redis Lua CAS with one-rotation grace and stolen-chain reuse detection. This is *better* than most production systems reviewed.

**Request lifecycle:** nginx (rate limit) → CORS → Metrics/Tenant/Audit/AITelemetry middleware → bearer auth (Redis cache, DB fallback, blacklist check, tenant match) → `require_roles` + object-level `assert_can_*` → thin endpoint → service → `CommitOnSuccessRoute` commits *before* the response is sent (a deliberate, correct fix for FastAPI's post-response teardown hazard).

## 2. Repository Map

```
studynexs-dev/
├── .github/workflows/ci.yml      # API tests + web build + docker build (lint report-only)
├── apps/
│   ├── api/                      # FastAPI monolith — 358 py files, 40.5k LOC
│   │   ├── app/core/             # config, security, deps, tenancy, RBAC, encryption, rate-limit
│   │   ├── app/db/models/        # 33 model files, UUID PKs, school_id everywhere
│   │   ├── app/modules/          # 25 domains (auth…eui) — endpoints/services/schemas[/jobs]
│   │   ├── app/workers/          # embedded outbox relay
│   │   ├── alembic/versions/     # 45 migrations, all reversible except one merge stub
│   │   ├── tests/ (747 tests) + tests_security/ (real-Redis suite)
│   │   └── Dockerfile            # multi-stage alpine, non-root, healthcheck
│   └── admin-web/                # Next 16 — 201 TS files, 24k LOC, 74 pages
│       ├── src/app/              # (marketing), login, dashboard, teacher, parent, student, demo
│       ├── src/components/       # ui/kit + briefing + curriculum + admissions + layout…
│       ├── src/lib/              # api client, auth-context, permissions, tenant, theme
│       ├── src/styles/           # 20 CSS files (platform-*, sn-*, marketing) ~8k LOC
│       └── e2e-*.cjs (11)        # custom Playwright harnesses (not in CI)
├── infra/ (docker-compose dev, nginx, observability stack, azure WAF bicep)
├── docs/ (extensive: STATUS, DECISION_LOG, architecture, AEI/EUI certifications)
└── 19 root-level *.md process artifacts (CODE_REVIEW*, P3–P6 reports, certificates…)
```

## 3. Module Dependency Summary

- **Layering is respected:** endpoints never contain SQL; services own logic; cross-module reads go through services or shared models. No circular imports found.
- **Shared platform services** (`ai/gateway`, `ai/vectorstore`, `ai/embeddings`, `core/staff_permissions`, `core/tenant_scope`) are consumed by all pillars — no duplicate AI stacks. The "build once in platform, consume from pillar" rule is actually followed.
- **Exceptions:** `examinations/answer_sheet_eval_service.py` imports from 7 other modules (ai, eui, files, curriculum, knowledge_graph…) — the fattest coupling point. `demo` imports `auth`'s private `_get_client_ip`. `analytics/` is an **empty scaffold** (4 `__init__.py`s, zero code).
- **Dark code:** `eui/` = 6,416 LOC across 38 files, **all behind default-off flags** (plus AEI passive layers) — a large, certified-but-inert subsystem riding along in every deploy.

## 4. Technology Stack

| Layer | Choice | Assessment |
|---|---|---|
| API | FastAPI 0.115+, Python 3.11, Pydantic v2 | Modern, idiomatic |
| DB | Postgres 16, SQLAlchemy 2.0 async, Alembic | Correct; partial unique indexes used for race safety |
| Cache/queue | Redis 7, Arq | Appropriate |
| Vector | Qdrant (memory store for tests) | Tenant-filtered correctly |
| Web | Next 16.2.11, React 19.2.4, Tailwind v4, framer-motion, lucide | **Only 4 runtime deps** — admirably lean |
| Deploy | Docker (alpine, non-root), Cloudflare (OpenNext) + Azure ACA intent | Dev solid; **prod story incomplete** |
| Observability | structlog, Prometheus `/metrics` (token-gated), OTel opt-in, Grafana/Tempo configs | Above-average for stage |

## 5. Major Risks (headline)

1. **File storage is local-disk only** — "Azure Blob (prod)" exists only in comments. On Azure Container Apps, every redeploy **destroys all uploaded answer sheets, identity documents, and receipts.** Data-loss class.
2. **`cryptography` is an undeclared dependency** — `core/encryption.py` (Aadhaar at-rest encryption, imported by `school_ops` models) only works because `google-genai → google-auth` pulls it in transitively. A base install (`pip install -e .` without `[ai]`) **fails to boot.**
3. **WeasyPrint is referenced by all 4 PDF renderers but declared nowhere** — receipts, question papers, report cards, lesson plans **silently ship HTML instead of PDF in every environment,** including the Docker image.
4. **Production CORS validator has holes** — it only rejects `localhost:3000/3001`; `:3002/:3003/:3006` and all `127.0.0.1` defaults would pass the boot guardrail into production.
5. **Frontend has zero unit tests** and its 11 Playwright e2e harnesses are **not wired into CI** — web regressions are caught only by `tsc` via `next build`.
6. **No production deployment pipeline** — CI builds an image but deploys nothing; no ACA bicep (only WAF), no migration-gated deploy, no rollback runbook, no DB backup story in repo.

## 6. Technical Debt Overview

- **Deliberate, documented debt (healthy):** lint report-only in CI, notification tenant-scoping gap, provider benchmarking pending — all recorded in DECISION_LOG.
- **Structural debt:** 920 inline `style={{}}` blocks bypassing the token system; 4 overlapping CSS namespaces (`platform-*`, `sn-*`, `ui-*`, `marketing`); god-pages (curriculum 44KB, ai-papers 39KB); `ai/endpoints/ai.py` at 1,017 lines mixing QP + report cards + credits + copilot.
- **Process debt:** 19 root-level markdown artifacts; `docs/` has parallel/partially superseded plans (MASTER_PLAN, ROADMAP, PRODUCT_PLAN, TRACK_AB…).
- **Dark-code debt:** EUI/AEI passive layers (~8k LOC combined) are maintained, tested, certified — and do nothing at runtime yet. That is a real ongoing carrying cost.

---

# PHASE 2 — WAR ROOM FINDINGS

Severity legend: **Critical** = fix before any real school touches prod · **High** = fix before/at launch · **Medium** = fix soon · **Low** = hygiene.

---

## 🔴 CRITICAL

### C1. Uploaded files are stored on local container disk only

- **Location:** `apps/api/app/modules/files/services/file_service.py` (L16–L46)
- **Description:** `FileService.upload()` writes to `UPLOAD_DIR` on the container filesystem. The Azure Blob path promised in comments and config (`AZURE_STORAGE_CONNECTION_STRING`) is **never implemented** — grep confirms zero blob SDK usage.
- **Why it matters:** ACA/Container filesystems are ephemeral. Every deploy, restart, or scale event silently deletes answer-sheet scans (marks evidence!), admission identity documents (Aadhaar scans — regulated PII), and receipt PDFs. Multi-replica scaling breaks reads entirely (file on replica A, request lands on B). This directly violates the audit-trail guarantees the evaluation pillar is built on.
- **Recommended solution:** Implement a `StorageBackend` protocol with `LocalDiskStorage` (dev) and `AzureBlobStorage` (prod, using the existing connection-string setting), selected in config; add a production boot guardrail requiring blob config; migrate `storage_path` semantics.
- **Expected impact:** Eliminates a guaranteed data-loss incident class.
- **Blocks production? YES.**

### C2. `cryptography` package is not a declared dependency

- **Location:** `apps/api/app/core/encryption.py` (L27) vs `apps/api/pyproject.toml`
- **Description:** `from cryptography.fernet import …` powers Aadhaar at-rest encryption and is imported at module scope by `db/models/school_ops.py` (imported by `models/__init__.py`, i.e., at app boot). It appears in **no dependency group**; it is present locally only because `google-genai → google-auth` requires it.
- **Why it matters:** Any install without `[ai]` (or a future google-genai release dropping the transitive dep) makes the API **unable to boot**. The Dockerfile happens to install `[ai]`, masking the bug — a time bomb.
- **Recommended solution:** Add `cryptography>=42` to core `dependencies` in pyproject + requirements.txt.
- **Expected impact:** One-line fix; removes a boot-failure trap.
- **Blocks production? YES.**

### C3. PDF generation is silently broken everywhere (WeasyPrint undeclared)

- **Location:** `fees/services/receipt_pdf.py` (L117–L126), `ai/services/paper_pdf.py`, `ai/services/report_card_pdf.py`, `curriculum/services/lesson_plan_pdf.py`
- **Description:** All four renderers do `try: from weasyprint import HTML … except ImportError: return HTML`. WeasyPrint is in no dependency group and the alpine image lacks its native libs (pango/cairo). **Every environment ships HTML fallback**; "export PDF" is marketing fiction.
- **Why it matters:** Fee receipts and report cards are legal/parent-facing documents. Schools expect PDFs. The silent fallback means nobody notices until a principal tries to print.
- **Recommended solution:** Either (a) add weasyprint + alpine native deps to the image and a startup log/metric when the fallback is active, or (b) make HTML-print the *explicit* documented behavior and remove the dead import. Decide, don't drift.
- **Expected impact:** Restores a shipped-in-name-only feature; removes silent degradation.
- **Blocks production? YES** (for any school expecting receipts/report cards as PDF).

### C4. Production CORS guardrail can be bypassed by the shipped defaults

- **Location:** `apps/api/app/core/config.py` (`_validate_production_config`, ~L316)
- **Description:** The validator's `unsafe_origins` set is `{"*", "http://localhost:3000", "http://localhost:3001"}`. The default `ALLOWED_ORIGINS` also contains `:3002 :3003 :3006` and five `127.0.0.1` variants — all of which **pass** the production check. An operator who forgets to set `ALLOWED_ORIGINS` boots production with dev origins + `allow_credentials=True`.
- **Why it matters:** Credentialed CORS from attacker-controllable local origins undermines the refresh-cookie CSRF defense (`validate_refresh_origin` trusts this same list).
- **Recommended solution:** In production, reject *any* origin matching `localhost|127.0.0.1` (regex), or require explicit non-default `ALLOWED_ORIGINS`.
- **Expected impact:** Closes a real config-footgun in the strongest part of the security story.
- **Blocks production? YES** (one-line validator fix).

---

## 🟠 HIGH

### H1. Zero frontend unit tests; e2e harnesses excluded from CI

- **Location:** `apps/admin-web/` (0 `*.test.*` files); `.github/workflows/ci.yml` (web job)
- **Description:** 24k LOC of client logic (auth-context token lifecycle, permissions maps, route guards, form flows) has no automated test in CI beyond `next build` type-checking. The 11 Playwright `.cjs` harnesses require live servers and never run in the pipeline.
- **Why it matters:** The single most regression-prone surface (session refresh, RBAC nav, payment forms) has no safety net. This is the sharpest asymmetry in the repo: backend 747 tests, frontend 0.
- **Recommended solution:** Add Vitest + React Testing Library for `lib/` (api client refresh logic, permissions, tenant, theme) as a CI gate; add one headless e2e smoke job in CI against a compose stack.
- **Expected impact:** Regression protection for auth/RBAC UI.
- **Blocks production? Yes** (for a trust-critical product).

### H2. No deployment pipeline, no rollback, no backups in repo

- **Location:** `.github/workflows/ci.yml` (build-only), `infra/azure/` (WAF bicep only)
- **Description:** CI validates but deploys nothing. No ACA/container-app IaC, no migration-gated deploy job, no image registry push, no DB backup/restore runbook.
- **Why it matters:** Constitution §69 requires migrations gating deploys and boring rollbacks; today "deploy" is undefined — meaning it's manual and unrepeatable.
- **Recommended solution:** Add deploy workflow (build → push → `alembic upgrade head` → ACA revision update → `/ready` gate), pin backups (PITR) in runbooks.
- **Expected impact:** Removes the single largest operational risk.
- **Blocks production? Yes.**

### H3. `X-Real-IP` trusted unconditionally for rate-limit identity

- **Location:** `apps/api/app/modules/auth/endpoints/auth.py` (`_get_client_ip`, L41–L52)
- **Description:** `_get_client_ip` prefers the `X-Real-IP` header. Behind the repo's nginx it's overwritten — but any path where the API is reachable directly (ACA ingress without the proxy, dev exposure, misconfigured Front Door) lets a client mint a fresh rate-limit bucket per request, **defeating OTP/login/demo-provisioning limits entirely**.
- **Why it matters:** Brute-force and demo-farm abuse become trivial the moment topology drifts.
- **Recommended solution:** Gate header trust behind a `TRUSTED_PROXY` setting (only honor `X-Real-IP` when the socket peer is the proxy), else use `request.client.host`.
- **Expected impact:** Restores rate-limit integrity independent of topology.
- **Blocks production? Yes.**

### H4. Notifications are not tenant-scoped at the query layer

- **Location:** `apps/api/app/modules/notifications/services/notification_service.py` (L43–L52)
- **Description:** `list_user_notifications`, `mark_read`, `unread_count` filter by `user_id` only; `school_id` is stored but never enforced on reads. Known gap (DECISION_LOG §5) — still open.
- **Why it matters:** Defense-in-depth violation of the sacred rule (§22). Any future bug that confuses user IDs across tenants leaks cross-school data. Cheap to fix, expensive to leave.
- **Recommended solution:** Add `Notification.school_id == current_user.school_id` to every query + a tenant-isolation test.
- **Expected impact:** Closes the documented §22 exception.
- **Blocks production? Yes** (it's a Prime Directive).

### H5. Scoped-teacher class list: pagination filtering bug

- **Location:** `apps/api/app/modules/academic/endpoints/academic.py` (`list_classes`, L42–L63)
- **Description:** Classes are paginated in SQL **then** filtered by teacher scope in Python, and `total` is overwritten with the filtered page length. A teacher whose classes fall on page 2 sees an empty page 1 with a wrong total; total_pages is wrong for everyone scoped.
- **Why it matters:** Live correctness bug in a core navigation query for teachers.
- **Recommended solution:** Push scope into the SQL WHERE (`Class.id.in_(allowed)`) before pagination.
- **Expected impact:** Correct lists + counts for scoped staff.
- **Blocks production? Yes** (teacher-facing correctness).

### H6. Money typed as `float` in ORM annotations and serialized as float in APIs

- **Location:** `apps/api/app/db/models/fee.py` (L74–L100, `Mapped[float]` on `Numeric` columns); `fee_service.get_fee_stats` (L204–L246, `float(total_collected)`); portal `_fee_pending` float math
- **Description:** Runtime values are Decimal (asyncpg returns Decimal for Numeric) and the payment path defensively re-wraps with `Decimal(str(x))` — but the **type system says float**, stats/portal endpoints emit floats, and one aggregation path does float arithmetic. Prime Directive 4 says Decimal end-to-end.
- **Why it matters:** The annotations invite the next engineer to do float math on money; two paths already do. Display-precision today, mis-recorded paise tomorrow.
- **Recommended solution:** Change annotations to `Mapped[Decimal]`; serialize money as string/Decimal via Pydantic; fix `_fee_pending` and `get_fee_stats` to Decimal.
- **Expected impact:** Restores the money invariant the constitution mandates.
- **Blocks production? Yes** (financial correctness posture).

### H7. Dead/dark code mass: EUI (6.4k LOC) all-off, `analytics/` empty, outbox handlers that no-op

- **Location:** `apps/api/app/modules/eui/**`, `apps/api/app/modules/analytics/**`, `app/workers/outbox_worker.py` (handlers, L38–L56)
- **Description:** EUI ships 38 files behind seven default-off flags. `analytics` is 4 empty `__init__.py`s. Outbox handlers for `fee_paid`/`attendance_marked`/`notice_published` just log — parents receive **no notification** despite the event plumbing implying they do.
- **Why it matters:** Carrying cost (review, CI time, import weight), and the outbox no-ops are a *product* gap masquerading as infrastructure: the "fee paid → parent notified" loop doesn't exist.
- **Recommended solution:** Delete `analytics/` scaffold; implement in-app notification dispatch in the three no-op handlers (the NotificationService already exists); keep EUI but document its dark status in README to stop it inflating perceived capability.
- **Expected impact:** Real parent notifications; leaner tree.
- **Blocks production? No** (but the no-op handlers are a launch-expectation trap).

### H8. Route-level loading/error coverage: 0 `loading.tsx`, 1 `error.tsx` for 74 pages

- **Location:** `apps/admin-web/src/app/**`
- **Description:** Pages handle loading internally with useState flags (portal pages do this well; several dashboard pages don't — see H9), but there is no route-segment skeleton or per-section error boundary. A render error in any dashboard page falls through to the single root error page.
- **Why it matters:** Constitution §57/§8 declares states mandatory. Blank-shell first paints and whole-app error blowouts read as unfinished software to a principal.
- **Recommended solution:** Add `loading.tsx` per portal segment (dashboard/teacher/parent/student) + `error.tsx` per segment; keep in-component skeletons.
- **Expected impact:** Perceived quality and resilience jump.
- **Blocks production? No, but borderline** — it violates the repo's own Production-Ready Policy.

### H9. Silent data-fetch failures on admin pages

- **Location:** e.g. `apps/admin-web/src/app/dashboard/students/page.tsx` (L56–L62) — `catch (err) { console.error(...) }`
- **Description:** Fetch failure renders an empty table with **no error message, no retry**. Same pattern on several dashboard pages (grep shows ~20 console-only catches). Portal pages, by contrast, do this correctly.
- **Why it matters:** UX Law 3/17: an admin can't distinguish "no students" from "the request failed" — corrosive to trust.
- **Recommended solution:** Standardize the portal pages' `error + retry` pattern into a shared `useApiList` hook; forbid console-only catches by ESLint rule.
- **Expected impact:** Trustworthy failure behavior everywhere.
- **Blocks production? Yes** for admin-critical pages.

---

## 🟡 MEDIUM (selected — full ledger available)

| # | Finding | Location | Why / Fix |
|---|---|---|---|
| M1 | Refresh-on-mount 401 noise: `AuthProvider.init` POSTs `/auth/refresh` for every anonymous visitor | `src/lib/auth-context.tsx` L51–L66 | Burns auth rate budget + log noise; skip when no session hint exists |
| M2 | Hardcoded "Greenwood Public School" + "· Term 1" fallbacks | `src/app/dashboard/DashboardShell.tsx` L24–L56 | Fake data can render in prod before profile loads; use skeleton not fiction |
| M3 | `viewport maximumScale: 1` blocks pinch-zoom | `src/app/layout.tsx` L27 | WCAG 1.4.4 failure; remove maximumScale |
| M4 | 920 inline `style={{…}}` blocks | across `src/**` | Bypasses tokens; extract to `sn-*`/utility classes incrementally |
| M5 | CI doesn't trigger on `develop` pushes | `.github/workflows/ci.yml` L9–L11 | Active branch only tested via PRs; add `develop` to push branches |
| M6 | requirements.txt drift (missing pypdf/pillow/pytesseract) | `apps/api/requirements.txt` | Two sources of truth already diverged; generate from pyproject |
| M7 | No `.env.example` | `apps/api` | Onboarding + config documentation gap (constitution §70) |
| M8 | nginx lacks security headers (HSTS, X-Content-Type-Options, X-Frame-Options, CSP) and any prod TLS variant | `infra/nginx/nginx.conf` | Add prod server block or document Front Door as the header layer |
| M9 | Bounded N+1s: `student_profile` (per-parent queries), `_incharge_summary` (per-class), tutor graph | `academic_service.py` L418–L433, `dashboard_service.py` L418–L446 | Fine at pilot; join/aggregate before multi-school scale |
| M10 | Unbounded `list_*` queries (exams, packs, admissions, payroll, staff, roster, fee roster…) | multiple services | Add pagination/limits before year-2 data volumes |
| M11 | Audit middleware opens a **second DB session per mutating request** and derives `resource_type` from `path.split("/")[-2]` | `core/audit_middleware.py` L68–L84 | Overhead + garbage resource labels; reuse request session post-commit or queue |
| M12 | OTP equality not constant-time; OTP logged in dev mode | `auth/services/auth_service.py` L69–L104 | Marginal risk (attempt cap) — use `secrets.compare_digest`; keep dev-log but ensure `is_development` gating is airtight |
| M13 | Demo creds (`Demo@1234`) in the client bundle | `src/lib/portal.ts` L26–L31 | Acceptable only while demo tenants are isolated + expiring; gate behind demo-host check |
| M14 | `/platform/engineering-status` exposes internal engineering telemetry to school admins | `platform/endpoints/engineering.py` | Restrict to a platform-operator role (which doesn't exist yet in the enum) |
| M15 | `UserRole` lacks `platform_operator`; `operations` role exists but is absent from most role-gates | `db/models/user.py` L14–L22 | Role model drift vs constitution §16.1 |
| M16 | TopBar 60s notification polling without backoff; keeps polling on auth failure | `components/layout/TopBar.tsx` L53–L59 | Add error backoff; stop after 401 |
| M17 | 4 parallel CSS token namespaces (`platform-*`, `sn-*`, `ui-*`, marketing) ~11k LOC | `src/styles` + globals + ui-kit | Consolidation plan needed; this is how design drift starts |
| M18 | `ai/endpoints/ai.py` = 1,017 lines (QP + bank + report cards + credits + copilot) | `ai/endpoints/ai.py` | Split into 4 routers; it's past the readability threshold |
| M19 | God-pages: curriculum 44KB / ai-papers 39KB / evaluate 20KB client components | `dashboard/teaching/**` | Decompose; these will resist every future change |
| M20 | `.gitignore` missing `uploads/`, `.pytest_cache/`, `.ruff_cache/` | `.gitignore` | 447 local upload files one `git add -A` away from history |
| M21 | Root README + 19 process artifacts at repo root | `/` | Move to `docs/reviews/`; root should sell the product, not the process |
| M22 | `getTenantSlug()` falls back to `"test"` in production builds if env unset | `src/lib/tenant.ts` L88 | Misconfigured prod web silently talks to the `test` tenant |
| M23 | Access-token in `sessionStorage` (XSS-readable) | `src/lib/api.ts` | Accepted trade-off (15-min TTL) — document as such; CSP would compensate (see M8) |
| M24 | Role/permission changes lag ≤15 min (JWT claim) + 60s (cache) with no force-revoke on role change | `core/dependencies.py` | Blacklist user's jti-family or bump a per-user token-version on role change |

## 🟢 LOW (representative)

- Rate limiter docstring says "sliding window", implementation is fixed-window (`core/rate_limit.py`).
- 34 frontend TODOs, 20 console statements, 28 `any` usages (mostly annotated legacy).
- Starlette TestClient deprecation warning in test output.
- `FeeService.get_fee_stats` imports inside function body (style inconsistency).
- `subjects`, `list_years` etc. missing `.limit()` but naturally tiny result sets.
- `FILE_UPLOAD_DIR` accessed via `hasattr(settings, …)` — the setting doesn't exist; add it properly.
- One merge migration with `pass` downgrade (acceptable for a merge node).

---

## What is genuinely GOOD (credit where due)

The review board wants to be explicit — this is **far above typical pre-launch quality** in several areas:

1. **Auth engineering** — session-keyed refresh rotation with atomic Lua CAS, one-rotation multi-tab grace, reuse-detection revocation, path-scoped HttpOnly cookies, origin-checked refresh, enumeration-safe login, fail-secure bcrypt. Textbook.
2. **Tenancy** — `school_id` from `CurrentUser` everywhere, JWT-vs-tenant match on every request, `TenantScope` FK ownership checks, Qdrant hard filters, IDOR test suite.
3. **Money** — row-locked payment path, dual idempotency (transaction_id + idempotency_key with amount-mismatch rejection), DB partial-unique race constraints, receipt counters with self-provisioning, escaped receipt HTML.
4. **AI platform** — single gateway, fallback chains, reserve-then-finalize credit metering with row-locked ledger, input/output guards, grounded RAG with citations, HITL on everything authoritative, per-feature rate limits. This is the moat and it's real.
5. **Test culture (backend)** — 747 tests including tenancy, concurrency, race safety, receipt escaping, client-IP, commit-route coverage assertions, and a separate real-Redis security suite.
6. **`CommitOnSuccessRoute`** — a subtle, correctly-diagnosed fix for FastAPI's post-response teardown commit hazard, enforced by a coverage test.

---

# SCORES

| Dimension | /10 | Rationale (one line) |
|---|---|---|
| **Architecture** | **8.0** | Disciplined modular monolith, clean seams, real shared AI platform; dark-code mass and one god-endpoint deduct |
| **Backend** | **8.0** | Idiomatic async FastAPI, strong services; N+1 pockets, unbounded lists, dep-declaration failures deduct |
| **Frontend** | **6.0** | Lean deps, working portals; but client-only data layer, god-pages, silent error catches, zero tests |
| **UI/UX** | **7.0** | Coherent dark-glass identity, real skeleton/empty patterns in portals; admin pages inconsistent, hardcoded fallback data, 920 inline styles |
| **Performance** | **6.5** | Async everywhere, indexed hot paths, lean bundle deps; client-fetch waterfalls, no caching layer on web, bounded N+1s |
| **Security** | **7.5** | Exceptional auth/tenancy/input-guarding for stage; CORS validator gap, X-Real-IP trust, missing headers deduct |
| **Accessibility** | **6.5** | 294 aria uses, skip links, reduced-motion, keyboard handlers on kit; maximumScale=1, div-buttons in kit, no audit tooling |
| **Maintainability** | **6.5** | Excellent docstrings & decision log; CSS namespace sprawl, root clutter, giant pages, requirements drift |
| **Scalability** | **7.0** | Multi-tenant-by-construction, Arq, Qdrant scoping; local-disk files kill horizontal scale today |
| **Testing** | **6.0** | Backend 9/10, frontend 0/10, e2e not in CI — the average hides an asymmetry that must be fixed |
| **Production Readiness** | **5.0** | Four critical blockers + no deploy/rollback/backup path — not shippable to a paying school this week |
| **Technical Debt** | **6.0** | Debt is mostly *known and logged* (good) but the dark-code and CSS masses are compounding |

## **Overall Grade: B**

*A genuinely strong engineering foundation with production-blocking gaps concentrated in the "last mile": storage, dependencies, deployment, and frontend verification. The core is A-grade; the operational shell is C-grade. Fix the 4 criticals + 5 highs and this is a B+/A- platform.*

---

# PRIORITIZED ROADMAP — TOP 100

Ranked by **business impact ÷ risk ÷ effort (ROI)**.

## ⚡ QUICK WINS (days; items 1–30)

| # | Action | Sev | Effort |
|---|---|---|---|
| 1 | Add `cryptography` to core deps (pyproject + requirements) | Crit | 5 min |
| 2 | Fix production CORS validator to reject all localhost/127.0.0.1 patterns | Crit | 30 min |
| 3 | Decide WeasyPrint: add dep + alpine libs **or** remove and document HTML-print | Crit | ½ day |
| 4 | Gate `X-Real-IP` trust behind a trusted-proxy setting | High | 2 h |
| 5 | Add `school_id` filter to all notification queries + isolation test | High | 2 h |
| 6 | Fix `list_classes` scope-after-pagination bug (scope in SQL) | High | 2 h |
| 7 | Add `develop` to CI push triggers | Med | 5 min |
| 8 | Remove `maximumScale: 1` from viewport | Med | 5 min |
| 9 | Add `uploads/`, cache dirs to `.gitignore` | Med | 5 min |
| 10 | Create `.env.example` with every settings key documented | Med | 1 h |
| 11 | Regenerate requirements.txt from pyproject (add pypdf/pillow/pytesseract) | Med | 15 min |
| 12 | Replace "Greenwood Public School"/"Term 1" fallbacks with skeleton states | Med | 1 h |
| 13 | Skip refresh-on-mount when no session hint (localStorage flag set at login) | Med | 2 h |
| 14 | Add error+retry UI to students/staff/classes/fees admin pages (share portal pattern) | High | 1 day |
| 15 | `secrets.compare_digest` for OTP comparison | Med | 15 min |
| 16 | Add security headers to nginx (or document Front Door ownership) | Med | 1 h |
| 17 | Delete empty `analytics/` module scaffold | Med | 10 min |
| 18 | Move 19 root MD artifacts to `docs/reviews/archive/` | Med | 30 min |
| 19 | Add `FILE_UPLOAD_DIR` as a real typed setting (kill `hasattr` hack) | Low | 30 min |
| 20 | Fix rate-limit docstring (fixed-window not sliding) | Low | 5 min |
| 21 | Stop TopBar polling after 401; add exponential backoff | Med | 1 h |
| 22 | ESLint rule: no console-only catch on api() calls | Med | 1 h |
| 23 | Restrict `/platform/engineering-status` pending platform_operator role | Med | 30 min |
| 24 | Fail prod boot when `NEXT_PUBLIC_TENANT_*` unset (web build check for `"test"` fallback) | Med | 1 h |
| 25 | Log + metric when PDF renderer falls back to HTML | Med | 1 h |
| 26 | Add `Retry-After` awareness + toast to web api() 429 handler (partially exists — surface it) | Low | 1 h |
| 27 | Emit metric when blacklist check degrades (Redis outage visibility) | Low | 30 min |
| 28 | Add `limit()` caps to unbounded list services (exams, packs, admissions, payroll, staff) | Med | ½ day |
| 29 | Fix demo login prefill to only render on demo hosts | Med | 1 h |
| 30 | Remove remaining 20 console statements via lint autofix | Low | 1 h |

## 🔧 MEDIUM-TERM (1–3 weeks; items 31–70)

| # | Action | Sev |
|---|---|---|
| 31 | **Implement AzureBlobStorage backend** + prod boot guardrail + migration of existing paths | Crit |
| 32 | **Build the deploy pipeline**: image push → alembic gate → ACA revision → `/ready` verification → rollback doc | High |
| 33 | Add Vitest + RTL; test api-client refresh single-flight, permissions maps, tenant resolution, theme | High |
| 34 | Wire one Playwright smoke run into CI (compose stack, reference tenant) | High |
| 35 | Convert money annotations to `Mapped[Decimal]`; Decimal-safe serialization on stats/portal endpoints | High |
| 36 | Implement outbox handlers: fee_paid / attendance absent / notice_published → NotificationService | High |
| 37 | Split `ai/endpoints/ai.py` into question-paper / report-card / credits / copilot routers | Med |
| 38 | Decompose curriculum (44KB) and ai-papers (39KB) pages into feature components | Med |
| 39 | Introduce a shared `useApiQuery`/`useApiList` hook (loading/error/retry/abort) and migrate the 25 highest-traffic pages | High |
| 40 | Add per-segment `loading.tsx` + `error.tsx` for dashboard/teacher/parent/student | High |
| 41 | Fix `student_profile` parent N+1 with a single join query | Med |
| 42 | Fix `_incharge_summary` per-class N+1 with grouped aggregate | Med |
| 43 | DB backup/restore runbook + PITR verification for Postgres | High |
| 44 | Per-user token-version (or jti-family revocation) so role changes invalidate immediately | Med |
| 45 | Add `platform_operator` role; wire into permissions surface + engineering-status gate | Med |
| 46 | Consolidate CSS: merge `platform-aliases` into tokens; publish "which namespace when" ADR; freeze new namespaces | Med |
| 47 | Reduce inline styles: codemod the 10 most repeated style objects into kit classes | Med |
| 48 | Add pagination to fee roster and staff directory endpoints + UI | Med |
| 49 | Audit middleware: reuse request session or enqueue audit rows via outbox (kill 2nd session/request) | Med |
| 50 | Add explicit `allow_methods`/`allow_headers` lists to CORS | Low |
| 51 | Add axe-core automated a11y checks to the e2e harness | Med |
| 52 | Kit `Card`/`ListRow`: render real `<button>` when interactive (not div+role) | Med |
| 53 | Add Playwright e2e for parent + student portals to the CI smoke | Med |
| 54 | Implement SMS (MSG91) dispatch for OTP — currently OTP only works via dev_otp | High (launch-dependent) |
| 55 | Frontend error-boundary telemetry (report to API endpoint or Sentry) | Med |
| 56 | Web bundle budget check in CI (fail > 250KB first-load per constitution §108) | Med |
| 57 | Add Alembic autogenerate diff check in CI (models vs migrations drift) | Med |
| 58 | Document and test the demo-tenant sweep/expiry job end-to-end | Med |
| 59 | Add request-body size limits at FastAPI level (beyond nginx 12m) | Low |
| 60 | Type the 28 `any` usages; enable `noImplicitAny` fully | Low |
| 61 | Introduce typed API-response models on web (`api<T>` everywhere; ban untyped calls via lint) | Med |
| 62 | Add soft-delete or archival strategy decision for students/users (currently hard rows only) | Med |
| 63 | Health endpoint: include migration-head check in `/ready` | Med |
| 64 | Structured frontend logging util (replace console; respects env) | Low |
| 65 | Rate-limit `/metrics` scrapes + document Prometheus auth | Low |
| 66 | Add `test_notifications_tenant_isolation` + regression suite for every H-item fixed | High |
| 67 | Prod nginx variant (TLS termination path) or explicit Front Door architecture doc | Med |
| 68 | Add DB index audit — verify indexes behind attendance/date and receipts/paid_at hot queries | Med |
| 69 | Capacity test with locustfile (exists!) against staging; record budgets | Med |
| 70 | Add CODEOWNERS + PR template encoding the constitution checklists | Low |

## 🏗 LONG-TERM ARCHITECTURAL (1–3 months; items 71–100)

| # | Action |
|---|---|
| 71 | Data-fetching architecture decision: adopt TanStack Query (or server components + streaming) — kill the 134-useEffect ad-hoc layer |
| 72 | Move read-heavy pages (students, classes, staff lists) to Server Components with client islands |
| 73 | Design-system consolidation: one token source, one component kit, deprecate `platform-*`/`ui-*` split |
| 74 | EUI activation-or-archival decision — 6.4k dark LOC must earn its keep or move to a branch |
| 75 | Bind Arq workers into CI (worker smoke test: enqueue → complete) |
| 76 | Multi-replica session-safe file serving via Blob SAS URLs (depends on #31) |
| 77 | Introduce OpenAPI-generated TypeScript client (kills manual type mirroring drift) |
| 78 | Formal RBAC matrix doc auto-generated from `staff_permissions.py` + endpoint gates |
| 79 | Postgres read-replica readiness pass (session/txn boundaries audit) |
| 80 | Razorpay online-payment integration (config exists; flow unimplemented) |
| 81 | MSG91/SendGrid/FCM notification channels (currently all `pass`) |
| 82 | Audit-log query UI for principals (data exists; no surface) |
| 83 | Per-tenant rate/credit/storage quotas enforcement layer (constitution O.3) |
| 84 | DPDP compliance pack: consent flows, deletion pathways, retention automation (blocking real student data per DECISION_LOG) |
| 85 | Backup verification automation (restore drill in CI monthly) |
| 86 | Blue/green or revision-split deploys on ACA with automated rollback on `/ready` failure |
| 87 | Observability SLOs: wire prometheus-alerts.yml to a real alert channel; define error budgets (§108.4) |
| 88 | Web performance instrumentation (CWV field data → budgets dashboard) |
| 89 | Semantic-cache layer for tutor/copilot repeated queries (cost lever, per §36) |
| 90 | Provider benchmark harness → lock production LLM default (DECISION_LOG D5 still open) |
| 91 | Split `answer_sheet_eval_service` dependencies via a facade (7-module import fan-in) |
| 92 | Extract PDF rendering into one shared `documents` service (4 near-identical renderers today) |
| 93 | Introduce contract tests for `/api/v1` stability (schemathesis or snapshot suite) |
| 94 | i18n foundation (Telugu/Hindi parents are the market; zero i18n scaffolding exists) |
| 95 | Offline-tolerant attendance page (constitution §104 promise; nothing yet) |
| 96 | Accessibility formal audit to WCAG 2.1 AA with remediation backlog |
| 97 | Docs consolidation: single source of truth for plans (5 overlapping planning docs today) |
| 98 | Flutter/mobile API-readiness pass (versioning headers, §111 negotiation) |
| 99 | Chaos test: Redis outage drill (auth degradation paths are written — verify them live) |
| 100 | Yearly academic-year rollover workflow (promotion/graduation) — currently unmodeled, guaranteed year-end crisis |

---

## Executive Summary

StudyNexs has an **unusually strong core** — the auth system, tenant isolation, money handling, and AI gateway are engineered with a care rarely seen pre-revenue, and the 747-test backend suite covers exactly the right invariants (tenancy, concurrency, money, escaping). The constitution isn't decoration; most of it is genuinely enforced in code.

The gaps are concentrated in the **operational last mile**: files that vanish on redeploy, two undeclared dependencies that make features silently fail or the app fail to boot, a CORS guardrail that doesn't guard, no deploy/rollback/backup machinery, and a frontend with zero automated verification. None of these are architectural — all are fixable in a focused 2–3 week hardening pass, after which this platform would credibly serve its pilot school.

**Recommended sequence:** Criticals C1–C4 (≈3 days) → Highs H1–H9 (≈2 weeks) → Quick Wins in parallel → medium-term items before onboarding school #2.

---

# ADDENDUM — Academic Readiness Review (scope + charter)

> **Added 2026-07-28, after the technical audit.** The WAR ROOM above validates that the *machine is built well*. It does **not** validate that the machine *teaches, grades, and communicates the way a real school does*. Those are different failure modes: engineering bugs crash; **pedagogy bugs erode trust silently**. Since StudyNexs's competitive advantage is academic intelligence, a separate **Academic Readiness Review (ARR)** — run *with* educators — must gate school onboarding. This addendum records (a) what a code audit *can* already say about the five academic questions, and (b) the proposed ARR charter.

## A.1 What the code already reveals per question

The codebase encodes dozens of **unvalidated pedagogical assumptions as constants**. Inventorying them is the concrete input the ARR needs.

### Q1. Does evaluation match how teachers actually grade? — *Partially inspectable; materially unvalidated*

- The marking engine (`ai/services/evaluation_engine.py`) decomposes model answers into ≤8 weighted criteria with partial credit at temperature 0.1. That *approximates* SSC "step marking" (formula/substitution/answer), but **nobody has compared its awards against a panel of real teachers marking the same scripts.**
- The 17 golden datasets in `tests/golden/` are **software-contract tests** (schema shape, override precedence, evidence exclusion) — *not* marking-fidelity benchmarks. There is **no dataset of real teacher-marked answer sheets** to measure agreement against. That asset does not exist and must be built.
- **Concrete suspect found:** `_OBJECTIVE_ANSWER_MAXLEN = 40` (`answer_sheet_eval_service.py`) routes any short answer with a compact key to **exact normalized string match**. A teacher accepts "photosynthesis"/"photo-synthesis"/a Telugu-transliterated spelling; exact match marks them wrong. This will produce visible, trust-burning false negatives in the first real batch.

### Q2. Does the curriculum workflow fit school operations? — *A real mismatch is visible in code*

- `can_approve_curriculum_pack` (`core/staff_permissions.py`) grants approval to the **class incharge** of the pack's class. The constitution says **HOD approval**. In AP/Telangana schools these are different people — the Class 8 incharge is often a language teacher who cannot meaningfully approve the Class 8 Science pack.
- There is **no subject-head/HOD role** in the `UserRole` enum. This is an org-model question only a school can settle — but the code has already picked an answer.

### Q3. Will principals interpret dashboards correctly? — *Best-designed area; thresholds unvalidated*

- Credit due: `dashboard_service.py` deliberately distinguishes `not_recorded / in_progress / attention_needed / healthy` and **never shows zero records as "0% attendance"** — genuine interpretability engineering.
- But: during `in_progress` the percentage shown is present/**marked**, not present/enrolled — will a principal read "94%" at 9 AM correctly?
- `attention_needed` fires below a hardcoded **90%** — is that the right alarm line for schools where 85% is seasonal normal? Only observation sessions with real principals answer that.

### Q4. Are parent explanations educationally appropriate? — *Weakest area*

- The parent copilot is properly grounded and PII-minimized, but the copy is **English-only**, uses register like *"mastery is 62% on Fractions, below the learning target."*
- The ungrounded fallback **leaks engineering language verbatim to parents**: *"approved curriculum grounding was not verified for this response"* (`parent_copilot_service.py`).
- No reading-level control, no Telugu/Hindi (roadmap item #94), no tone review by anyone who talks to parents for a living.

### Q5. Are learning-gap recommendations pedagogically sound? — *Thoughtful heuristics; invented constants; one structural gap*

- The mastery model (`mastery/services/compute.py`, `flag_rules.py`) is deterministic and conservative by design — LLM only verbalizes, never computes; minimum 2 assessments before flagging; 21-day cool-off. Good bones.
- But **every number is invented**: exam-type weights 0.5→2.5, 90-day recency half-life, trend window 3, gap thresholds 15/25pp, absolute floor 40%, weak threshold 70% (duplicated as a literal in **three** modules). None traces to teacher judgment or learning-science evidence.
- **Structural gap:** the tutor recommends by **lowest mastery % ascending** (`tutor_service.py`) — no prerequisite ordering, even though the knowledge graph with concept edges exists precisely to answer "teach fractions *before* ratios." Remediating the weakest topic first is often pedagogically backwards.

### A.1.1 Pedagogical constants inventory (extract for ARR Track E)

| Constant | Value | Location | Encodes the assumption that… |
|---|---|---|---|
| `_OBJECTIVE_ANSWER_MAXLEN` | 40 chars | `answer_sheet_eval_service.py` | Any short answer can be graded by exact string match |
| `TYPE_WEIGHTS` | slip/quiz/assignment 0.5 · unit 1.0 · mid/quarterly 1.5 · half-yearly 2.0 · final 2.5 | `mastery/services/compute.py` | A final exam signal is worth 5× a slip test |
| `HALF_LIFE_DAYS` | 90 | `compute.py` | Learning evidence halves in relevance every 90 days |
| `TREND_WINDOW` / `TREND_MIN_DELTA` | 3 / 10pp | `compute.py` | 3 datapoints and a 10-point swing define a trend |
| `GAP_MEDIUM` / `GAP_HIGH` | 15pp / 25pp below class avg | `mastery/services/flag_rules.py` | Those gaps are the medium/high alarm lines |
| `ABSOLUTE_FLOOR` | 40% | `flag_rules.py` | Just above the SSC 35% pass line is the danger floor |
| `MIN_ASSESSMENTS` | 2 | `flag_rules.py` | Two datapoints are enough to alert a parent |
| `COOLOFF_DAYS` | 21 | `flag_rules.py` | Three weeks before the same topic may re-flag |
| `_WEAK_THRESHOLD` | 70% (×3 duplicated literals) | `tutor_service.py`, `parent_copilot_service.py`, `portal_service.py` | Below 70% mastery = "weak topic" |
| Attendance alarm | < 90% | `dashboard_service.py` | Below 90% present-of-marked needs principal attention |
| Tutor ordering | mastery % ascending | `tutor_service.py` | The weakest topic should be remediated first (ignores prerequisites) |
| Eval determinism | temperature 0.1, ≤8 criteria | `evaluation_engine.py` | 8 rubric criteria suffice for any subjective answer |

## A.2 Academic Readiness Review — proposed charter

A **separate, gated review before school #1 onboarding**, run *with* educators, not about them.

| Track | Validates | Method | Pass gate |
|---|---|---|---|
| **A. Marking fidelity** | Q1 | Build a golden set of ~200 real (anonymized) SSC answers across Maths/Science/English, marked independently by 3 teachers; measure AI-vs-teacher agreement and criteria plausibility | ≥90% within ±½ mark on objective/short; teacher-rated rubric plausibility ≥4/5 on subjective; zero over-max awards |
| **B. Workflow fit** | Q2 | Shadow a real school's paper-setting + curriculum-approval cycle; map actual actors to roles; time the onboarding flow with a real HOD | Approval chain matches school org (resolve HOD-vs-incharge); pack onboarding ≤ agreed time budget |
| **C. Dashboard interpretation** | Q3 | Think-aloud sessions: 3 principals read live dashboards cold; record misreadings | Zero critical misinterpretations (attendance state, intervention severity); thresholds re-set from their feedback |
| **D. Parent communication** | Q4 | Educator + parent panel reviews 20 generated briefings/answers for register, accuracy, anxiety-induction, language need | No harmful/confusing message; fallback copy rewritten; language decision made |
| **E. Pedagogical soundness** | Q5 | Teacher panel reviews the constants inventory (A.1.1) + flag/tutor outputs for 10 real students against their own judgment of those students | Teachers agree with ≥80% of flags; prerequisite-ordering decision taken; constants become per-school-configurable where teachers disagreed |

### Prerequisites the ARR needs that do not exist yet

1. **Marking-fidelity benchmark dataset** (Track A input) — ~200 anonymized, teacher-marked real answers. Long lead time; needs scheduled teacher hours.
2. **Pedagogical constants inventory** — delivered above (A.1.1); keep it current as constants change.

### Sequencing position

The engineering WAR ROOM's Criticals (C1–C4) still gate first — a school can't trust grading if its answer sheets vanish on redeploy. But **Tracks A and E should run in parallel** with the technical hardening pass, because building the benchmark dataset has the longest lead time and requires teacher hours that must be scheduled now.

---

# ADDENDUM B — Deployment-Context Revision (OCI single-VM, one-school pilot)

> **Added 2026-07-28, after owner correction.** The original audit weighted several findings against an Azure Container Apps deployment. The **actual Gate 1 target** (per `docs/DEPLOYMENT_ARCHITECTURE.md`) is a **single Oracle Cloud VM** running Docker Compose (Nginx + FastAPI + Postgres + Redis + Qdrant), web on Cloudflare, uploads on a **volume-mounted local disk** (`/opt/studynexs/data`) until Gate 2+, object storage explicitly deferred, and a **documented manual deploy runbook** (Gate 1A). Findings are revised accordingly. The original entries above are preserved unmodified for the record; **this addendum supersedes their severity/framing where stated.**

## B.1 Finding revisions under the OCI reality

| Finding | Original | Revised | Reasoning |
|---|---|---|---|
| **C1** file storage local-disk | Critical — "files vanish on redeploy" | **High, conditional** | On a VM with `/opt/studynexs/data` volume-mounted, files **persist** across container restarts — the "vanish" claim was ACA-specific. Residual risks: uploads are a **single-disk SPOF** that must join the backup routine (the deployment doc requires backups before pilot, but **no backup script exists in `infra/`**), and horizontal scaling stays blocked (accepted at Gate 1). Acceptable for 1 school **only if** the prod compose actually mounts the volume and backups cover it. |
| **H2** no deploy pipeline | High — build CI/CD | **Reframed** | For 1 VM + 1 school, the documented manual Gate 1A runbook is legitimate. The real gaps: **a production compose file does not exist in the repo** (only `docker-compose.dev.yml`), no backup script, no tested restore. "Script the runbook + backups + one restore drill" replaces "build a pipeline." |
| **H3** X-Real-IP trust | High | High, **easier fix** | Nginx fronts everything on the VM. The fix reduces to: prod compose binds the API to `127.0.0.1:8000` (dev compose exposes `8000:8000` publicly — prod must not), making the header trustworthy by topology. |
| Roadmap #31/#76 | AzureBlobStorage | **OCI Object Storage, Gate 2+** | Matches the repo's own storage phase table. Not a pilot blocker. |

**Unchanged regardless of cloud:** C2 (`cryptography` undeclared), C3 (WeasyPrint), C4 (CORS validator), H4 (notification tenancy), H5 (teacher pagination bug), all frontend findings.

## B.2 "Finished product" framing — findings that get WORSE

The school will treat this as a **finished product**, not a pilot. That elevates:

- **C3 PDFs** — the school *will* print receipts and report cards in week 1.
- **H7 outbox no-ops** — "fee paid → parent notified" doesn't exist; a finished product implies it does.
- **M2 "Greenwood Public School"** fallback — the real school's principal seeing another school's name flash is unacceptable.
- **M13 demo credentials + demo copy on the login page** — a real school's login screen needs a real-school mode.
- **Q4 parent copy** (English-only, engineering-jargon fallback) — real parents read it from day 1.

*(Owner direction: operational-channel items such as OTP/SMS delivery are explicitly **descoped from this review's priorities** — see Addendum C. They remain recorded but do not gate the academic-intelligence work.)*

---

# ADDENDUM C — Academic Intelligence Layer Assessment (the product-definition review)

> **Added 2026-07-28 at owner direction.** Product definition (canonical): *"An AI-first Academic Intelligence / School Operating System where curriculum, assessment, evaluation, learning gaps, teacher decisions, parent communication, and principal intelligence all flow from the **same educational understanding layer**."* Under this definition the decisive audit question is not "is the software solid" (Parts 1–2) but **"does one educational understanding layer actually exist in this codebase?"** This addendum answers that question and **supersedes the ops-centric prioritization** of the earlier roadmap for strategic sequencing. Engineering criticals C2/C3/C4 remain as cheap parallel hygiene.

## C.1 Core architectural finding: two understanding spines, joined by string matching

**Spine 1 — the CurriculumPack/Concept spine (grounded, correct).**
QP generation, rubrics, evaluation grounding, concept cards, and the knowledge graph all flow from **approved CurriculumPacks**. `CurriculumConcept` nodes are promoted on pack approval (`db/models/knowledge_graph.py`); questions link to concepts via `TESTS` edges resolved from real grounding citations (`question_concept_link_service.py`). This half genuinely matches the product definition.

**Spine 2 — the free-text topic spine (where mastery actually lives).**
Mastery — the input to learning gaps, flags, tutor recommendations, parent briefings, and principal interventions — is computed from `Exam.topic`, a **free-text `String(120)`** (`db/models/examination.py` L44), plus per-question topic labels in `question_schema` JSONB. "Normalization" is whitespace-collapse + casefold (`mastery/services/topic_norm.py`). A teacher typing "Linear Equations" vs the pack's "Linear Equations in One Variable" produces **two different topics that never connect.**

**The bridge is title string-matching.** `StudentWeakConceptService._topic_title_map` maps mastery topics → concept nodes **by comparing topic-title strings** (`student_weak_concept_service.py`). When the strings drift — inevitable with teacher free-text — the student's gap silently falls off the concept graph, and everything downstream (tutor lesson selection, parent focus areas, `STRUGGLES_WITH` edges, principal interventions) degrades to string-land.

## C.2 Supporting findings under the product definition

| # | Finding | Evidence | Why it contradicts "one understanding layer" |
|---|---|---|---|
| AI-1 | **No `PREREQUISITE` edge type** — graph is `CONTAINS / PART_OF / TESTS / STRUGGLES_WITH` only | `db/models/knowledge_graph.py` L35–39 | The graph is a *containment hierarchy*, not a knowledge graph. Understanding that can't express "fractions before ratios" isn't understanding — which is exactly why the tutor falls back to lowest-%-first ordering. |
| AI-2 | **EUI (6.4k LOC) *is* the stated core layer, and it is 100 % dark** | 7 default-off flags in `core/config.py`; `modules/eui/**` | Educational Identity, Context Engine, Capability Registry, KAI, EKG expansion, Trust Framework — the layer the one-sentence product describes exists as certified passive code. The live product runs on Spine 2. |
| AI-3 | **Answer understanding stops at 40 characters** | `_OBJECTIVE_ANSWER_MAXLEN = 40` exact-match, `answer_sheet_eval_service.py` | The understanding layer doesn't understand "photosynthesis" ≈ "photo synthesis". AEI Batch A maths normalization addresses this class — but is also flag-off. |
| AI-4 | **Mastery constants are invented, not learned or elicited** | Constants inventory, Addendum A.1.1 | The layer's "judgment" is a table of guessed numbers duplicated across three modules. |

## C.3 Revised strategic sequence (academic-intelligence-first)

Supersedes the ops-centric ordering for strategic work. Engineering criticals run in parallel as hygiene.

| # | Move | Why it IS the product |
|---|---|---|
| **1** | **Unify the spines: exam/question topic tagging references pack topics by ID, not free text.** Teacher picks from the approved pack's topics; free-text remains an escape hatch that creates a *pending-mapping* item instead of an orphan string. | This single change makes "everything flows from the same educational understanding" **true**. Mastery → gaps → tutor → parent → principal all land on concept/topic IDs instead of casefolded strings. Every downstream feature gets more accurate for free. Must ship **before** the school's teachers start creating exams — retro-mapping months of free-text topics later is far more painful. |
| **2** | **Add `PREREQUISITE` edges + prerequisite-aware tutor ordering.** Seed from pack chapter/topic order (a defensible proxy); refine with teacher input via ARR Track E. | Turns the containment tree into actual understanding; fixes pedagogically-backwards "weakest-first" remediation. |
| **3** | **Answer equivalence for objective grading.** Activate/extend the AEI maths-normalization path beyond its flag; add spelling/transliteration tolerance for short answers. | The understanding layer must understand *answers*, not just curriculum. Highest teacher-visible quality win. |
| **4** | **Pedagogical constants → per-school configuration + ARR Tracks A/E.** | The layer's judgment thresholds become school-tunable data (content-is-data directive) instead of invented constants. |
| **5** | **EUI decision (product-owner call):** begin feeding one EUI phase (identity or context resolution) into the live spine, **or** explicitly park it. | Either the named understanding layer starts operating, or the product story and the codebase stop diverging. |
| ∥ | Engineering hygiene in parallel: C2 `cryptography` dep · C3 WeasyPrint decision · C4 CORS validator · M2 Greenwood fallback · H5 pagination fix (≈2 days total). | Cheap; doesn't compete with the above. |

**First commit recommendation: #1 (spine unification).** Highest-leverage change in the repository under the product definition — everything else in the academic stack compounds on it.

## C.4 Design brief — Spine Unification (Move #1, for approval)

**Goal.** Every topic signal that feeds mastery resolves to a **pack topic ID** (and thereby to concept nodes) instead of a free-text string. Zero disruption to existing mark entry; free-text remains possible but becomes a tracked mapping task rather than a silent orphan.

**Data model (additive, reversible — expand-then-contract):**

1. `exams.topic_id` — new nullable `UUID FK → curriculum_topics.id`. Existing `exams.topic` (String) **stays** for display/back-compat.
2. `question_schema` items gain optional `"topic_id": "<uuid>"` alongside the existing `"topic"` string (JSONB — no migration needed for the key itself).
3. New table `topic_alias` (`school_id`, `raw_topic_normalized`, `topic_id`, `created_by`, `status: suggested|confirmed`) — the durable memory of "this free-text string means this pack topic." Written once, reused forever; retro-fixes historical exams without touching mark rows.

**Resolution order in mastery compute** (`topic_pcts_for_mark`): `question.topic_id` → `exam.topic_id` → `topic_alias` lookup on the normalized string → (fallback) today's normalized free-text behavior. Ledger rows gain an optional `topic_id`; downstream graph linking uses IDs when present and falls back to today's title match only for unmapped rows.

**Teacher UX (exam create/edit):**
- Topic field becomes a **picker of the approved pack's chapters/topics** for that class × subject (data already served by the pack detail endpoint).
- Free-text entry still allowed → creates a `topic_alias(status=suggested)`; the teaching curriculum screen shows a small "unmapped topics" queue where an incharge confirms mappings (one click each).
- Papers imported from approved AI question papers (`source_paper_id`) auto-carry `topic_id`s from their grounding citations — no teacher action.

**Downstream effects (no interface changes needed):**
- `StudentWeakConceptService` prefers ledger `topic_id` → exact concept resolution; string-matching remains only as legacy fallback.
- Tutor recommendations, parent focus areas, and principal interventions inherit ID-accurate gap data automatically.

**Explicitly out of scope for Move #1:** prerequisite edges (Move #2), answer equivalence (Move #3), any EUI activation (Move #5).

**Validation plan:** migration up+down tested; mastery recompute regression tests extended with ID-tagged + alias-mapped + unmapped cases; tenant-isolation test for `topic_alias`; e2e: create exam via picker → enter marks → verify weak-concept edge lands on the right concept node.

**Risk:** Low-to-medium. Additive schema; behavior identical for unmapped legacy data; the only UX change is the topic picker (strictly better than a blank text box).

---

*Audit record complete. No code was modified during this review. Implementation of any item requires explicit product-owner (ARM) approval.*

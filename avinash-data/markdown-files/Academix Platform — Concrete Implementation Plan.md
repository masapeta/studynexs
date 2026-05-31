# Academix Platform — Concrete Implementation Plan

> **Status**: Awaiting User Approval  
> **Date**: May 11, 2026  
> **Scope**: Greenfield build → Production-ready SaaS for Indian schools

---

## Executive Summary

After reviewing **all 28 markdown documents**, the **code graph**, the **security audit**, the **E2E test suite**, and **11 prior conversations**, this plan consolidates everything into a **single, unambiguous execution roadmap**.

### What Exists Today (school-management-system repo)

| Layer | Status |
|-------|--------|
| **Backend** | FastAPI modular monolith with 13 routers (`auth`, `users`, `academic`, `timetable`, `examinations`, `attendance`, `fees`, `files`, `ai`, `communications`, `notifications`, `school_ops`, `analytics`) |
| **Frontend** | `staff-web` (Next.js) — implemented with hybrid auth (HttpOnly refresh cookie + in-memory access token) |
| **Auth** | OTP + password login, JWT with Redis blacklist, RBAC via `require_roles()`, tenant isolation via `X-Tenant-Slug` |
| **Security** | Cookie-based refresh tokens, HMAC webhooks, outbox pattern, production guardrails, IP spoofing fix done |
| **Testing** | Playwright E2E (golden paths), pytest integration suites for webhooks/RBAC/fees |
| **Planned portals** | `parent-web`, `student-web`, `admin-web` — not yet scaffolded |

### Critical Gaps Identified

| # | Gap | Severity |
|---|-----|----------|
| 1 | No pagination on `/students`, `/teachers`, `/classes`, `/subjects` | High — will break at 500+ students |
| 2 | `get_current_user` does a full DB round-trip on every request — no caching | Medium — latency at scale |
| 3 | `exam_marks_bulk_upsert` flushes inside loop — N round-trips | Medium — slow bulk grading |
| 4 | No horizontal rate limiting on `/verify-otp` (only vertical per-OTP) | Medium — brute-force risk |
| 5 | Reconciliation script has cross-schema DB coupling | Low — operational debt |
| 6 | 5 pre-existing `test_students.py` failures (schema changed) | Low — test debt |
| 7 | No CI/CD pipeline deployed | High — manual deployments |
| 8 | No observability (logging/metrics/tracing) in production | High — blind in prod |
| 9 | Platform operator console (multi-tenant SaaS control plane) not started | Deferred — needed for school #2+ |
| 10 | AI service is scaffold only — no RAG, no tutor, no agents | Expected — Phase 4 |

---

## Architecture Decision: Modular Monolith (Confirmed)

> [!IMPORTANT]
> The codebase has already consolidated from microservices into a **modular monolith**. This is the correct decision for a small team. **Do NOT split back into microservices** until you are past 50 schools and have a team of 10+.

```
school-management-system/
├── apps/
│   ├── api/                          # FastAPI monolith (THE backend)
│   │   ├── alembic/                  # DB migrations (linear chain)
│   │   ├── app/
│   │   │   ├── core/                 # config, database, dependencies, security, tenant
│   │   │   ├── db/models/            # SQLAlchemy models (all domains)
│   │   │   ├── modules/              # Domain modules (13 today)
│   │   │   │   ├── auth/             # OTP, JWT, RBAC
│   │   │   │   ├── users/            # Profiles, onboarding
│   │   │   │   ├── academic/         # Classes, subjects, enrollments
│   │   │   │   ├── attendance/       # Daily marking, reports
│   │   │   │   ├── examinations/     # Exams, marks, report cards
│   │   │   │   ├── fees/             # Fee structures, payments, Razorpay
│   │   │   │   ├── timetable/        # Period scheduling
│   │   │   │   ├── communications/   # Notices, chat (future WebSocket)
│   │   │   │   ├── notifications/    # Push, SMS, email dispatch
│   │   │   │   ├── school_ops/       # Transport, library, events
│   │   │   │   ├── files/            # Upload, pre-signed URLs
│   │   │   │   ├── ai/              # Tutor, profiler, agents (Phase 4)
│   │   │   │   └── analytics/        # Dashboards, reports (Phase 5)
│   │   │   ├── shared/schemas/       # Common envelope, pagination
│   │   │   └── workers/              # Outbox relay, background tasks
│   │   ├── scripts/                  # Seed data, reconciliation, CI helpers
│   │   └── tests/                    # pytest integration suites
│   ├── staff-web/                    # Next.js — teacher/admin portal (DONE)
│   ├── parent-web/                   # Next.js — parent portal (Phase 3)
│   ├── student-web/                  # Next.js — student portal (Phase 3)
│   └── platform-web/                 # Next.js — SaaS operator console (Phase 6)
├── infra/
│   ├── docker/                       # docker-compose.dev.yml
│   ├── nginx/                        # nginx.conf (gateway)
│   └── azure/                        # Bicep IaC templates (Phase 2)
├── docs/
│   ├── CODE_GRAPH.md
│   ├── code-graph.json
│   ├── ADR/                          # Architecture Decision Records
│   └── RUNBOOK.md
└── .github/workflows/               # CI/CD (Phase 2)
```

---

## Phase 1: Harden & Stabilize (Weeks 1–3)

**Goal**: Fix all known gaps, pass all tests, achieve "deploy-ready" quality.

### 1.1 Fix Test Failures & Pagination

#### [MODIFY] `apps/api/app/modules/academic/endpoints/students.py`
- Fix 5 failing `test_students.py` tests — update request schemas to include `apaar_number`
- Add cursor-based pagination to `GET /students` (same pattern as `GET /users`)

#### [MODIFY] `apps/api/app/modules/users/endpoints/users.py`
- Verify existing pagination works; extend to `/teachers`, `/classes`, `/subjects`

#### [MODIFY] `apps/api/app/shared/schemas/common.py`
- Ensure `PaginatedResponse` schema is reusable across all list endpoints

### 1.2 Auth Performance — Redis User Cache

#### [MODIFY] `apps/api/app/core/dependencies.py`
- Add Redis cache for `get_current_user` with **60-second TTL**
- Invalidate on: role change, deactivation, school settings change
- Fallback to DB on cache miss — never block on Redis failure

```python
# Pseudocode for cached user lookup
async def get_current_user(token, db, redis):
    payload = decode_jwt(token)
    cache_key = f"user:{payload['sub']}"
    cached = await redis.get(cache_key)
    if cached:
        return UserFromCache(cached)
    user = await db.get(User, payload['sub'])
    await redis.setex(cache_key, 60, serialize(user))
    return user
```

### 1.3 Bulk Write Optimization

#### [MODIFY] `apps/api/app/modules/examinations/services/exam_service.py`
- Refactor `exam_marks_bulk_upsert` to collect all marks, then do **one `db.flush()`** after the loop
- Use `insert().on_conflict_do_update()` for set-based upsert where possible

### 1.4 Horizontal Rate Limiting

#### [MODIFY] `apps/api/app/modules/auth/endpoints/auth.py`
- Add Redis-backed IP+fingerprint throttle on `/verify-otp`: **10 attempts per IP per 15 minutes**
- Add same throttle on `/auth/login` (password path): **5 attempts per IP per 15 minutes**

#### [MODIFY] `infra/nginx/nginx.conf`
- Add `limit_req_zone` for `/api/v1/auth/` endpoints: **30 req/min per IP burst 10**

### 1.5 Verification Gate

```bash
# All must pass before moving to Phase 2
cd apps/api && pytest tests/ -v --tb=short          # All green
cd apps/staff-web && npx playwright test             # Golden paths pass
docker compose -f infra/docker/docker-compose.dev.yml up -d  # All services healthy
curl http://localhost/api/v1/health                   # 200 OK
```

---

## Phase 2: CI/CD & Cloud Deployment (Weeks 4–6)

**Goal**: Automated pipeline, Azure pilot environment, zero-downtime deploys.

### 2.1 GitHub Actions CI

#### [NEW] `.github/workflows/api-ci.yml`
- **Trigger**: Push to `main`, PR to `main`
- **Steps**: Lint (ruff), Type check (mypy), Unit tests (pytest), Migration smoke (alembic upgrade head on ephemeral Postgres)
- **Secrets**: Use GitHub Actions secrets for test DB credentials

#### [NEW] `.github/workflows/staff-web-ci.yml`
- **Trigger**: Push to `main`, PR to `main`
- **Steps**: Lint (eslint), Type check (tsc), Build (next build), E2E smoke (Playwright against API)

#### [NEW] `.github/workflows/deploy-pilot.yml`
- **Trigger**: Manual dispatch or merge to `pilot` branch
- **Steps**: Build Docker images → Push to Azure Container Registry → Deploy to Azure Container Apps
- **Rollback**: Tag-based, previous image always available

### 2.2 Azure Infrastructure (Bicep IaC)

#### [NEW] `infra/azure/main.bicep`
```
Resources to provision:
├── Azure Database for PostgreSQL Flex (Free tier, 32GB)
├── Azure Cache for Redis (Basic C0, 250MB)
├── Azure Container Apps Environment
│   └── api (0.5 vCPU, 1GB, min 1 max 3 replicas)
├── Azure Static Web Apps (staff-web)
├── Azure Blob Storage (5GB free)
├── Azure Key Vault (all secrets)
└── Azure Container Registry (Basic)
```

### 2.3 Production Config Hardening

#### [MODIFY] `apps/api/app/core/config.py`
- Ensure all validators crash on boot if misconfigured in production:
  - `DEBUG=True` → crash
  - `ALLOWED_ORIGINS` contains `*` or `localhost` → crash
  - Default JWT secret → crash
  - Missing `REDIS_URL` → crash (no silent fallback)

### 2.4 Observability Stack

#### [MODIFY] `apps/api/app/core/config.py` + `main.py`
- Add `structlog` JSON logging with `request_id`, `school_id`, `user_id` context
- Add `/health` and `/ready` endpoints (DB + Redis connectivity check)
- Add request duration middleware (log slow requests > 500ms)

#### [NEW] `infra/azure/monitoring.bicep`
- Azure Monitor workspace
- Log Analytics for structured log ingestion
- Alert rules: 5xx rate > 1%, P95 latency > 2s, container restart

### 2.5 Verification Gate

- [ ] `git push` triggers CI, all checks green
- [ ] `pilot` branch deploy provisions Azure resources via Bicep
- [ ] `https://pilot.academix.in/api/v1/health` returns 200
- [ ] `staff-web` loads at `https://pilot.academix.in`
- [ ] Secrets are in Key Vault, not in `.env` files

---

## Phase 3: Multi-Portal & Parent/Student Apps (Weeks 7–12)

**Goal**: Parent and student portals live, same API, role-scoped views.

### 3.1 Parent Portal

#### [NEW] `apps/parent-web/`
- Scaffold with `npx -y create-next-app@latest ./` (App Router, TypeScript, Tailwind)
- Mirror `staff-web` patterns: `lib/api.ts`, `AuthContext.tsx`, hybrid cookie auth
- **Pages**: Login, Dashboard (child overview), Attendance, Fees (pay via Razorpay), Report Card, Notices, Teacher Chat
- **RBAC**: API already enforces `parent` role scoping — portal just calls existing endpoints
- **Design**: Premium dark theme, mobile-first (parents use phones), Inter font

### 3.2 Student Portal

#### [NEW] `apps/student-web/`
- Same scaffold as parent-web
- **Pages**: Login (username/password), Dashboard, Timetable, Attendance (self-view), Marks, Notices, AI Tutor (Phase 4 placeholder)
- **RBAC**: Student can only see own data — enforced by API
- **Design**: Vibrant, gamified feel (leaderboard placeholder, XP display)

### 3.3 API Enhancements for Portals

#### [MODIFY] `apps/api/app/modules/fees/endpoints/fees.py`
- Add `POST /fees/initiate-payment` — creates Razorpay order, returns `order_id`
- Add `POST /fees/webhooks/razorpay` — verify signature, update status, generate receipt
- Parent-only: `GET /fees/my-children-dues` (already partially exists)

#### [MODIFY] `apps/api/app/modules/communications/endpoints/`
- Add `GET /notices/my-notices` — filtered by `target_roles` containing current user's role
- Add read-receipt tracking: `POST /notices/{id}/read`

### 3.4 Verification Gate

- [ ] Parent can login, see child's attendance, pay fee (Razorpay test mode), view report card
- [ ] Student can login, see timetable, view marks, read notices
- [ ] No cross-tenant data leakage (test with 2 schools seeded)
- [ ] Mobile responsive (test at 375px viewport)

---

## Phase 4: AI Layer — Tutor & Intelligence (Weeks 13–20)

**Goal**: Working AI tutor, student profiling, semantic caching.

### 4.1 RAG Pipeline

#### [MODIFY] `apps/api/app/modules/ai/`
- **Vector Store**: Qdrant (Docker for dev, Qdrant Cloud for prod)
- **Embeddings**: `text-embedding-004` (Google AI)
- **Ingestion**: Admin uploads syllabus PDF → extract text (PyMuPDF) → chunk (512 tokens, 50 overlap) → embed → store in Qdrant collection `school_{school_id}_knowledge`
- **Retrieval**: Top-5 chunks by cosine similarity > 0.75

#### [NEW] `apps/api/app/modules/ai/services/rag_service.py`
```python
class RAGService:
    async def ingest_document(self, school_id, file_path, subject_id)
    async def query(self, school_id, question, subject_id=None) -> list[Chunk]
    async def delete_collection(self, school_id)
```

### 4.2 AI Tutor Agent

#### [NEW] `apps/api/app/modules/ai/services/tutor_agent.py`
- **Framework**: LangGraph (state machine with tool use)
- **LLM Tier**: Gemini 1.5 Flash (default) → Gemini 1.5 Pro (complex) → Ollama gemma (offline)
- **Flow**: Question → classify (academic/non-academic) → RAG retrieve → generate answer → cache → respond
- **Guardrails**: Content safety filter, max 2000 token response, no PII in prompts
- **Streaming**: SSE endpoint `GET /ai/tutor/stream?question=...`

### 4.3 Semantic Cache

#### [NEW] `apps/api/app/modules/ai/services/cache_service.py`
- **Layer 1**: Redis exact-match cache (question hash → response, 24h TTL)
- **Layer 2**: Qdrant semantic cache (embed question → find similar > 0.92 similarity)
- **Scope**: Per-school (school_id in Qdrant filter)
- **Target**: 60%+ cache hit rate at 500 students/school

### 4.4 Student Profiler (Background)

#### [NEW] `apps/api/app/modules/ai/services/profiler_service.py`
- **Trigger**: Weekly Celery Beat task (Sunday midnight)
- **Input**: Grades, attendance, AI tutor interactions
- **Output**: JSON profile stored in `ai_student_profiles` table (PostgreSQL JSONB — no MongoDB needed for MVP)
- **Alerts**: If attendance < 75% or grade drop > 15% → push notification to parent + teacher

### 4.5 Verification Gate

- [ ] Upload a CBSE Math chapter PDF → ask "What is Pythagoras theorem?" → get RAG-grounded answer
- [ ] Same question from 2nd student → served from semantic cache (0 LLM cost)
- [ ] Student profile generated for seeded data → alert triggered for low-attendance student
- [ ] Gemini API failure → automatic fallback to Flash → to Ollama

---

## Phase 5: Operations & Analytics (Weeks 21–28)

**Goal**: Fee collection with Razorpay, transport, library, analytics dashboards.

### 5.1 Fee Management (Razorpay Integration)

- Fee structure CRUD (admin)
- Individual student fee record generation (batch job per academic year)
- Razorpay order creation → checkout → webhook verification → receipt PDF
- Overdue alerts via SMS (MSG91) + push (FCM)
- Dashboard: collection rate, defaulters list, class-wise summary

### 5.2 Transport Management

- Route CRUD with stops (JSONB)
- Student-route mapping
- Basic GPS tracking placeholder (Phase 6 — needs mobile app)

### 5.3 Library Management

- Book inventory CRUD
- Issue/return tracking
- Overdue fine calculation
- AI book recommendations (Phase 4 agent can suggest based on student profile)

### 5.4 Analytics Dashboards

- School-wide KPIs: attendance %, fee collection %, top/bottom performers
- Class-level comparisons
- Teacher workload analysis
- Student risk scores (from profiler)
- Export to PDF/Excel

### 5.5 Verification Gate

- [ ] Admin creates fee structure → generates 500 student records → parent pays → receipt generated
- [ ] Razorpay webhook handles duplicate payments (idempotency)
- [ ] Analytics dashboard loads in < 2 seconds for 500-student school
- [ ] Library issue/return flow works end-to-end

---

## Phase 6: Multi-Tenant SaaS & Platform Console (Weeks 29–36)

**Goal**: Onboard school #2 without code changes. Platform operator console.

### 6.1 Platform Identity Model

| Actor | Auth | Scope |
|-------|------|-------|
| School User | School JWT (cookie) | One tenant |
| Platform Operator | Platform JWT (separate cookie namespace) | Cross-tenant |

### 6.2 School Onboarding APIs

```
POST   /platform/schools              — Create school (draft)
PUT    /platform/schools/{id}/activate — Activate (draft → active)
POST   /platform/schools/{id}/seed-admin — Create first admin user
GET    /platform/schools               — List/search/filter
PUT    /platform/schools/{id}/suspend   — Suspend tenant
```

### 6.3 Platform Console

#### [NEW] `apps/platform-web/`
- Separate Next.js app with platform JWT auth
- Pages: School list, onboarding wizard, subscription management, audit logs, support tickets
- **Never** share cookies/tokens with school portals

### 6.4 Module Flags

- Per-school `enabled_modules` JSONB in `schools` table
- API dependency: `require_module("fees")` — returns 403 if module disabled for school
- Enforced at API layer, not just UI

### 6.5 Verification Gate

- [ ] Platform operator creates School B → seeds admin → admin logs in → sees empty dashboard
- [ ] School A data is completely invisible to School B (verified by direct DB query)
- [ ] Disabling "fees" module for School B → `/fees/*` returns 403 for School B users
- [ ] Platform JWT rejected on school routes; school JWT rejected on platform routes

---

## Phase 7: Mobile App & Advanced AI (Weeks 37–52)

**Goal**: Flutter mobile apps, voice tutor, WhatsApp integration.

### 7.1 Flutter Mobile (Student + Parent)

- Shared codebase, role-based navigation
- Secure storage for refresh tokens (not cookies — native `flutter_secure_storage`)
- Offline-first: cache timetable, notices, recent grades locally
- Push notifications via FCM

### 7.2 Voice Tutor (Phase 2 of AI)

- STT: OpenAI Whisper (local) or Azure Speech
- TTS: edge-tts (free, no API key)
- Flow: Student speaks → Whisper transcribes → Tutor agent responds → edge-tts speaks

### 7.3 WhatsApp Notifications

- MSG91 WhatsApp Business API
- Parent fee reminders, attendance alerts, weekly AI digest
- Template-based messages (WhatsApp policy compliance)

---

## Security Architecture (Cross-Cutting)

> [!CAUTION]
> Every item below is **non-negotiable** for production. Skip none.

### Authentication

| Control | Implementation |
|---------|---------------|
| Access Token | JWT, 15-min expiry, in-memory only (never localStorage) |
| Refresh Token | HttpOnly, Secure, SameSite=Lax cookie, path-scoped to `/api/v1/auth/refresh`, 30-day expiry |
| Token Blacklist | Redis SET with TTL = remaining token life |
| OTP | Redis with 5-min TTL, max 3 attempts, 5-min cooldown between sends |
| Password | bcrypt with cost 12, fail-secure on malformed hashes |
| Rate Limiting | Nginx `limit_req_zone` + Redis-backed per-IP throttle on auth endpoints |

### Authorization (RBAC)

| Resource | student | parent | teacher | class_incharge | admin | super_admin |
|----------|---------|--------|---------|----------------|-------|-------------|
| Own profile | R | R/W | R/W | R | R/W | R/W |
| Child data | — | R (linked) | — | — | R/W | R/W |
| Class data | R (own) | R (child's) | R/W (assigned) | R/W | R/W | R/W |
| School-wide | — | — | — | — | R/W | R/W |
| Platform | — | — | — | — | — | R/W |

### Tenant Isolation

- `school_id` on **every table row** — extracted from JWT, never from request body
- All queries filter by `school_id` from JWT claims
- Qdrant collections scoped by `school_id`
- Redis keys prefixed with `school:{school_id}:`

### Data Protection (DPDP Act)

- Encryption at rest (Azure managed keys)
- Encryption in transit (TLS 1.3 enforced)
- PII minimization: collect only what's needed
- Parental consent flow for AI tutoring (opt-in)
- Audit log: append-only for admin/AI actions
- Data retention: configurable per school
- Right to deletion: hard-delete endpoint with audit trail

---

## Infrastructure Scaling Strategy

```
Phase 1-2 (1 school):    Docker Compose on laptop → Azure Free Tier
Phase 3-5 (1-5 schools): Azure Container Apps (0.5 vCPU, auto-scale 1-3)
Phase 6   (5-10 schools): Azure Container Apps (1 vCPU, auto-scale 1-5)
Phase 7   (10+ schools):  AKS cluster, read replicas, Qdrant Cloud
```

| Component | Pilot (Free) | Production (10 schools) |
|-----------|-------------|------------------------|
| PostgreSQL | Azure Flex Free (32GB) | Azure Flex Burstable B2ms |
| Redis | Azure Basic C0 (250MB) | Azure Standard C1 (1GB) |
| Compute | Container Apps (0.5 vCPU) | Container Apps (1 vCPU, 3 replicas) |
| Storage | Azure Blob (5GB free) | Azure Blob (unlimited) |
| Secrets | Azure Key Vault | Azure Key Vault |
| CDN | Azure Static Web Apps | Azure CDN |
| Vector DB | Qdrant Docker | Qdrant Cloud |
| LLM | Gemini Flash (1500 free/day) | Gemini Flash + Pro (paid) |
| Monitoring | structlog → console | Azure Monitor + Log Analytics |

---

## Open Questions

> [!IMPORTANT]
> **Q1**: The existing codebase is in `school-management-system` repo. Should we continue building there, or create a fresh `academix-platform` repo (greenfield) and selectively copy proven modules? The greenfield guide in your docs recommends option B.

> [!IMPORTANT]  
> **Q2**: The current backend is a modular monolith (consolidated from earlier microservices). Do you want to **stay with this** (recommended for your team size) or split back into microservices?

> [!WARNING]
> **Q3**: Your pilot target is September 2026 (per FIVE_YEAR_PLAN). That's ~4 months away. Phases 1-3 (harden + deploy + parent/student portals) are the **minimum viable product**. Should we prioritize these 3 phases and defer AI (Phase 4) to post-pilot?

> [!NOTE]
> **Q4**: The business plan mentions MongoDB for AI sessions. The current codebase uses PostgreSQL JSONB for everything. Do you want to introduce MongoDB now, or keep PostgreSQL-only until AI session volume justifies it? (Recommendation: stay PostgreSQL-only for MVP.)

---

## Verification Plan

### Automated Tests (CI — every PR)
```bash
# Backend
cd apps/api && pytest tests/ -v --tb=short
cd apps/api && alembic upgrade head && alembic downgrade -1  # Migration reversibility

# Frontend  
cd apps/staff-web && npx playwright test
cd apps/parent-web && npx playwright test
```

### Security Verification (Monthly)
- [ ] OWASP ZAP scan against pilot environment
- [ ] Manual IDOR test: login as parent → try accessing another parent's child data
- [ ] Verify JWT blacklist works: logout → reuse token → expect 401
- [ ] Verify tenant isolation: School A token → School B endpoint → expect 403
- [ ] Check no secrets in logs (grep for passwords, API keys)

### Load Testing (Pre-launch)
- [ ] Locust: 500 concurrent users, 60-second ramp, target < 200ms P95
- [ ] Verify semantic cache hit rate > 50% under load
- [ ] Verify Redis handles 10K commands/second (OTP + cache + blacklist)

### Manual Verification (Pre-pilot)
- [ ] Complete school onboarding: create school → seed admin → create classes → enroll students → mark attendance → enter grades → generate report card
- [ ] Parent pays fee via Razorpay test mode → receipt generated
- [ ] AI tutor answers curriculum question with RAG context
- [ ] Push notification reaches parent's device (FCM test)

---

*Approve this plan to begin execution. I will create a `task.md` checklist and start with Phase 1.*

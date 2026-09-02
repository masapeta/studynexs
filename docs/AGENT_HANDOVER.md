# StudyNexs — Agent Handover Log

> **Purpose.** A permanent, append-only engineering journal so that **another senior AI coding
> agent can continue implementation immediately using only the repository — with no access to
> previous conversations.** If knowledge lives only in a chat, it is lost. It belongs here.
>
> Owner: Avinash Reddy Masapeta (ARM). Governing charter: [`/CLAUDE.md`](../CLAUDE.md). Product
> truth: [`docs/PRODUCT.md`](./PRODUCT.md), [`docs/STATUS.md`](./STATUS.md). Decisions:
> [`docs/DECISION_LOG.md`](./DECISION_LOG.md).

## How to maintain this log

1. **Append, never overwrite.** Add a new `# Engineering Session NN` entry for every significant
   session. Keep prior validated sessions intact — this is the running history.
2. **The latest session is the source of truth for current state.** It must be complete enough
   that a fresh agent can continue with zero conversation history.
3. **Each session carries the full section set** (Engineering Context → Repository Memory). If a
   section is unchanged from the prior session, restate the current truth anyway — don't force the
   reader to diff sessions.
4. **Never commit unless ARM asks** (Prime Directive 9). **Never write secrets here** — reference
   variables by name only.
5. On finishing a session, run the **Closing checklist** (end of this file).

---

## Current status (machine-readable)

```json
{
  "project": "StudyNexs",
  "phase": "Demo Ready (Gate 1) — business milestone pivot",
  "latest_session": 10,
  "engineering_batch": "Batches 27–28 complete; Engineering OS docs committed",
  "business_milestone": "Gate 1A — Demo Online (in progress)",
  "branch": "develop",
  "active_repo": "D:/Projects/studynexs-platform/studynexs-dev",
  "base_commit": "45ed42a (HEAD; pushed 2026-07-15)",
  "working_tree": "clean after push; Gate 1 work in progress (uncommitted)",
  "build": { "api_import": "passing", "web_next_build": "passing (2026-07-15)", "docker_api": "not re-run this session" },
  "tests": {
    "backend_functions": 340,
    "state": "green — full tests/ suite 340 passed, 2 skipped, 0 errors (2026-07-15 isolated run)",
    "evidence": "pytest tests/ -q --tb=no ~1077s; prior failures classified as test DB contention"
  },
  "lint": { "backend_ruff": "not run this session", "frontend_eslint": "pre-existing TutorLessonPlayer warnings" },
  "ai": {
    "default_llm_provider_config": "gemini",
    "teacher_copilot": "✅ Batch 15",
    "student_copilot": "✅ Batches 25–26",
    "parent_copilot": "✅ Batches 27–28",
    "knowledge_graph": "✅ Batches 17–23",
    "rag_hybrid": "✅ Batch 24"
  },
  "infra": { "demo_url_https": "not deployed — Gate 1 step 2", "api_host": "azure-container-apps (planned)", "web_host": "cloudflare-opennext (wrangler ready)" },
  "next_priority": [
    "Gate 1A: HTTPS demo deployment (blocked on credentials)",
    "Gate 1B: Demo Reliable — AI key, reliability targets, CurriculumPack, demo polish",
    "Gate 1 EXIT: first principal demo — then stop polishing"
  ],
  "deferred": "Batch 29 Learning Analytics until first principal demo",
  "blockers": [],
  "pending_owner_decisions": ["Cloudflare/Azure demo env credentials", "own GEMINI_API_KEY for demo", "pilot meeting date"],
  "last_validated": "2026-07-15"
}
```

---

# Engineering Session 01 — 2026-07-10

- **Date:** 2026-07-10
- **Engineering batches:** 1–11 (foundational hardening → Aadhaar encryption → Shared AI Platform foundation)
- **Branch:** `claude/studynexs-engineering-kickoff-a6761c` (base `phase-0-foundation`)
- **Base commit:** `0828998` — all session work is **uncommitted** on the worktree
- **Model of work:** autonomous engineering batches, validated per batch (`CLAUDE.md` §6–§7)

## 1. Session summary

Started from a full read-only Engineering Assessment (1 Sev-1, 9 High, top-100). ARM approved
autonomous implementation. Delivered, in priority order:

| Batch | Focus | Outcome |
|---|---|---|
| 1 | Correctness & safety | Sev-1 fee self-clearing closed; PII log masking; mastery scope-authz; logout refresh revocation; Redis-blacklist SPOF guard; 2 broken tests fixed |
| 2 | Production blockers | `/metrics` annotation bug fixed; Arq worker handler registration (`on_startup`) + `arq.Retry`; payroll GET made read-only + explicit idempotent `generate_payroll` |
| 3 | CI/CD | `.github/workflows/ci.yml` — pytest (main+security) / `next build` / docker image are hard gates |
| 4 | Money correctness | idempotency-key fingerprint; fee roster Decimal accumulation + fixed status logic; **fixed a latent prod 500** (`min(uuid)` in roster) |
| 5 | Security/authz | `GET /jobs/{id}` IDOR closed; role ceiling now applies to target's current role; `class_incharge` user-list PII masked |
| 6 | Commit-timing (last High) | `CommitOnSuccessRoute` commits the request session **before** the response is sent; applied to all 21 module routers; `get_db` stashes session + rolls back only |
| 7 | Backend lint | ruff cleanup; CI lint later set **report-only** per ARM (see Engineering Context) |
| 8 | Aadhaar encryption at rest | `app/core/encryption.py` `EncryptedString` (Fernet/MultiFernet, key rotation, legacy-plaintext passthrough); prod guardrail; reversible migration; **merged two forked alembic heads → single head** |
| 9 | Embeddings (shared) | `app/modules/ai/embeddings/` — provider-agnostic `EmbeddingProvider` ABC + OpenAI/Stub adapters + `EmbeddingService` |
| 10 | Vector store (shared) | `app/modules/ai/vectorstore/` — `VectorStore` ABC (`search` **requires** `school_id`), Qdrant + in-memory adapters |
| 11 | RAG (shared) | `app/modules/ai/rag/` — `RagService.index_pack` / `retrieve` (tenant+pack-scoped) / `build_context` with citations |

Batches 9–11 were validated against **live OpenAI + live Qdrant**, not just stubs.

## 2. Engineering Context (the *why*)

- **Evolve, don't greenfield** (`DECISION_LOG` D1). The invisible foundation (tenancy, auth/session,
  fee concurrency) already works and is expensive to re-earn; every batch is additive on top.
- **Commit-before-response (Batch 6) — why a custom route class.** On the pinned FastAPI, generator-
  dependency teardown runs *after* the response is sent, so committing in `get_db`'s teardown turned
  a commit-time failure into a silent 2xx with lost data. **Rejected alternatives:** (a) explicit
  `commit()` in every service — too broad, easy to miss one; (b) setting `route_class` on the app
  router or a central post-mount rehome — *proven not to work* on this FastAPI version (included
  routers nest under a private `_IncludedRouter`; the wrapper never applied). **Chosen:**
  `route_class=CommitOnSuccessRoute` on each module router (verified by `tests/test_commit_route.py`
  which fails if any new router forgets it). Trade-off: 21 one-line router edits, but it's explicit
  and test-guarded.
- **Shared AI Platform, not per-feature AI.** Embeddings, vector store, and RAG are **shared
  services** (`app/modules/ai/{embeddings,vectorstore,rag}`) that the four pillars consume — never a
  second gateway/embedder/store (`CLAUDE.md` §32/§33.1, §4.1). Providers are behind ABCs with a
  **provider→model separation** so the production model choice stays a config decision.
- **RAG grounding unit = the curriculum *topic*** (structured chapter→topic tree), not full
  textbook text — copyright-safe by design (`CLAUDE.md` §39.1). Retrieval is **tenant- and
  pack-scoped**; `VectorStore.search` *requires* `school_id` at the type level so cross-tenant
  retrieval is impossible to write by accident.
- **Aadhaar encryption (Batch 8).** Chose an app-level `EncryptedString` SQLAlchemy type
  (Fernet/MultiFernet) over pgcrypto: keeps keys in the app secret store, supports **rotation**
  (MultiFernet decrypts old, encrypts new), and a **legacy-plaintext passthrough** so the migration
  is backward-compatible (reads pre-existing plaintext, writes ciphertext). A production boot
  guardrail refuses to start without `AADHAAR_ENCRYPTION_KEYS`.
- **Lint is intentionally report-only right now.** ARM isolated a repo-wide `ruff format` (219-file
  normalization) out of the functional diff so review stays focused on behavior. Lint is therefore a
  **reported signal, not a merge gate**, until a dedicated formatting commit lands. This is a
  deliberate deferral, not an oversight.
- **Assumptions:** local dev toolchain (Docker/Postgres/Redis/Node/OpenAI key) is available;
  `apps/api/.env` (git-ignored) carries real keys copied from the main repo.
- **Deferred by design:** frontend `eslint`→0 (report-only), full `ruff`→0 (report-only), Azure Blob
  storage (local disk today), real SMS/OTP + notification delivery (stubbed), WeasyPrint PDF (HTML
  fallback), Knowledge Graph tables (planned spine-first).
- **Frozen by design:** the `/api/v1` contract (additive-only), branding, the tenancy/auth/session
  spine, money-as-Decimal, human-in-the-loop for authoritative AI.
- **Risks accepted:** (a) local full-suite test flakiness (harness, not product — see Repository
  Memory); (b) lint backlog while report-only; (c) `AI_DEFAULT_PROVIDER` config default is `gemini`
  while embeddings run on OpenAI — production LLM provider is an open benchmark decision.

## 3. Current Configuration

### AI
| Item | Value |
|---|---|
| Default LLM provider (config) | `gemini` (`AI_DEFAULT_PROVIDER`); OpenAI key present & used for embeddings; **final prod provider = open decision** |
| LLM gateway | `app/modules/ai/gateway` (provider-agnostic; OpenAI/Gemini/Anthropic/Ollama adapters, lazy-imported) |
| Embedding provider / model | `openai` / `text-embedding-3-small` (1536-dim) — `EMBEDDING_PROVIDER` / `EMBEDDING_MODEL` |
| Vector database | Qdrant (`VECTOR_STORE=qdrant`, `QDRANT_HOST/PORT/API_KEY`); `qdrant-client` in the `[rag]` extra |
| RAG strategy | topic-chunked CurriculumPack → embed → Qdrant; retrieve tenant+pack-scoped; `[n] (source: chapter › topic)` citations. **Not yet wired into QP generation.** |
| Prompt framework | in-service composed `LLMMessage`s via the gateway (no external framework) |

### Infrastructure
| Item | Value |
|---|---|
| Database | PostgreSQL 16 (async `asyncpg` + SQLAlchemy 2.0) |
| Cache / auth store | Redis 7 (OTP, JWT blacklist, refresh JTIs, rate limits, user cache) |
| Object storage | Azure Blob — **config only, not implemented** (local disk today) |
| Message queue | Arq (Redis-backed) |
| Auth | JWT access (15 min) + HttpOnly refresh cookie (30 d); Redis blacklist; per-device `sid` |
| Gateway / hosting | Nginx → Azure Container Apps (API); Cloudflare OpenNext (web) |

### Development
| Item | Value |
|---|---|
| Python | target 3.11 (ruff `py311`); local interpreter is 3.14 |
| Node | 20 (CI); Next.js 16 / React 19 / Tailwind v4 |
| Package managers | `pip` (editable `-e ".[dev,ai,observability,rag]"`), `npm` |
| Docker | `infra/docker/docker-compose.dev.yml` (Postgres/Redis/Qdrant/API/Nginx) |
| CI provider | GitHub Actions (`.github/workflows/ci.yml`) |

### Environment variables (names only — never store values here)
- **Required (prod):** `ENVIRONMENT`, `JWT_SECRET_KEY` (≥32, non-default), `POSTGRES_*`, `REDIS_URL` (non-localhost), `ALLOWED_ORIGINS` (no localhost/wildcard), `COOKIE_SECURE=true`, `AADHAAR_ENCRYPTION_KEYS`, and the key for whichever `AI_DEFAULT_PROVIDER` is chosen.
- **Required (this AI foundation):** `OPENAI_API_KEY` (embeddings; in `apps/api/.env`), `QDRANT_HOST/PORT` (+`QDRANT_API_KEY` if secured).
- **Optional:** `AI_FALLBACK_PROVIDER`, `AI_VISION_FALLBACK_PROVIDER`, `OLLAMA_*`, `METRICS_TOKEN`, `OTEL_*`, `TUTOR_TTS_*`, `AZURE_SPEECH_*`, `DEBUG`.
- **Future:** `AZURE_STORAGE_CONNECTION_STRING`, `MSG91_*`, `SENDGRID_API_KEY`, `RAZORPAY_*` + `WEBHOOK_SECRET`, FCM push credentials.

## 4. Repository Statistics (as of this session)

| Metric | Value |
|---|---|
| Backend domain modules | 20 (`app/modules/*`; `analytics` is empty scaffolding, unmounted) |
| Frontend applications | 1 (`apps/admin-web`; hosts admin + marketing + parent/student/teacher routes) |
| Shared packages | 0 (`packages/` is the documented target for mobile phase) |
| Database migrations (Alembic) | 32 (single linear head after Batch 8 merge) |
| API endpoints | ~152 route handlers, all under `/api/v1` |
| Backend tests | 283 test functions across 55 files (`tests/` + `tests_security/`) |
| Backend LOC | ~22.9k (`apps/api/app`) |
| Frontend LOC | ~19.7k TS/TSX (`apps/admin-web/src`) + ~8k CSS |
| Docs | `PRODUCT`, `STATUS`, `DECISION_LOG`, `BACKLOG`, `PRICING`, `PRODUCT_PLAN`, `PHASE_1_EXIT`, `PILOT_DISCOVERY`, `WAR_ROOM_REVIEW`, `IP_PROTECTION_GUIDE`, `TRACK_AB_EXECUTION`, this file, `docs/api`, `docs/runbooks`, `docs/pilot` |

## 5. Progress Against Product Vision (four pillars + platform)

```
Curriculum Intelligence        ■■■■□□□□□□  40%   pack model + versioning + RAG retrieval exist; ingestion/Knowledge Graph pending
Assessment Intelligence        ■■■□□□□□□□  30%   QP gen + answer-sheet eval + HITL exist; not pack-grounded; rubric-per-criterion + LLM subjective pending
Learning Intelligence          ■■□□□□□□□□  15%   mastery compute + template tutor; adaptive/analytics pending
School Operations Intelligence ■■■■■■□□□□  60%   students/staff/fees/attendance/exams/finance built; payroll hardened this session
Shared AI Platform             ■■■■■■□□□□  60%   gateway + metering + credits + embeddings + vector store + RAG foundation done
Knowledge Graph                ■□□□□□□□□□  10%   modeled in CLAUDE.md §39.3; no tables yet (spine-first when built)
Flutter mobile                 □□□□□□□□□□   0%   not started (backend is API-agnostic and mobile-ready in shape)
```
*(Bars are engineering-judgment estimates, not measured coverage.)*

## 6. Validation performed this session

- **Per-batch:** `python -c "import app.main"`, targeted `pytest`, `ruff check` on touched files.
- **Batch 8:** 7 encryption + 18 admission tests green; migration `upgrade`→`downgrade` validated on a scratch DB.
- **Batches 9–11:** 7 (embeddings) + 6 (vectorstore) + 3 (rag) tests, validated against **live OpenAI + live Qdrant**.
- **CI:** `.github/workflows/ci.yml` runs pytest (main + security), `next build`, and docker image build as hard gates on a **fresh** Postgres/Redis each job — which runs clean (the local flakiness does not reproduce there).
- **Frontend:** `next build` green; payroll page updated to the read-only + generate model.
- **Not fully validated:** a single local **full-suite** green run — blocked by the harness flakiness in Repository Memory. Every file passes in focused runs; CI is clean.

## 7. Pending Owner Decisions (decision inbox — blocks/steers engineering)

| Decision required | Why | Recommendation | Options / impact | Default if silent |
|---|---|---|---|---|
| Final **production LLM provider** | `AI_DEFAULT_PROVIDER` is a placeholder; cost/quality unbenchmarked | Benchmark Gemini vs OpenAI vs Claude on QP + eval golden sets, then lock | Gemini (cheap) / OpenAI (proven here) / Claude (quality) — affects cost-per-school | Keep provider-agnostic; embeddings on OpenAI |
| **Commit the worktree** | ~59 files of validated batch work are uncommitted (Prime Directive 9 — only ARM commits) | Commit as a few logical commits (foundation fixes / encryption / AI platform) | commit now vs keep accumulating | Hold — do not commit until asked |
| Hand over **textbook / question-paper folder** | Needed to build Document Intelligence ingestion + real pack content | Share when starting the ingestion batch | provide path when ready | Build ingestion against structured pack data only |
| **DPDP** consent / retention / residency | Required before real student PII goes live | Draft consent records + retention + privacy notice as a batch | build now vs before pilot go-live | Defer until pre-pilot, keep encryption in place |

## 8. Autonomous Work Remaining (no owner input needed; recommended order)

1. **AI Platform / Curriculum Intelligence** — wire `RagService` into question-paper generation so academic AI is **pack-grounded + cited** (the single highest-leverage next step). *(M)*
2. **Assessment Intelligence (§40)** — rubric-per-criterion scoring, LLM-assisted subjective eval (replace the token-overlap heuristic), audited marks overwrites, shared engines (rubric/marking/feedback/learning-gap). *(L)*
3. **Document Intelligence (§38.1)** — one OCR/parse/chunk/embed/index/version pipeline feeding RAG + graph. *(L)*
4. **Curriculum Intelligence** — `ConceptCard` first-class table (tutor grounding); curriculum-management UI. *(M)*
5. **Knowledge Graph (§39.3)** — spine tables first (`Curriculum→Subject→Chapter→Topic→Concept`), then `Question→Concept`, then `Student→weak Concept`. *(M)*
6. **Backend** — implement Azure Blob storage behind the file-service seam; real notification delivery (replace stubs). *(M)*
7. **Testing** — make the local full-suite deterministic (single event-loop scope) — see Repository Memory; run migrations in tests, not `create_all`. *(M)*
8. **Frontend** — mobile nav drawer (<768px), a11y fixes (contrast, focus trap, pinch-zoom), toast/confirm service replacing native `alert/confirm`. *(M)*
9. **DevOps** — CD (image → ACR → deploy + migration job); backups + restore; extend IaC beyond the WAF edge. *(L)*
10. **Documentation / lint** — drive ruff & eslint to zero, then flip CI lint to blocking; refresh STATUS/README. *(S–M, incremental)*
11. **Mobile** — Flutter foundation once the shared API/RBAC/design contracts are stable. *(L)*

*(S/M/L = rough effort. Build platform capabilities before isolated features — `CLAUDE.md` §14.2, §4.1.)*

## 9. Repository Memory (non-obvious knowledge — read before debugging)

- **Local full-suite flakiness is NOT a product bug.** After many back-to-back full runs the local
  stack degrades and pytest throws non-deterministic `asyncpg ConnectionDoesNotExistError: connection
  closed in the middle of operation` / `DeadlockDetectedError` / `duplicate key ...
  pg_type_typname_nsp_index` — **different tests each run**. Root cause: asyncpg connections lingering
  across pytest-asyncio's **per-test event loops** in the function-scoped engine fixture (`tests/
  conftest.py`). Every test passes in **focused/isolated** runs; **CI is clean** (fresh Postgres per
  job). Do **not** chase it as a code defect. Fixes tried that did **not** help: hard-DB-reset,
  `DROP SCHEMA CASCADE`-at-start (made it *worse* — ACCESS EXCLUSIVE lock races lingering conns; was
  reverted). The durable fix is a **single session-scoped event loop** (`asyncio_default_*_loop_scope
  = "session"` in `pyproject.toml`) + transactional per-test isolation — not yet applied.
- **`apps/api/.env` (git-ignored) holds the real `OPENAI_API_KEY`**, copied from the main repo, so
  `Settings` loads it. A fresh clone/worktree must recreate it or embeddings/RAG won't run.
- **FastAPI teardown timing:** on the pinned version, `yield`-dependency teardown runs *after* the
  response is sent — the entire reason `CommitOnSuccessRoute` exists. Setting `route_class` centrally
  does **not** propagate to included routers (they nest under a private `_IncludedRouter`); it must be
  set per module router. `tests/test_commit_route.py` enforces full coverage.
- **Alembic had two forked heads**; Batch 8 merged them into a single head. Always `alembic heads`
  before adding a migration.
- **Latent prod bug fixed:** the fee roster used `func.min(uuid)` which Postgres rejects → `GET
  /fees/roster` was 500-ing. Now selects each student's earliest-owing record via a bounded query.
- **Money-as-float regressions recur at serialization.** Storage is Decimal-clean; the trap is casting
  to `float` in stats/roster/payroll aggregation. Accumulate in `Decimal`, cast to a JSON number only
  at the response boundary (returning raw `Decimal` serializes as a JSON **string** and breaks
  clients — this exact regression was caught in payroll review).
- **`analytics` module is empty scaffolding** and unmounted — don't assume it works.
- **Payroll:** `GET /ops/payroll` must stay read-only; entry creation is the explicit idempotent
  `POST /ops/payroll/generate` (a prior version fabricated + persisted salary rows on read).
- **`VectorStore.search` requires `school_id`** by signature — the tenant-isolation rule is encoded in
  the type, not left to discipline. Keep it that way for every new store method.
- **Notifications were historically not school-scoped** (accepted defense-in-depth gap, `DECISION_LOG`
  §5). New code must scope everything by `school_id`.

## 10. Next batch (start here)

**Wire `RagService` into question-paper generation** — retrieve pack-scoped topic context, inject as
grounded + cited context into the QP prompt via the gateway, meter it, keep HITL approval. This turns
Assessment Intelligence from ungrounded generation into the constitution's grounded-and-cited standard
(`CLAUDE.md` §39, §40, §109), and it exercises the whole shared platform end-to-end
(`EmbeddingService` → `VectorStore` → `RagService`). Consume the shared services — **never a provider
SDK directly.** Request the textbook/QP folder from ARM when moving to full Document Intelligence
ingestion.

## Closing checklist (run before ending any session)

- [ ] `CHANGELOG.md`, `STATUS.md`, `ROADMAP.md`, `AGENT_HANDOVER.md` updated
- [ ] **`PLATFORM_STATUS.md`** + **`docs/engineering/{platform,modules,roadmap}.json`** + affected **`docs/modules/*.md`**
- [ ] Tests run; counts reflected in `engineering-status.json`

- [x] `AGENT_HANDOVER.md` updated with a new/append session reflecting current state.
- [x] `STATUS.md` reflects the current implementation state (refreshed 2026-07-10 — "Since 2026-06-15" section + corrected stats/CI/RAG/known-issues).
- [x] `DECISION_LOG.md` contains this session's architectural decisions (commit-before-response, shared AI platform, Aadhaar encryption).
- [x] `ROADMAP.md` created (`docs/ROADMAP.md`) with milestones + pillar progress.
- [x] No important implementation knowledge exists only in the conversation — captured in §2 and §9.
- [x] A fresh senior agent can continue from the repository alone (this file + `CLAUDE.md`).
- [x] Repository documentation is internally consistent (STATUS/ROADMAP/CHANGELOG/DECISION_LOG/AGENT_HANDOVER + the six `docs/*_INTELLIGENCE`/architecture companions cross-reference and agree as of 2026-07-10).

> **Continuity note for the next agent:** the shared AI platform foundation
> (`app/modules/ai/{embeddings,vectorstore,rag}`) is built and live-validated. Your first move is
> §10. Do not rebuild AI plumbing — extend the shared services. Do not chase the local test flakiness
> (§9). Commit only when ARM asks.

---

# Engineering Session 02 — 2026-07-10

- **Date:** 2026-07-10
- **Engineering batch:** 12 — Grounded Assessment Intelligence
- **Branch:** `claude/studynexs-engineering-kickoff-a6761c` (base `phase-0-foundation`)
- **Base commit:** `0828998` — all session work is **uncommitted** on the worktree
- **This session is the source of truth for current state.** Session 01 (Batches 1–11) remains
  above as history; where they differ, this entry wins.

## 0. Immediate Resume Checklist (do these first)

1. Read [`/CLAUDE.md`](../CLAUDE.md) (the constitution) and then this session (02).
2. `git branch --show-current` → expect `claude/studynexs-engineering-kickoff-a6761c`; `git status`
   → expect the uncommitted tree in §15 (do **not** commit unless ARM asks — Prime Directive 9).
3. Ensure `apps/api/.env` exists with a real `OPENAI_API_KEY` (git-ignored; embeddings/RAG need it).
   A fresh worktree must recreate it from the main repo.
4. Confirm local stack: `docker ps` shows `studynexs-postgres`, `studynexs-redis`, `studynexs-qdrant`.
5. Build/import: `cd apps/api && python -c "import app.main"`.
6. Focused tests (fast, no full-suite): `python -m pytest tests/test_assessment_grounding.py
   tests/test_rag.py tests/test_embeddings.py tests/test_vectorstore.py -q`.
7. `python -m alembic heads` → single head `v2c3d4e5f6a7`. `python -m alembic current` on a live DB.
8. Continue **Batch 13** = §10 below. Do not re-do §20.

## 1. Session summary

Converted the shared AI platform foundation into a **visible product capability**: question-paper
generation is now **grounded in a school's APPROVED CurriculumPack** and flows exactly as the
architecture intends — **Teacher → Assessment Intelligence → RAG → Embedding → Vector store →
provider** — never calling a provider SDK directly.

| Area | What shipped |
|---|---|
| Grounding seam | `app/modules/ai/services/assessment_grounding.py` — `ground_for_pack()` consumes **only** `RagService`; chapter/topic-aware retrieval (per-topic when topics named, else broad), deduped + numbered so citations line up with stored sources |
| Grounded generation | `question_paper_service.generate_paper(pack_id=…)` — validates the pack (approved + class/subject match), retrieves cited context, builds a curriculum-aware prompt, refuses if the pack has no curriculum (no ungrounded fallback), persists `pack_id` / `grounded` / `grounding_sources` |
| Per-question metadata | Bloom level, difficulty, learning outcome, concepts, and **citation indices** now generated and **preserved through the output guard** (previously silently dropped) |
| Provenance / trace | New `question_papers` columns `pack_id` (FK), `grounded` (bool), `grounding_sources` (JSONB); per-question `citations` map back to numbered sources |
| Robustness fix | `QdrantVectorStore.search`/`delete` now treat a **missing collection** as empty/no-op instead of raising 404 (bit us the first time a namespace is queried before indexing) |
| HITL preserved | Grounded papers are still created `DRAFT`; teacher edits/approves; **AI never auto-publishes** (§40, CLAUDE.md) |

## 2. Engineering Context (the *why*)

- **Grounding is a seam, not a rewrite.** `assessment_grounding.ground_for_pack` is a thin layer
  that talks only to `RagService`. Rejected: (a) calling the embedder/vector store directly from
  the QP service — would fork the platform and break provider-agnosticism; (b) a new "grounded QP"
  service duplicating generation — chose to **extend** `generate_paper` with an optional `pack_id`
  so the ungrounded path stays byte-for-byte backward-compatible and both share validation, credit
  metering, parsing, and persistence.
- **Retrieve-then-refuse, never silently ungrounded.** When a `pack_id` is supplied, grounding is
  *expected*: if the pack has no chapters/topics the call **raises** (a 400) rather than falling back
  to an ungrounded LLM paper. This is CLAUDE.md §109 ("no generation relies solely on the LLM when
  grounding is expected") encoded as control flow, verified by
  `test_generation_refuses_when_pack_has_no_curriculum`.
- **Ground on APPROVED packs only.** Drafts are mutable; grounding + stored citations on a moving
  target would go stale and break traceability. So the grounded path requires `PackStatus.APPROVED`
  (immutable) and rejects drafts with an actionable message. Trade-off: a teacher must approve the
  pack first — acceptable, and it protects the audit trail.
- **Validate before spend.** Pack validation (not-found / wrong class-subject / not-approved) runs
  **before** QP credits are reserved, so a bad request never charges the teacher. Retrieval embedding
  cost (small, separately metered) is incurred before the QP reservation by design — the pack is
  validated first, and an empty pack raises before the LLM runs.
- **Grounding unit stays the curriculum *topic*.** We reused the Session-01 RAG grounding unit
  (structured chapter→topic, copyright-safe) rather than ingesting full textbook text — full
  document ingestion is Document Intelligence (a later batch), and it will feed the *same*
  embed→index→retrieve pipeline.
- **Metadata rides in `sections` JSONB, not new columns.** Bloom/difficulty/LO/concepts/citations
  vary per question and per board; a JSONB shape keeps the schema stable and boards additive. The one
  required change was teaching the **output guard** to preserve+sanitize these fields (it strips
  anything it doesn't recognize — a good default that would otherwise have dropped the new metadata).
- **Assumptions:** OpenAI key present in `apps/api/.env`; Qdrant reachable locally; the pilot QP
  credit model (`qp_full` = 5 credits) is unchanged (grounded generation is still a "full" paper).
- **Deferred by design:** rubric-per-criterion evaluation + LLM subjective marking (next), Document
  Intelligence ingestion, ConceptCard as a first-class table, Knowledge Graph tables, Curriculum
  management UI, a frontend surface to *pick a pack* when generating (API accepts `pack_id` now).
- **Frozen by design:** the ungrounded free-text generation path (backward-compatible), the
  `/api/v1` contract (additive only), HITL for authoritative AI, provider-agnosticism.
- **Risks accepted:** (a) retrieval re-embeds a query each generation (cheap; packs are small);
  (b) grounded generation quality depends on pack richness — an empty/thin pack yields thin grounding
  (mitigated by the refuse-on-empty guard); (c) local full-suite flakiness persists (harness, §9).

## 3. Current Configuration

### AI
| Item | Value |
|---|---|
| Default LLM provider (config) | `gemini` (`AI_DEFAULT_PROVIDER`); OpenAI key present & used for embeddings; **final prod provider = open decision** |
| LLM gateway | `app/modules/ai/gateway` (provider-agnostic; OpenAI/Gemini/Anthropic/Ollama adapters, lazy-imported; fallback provider supported) |
| Embedding provider / model | `openai` / `text-embedding-3-small` (1536-dim) — `EMBEDDING_PROVIDER` / `EMBEDDING_MODEL` |
| Vector database | Qdrant (`VECTOR_STORE=qdrant`, `QDRANT_HOST/PORT/API_KEY`); `qdrant-client` in the `[rag]` extra |
| RAG strategy | topic-chunked CurriculumPack → embed → Qdrant; retrieve tenant+pack-scoped; `[n] (source: chapter › topic)` citations |
| Assessment grounding | `assessment_grounding.ground_for_pack` (chapter/topic-aware retrieval via `RagService`) → curriculum-aware prompt → grounded, cited QP |
| Prompt framework | in-service composed `LLMMessage`s via the gateway (no external framework) |

### Infrastructure
| Item | Value |
|---|---|
| Database | PostgreSQL 16 (async `asyncpg` + SQLAlchemy 2.0) |
| Cache / auth store | Redis 7 (OTP, JWT blacklist, refresh JTIs, rate limits, user cache) |
| Object storage | Azure Blob — **config only, not implemented** (local disk today) |
| Message queue | Arq (Redis-backed) |
| Auth | JWT access (15 min) + HttpOnly refresh cookie (30 d); Redis blacklist; per-device `sid` |
| Gateway / hosting | Nginx → Azure Container Apps (API); Cloudflare OpenNext (web) |

### Development
| Item | Value |
|---|---|
| Python | target 3.11 (ruff `py311`); local interpreter is 3.14 |
| Node | 20 (CI); Next.js 16 / React 19 / Tailwind v4 |
| Package managers | `pip` (editable `-e ".[dev,ai,observability,rag]"`), `npm` |
| Docker | `infra/docker/docker-compose.dev.yml` (Postgres/Redis/Qdrant/API/Nginx) |
| CI provider | GitHub Actions (`.github/workflows/ci.yml`) — pytest×2 / next build / docker are gates; lint report-only |

### Environment variables (names only — never store values here)
- **Required (prod):** `ENVIRONMENT`, `JWT_SECRET_KEY` (≥32, non-default), `POSTGRES_*`, `REDIS_URL`
  (non-localhost), `ALLOWED_ORIGINS` (no localhost/wildcard), `COOKIE_SECURE=true`,
  `AADHAAR_ENCRYPTION_KEYS`, and the key for whichever `AI_DEFAULT_PROVIDER` is chosen.
- **Required (AI/RAG):** `OPENAI_API_KEY` (embeddings; in `apps/api/.env`), `QDRANT_HOST/PORT`
  (+`QDRANT_API_KEY` if secured).
- **Optional:** `AI_FALLBACK_PROVIDER`, `AI_VISION_FALLBACK_PROVIDER`, `OLLAMA_*`, `METRICS_TOKEN`,
  `OTEL_*`, `TUTOR_TTS_*`, `AZURE_SPEECH_*`, `EMBEDDING_PROVIDER`, `EMBEDDING_MODEL`, `VECTOR_STORE`,
  `DEBUG`.
- **Future:** `AZURE_STORAGE_CONNECTION_STRING`, `MSG91_*`, `SENDGRID_API_KEY`, `RAZORPAY_*` +
  `WEBHOOK_SECRET`, FCM push credentials.

## 4. Repository Statistics (as of this session)

| Metric | Value |
|---|---|
| Backend domain modules | 20 (`app/modules/*`; `analytics` is empty scaffolding, unmounted) |
| Frontend applications | 1 (`apps/admin-web`; admin + marketing + parent/student/teacher routes) |
| Shared packages | 0 (`packages/` is the documented target for the mobile phase) |
| Database migrations (Alembic) | 33 (single linear head `v2c3d4e5f6a7`) |
| API endpoints | ~152 route handlers, all under `/api/v1` |
| Backend tests | 291 test functions across ~56 files (`tests/` + `tests_security/`) |
| Backend LOC | ~23k (`apps/api/app`) |
| Frontend LOC | ~19.7k TS/TSX (`apps/admin-web/src`) + ~8k CSS |
| Docs | `PRODUCT`, `PRODUCT_PLAN`, `MASTER_PLAN`, `STATUS`, `DECISION_LOG`, `ROADMAP`, `BACKLOG`, `CHANGELOG`, `AI_ARCHITECTURE`, `ASSESSMENT_INTELLIGENCE`, `CURRICULUM_INTELLIGENCE`, `KNOWLEDGE_GRAPH`, `MOBILE_ARCHITECTURE`, `DESIGN_SYSTEM`, `PRICING`, `IP_PROTECTION_GUIDE`, `PHASE_1_EXIT`, `PILOT_DISCOVERY`, `WAR_ROOM_REVIEW`, `TRACK_AB_EXECUTION`, this file |

## 5. Progress Against Product Vision (four pillars + platform)

```
Curriculum Intelligence        ■■■■□□□□□□  40%   pack model + versioning + RAG retrieval; ingestion / Knowledge Graph / management UI pending
Assessment Intelligence        ■■■■■□□□□□  45%   grounded+cited QP generation shipped; answer-sheet eval exists; rubric-per-criterion + subjective LLM eval pending
Learning Intelligence          ■■□□□□□□□□  15%   mastery compute + template tutor; adaptive/analytics pending
School Operations Intelligence ■■■■■■□□□□  60%   students/staff/fees/attendance/exams/finance built; payroll hardened (S01)
Shared AI Platform             ■■■■■■■□□□  70%   gateway + metering + credits + embeddings + vector store + RAG + grounding seam live
Knowledge Graph                ■□□□□□□□□□  10%   modeled in CLAUDE.md §39.3 + docs/KNOWLEDGE_GRAPH.md; no tables yet
Flutter mobile                 □□□□□□□□□□   0%   not started (backend is API-agnostic and mobile-ready in shape)
```
*(Bars are engineering-judgment estimates, not measured coverage.)*

## 6. Validation performed this session

- **Import:** `python -c "import app.main"` clean after all edits.
- **New tests:** `tests/test_assessment_grounding.py` (7) — grounded generation cites curriculum &
  maps Bloom/difficulty/LO; refuses on empty pack (no LLM call); requires approved pack; rejects
  wrong class/subject; ungrounded path unchanged; output-guard metadata preservation. Plus
  `tests/test_vectorstore.py::test_qdrant_search_missing_collection_is_empty_not_404` (live Qdrant).
- **Regression:** 53 AI-related tests re-run green (`test_ai_hardening`, `test_question_bank*`,
  `test_question_paper`, `test_ai_credits`, `test_assessment_grounding`); embeddings/RAG/vectorstore
  (16) green incl. **live OpenAI + live Qdrant**.
- **Migration:** `v2c3d4e5f6a7` validated **up → down → up** on a scratch DB (`studynexs_migtest`);
  columns + FK created, dropped on downgrade, re-created. Single-parent downgrade is unambiguous.
- **Lint:** all new/changed lines ruff-clean; remaining ruff items in touched files are pre-existing
  baseline (report-only, isolated per ARM's formatting directive).
- **Not validated:** a single local **full-suite** green run — blocked by the harness flakiness (§9).

## 7. Pending Owner Decisions (decision inbox — blocks/steers engineering)

| Decision required | Why | Recommendation | Options / impact | Default if silent |
|---|---|---|---|---|
| Final **production LLM provider** | `AI_DEFAULT_PROVIDER` is a placeholder; cost/quality unbenchmarked | Benchmark Gemini vs OpenAI vs Claude on the grounded-QP + eval golden sets, then lock | Gemini (cheap) / OpenAI (proven here) / Claude (quality) — cost-per-school | Keep provider-agnostic; embeddings on OpenAI |
| **Commit the worktree** | ~60+ files of validated batch work are uncommitted (only ARM commits) | Commit as a few logical commits (see §15 boundaries) | commit now vs keep accumulating | Hold — do not commit until asked |
| Hand over **textbook / question-paper folder** | Needed for Document Intelligence ingestion + richer pack content | Share when starting the ingestion batch | provide path when ready | Build against structured pack data only |
| **DPDP** consent / retention / residency | Required before real student PII goes live | Draft consent + retention + privacy-notice as a batch | build now vs before pilot go-live | Defer to pre-pilot; encryption already in place |

## 8. Autonomous Work Remaining (no owner input needed; ARM's recommended order)

1. **Assessment Intelligence — evaluation depth (§40).** Rubric-per-criterion scoring, LLM-assisted
   subjective evaluation (replace token-overlap heuristic), audited marks overrides — all **HITL, no
   auto-publish**. *(L)*
2. **AI Teacher Copilot enhancements.** Grounded, cited assistance for lesson planning / QP review /
   feedback, reusing `RagService`. *(M)*
3. **Document Intelligence (§38.1).** One OCR/parse/chunk/embed/index/version pipeline feeding RAG +
   graph; request the textbook/QP folder from ARM. *(L)*
4. **Knowledge Graph (§39.3).** Spine tables first (`Curriculum→Subject→Chapter→Topic→Concept`), then
   `Question→Concept`, then `Student→weak Concept`. *(M)*
5. **Learning Intelligence.** Adaptive practice + analytics on mastery + graph. *(L)*
6. **Curriculum Intelligence.** `ConceptCard` first-class table (tutor grounding) + curriculum-
   management UI (pack build/approve; and let teachers pick a pack when generating QPs). *(M)*
7. **Backend.** Azure Blob behind the file-service seam; real notification delivery. *(M)*
8. **Testing.** Make local full-suite deterministic (session-scoped event loop) — §9. *(M)*
9. **Frontend.** Mobile nav (<768px), a11y (contrast/focus/pinch-zoom), toast/confirm service; surface
   grounded-QP citations + Bloom/difficulty in the paper UI. *(M)*
10. **DevOps.** CD (image → ACR → deploy + migration job); backups + restore; extend IaC. *(L)*
11. **Mobile.** Flutter foundation once shared API/RBAC/design contracts are stable. *(L)*

*(S/M/L = rough effort. Build platform capabilities before isolated features — CLAUDE.md §14.2, §4.1.)*

## 9. Repository Memory (non-obvious knowledge — read before debugging)

- **Local full-suite flakiness is NOT a product bug.** Back-to-back full runs degrade the local
  stack → non-deterministic `asyncpg ConnectionDoesNotExistError` / `DeadlockDetectedError` /
  `duplicate key pg_type_typname_nsp_index` (different tests each run). Every test passes in focused
  runs; CI is clean (fresh Postgres per job). Do **not** chase it. Durable fix (not yet applied):
  session-scoped event loop (`asyncio_default_*_loop_scope = "session"`) + transactional per-test
  isolation. ARM directive: don't spend time on it absent new evidence of an app defect.
- **Qdrant `search`/`delete` on a missing collection now return empty/no-op** (not 404). This is the
  first-ever-query case, before a namespace is indexed. `ground_for_pack` relies on it (probe → index
  → retrieve). Keep this behavior if you add store methods.
- **The output guard drops unknown question fields.** `sanitize_paper_sections` only keeps an
  allowlist; any new per-question field (like the Bloom/difficulty/LO/citations added this session)
  must be added to `_apply_question_metadata` or it will be silently stripped on save.
- **Grounded QP requires an APPROVED pack** matching the class **and** subject; a Maths pack cannot
  ground a Science paper. Validation runs before credits are reserved.
- **`VectorStore.search` requires `school_id`** by signature — tenant isolation is in the type, not
  left to discipline. `RagService.retrieve` also hard-filters `pack_id`.
- **`apps/api/.env` (git-ignored) holds the real `OPENAI_API_KEY`** — a fresh clone/worktree must
  recreate it or embeddings/RAG won't run.
- **FastAPI teardown timing:** `yield`-dependency teardown runs *after* the response — the reason
  `CommitOnSuccessRoute` exists; it must be set per module router (`tests/test_commit_route.py`
  enforces coverage).
- **Alembic:** single head `v2c3d4e5f6a7`. Always `alembic heads` before adding a migration. The
  `ᬬ…` unicode-escape trap mangles migration filenames on Windows — use forward-slash paths.
- **Money-as-float regressions recur at serialization** — accumulate in `Decimal`, cast to a JSON
  number only at the response boundary. **`analytics` module is empty scaffolding** (unmounted).

## 10. Next batch (start here → Batch 13)

**Assessment Intelligence — evaluation depth.** Bring the same grounded rigor to *marking*:
rubric-per-criterion scoring, LLM-assisted subjective evaluation grounded via `RagService`
(answer key + curriculum), and audited teacher overrides — **HITL, teachers final, no auto-publish**
(§40, §109). Reuse the shared platform end-to-end (`EmbeddingService` → `VectorStore` → `RagService`
→ gateway); **never a provider SDK directly.** Then AI Teacher Copilot, then Document Intelligence
(request the textbook/QP folder from ARM at that point).

## 15. Uncommitted Changes (commit boundaries for when ARM approves)

All Session-01 + 02 work is uncommitted on the worktree (base `0828998`). Suggested logical commits:

- **`feat(ai): grounded Assessment Intelligence`** (this session) — NEW
  `app/modules/ai/services/assessment_grounding.py`, `tests/test_assessment_grounding.py`,
  `alembic/versions/v2c3d4e5f6a7_qp_curriculum_grounding.py`; MODIFIED
  `question_paper_service.py`, `db/models/question_paper.py`, `schemas/question_paper.py`,
  `gateway/output_guard.py`, `endpoints/ai.py`, `vectorstore/qdrant_store.py`,
  `tests/test_vectorstore.py`.
- **`feat(ai): shared AI platform foundation`** (S01 B9–11) — `app/modules/ai/{embeddings,vectorstore,rag}/`
  + `tests/test_embeddings.py|test_vectorstore.py|test_rag.py`.
- **`feat(security): Aadhaar encryption at rest`** (S01 B8) — `app/core/encryption.py`,
  `alembic/…t0a1b2c3d4e5_merge_heads.py`, `…u1b2c3d4e5f6_encrypt_aadhaar_widen.py`,
  `db/models/school_ops.py`, `tests/test_encryption.py`.
- **`fix: foundational hardening`** (S01 B1–6) — the 21 modified module endpoint files + `core/api_route.py`,
  `core/database.py`, `core/pii.py`, fees/mastery/auth/ops/jobs/users services + their tests.
- **`ci: pipeline`** (S01 B3) — `.github/` (untracked).
- **`docs: engineering docs suite`** — `docs/*.md` new files (this handover, ROADMAP, AI_ARCHITECTURE,
  ASSESSMENT_INTELLIGENCE, CURRICULUM_INTELLIGENCE, KNOWLEDGE_GRAPH, MOBILE_ARCHITECTURE, DESIGN_SYSTEM,
  CHANGELOG).
- **Keep separate:** any repo-wide `ruff format` normalization (ARM directive — never mix formatting
  with behavior). `apps/api/.env` is git-ignored and must never be committed.

*Counts: ~48 tracked-file modifications + ~19 untracked new paths. `git status --short` is authoritative.*

## 16. Repository Health

| Area | Status | Notes |
|---|---|---|
| Build (API import) | 🟢 | `import app.main` clean |
| Build (web `next build`) | 🟢 | green as of S01; unchanged this session |
| Backend tests | 🟡 | green in focused/CI runs; local **full-suite flaky** (harness — §9), not a product defect |
| Frontend tests | 🟡 | eslint report-only (~127 issues); no unit-test layer yet |
| Lint (backend ruff) | 🟡 | report-only; **new code clean**, pre-existing baseline remains (isolated per ARM) |
| Formatting | 🟡 | repo-wide `ruff format` deliberately deferred to its own commit |
| CI | 🟢 | pytest×2 / next build / docker are hard gates on fresh services |
| Security | 🟢 | Sev-1 + 9 High closed (S01); Aadhaar encrypted at rest; tenant isolation enforced in RAG |
| AI platform / RAG | 🟢 | embeddings + vector store + RAG live-validated (OpenAI + Qdrant) |
| Assessment Intelligence | 🟢 | grounded QP shipped + tested |
| Curriculum Intelligence | 🟡 | pack model + retrieval; ingestion / UI / graph pending |
| Mobile | 🔴→⚪ | 0% (planned, not blocking) |
| Docs consistency | 🟡 | `STATUS.md` was behind reality; reconciled this session where touched |

## 17. Current Architecture Snapshot

- **Backend** — FastAPI modular monolith (Python 3.11, async SQLAlchemy 2.0 + asyncpg), 20 modules,
  `CommitOnSuccessRoute`, `APIResponse` envelope, multi-tenant (`school_id` from `CurrentUser`),
  RBAC (`require_roles` + `StaffScope` + object-level asserts). **Implemented.**
- **Frontend** — Next.js 16 / React 19 / Tailwind v4 (`apps/admin-web`). **Implemented.**
- **Shared AI Platform** — gateway (provider-agnostic, fallback), metering + credits, telemetry,
  embeddings, vector store, RAG, assessment grounding. **Implemented / live.**
- **Assessment Intelligence** — grounded, cited QP generation + HITL workflow. **Implemented**;
  evaluation depth **partial**.
- **Curriculum Intelligence** — CurriculumPack (chapter→topic, draft→approve immutable, versioning,
  blueprint) + RAG retrieval. **Partial** (ingestion / UI / concept model planned).
- **Learning Intelligence** — mastery compute + template tutor. **Partial.**
- **School Operations Intelligence** — students/staff/fees/attendance/exams/finance/payroll.
  **Implemented.**
- **Knowledge Graph / Document Intelligence / Flutter** — **Planned** (modeled in CLAUDE.md + docs).
- **Auth / RBAC / Tenant isolation / DPDP encryption** — **Implemented.**

## 18. Work Already Completed — do NOT re-do

The next agent should **not** re-review, re-implement, or undo:
- Batches 1–7 foundational hardening (Sev-1 fee self-clear, PII masking, mastery authz, logout
  revoke, `/metrics`, Arq worker registration, payroll read-only+generate, idempotency, fee roster
  `min(uuid)` 500 fix, jobs IDOR, role ceiling, `CommitOnSuccessRoute` on all 21 routers, backend ruff).
- Batch 8 Aadhaar encryption at rest (+ merged forked alembic heads).
- Batches 9–11 shared AI platform (embeddings + vector store + RAG) — **validated live**.
- Batch 12 (this session) grounded Assessment Intelligence — QP generation grounded + cited.
- Do not re-introduce the repo-wide `ruff format` into a functional diff (ARM directive).
- Do not chase the local test-suite flakiness as a code bug (§9).

## Closing checklist (run before ending any session)

- [ ] `CHANGELOG.md`, `STATUS.md`, `ROADMAP.md`, `AGENT_HANDOVER.md` updated
- [ ] **`PLATFORM_STATUS.md`** + **`docs/engineering/{platform,modules,roadmap}.json`** + affected **`docs/modules/*.md`**
- [ ] Tests run; counts reflected in `engineering-status.json`

- [x] `AGENT_HANDOVER.md` appended with Session 02 reflecting current state (Session 01 preserved).
- [x] `STATUS.md` reflects current state (reconciled this session — see docs).
- [x] `DECISION_LOG.md` contains this session's decisions (grounded generation, approved-pack-only,
      output-guard metadata, Qdrant missing-collection).
- [x] `ROADMAP.md` reflects the remaining roadmap (Assessment eval → Copilot → Document Intelligence
      → Knowledge Graph → Learning Intelligence).
- [x] No important implementation knowledge exists only in the conversation — captured in §2, §9, §15.
- [x] A fresh senior agent can continue from the repository alone (this file + `CLAUDE.md`).
- [x] Repository documentation is internally consistent (handover ↔ STATUS ↔ DECISION_LOG ↔ ROADMAP).

> **Continuity note (Session 02):** Grounded Assessment Intelligence is shipped and validated. Your
> first move is §10 (Batch 13 — evaluation depth). Consume the shared platform; never a provider SDK
> directly. Do not rebuild AI plumbing, do not chase test flakiness (§9), do not re-do §18. Commit
> only when ARM asks.

---

# Engineering Session 03 — 2026-07-11

- **Date:** 2026-07-11
- **Engineering batch:** 13 — Assessment Intelligence evaluation depth **+ merge recovery**
- **Branch:** `develop`
- **Active repo:** `D:\Projects\studynexs-platform\studynexs-dev`
- **HEAD:** `34aec0c` (foundation restored from merge parent `5f76c00`; **uncommitted**)
- **This session is the source of truth for current state.** Sessions 01–02 remain as history.

## 0. Immediate Resume Checklist

1. Read [`/CLAUDE.md`](../CLAUDE.md) and this session (03).
2. `git branch --show-current` → `develop`; `git status` → ~88 staged/uncommitted files (restore + eval fix + docs).
3. `apps/api/.env` with `OPENAI_API_KEY` for embeddings/RAG tests (git-ignored).
4. `cd apps/api && python -c "import app.main"`.
5. Focused eval tests: `pytest tests/test_evaluation_engine.py tests/test_answer_sheet_eval.py -q`.
6. Continue **Batch 14** = §10 below (pack-grounded eval marking + eval UI).

## 1. Session summary

| Area | What shipped / fixed |
|---|---|
| **Merge recovery** | Commit `34aec0c` had deleted the shared AI foundation (embeddings, RAG, vector store, `assessment_grounding`, `CommitOnSuccessRoute`, encryption, CI, migrations, docs). Restored **87 files** from merge parent `5f76c00` onto `develop`. |
| **Eval half-merge fix** | `execute_evaluation` expected `(suggestions, subjective_results)` but `_grade_exam` returned a single dict → every evaluation failed. Completed wiring. |
| **Marking engine** | `evaluation_engine.py` — rubric-per-criterion batch subjective marking via gateway; criteria sum authoritative; defensive clamping. |
| **Eval service** | Objective → deterministic; subjective → engine; heuristic fallback on provider failure; `method` provenance; one credit per evaluation. |
| **Conflict fix** | `tutor.py` merge marker resolved — `CommitOnSuccessRoute` + `logger` both kept. |
| **Validation** | Full `tests/` suite **289 passed**, 1 skipped (2026-07-11). Ruff clean on touched files. |

## 2. Engineering Context (the *why*)

- **Restore, don't rebuild.** The foundation in `5f76c00` was live-validated; `34aec0c` was a bad merge
  finalize that reverted it. Restoring from the merge parent is the smallest safe fix.
- **Criteria are authoritative.** The suggested mark reconciles with the rubric breakdown (sum of awarded
  points, clamped) so teachers see explainable partial credit, not a single opaque number.
- **Graceful degradation.** Provider outage → heuristic per subjective question; objective grading and
  the sheet continue. Never fail the whole evaluation because one LLM call failed.
- **Reuse-first for HITL.** `approve()`, `teacher_overrides`, and `list_corrections_history` already
  provided audited overrides — Batch 13 only changed how suggestions are produced.
- **Deferred:** ~~`ground_for_evaluation` (pack-grounded marking at eval time); eval UI surfacing criteria.~~ ✅ Batch 14 (same session continuation).

## 3. Validation performed this session

- `import app.main` — clean after restore + eval fix.
- `pytest tests/test_evaluation_engine.py tests/test_answer_sheet_eval.py` — 19 passed.
- `pytest tests/` — **289 passed**, 1 skipped (~10 min).
- Foundation tests (embeddings, vectorstore, rag, grounding, commit_route, encryption) — green after restore.
- Ruff — clean on `answer_sheet_eval_service.py`, `tutor.py`, `evaluation_engine.py`.

## 4. Autonomous Work Remaining (recommended order)

1. **Pack-grounded evaluation marking** — `ground_for_evaluation` via `RagService` (best-effort; never block marking). *(M)*
2. **Eval UI** — surface rubric criteria, missing concepts, confidence in corrections flow. *(M)*
3. **AI Teacher Copilot** — grounded lesson/QP/feedback assistance. *(M)*
4. **Document Intelligence** — OCR/parse/chunk/embed pipeline. *(L)*
5. **Knowledge Graph schema** — spine tables. *(M)*

## 5. Next batch (start here → Batch 15)

**AI Teacher Copilot** — grounded, cited assistance for lesson planning / QP review / feedback,
reusing `RagService`. HITL unchanged.

### Batch 14 completed (Session 03 continuation)

- `ground_for_evaluation` in `assessment_grounding.py` — best-effort pack RAG at mark time; never blocks marking.
- Wired in `answer_sheet_eval_service._grade_subjective_items` when paper has `pack_id`.
- Eval UI (`admin-web` …/exams/[examId]/evaluate`) shows method, confidence, per-criterion rubric, missing concepts.
- Tests: +3 in `test_assessment_grounding.py`; focused eval+grounding suite **29 passed**.

## 6. Work Already Completed — do NOT re-do

- Batches 1–12 (see Sessions 01–02 and §18 in Session 02).
- Batch 13 rubric engine + eval wiring + merge recovery (this session).
- Do not re-revert or re-delete the shared AI foundation.

## Closing checklist (Session 03)

- [x] `AGENT_HANDOVER.md` appended with Session 03.
- [x] `STATUS.md`, `ROADMAP.md`, `CHANGELOG.md`, `ASSESSMENT_INTELLIGENCE.md`, `DECISION_LOG.md` updated.
- [x] Full test suite green (289 passed).
- [ ] Commit when ARM asks (88 files uncommitted on `develop`).

> **Continuity note (Session 03):** Batches 13–14 complete. Start §5 (Batch 15 — Teacher Copilot).
> Commit only when ARM asks.

---

# Engineering Session 04 — 2026-07-12

- **Date:** 2026-07-12
- **Engineering batch:** 15 — AI Teacher Copilot
- **Branch:** `develop`
- **Active repo:** `D:\Projects\studynexs-platform\studynexs-dev`
- **HEAD:** `1a7adbc` + Batch 15 working tree (**uncommitted**)
- **This session is the source of truth for current state.**

## 1. Session summary

| Area | What shipped |
|---|---|
| **Teacher Copilot service** | `teacher_copilot_service.py` — grounded lesson plans, QP review, feedback drafting |
| **API** | Copilot routes on `/api/v1/ai/copilot/*`; optional `pack_id` on lesson-plan generate |
| **Data model** | `lesson_plans.pack_id`, `grounded`, `grounding_sources` (migration `w3d4e5f6a7b8`) |
| **Credits** | `lesson_plan` (2), `feedback_draft` (1); reuses `quality_check` for QP review |
| **Admin UI** | Pack picker + grounded mode on lesson plans and AI papers; Copilot review panel |
| **Tests** | `test_teacher_copilot.py` (5 passed); focused suite 25 passed |

## 2. Validation

- `import app.main` — passing
- `pytest tests/test_teacher_copilot.py tests/test_evaluation_engine.py tests/test_assessment_grounding.py tests/test_engineering_status.py` — **25 passed**
- Test collection: **300** tests; full suite **299 passed**, 1 skipped (2026-07-12)

## 3. Next batch

**Batch 16 — Document Intelligence ingestion** — unified OCR/parse/chunk/embed/index pipeline.

## Closing checklist (Session 04)

- [x] Engineering dashboard + handover docs updated
- [x] Focused tests green
- [ ] Full `pytest tests/` at batch close (recommended before commit)
- [ ] `npm run build` on admin-web (recommended before commit)
- [ ] Commit when ARM asks

---

# Engineering Session 05 — 2026-07-12

- **Date:** 2026-07-12
- **Engineering batch:** 16 — Document Intelligence ingestion
- **Branch:** `develop`
- **Active repo:** `D:\Projects\studynexs-platform\studynexs-dev`
- **HEAD:** `8406f6e` + Batch 16 working tree (**uncommitted**)
- **This session is the source of truth for current state.**

## 1. Session summary

| Area | What shipped |
|---|---|
| **Shared OCR** | `document_ocr.py`; admissions OCR delegates (§38.1) |
| **Document Intelligence service** | `document_intelligence_service.py` — OCR → chunk → sanitize → embed → index |
| **RAG extension** | `RagService.index_document_chunks()` — `kind: document_chunk` in curriculum collection |
| **Data model** | `document_ingestions` audit table (migration `x4e5f6a7b8c9`) |
| **API** | `POST /api/v1/curriculum/packs/{pack_id}/ingest-document`, `GET .../ingest-status` |
| **Admin UI** | Teaching → Documents (`/dashboard/teaching/document-ingest`) |
| **Tests** | `test_document_intelligence.py` (6 passed) |

## 2. Validation

- `alembic upgrade head` — applied `x4e5f6a7b8c9`
- `pytest tests/` — **305 passed**, 1 skipped (2026-07-12)
- `npm run build` (admin-web) — passing

## 3. Next batch

**Batch 17 — Knowledge Graph schema (curriculum spine)**

## Closing checklist (Session 05)

- [x] Engineering dashboard + handover docs updated
- [x] Full `pytest tests/` green
- [x] `npm run build` on admin-web
- [ ] Commit when ARM asks

---

# Engineering Session 06 — 2026-07-12

- **Date:** 2026-07-12
- **Engineering batch:** 17 — Knowledge Graph schema (curriculum spine)
- **Branch:** `develop`
- **Active repo:** `D:\Projects\studynexs-platform\studynexs-dev`
- **HEAD:** `f184db3` + Batch 17 working tree (**uncommitted**)

## 1. Session summary

| Area | What shipped |
|---|---|
| **Graph tables** | `curriculum_concepts`, `kg_edges` (migration `y5f6a7b8c9d0`) |
| **KnowledgeGraphService** | `build_spine_from_pack`, `get_spine`, `backfill_approved_packs` |
| **Approve hook** | Pack approval materializes Pack→Chapter→Topic→Concept edges |
| **API** | `GET /api/v1/curriculum/packs/{pack_id}/graph` |
| **Tests** | `test_knowledge_graph.py` (6 passed) |

## 2. Validation

- `alembic upgrade head` — applied `y5f6a7b8c9d0`
- Focused KG + curriculum tests — **9 passed**
- Full `pytest tests/` — pending at batch close

## 3. Next batch

**Batch 18 — ConceptCard first-class table**

---

# Engineering Session 07 — 2026-07-12

- **Engineering batch:** 18 — ConceptCard first-class table
- **HEAD:** `e349e43` + Batch 18 working tree (**uncommitted**)

## Shipped

- `concept_cards` table + `ConceptCardService` (draft → approve)
- API: `/curriculum/concepts/{id}/cards`, `/concept-cards/{id}/approve`, pack list
- Tutor: approved cards served in `get_lesson` by concept slug
- Tests: `test_concept_card.py` (4 passed)

## Next batch

**Batch 19 — Question → Concept graph links**

---

# Engineering Session 08 — 2026-07-12

- **Engineering batch:** 19 — Question → Concept graph links
- **HEAD:** `aade136` + Batch 19 working tree (**uncommitted**)

## Shipped

- Extended KG enums: `QUESTION_BANK_ITEM` node type, `TESTS` edge type (migration `a8b9c0d1e2f3`)
- `QuestionConceptLinkService` — resolves citations + concept labels → spine concepts
- Bank ingest hook: grounded paper approval creates TESTS edges per question
- Spine rebuild remaps question links when concept ids rotate
- API: `GET /api/v1/ai/question-bank/items/{item_id}/concepts`
- Tests: `test_question_concept_links.py` (6 passed)
- Full suite: **321 passed**, 1 skipped

## Next batch

**Batch 20 — Content Review Queue**

---

# Engineering Session 09 — 2026-07-12

- **Engineering batch:** 20 — Content Review Queue
- **HEAD:** `e54818d` + Batch 20 working tree (**uncommitted**)

## Shipped

- `content_review_items` table + `ContentReviewService`
- API: `/curriculum/content-review/queue`, approve/reject, concept gap enqueue
- Tutor auto-enqueues gap when no approved ConceptCard for slug
- Document ingest → review queue on completion
- Tests: `test_content_review_queue.py` (5 passed)

## Next batch

**Batch 25 — Student Copilot MVP**

---

## Machine-readable snapshot (read this first)

> A quick, structured state for any agent (Claude Code, Cursor, …) before reading the full log above.
> Keep this block at the very end of the file and refresh it every session.

```yaml
project: StudyNexs
current_phase: "Gate 1A — Demo Online"
business_milestone: "Gate 1 (1A in progress, 1B pending)"
last_completed_batch: "Batch 28 — Parent Copilot UI"
last_commit: "45ed42a (pushed)"
deferred_batch: "29 — Learning Analytics (until first principal demo)"
working_tree: "Gate 1 housekeeping + execution docs (uncommitted)"
tests:
  full_suite: "340 passed, 2 skipped, 0 errors (2026-07-15 isolated)"
  evidence: "pytest tests/ -q --tb=no ~1077s"
gate_1_next:
  - "1A: HTTPS demo deployment (credentials)"
  - "1B: Demo Reliable targets + polish"
  - "EXIT: principal demo then stop"
docs:
  gate1_execution: docs/pilot/GATE1_EXECUTION.md
  validation_standard: docs/engineering/004-validation-and-testing.md
blockers:
  - "Demo HTTPS deploy needs cloud credentials"
  - "ARM-owned Gemini key for reliable live AI"
owner_decisions_pending:
  - "Pilot meeting timing"
  - "When to commit Gate 1 work"
last_validated: "2026-07-15"
```

---

# Engineering Session 05 — 2026-07-12

- **Date:** 2026-07-12
- **Engineering batches:** 21–24
- **Branch:** `develop`
- **Commit policy:** **Uncommitted** — await ARM approval

## 1. Session summary

| Batch | Focus | Outcome |
|-------|-------|---------|
| 21 | Curriculum management UI | `/dashboard/teaching/curriculum` — pack approve, spine, concept cards, review queue |
| 22 | Student → weak Concept links | `STRUGGLES_WITH` edges synced from mastery recompute |
| 23 | Graph queries for copilots | Concept context + student weak-concepts APIs |
| 24 | RAG hybrid + re-rank | `HybridRetrievalService`; `ground_for_pack` wired; search API |

## 2. Validation

- **API tests:** 333 passed, 2 skipped (full `apps/api/tests/` suite)
- **Admin web:** `npm run build` passing (Batch 21 UI)
- **Migrations:** through `c0d1e2f3a4b5` (Batch 22)

## 3. Key paths

```
apps/admin-web/src/app/dashboard/teaching/curriculum/page.tsx
apps/api/app/modules/knowledge_graph/services/student_weak_concept_service.py
apps/api/app/modules/knowledge_graph/services/graph_query_service.py
apps/api/app/modules/ai/rag/hybrid.py
apps/api/app/modules/curriculum/endpoints/rag.py
apps/api/tests/test_rag_hybrid.py
```

## 4. Next batch

**Batch 25 — Student Copilot MVP** — grounded study assistance using weak-concept graph,
ConceptCards, and hybrid RAG.

---

# Engineering Session 10 — 2026-07-15

- **Date:** 2026-07-15
- **Engineering batches:** 25–28 + Engineering OS docs
- **Branch:** `develop`
- **HEAD:** `45ed42a` (pushed)
- **Business pivot:** Gate 1A/1B Demo Ready — defer Batch 29 until Gate 1 exit (principal demo)

## 1. Session summary

| Commit | Focus |
|--------|-------|
| `9860c56` | Batch 27 — Parent Copilot API (`/parent-copilot/students/{id}/briefing\|ask`) |
| `c1fa99c` | Batch 28 — Parent UI on `/parent/child/[studentId]` + dashboard v2.6 |
| `45ed42a` | Engineering OS — `004-validation-and-testing.md`, `005-development-lifecycle.md` |

Pilot readiness assessment (read-only): Gate 1 localhost ~6.5/10; HTTPS ~4/10. Bottleneck shifted from engineering to **customer experience**.

## 2. Validation evidence

- `pytest tests/ -q --tb=no` — **340 passed, 2 skipped, 0 errors** (~1077s, isolated run)
- `npm run build` — exit 0
- Prior multi-pytest failures: **environmental** (shared test DB contention), not product regressions

## 3. Engineering context

- **Architecture:** v2.6 — Teacher + Student + Parent Copilot complete
- **Engineering OS:** frozen (`001`–`005`); grow module docs + dashboard per batch
- **Next (ARM-approved):** Gate 1 execution — see [`pilot/GATE1_EXECUTION.md`](./pilot/GATE1_EXECUTION.md)

## 4. Gate 1 priority (1A → 1B → EXIT)

1. **1A Demo Online** — HTTPS deploy (blocked on credentials)
2. **1B Demo Reliable** — reliability targets, CurriculumPack, demo polish
3. **EXIT** — principal demo, no critical issues, **stop** — then Gate 2 or reprioritize from feedback

See [`pilot/GATE1_EXECUTION.md`](./pilot/GATE1_EXECUTION.md).

## 5. Key paths (Batches 27–28)

```
apps/api/app/modules/parent_copilot/
apps/admin-web/src/app/parent/child/[studentId]/page.tsx
docs/engineering/004-validation-and-testing.md
docs/pilot/GATE1_EXECUTION.md
```

## 6. Blockers / owner decisions

- Demo deploy: Cloudflare + API host env (credentials)
- G1-09: ARM-owned Gemini key for demo
- Pilot meeting date drives urgency

## 7. Do not

- Commit without ARM approval (**Batch 29 commits after Gate 1A validate + freeze**)
- Start Batch 30 before Gate 1 exit
- Create new foundational architecture docs (framework is sufficient; `SECURITY_ARCHITECTURE.md` later)
- Rewrite Engineering OS core standards without proven gap

## 8. Batch 29 + freeze sequence (ARM 2026-07-15)

| Step | Status |
|------|--------|
| Batch 29 code (reserved hosts, runtime tenant, Dockerfile `[rag]`) | ✅ local |
| Architecture docs draft (`URL`, `DEPLOYMENT`, `PLATFORM`) | ✅ local |
| Gate 1A HTTPS live | ⬜ blocked on OCI + Cloudflare credentials |
| Validate tenant routing, login, AI, smokes on HTTPS | ⬜ |
| Freeze `DEPLOYMENT_ARCHITECTURE.md` v1.0 | ⬜ after 1A |
| Commit 1: `feat(platform): implement infrastructure readiness (Batch 29)` | ⬜ after freeze |
| Commit 2: `docs(platform): add deployment, platform and URL architecture` | ⬜ after freeze |

---

# Engineering Session 11 — Stage 2A Academic Onboarding Core (2026-07-22)

**Authorization:** ARM — Stage 2A production academic onboarding for paid-school tenants. Gate 1A HTTPS remains separate. **Committed** (isolated Stage 2A batch).

## Done

- **Backend:** `CurriculumExtractionService`, onboarding endpoints, `intelligence_status`, `pack_readiness`, `curriculum_authz` (resource-derived class scope on all draft mutations), `PackService` chapter/outcome edit+delete, `retry_rag_index`, credit purpose `curriculum_extraction` (3).
- **Frontend:** Wizard `/dashboard/teaching/curriculum/onboarding`, `OnboardingReviewPanel` (chapter/topic/LO correction), `AcademicIntelligenceBanner`, role-aware links on curriculum / lesson-plans / ai-papers; incharge class selector restricted.
- **Docs:** Decision log D-2026-07-22, execution plan slice 2A, blueprint, module + platform.json + CHANGELOG.

## Verification (final)

| Check | Result |
|-------|--------|
| `pytest tests/test_academic_onboarding.py` | 15 passed |
| Full `pytest tests/` | 397 passed, 2 skipped |
| `npm run build` (admin-web) | OK |
| Reference smoke | 32/32 green |
| `e2e-smoke.cjs` | 19/19 green |
| `e2e-reference-journeys.cjs` | 18/18 green |
| `e2e-onboarding-review.cjs` | PASS (exactly 1 pack-detail GET) |

## Reference School demo path

1. Tenant `reference` — login as principal/admin.
2. **Teaching → Curriculum → Academic onboarding** (or `/dashboard/teaching/curriculum/onboarding`).
3. Pick class + subject + year; paste chapter list; **Generate draft pack**.
4. Review and correct structure in-panel; **Approve pack (HOD)**.
5. Banner progresses to **Academic Intelligence Ready** (KG + RAG audit events).
6. **Lesson plans** / **Question papers** — select approved pack; banner confirms readiness; generate grounded output.

## Out of scope (deferred)

Public signup, tenant cloning, TTL cleanup, digital assessment, parent automation (Stage 2B+).

## Stop point

**Stage 2A accepted and committed.** Stage 2B remains frozen.

---

# Engineering Session 12 — Gate S production-trust remediation, Phases 0–3b (2026-08-24)

**Authorization:** ARM — remediate the Production Trust Audit
([`reviews/PRODUCTION_TRUST_AUDIT_2026-08.md`](./reviews/PRODUCTION_TRUST_AUDIT_2026-08.md),
ORANGE / 5.0-of-10) in strict priority order. **No new features.** Uncommitted.

## Engineering context (the *why*)

The audit's central finding was not any single bug: it was that **970 passing tests coexisted
with every P1 still reproducible by hand**. Phase 0 found the mechanism. pytest inserts its
rootdir (`apps/api`) at `sys.path[0]` because `tests/` has no `__init__.py`, and a real
directory outranks an editable-install finder — so pytest imported the *local* `app/` while
the editable install pointed at the archived `academix-platform` repo, which is what `uvicorn`
actually served (140 routes vs 182). **I verified that the obvious guard —
`assert "academix-platform" not in app.__file__` — passes while the bug is active.**

Consequence for the rest of this gate: every phase is verified against the **running API**,
not pytest alone, and each fix's regression test is proven red before green. Recorded as a
standing decision in `decisions/DECISION_LOG.md` (2026-08-24).

## Done

### Phase 0 — canonical runtime (P0-ENV-001)

- Uninstalled the stale editable install (`app` → `D:/Projects/academix-platform/apps/api/app`)
  and reinstalled from canonical `apps/api`.
- **`tests/test_canonical_runtime.py`** (new, 3 tests). The load-bearing assertion reads the
  *installed distribution record* (setuptools `__editable___*_finder.MAPPING`, falling back to
  PEP 610 `direct_url.json`) — not `app.__file__`, which pytest masks. Note
  `Distribution.from_name` can resolve to a local `studynexs_api.egg-info` in the source tree,
  which also hides a bad install, so the finder is checked first. Route canaries pin 5
  endpoints instead of a count so new endpoints don't break the test.
- CI: added a **hard gate** step (`pytest tests/test_canonical_runtime.py`) before the
  report-only lint step in `.github/workflows/ci.yml`.
- Corrected the stale "Runtime path references to `academix-platform` — ✅ None" row in
  `CANONICAL_REPOSITORY.md` (it was true for the Docker bind mount, false for local dev).

### Phase 1 — fee privacy (P0-SEC-001)

- `app/modules/fees/endpoints/fee.py`: removed `"teacher"` from `GET /fees/recent`
  (`require_roles("admin", "super_admin")`), matching `/stats` and `/roster`.
- **`tests/test_fee_authorization_matrix.py`** (new, 26 tests): every `UserRole` × every fee
  aggregate, on **seeded real payment data**. Encodes two audit lessons — a `200` with `[]` is
  not an authorization pass (a guard test asserts the seed is visible to admin first, so the
  deny-cases can't be vacuous), and every role is enumerated rather than one per tier. Plus a
  static guard that fails if any fee route ever names a teaching/portal role in `require_roles`.

### Phase 2 — LLM structured-output parsing (P1-AI-001/002)

Root cause: **there was no JSON parser.** Nine sites each called bare
`json.loads(result.text)`, and `gemma4:cloud` returns markdown-fenced JSON for structured
prompts and bare JSON only for trivial ones (confirmed by capturing both shapes live). Hence
a 100% failure rate on precisely the three flagship AI surfaces, and nowhere else.

- **`app/modules/ai/gateway/json_parse.py`** (new): `parse_llm_json(raw, *, feature, expect)`
  tries exact → whitespace-stripped → fence-stripped → prose-sliced, validates the top-level
  container type, and raises `LLMJsonError` otherwise. Brace slicing is **string-literal
  aware** (a naive `find`/`rfind` mis-slices on braces inside generated question text). It
  **does not repair malformed JSON** — a silently "fixed" paper or grade is worse than a clean
  failure, so truncated JSON still raises.
- Wired into all 9 sites (tutor, QP, evaluation engine, 3× teacher copilot, curriculum
  extraction, 2× parent copilot). Each site keeps its own user-facing message and log event;
  `except (json.JSONDecodeError, TypeError)` → `except LLMJsonError`. The parent-copilot and
  curriculum-extraction **graceful fallbacks are preserved** — those degrade quietly, which is
  why they masked how widespread the defect was.
- **Privacy tightening (not in the original scope, but required by §31/§43/§62.5):** two
  pre-existing log lines (`question_paper_service`, `evaluation_engine`) logged raw provider
  text via `raw=(result.text or "")[:400]`. Routing tutor/parent/evaluation output through one
  parser would have widened that to **all nine** sites — i.e. student names, mobiles, answers
  and marks into the log store. The parser now logs only a structural fingerprint
  (`starts=… fence=yes braces=1/0 …`) plus length. No raw model output is logged anywhere.
- **Student-facing copy:** `"Copilot returned invalid JSON"` was rendered verbatim in the
  student tutor. Now `"The tutor could not put that into words just now. Please try again."`
  (this also discharges part of Phase 6).

Regression tests are **call-site level**, because a utility-only test would not have caught the
original bug:

- `tests/test_llm_json_parse.py` (27) — parser behaviour, incl. a verbatim captured provider
  payload, braces inside strings, and "truncated JSON is *not* repaired".
- `tests/test_llm_json_call_sites.py` (16) — asserts each module calls `parse_llm_json` with
  its feature tag, plus an **AST guard** banning `json.loads(<llm result>.text)` anywhere in
  `app/`. (A first attempt used string matching and false-positived on the anti-pattern
  documented in the parser's own docstring; the AST walk is immune to prose.)
- `tests/test_llm_json_no_leak_endpoint.py` (20) — hostile payloads (traceback, API key, DSN,
  system prompt, HTML 502) never reach a user message; PII never reaches the logs; diagnostics
  are still present. Includes a **guard-the-guard** test: `caplog` is empty for structlog
  (stdout), so the first PII assertion passed against `''` — a false green of exactly the kind
  this audit is about. Switched to `capsys` and proved it red.

### Phase 3a — attendance follows a class change (P1-DATA-001)

- `app/modules/attendance/services/attendance_service.py`: added
  `"class_id": stmt.excluded.class_id` to `mark_bulk`'s `ON CONFLICT … set_`.
  `uq_attendance_student_date` is `(school_id, student_id, date)` — one row per student per
  day — so a mid-day class change must **move** the row. It didn't, so the receiving teacher
  got "Attendance marked for 1 students" while their register stayed empty and the class the
  student had **left** kept counting them. Silent, and it corrupts the record every time.
- **Checked the sibling upserts before assuming this was isolated:** `mastery_service` already
  updates `class_id` on conflict, and `ExamMark` has no `class_id` (class comes via the exam).
  Attendance was the only defective site — an oversight, not a policy. Also confirmed
  `mark_bulk` is the *only* attendance write path.
- **`tests/test_attendance_class_change.py`** (new, 3 tests). Two assert on the **register and
  summary a teacher actually sees** — the stored row alone would not have exposed the
  double-counting. The third pins the ordinary same-class correction path (one row updated in
  place, no duplicate) so the fix cannot over-correct.

## Verification

| Check | Result |
|-------|--------|
| `app.__file__` from a neutral cwd, no `PYTHONPATH` | canonical `studynexs-dev/apps/api/app` |
| `/openapi.json` served paths (plain `uvicorn`) | **182** (was 140); 5/5 canaries present |
| Phase 0 guard — bug reintroduced | **FAILED** as designed, then 3 passed after repair |
| Live: `teacher` → `GET /fees/recent` | **200 → 403** (was 50 receipts / 49 families / ₹125,000) |
| Live: `admin` / `super_admin` → all 3 aggregates | 200 retained (no over-tightening) |
| Phase 1 suite — bug reintroduced | **3 FAILED** as designed (live probe + payload + static) |
| `pytest tests/test_fee_authorization_matrix.py` | 26 passed |
| Affected suites (fees, authorization, staff perms, runtime) | **51 passed, 1 failed** |
| Live Phase 2 repro (`tmp/qa-audit/p2_repro.py`) | **10-of-14 failing → 0-of-14** |
| Live: Student Tutor `/ask` × 7 hostile+normal prompts | `400 → 200` all 7; `grounded: true`, citations present |
| Live: Student Tutor **in the browser** | grounded answer + 2 sources rendered where `Copilot returned invalid JSON` used to appear |
| Live: QP generate × 2 | `400 → 200`; 41 marks / 4 sections / 11 questions |
| Live: Teacher Copilot feedback-draft | `400 → 200`; grounded feedback + `citation_sources` |
| Live controls (parent briefing / parent ask / lesson plan / onboarding) | 200 / 200 / 201 / 201 — unchanged |
| Phase 2 tests — call site reverted to `json.loads` | **2 FAILED** as designed (feature-tag + AST guard, named file:line) |
| Phase 2 tests — raw logging reintroduced | **1 FAILED** as designed (caught a student name + mobile in logs) |
| `pytest` Phase 2 files (3 new files) | 63 passed |
| Directly-affected suites (student/teacher/parent copilot, tutor, QP, evaluation engine) | **36 passed** |
| Wider AI + curriculum suites (credits, routing, hardening, telemetry, governance, bank, policy, golden harness, grounding) | **80 passed** |
| QP studio / bank compose+ingest / exam questions / tutor speech+TTS / AEI readiness | **61 passed, 1 skipped** |
| Answer-sheet evaluation (consumes the parser) | **23 passed** |
| Fee matrix + curriculum pack | **29 passed** |
| Live Phase 3a repro, **before** fix | row stayed on `Grade 1 B` after `Grade 1 C` marked the student; C's register **empty**, B counted a departed student |
| Live Phase 3a, **after** fix (clean slate) | exactly **one** row, on `Grade 1 C`; A summary `total: 0`, C `present: 1` |
| Phase 3a tests \u2014 `class_id` removed from `set_` | **2 FAILED** as designed (register empty for the marking teacher); the over-correction control still passed |
| `pytest` attendance suites (new + existing + dashboard state) | **8 passed** |
| `ruff` on changed files | clean (2 pre-existing issues untouched: 4 E501s in `teacher_copilot_service` prompt strings \u2014 4 on HEAD, 4 now \u2014 and an unused `AttendanceStatus` import that predates this session) |

**Full-suite note (honest):** the complete suite was **not** run to green in this session. Its
DB-backed AI tests average ~6 s each (measured: 29 tests / 162 s; 23 tests / 156 s), so a full
pass exceeds an hour. Two concurrent runs early on collided on the shared test database and
produced a misleading `E`/`F` storm — **that was a harness artifact, not a code regression**;
re-running single-threaded produced all dots. I verified 229 tests across every suite touching
the changed modules instead. A clean full-suite run is still outstanding.

**The 1 failure is pre-existing and unrelated:**
`test_authorization.py::test_receipt_download_object_level_access` → `assert 503 == 200`,
the WeasyPrint/`libgobject` PDF defect the audit already recorded. Deferred to Phase 5.

## Known-failing / deferred (do not re-diagnose)

- **P1-PDF-001** — all 5 PDF surfaces 503 (WeasyPrint cannot load `libgobject-2.0-0.dll`,
  resolving it from a Tesseract-OCR directory). Phase 5.
- Phases 3–7 not started: academic data safety (negative marks, exam `total_marks` bounds +
  `Numeric(6,2)` overflow→500, attendance stale `class_id`, report-card period scoping,
  −207.78% card), evaluation stale state, PDFs, remaining user-facing error copy,
  12-journey verification.
- **Deliberate residual test data — delete during Phase 3, it is the live evidence:** negative
  marks on `Ansh Patel` (`06ea5682-5d82-4c1c-9eea-6a8789905447`, `-100.00` on a 20-mark slip
  test) and the **−207.78%** report card in tenant `sia` (P1-DATA-002 / P1-DATA-004).

## Environment notes for the next agent

- **Always confirm `pytest tests/test_canonical_runtime.py` passes first.** If it fails, the
  runtime is serving the wrong repo and every other result is meaningless.
- `uvicorn app.main:app` now works from any cwd with **no `PYTHONPATH`**. If you find yourself
  needing `PYTHONPATH`, the install has regressed.
- Audit probe scripts live in `tmp/qa-audit/` (untracked). `qa.py` must use
  `http://127.0.0.1:8000` — `localhost` adds ~2 s/request via IPv6 fallback on Windows and
  produced a false "everything is over budget" reading during the audit.
- Residual audit test data left deliberately: negative marks on `Ansh Patel` and the
  −207.78% report card in `sia` are the live evidence for Phase 3. Delete after fixing.

## Stop point

**Phases 0–1 complete and verified in the running product.** Phase 2 (shared
`parse_llm_json()`) awaiting go-ahead.

---

# Engineering Session 13 — Gate S Phase 8/9 closure (2026-09-02)

**Authorization:** ARM request: `commit and push then Gate S (Phase 8 and Phase 9)`.

## Done

- Confirmed trust-remediation checkpoint was committed and pushed:
  - commit `71dadb9`
  - branch `develop`
  - remote `studynexs-github/develop`
- Executed **Phase 8** final regression sweep across the published trust-fix surfaces.
- Completed **Phase 9** status closure updates in:
  - `docs/STATUS.md`
  - `docs/AGENT_HANDOVER.md` (this entry)

## Phase 8 verification evidence

### Frontend trust harness sweep (all green)

- `node --test tests/e2e-harness-utils.test.mjs` → `4 passed, 0 failed`
- `node e2e-learning-intelligence.cjs` → `ALL GREEN (6 checks)`
- `node e2e-parent-intelligence.cjs` → `ALL GREEN (7 checks)`
- `node e2e-student-intelligence.cjs` → `ALL GREEN (6 checks)`
- `node e2e-assessment-intelligence-v1.cjs` → `ALL GREEN (18 checks)`
- `node e2e-reference-journeys.cjs` → `ALL GREEN (18 checks)`

### Backend targeted trust regression sweep

- `pytest` run:
  - `tests/test_canonical_runtime.py`
  - `tests/test_student_copilot.py`
  - `tests/test_parent_copilot.py`
  - `tests/test_pdf_runtime.py`
  - `tests/test_pdf_surfaces_runtime_fallback.py`
  - `tests/test_pdf_endpoint_runtime_fallback.py`
  - `tests/test_eval_state_reset_guard.py`
- Result: **`29 passed, 1 skipped`**

### Live report-card scoping re-verification (Phase 3c–3e confirmation)

- `scripts/qa/repro_report_card_scoping.py` with `QA_ALLOW_WRITE=1`:
  - scoped totals reported correctly,
  - old-year totals isolated,
  - invalid legacy approval blocked (`HTTP 422`, `Report card totals are outside the valid range`),
  - script confirms `PASS` and cleans QA fixtures.

## Phase 9 closure state

- Gate S status matrix now reflects completion through Phase 8/9 with explicit
  evidence (live-verified vs regression-verified).
- Historical stale wording in prior entries remains preserved for audit history;
  this session is the current closure checkpoint.

## Residual risk / next checkpoint

- Full-repository pytest/lint sweep was not re-run in this closure step; this
  pass was intentionally scoped to Gate S trust surfaces and runtime proofs.
- Next natural checkpoint is a full-suite green run for release packaging.

## Stop point

**Gate S Phase 8/9 closure completed for the current trust-remediation batch.**

---


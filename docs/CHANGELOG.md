# Changelog

All notable changes to StudyNexs. Format based on [Keep a Changelog](https://keepachangelog.com/);
this project is pre-1.0 and pre-release (no versioned releases yet). Record engineering-visible
changes under **[Unreleased]** until the first tagged release. Architectural *reasoning* lives in
[`DECISION_LOG.md`](./DECISION_LOG.md); session detail in [`AGENT_HANDOVER.md`](./AGENT_HANDOVER.md).

## [Unreleased]

> Session 2026-07-10 — Batches 1–11. All changes are on the worktree branch
> `claude/studynexs-engineering-kickoff-a6761c`, **uncommitted** (Prime Directive 9).

### Security
- **Sev-1 fixed:** `POST /fees/pay` no longer admits `parent` and rejects unverifiable
  `online`/gateway-claimed payments — a parent could previously mark their child's fee PAID with no
  money movement.
- Logout now revokes the browser refresh session (per-device `sid`); previously dead code for cookie clients.
- Mastery heatmap/digest/flags now enforce staff scope (was: any teacher could read any class's per-student mastery).
- `GET /jobs/{id}` enforces creator/admin ownership (was tenant-scoped only — IDOR).
- Role ceiling now applies to a target's current role (admin can't edit/deactivate a principal).
- PII removed from login logs (mobile/username); `mask_mobile`/`mask_email` added to `pii.py`; `class_incharge` user list masks contact PII.
- **Aadhaar encryption at rest** — `EncryptedString` (Fernet/MultiFernet, rotation) on admission/staff Aadhaar columns; prod boot guardrail requires `AADHAAR_ENCRYPTION_KEYS`.
- Redis-blacklist check degrades gracefully on outage instead of 500-ing every request.

### Fixed
- `/metrics` endpoint annotation bug (was a required query param → 422/500).
- Arq worker registered no handlers under the documented start command — now registers via `on_startup`; `run_job` raises `arq.Retry` (not a plain exception) when the row isn't yet committed.
- `GET /ops/payroll` fabricated + persisted salaries on read — now read-only with an explicit idempotent `POST /ops/payroll/generate`.
- Fee roster 500'd on `min(uuid)` — now selects each student's earliest-owing record via a bounded query; status logic corrected; money accumulated in `Decimal`.
- Idempotency key reused with a different amount no longer returns an unrelated receipt.

### Added
- **CI:** `.github/workflows/ci.yml` — pytest (main + security) + `next build` + docker image as hard gates.
- **Commit-before-response:** `CommitOnSuccessRoute` (`app/core/api_route.py`) on all 21 routers; commit-time failures surface as 5xx instead of a false 2xx.
- **Shared AI Platform foundation** (consumed by all pillars; never a per-feature SDK call):
  - `app/modules/ai/embeddings/` — provider-agnostic `EmbeddingProvider` (OpenAI + stub) + `EmbeddingService`.
  - `app/modules/ai/vectorstore/` — `VectorStore` ABC (`search` requires `school_id`) + Qdrant + in-memory adapters.
  - `app/modules/ai/rag/` — `RagService.index_pack` / `retrieve` (tenant+pack-scoped) / `build_context` with citations.
- ~30 regression tests across the batches; encryption (7), admission (18), embeddings (7), vectorstore (6), rag (3) validated (live OpenAI + Qdrant for the AI foundation).
- Documentation knowledge base: `AGENT_HANDOVER.md`, `ROADMAP.md`, this changelog, and `docs/{AI_ARCHITECTURE,CURRICULUM_INTELLIGENCE,ASSESSMENT_INTELLIGENCE,KNOWLEDGE_GRAPH,MOBILE_ARCHITECTURE,DESIGN_SYSTEM}.md`.

### Changed
- Alembic: two forked heads merged into a single linear head.
- Money aggregation uses `Decimal` end-to-end; cast to a JSON number only at the response boundary.
- CI lint (`ruff`/`eslint`) is **report-only** pending a dedicated formatting pass (owner decision).

### Known issues
- Local **full test suite** is flaky (asyncpg connections lingering across pytest-asyncio per-test event loops); focused runs and CI are green. Durable fix = single session-scoped event loop (not yet applied). See `AGENT_HANDOVER.md` §9.

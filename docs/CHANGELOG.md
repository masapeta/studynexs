# Changelog

All notable changes to StudyNexs. Format based on [Keep a Changelog](https://keepachangelog.com/);
this project is pre-1.0 and pre-release (no versioned releases yet). Record engineering-visible
changes under **[Unreleased]** until the first tagged release. Architectural *reasoning* lives in
[`DECISION_LOG.md`](./DECISION_LOG.md); session detail in [`AGENT_HANDOVER.md`](./AGENT_HANDOVER.md).

## [Unreleased]

> Session 2026-07-12 — Batch 20 (Content Review Queue). **Uncommitted.**

### Added
- **`content_review_items` table** — pending/approved/rejected HITL queue (migration `b9c0d1e2f3a4`).
- **`ContentReviewService`** — concept card gaps + document ingest review; approve promotes ConceptCard.
- **Content Review API** — queue list, enqueue, edit, approve, reject under `/api/v1/curriculum/content-review/`.
- **Tutor hook** — missing approved card auto-enqueues tutor gap item.
- **Document ingest hook** — completed ingest enqueues teacher review item.
- **`tests/test_content_review_queue.py`** (5).

### Changed
- Engineering dashboard refreshed for Batch 20.

---

> Session 2026-07-12 — Batch 19 (Question → Concept graph links). Committed on `develop`.

### Added
- **`KgNodeType.QUESTION_BANK_ITEM` + `KgEdgeType.TESTS`** — question bank items linked to spine concepts (migration `a8b9c0d1e2f3`).
- **`QuestionConceptLinkService`** — citation/concept resolution on bank ingest; spine rebuild remaps links.
- **API** — `GET /api/v1/ai/question-bank/items/{item_id}/concepts`.
- **`tests/test_question_concept_links.py`** (6).

### Changed
- **`ingest_from_paper`** — creates TESTS edges for grounded papers with citations.
- **`build_spine_from_pack`** — preserves/remaps question links on spine rebuild.
- Engineering dashboard refreshed for Batch 19.

---

> Session 2026-07-12 — Batch 18 (ConceptCard first-class table). **Uncommitted.**

### Added
- **`concept_cards` table** — teacher-approved explanation, examples, hints (migration `z6a7b8c9d0e1`).
- **`ConceptCardService`** — draft → approve workflow; one card per concept.
- **ConceptCard API** — CRUD + approve under `/api/v1/curriculum/`.
- **Tutor integration** — approved cards served via `get_lesson` when concept slug matches.
- **`tests/test_concept_card.py`** (4).

### Changed
- Engineering dashboard refreshed for Batch 18.

---

> Session 2026-07-12 — Batch 17 (Knowledge Graph). Committed on `develop`.

> Session 2026-07-11 — Merge recovery + Batches 13–14. Committed on `develop`.

### Fixed
- **Merge recovery:** commit `34aec0c` had accidentally reverted the shared AI platform foundation
  (embeddings, RAG, vector store, `assessment_grounding`, `CommitOnSuccessRoute`, encryption, CI,
  migrations, docs). Restored 87 files from merge parent `5f76c00`.
- **`answer_sheet_eval_service` half-merge:** caller expected `(suggestions, subjective_results)` but
  `_grade_exam` returned a single dict — every evaluation failed at runtime. Completed engine wiring.
- **`tutor.py` merge conflict marker** (`<<<<<<< HEAD`) — resolved; `CommitOnSuccessRoute` + logger
  both preserved.

### Added
- **`evaluation_engine.py`** — shared rubric-per-criterion marking engine (`evaluate_subjective`,
  `sanitize_evaluation`, `GroundingContext`); batch subjective LLM via gateway; criteria authoritative.
- **`tests/test_evaluation_engine.py`** (8) — engine units + service integration + fallback + single-charge metering.
- **`ground_for_evaluation`** — best-effort pack-grounded RAG at mark time; wired into subjective grading.
- **`tests/test_assessment_grounding.py`** (+3) — evaluation grounding paths.
- **Eval UI** — rubric criteria, missing concepts, confidence, and marking method in teacher review.

### Changed
- **Answer-sheet evaluation:** objective → deterministic; subjective → LLM rubric engine with
  heuristic fallback; `method` provenance on suggestions; one credit per evaluation (subsequent LLM
  calls cost-only for observability).
- Documentation refreshed for Session 03 (`AGENT_HANDOVER`, `STATUS`, `ROADMAP`, this file,
  `ASSESSMENT_INTELLIGENCE`, `DECISION_LOG`).

### Security
- (none this session — foundation restore re-enabled existing hardening from Batches 1–8)

### Known issues
- Local full suite was **green** in one 289-pass run (2026-07-11); intermittent asyncpg cross-loop
  flakiness may still appear on repeated back-to-back runs (see `AGENT_HANDOVER.md` §9).
- ~~Eval marking does not yet use pack-grounded RAG (`grounding=None`).~~ **Fixed in Batch 14** — best-effort when approved pack exists.

---

> Session 2026-07-10 — Batches 1–12. Prior work on worktree branch
> `claude/studynexs-engineering-kickoff-a6761c`, merged into `develop` history.

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

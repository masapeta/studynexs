# Assistant Execution Architecture — Design of Record

- **Status:** Accepted (design), Implementation in progress (Phases 3–11 landed; QP ops hardening)
- **Version:** 1.10
- **Date:** 2026-10-23
- **Owner:** Avinash Reddy Masapeta (ARM)
- **Subsystem:** Workspace Assistant (`app/modules/workspace/assistant`)
- **Related ADR:** [`ADR-0003-assistant-execution-and-workflow-architecture.md`](../decisions/ADR-0003-assistant-execution-and-workflow-architecture.md)
- **Related:** [`AEI.md`](./AEI.md), [`ADR-0002`](../decisions/ADR-0002-educational-understanding-intelligence-platform-architecture.md), constitution §14.2, §33, §34, §42

---

## 0. Purpose and scope

This is the **design of record** for how a user request becomes a governed, structured result inside the StudyNexs assistant. It fixes the production architecture so that all planned execution categories — **capability, composition, workflow, action, clarification** — share **one** semantic representation, **one** governed runtime, and **one** authorization boundary.

It is **design**, not a build order. It describes the target so that every increment (starting with Question Paper as the first workflow consumer) attaches at a defined seam instead of inventing a parallel path. The JEV/planner decision is settled (§1); this document does **not** reopen it.

Non-goals (explicitly out of scope for the current phase, per the locked brief): no agent framework, no MCP runtime, no `execution_type` field on `CapabilityContract`, no second registry / second semantic model / second router, no speculative subsystems without a real consumer.

---

## 1. Locked decision (settled — do not reopen)

The planner backend is a **default-off, config-selected** stage. Committed in `4d82341`.

```
PLANNER_BACKEND = gemma   (default, production)
              | jev       (opt-in)
              | hybrid     (opt-in: JEV + confidence-gated Gemma fallback)
PLANNER_JEV_CONFIDENCE_THRESHOLD = 0.95   (configurable; not hardcoded in business logic)
```

- **JEV** = the bounded semantic/task decision layer **and** an LLM cost/latency optimization layer. Measured: ~17× cheaper per planner call, ~1.8× faster, ~64% lower planner-stage cost at ~30% fallback. JEV is **never** the source of truth.
- **Gemma** = fallback + complex reasoning/generation.
- Only the **planning stage** varies. The `PlannerDecision` it produces feeds the **identical** downstream runtime regardless of backend (`AssistantService._plan`).

Cost framing rule (binding): the 64% applies to the **planner stage only**, not to total AI spend. Workflow generation, evaluation, tutoring, and report generation have separate generative-model costs and are measured separately (§8).

---

## 2. The canonical execution chain

```
USER (chat)  /  Traditional Web UI
   │
   ▼
JEV  OR  Gemma fallback            ← planning stage only (config-selected)
   │
   ▼
PlannerDecision                    ← the ONE canonical semantic/task representation
   │
   ▼
Execution classification           ← application-controlled dispatch (no 2nd router)
   ├── Capability      (one deterministic governed operation)
   ├── Composition     (bounded multi-capability analytical query)
   ├── Workflow        (first-class multi-step product process)
   │      ├── deterministic
   │      └── agentic  (execution strategy only — same contract)
   ├── Action          (governed state-changing operation)
   └── Clarification   (ask the user)
   │
   ▼
Governed StudyNexs Runtime         ← resolver · derivation · temporal integrity ·
   │                                  authorization · tenant isolation · SchoolPack · audit
   ▼
ERP / RAG / external services      ← source of truth
   │
   ▼
Structured Result                  ← UI-independent typed block
   │
   ├── Native StudyNexs UI (chat + traditional surfaces)
   └── MCP Apps adapter (interoperability boundary only)
```

**Invariant:** everything below `PlannerDecision` is governed. No path — model, workflow, action, agent, MCP, or UI — reaches ERP/DB except through the governed runtime.

---

## 3. What exists today (grounded in code)

The chain above is **already real** for capability / composition / mixed / document / clarify / navigate. The `act` route exists but is a stub (`_action_not_supported`) — Action has **no consumer yet**, which is why QP approval becomes its first genuine consumer.

`PlannerDecision` (in `planner.py`) already models the taxonomy:

```python
route:  "STRUCTURED" | "DOCUMENT" | "MIXED" | "ACTION" | "CLARIFICATION" | "NAVIGATE"
action: "tool" | "compose" | "mixed" | "document" | "act" | "navigate" | "clarify"
tool, params, plan, navigate_to, message, document_query,
temporal (TemporalIntent), operation, metric
```

Dispatch (in `AssistantService._handle_turn`) is a single `if decision.action == ...` ladder:

| `action` | Consumer today | Status |
|---|---|---|
| `tool` | `_run_tool` → capability | ✅ real |
| `compose` | `_run_compose` → composition | ✅ real |
| `mixed` | `_run_mixed` | ✅ real |
| `document` | `_run_document` → RAG | ✅ real |
| `navigate` | nav block | ✅ real |
| `clarify` | guide block | ✅ real |
| `act` | `_action_not_supported` | 🔲 stub — Action boundary lands here |
| `workflow` | `_run_workflow` → executor → registry | ✅ real (Phase 4; QP first consumer) |

**Design consequence:** Workflow is added as a **new classification** feeding a **generic workflow boundary**, and Action replaces the `act` stub. Neither introduces a QP-specific branch (§5).

---

## 4. The governed runtime (frozen)

These are the semantic/authorization authorities. Every execution category runs through them; none may be bypassed or duplicated:

- **Capability Contracts** (`contracts.py`) — the single semantic source of truth per capability (entity/operation/scope/temporal_mode/required+derivable params).
- **Resolver** (`resolver.py`) — entity resolution (e.g. admission no → student), tenant-scoped.
- **Derivation** (`derivation.py`) — fill a required param via an authoritative CURRENT relationship; skipped for PAST requests.
- **Temporal Integrity** (`temporal.py`, `conversation.py`) — semantic temporality understood independently of tool selection; the P0.1 invariant.
- **Authorization** — role + object-level, server-side, always.
- **Tenant isolation** — `school_id` from `CurrentUser`, never the client.
- **SchoolPack** (`school_pack.py`) — per-tenant semantic mapping, blind to the runtime.
- **Audit** — consequential actions recorded.

Workflows and actions **consume** these; they never re-implement them.

---

## 5. The workflow model (generic — the core of this phase)

A **Workflow** is a first-class, multi-step product process. QP is the **first consumer**, not the definition. The model must serve QP, Evaluation, Lesson Planning, Remediation, and Parent Intervention without QP-specific shapes.

### 5.1 WorkflowDefinition (registry entry)

A workflow is declared once, discovered by the planner via a bounded `target`, and dispatched generically:

```
WorkflowDefinition
  workflow_id            e.g. "question_paper"
  version                semantic version of the workflow contract
  input_contract         typed inputs (validated before run)
  output_contract        typed outputs (→ StructuredResult artifact)
  execution_mode         "deterministic" | "agentic"   (strategy only)
  authorization          required roles + object-level checks
  approval_required      bool + who may approve
  audit_metadata         what to record
  timeout / retry / cancel semantics (where the executor needs them)
```

`execution_mode` lives on the **WorkflowDefinition**, not on `CapabilityContract` (contract stays frozen). The router/classifier never inspects it — the executor does. This is what lets Remediation become agentic later without touching JEV, `PlannerDecision`, contracts, resolver, derivation, temporal, authz, or SchoolPack.

### 5.2 Lifecycle (canonical, generic)

```
created → queued → running → waiting_for_input → waiting_for_approval → completed
                     │                                                     ↑
                     └──────────────→ failed / cancelled                   │
                                        approval (server-side) ────────────┘
```

QP maps onto this **without a new engine**: its existing `PaperStatus` (DRAFT → EDITED → PENDING_APPROVAL → APPROVED → PUBLISHED) is the domain projection of `running → waiting_for_approval → completed`. The generic lifecycle wraps the existing status; it does not replace it.

### 5.3 Execution boundary

- Use **existing Arq + service patterns**. Do **not** invent a separate workflow engine if Arq + the service layer suffice.
- A deterministic workflow (QP) may run synchronously-with-progress or as an Arq job; an async/long workflow runs on Arq. The executor is an implementation detail behind the WorkflowDefinition.
- The workflow **calls existing governed services** (e.g. `question_paper_service.generate_paper`). It does **not** rewrite QP generation, grounding, validation, or approval.

### 5.4 Registry decision

Reuse-first: inspect `CapabilityContract`, `PlannerDecision`, the QP service, the tool catalog, and Arq jobs before adding anything. A **separate `WorkflowDefinition`** is justified because a workflow is a *multi-step process with lifecycle + approval*, which does not belong in `CapabilityContract` (a single deterministic operation). It is a distinct production object, not a second semantic model — `PlannerDecision` remains the only semantic representation; `WorkflowDefinition` is execution metadata, analogous to how contracts are capability metadata.

### 5.5 What Phase 3 implemented (grounded)

Module `app/modules/workspace/workflows/` — a **contract + lifecycle model only**, no engine:

- `definition.py` — `WorkflowDefinition` (frozen dataclass: `workflow_id`, `version`, `name`, `io`, `execution_mode`, `required_roles`, `approval_required`, `is_async`, `domain_resource`, `audit_action`, `tags`) + `WorkflowIO` (references existing Pydantic schemas) + `ExecutionMode` (`deterministic` implemented, `agentic` architectural only). Fail-fast validation in `__post_init__`.
- `lifecycle.py` — `WorkflowState` enum + an **explicit transition allow-list** (`can_transition`, `is_terminal`, `TERMINAL_STATES`). A small state machine, not a transition engine. Not every workflow uses every state.
- `registry.py` — fail-fast lookup (`register_workflow`/`get_workflow`/`list_workflows`), mirroring the capability contract registry. **Question Paper is registered** against its *real* domain schemas (`GenerateRequest` in, `QuestionPaperOut` out) with `execution_mode=deterministic`, `approval_required=True`, roles matching the existing QP endpoints.

**Wrapping, not owning (validated by tests):** the generic `WorkflowState.WAITING_FOR_APPROVAL` is a distinct orchestration concept from QP's domain `PaperStatus.PENDING_APPROVAL`. The workflow layer does **not** import, redefine, or map QP's status — QP keeps `DRAFT → EDITED → PENDING_APPROVAL → APPROVED → PUBLISHED` as its authoritative business lifecycle. No mapping engine exists.

**Not built in Phase 3 (documented, not stubbed):** no executor is wired into the assistant (that is Phase 4), no `AgentExecutor`, no agent framework, no MCP, no full action engine, no Arq wiring yet. `WorkflowDefinition` is the only new abstraction — justified by immediate QP validation (brief §25 exception).

**Cross-workflow compatibility check (design-level, brief §19):**

| Workflow | Exec mode | Approval | Async | State complexity | Fits model? |
|---|---|---|---|---|---|
| Question Paper | deterministic | yes | no (sync-with-progress) | medium | ✅ validated in code |
| Evaluation | deterministic | maybe | yes (Arq) | medium | ✅ representable |
| Lesson Plan | TBD | maybe | maybe | low/medium | ✅ representable |
| Remediation | potentially agentic | maybe | maybe | high | ✅ `execution_mode=agentic` reserved |
| Parent Intervention | deterministic + action | yes | maybe | medium | ✅ workflow + Action (Phase 8) |

### 5.6 What Phase 4 wired (Question Paper — first consumer)

The generic pattern now runs end to end for QP, with **no QP-specific router** and **no rewrite** of QP logic:

- **`PlannerDecision`** gained the minimum: a `WORKFLOW` route, a `workflow` action, and a `workflow_id` field. A workflow is **not** overloaded onto `tool` (it is not a capability). `PlannerDecision` remains the only semantic model.
- **Gemma** learned the `WORKFLOW` route semantically (paraphrase-based, not keyword-matched): "create/prepare/generate a test/exam/question paper for a class & subject" → `workflow_id="question_paper"` + params (`class_label`, `subject`, `total_marks`, `topics`).
- **JEV** exposes each registered workflow as a namespaced bounded Choice option (`workflow:<id>`); a confident workflow choice maps to the same canonical workflow decision. Follow-ups still route to Gemma (unchanged carry-over). Confidence gate unchanged.
- **Dispatch:** `AssistantService._run_workflow` → `workflows.executor.run_workflow` — the **single controlled workflow-resolution path** (`app/modules/workspace/workflows/executor.py`). It resolves class/subject via the existing assistant resolver, authorizes via the existing `get_staff_scope` + `assert_qp_generate` (JEV/Gemma selecting the workflow grants nothing), finds the newest **APPROVED** CurriculumPack, enforces the existing monthly credit cap, and calls the existing `generate_paper`. Returns a `kind="workflow"` structured block reporting `workflow_state=waiting_for_approval` alongside the authoritative domain `paper_status=draft`.
- **HITL preserved:** the executor never approves. The result block's actions point at the existing server-side `/submit` and `/approve` endpoints. A model cannot approve a paper.
- **Failure/clarify:** unknown workflow → guide; missing/ambiguous class or subject → clarify; no approved pack → guide; generation failure → `WorkflowError` → safe guide. No partial state.

> **Resolved in Phase 10 — QP generation is now asynchronous.** Production QP generation no longer blocks the request: `_run_question_paper` keeps all fast up-front work (resolve class/subject, authorize, approved-pack gate, pre-flight credit **check**) then **enqueues** `question_paper_generate` on the existing Arq worker and returns a `kind="workflow"` block at `workflow_state=queued` carrying `summary.job_id`. The worker runs the **unchanged** `generate_paper` pipeline; the chat polls the existing `GET /api/v1/jobs/{job_id}` and swaps the turn to `waiting_for_approval` (with a Review link to the generated paper) on `done`, or an honest error on `failed`. **No** change to the planner, registry routing, or `generate_paper`. `is_async=True` on the `question_paper` definition now matches real behavior. **TESTING still runs synchronously** (preserves the existing QP tests + deterministic CI). **Idempotency:** an in-flight (`QUEUED`/`RUNNING`) job for the same school + creator + class + subject is reused — a double-submit or client retry cannot produce two papers or two credit charges. **Graceful degradation:** if enqueue fails (Redis/worker outage) the executor falls back to synchronous generation, exactly as Evaluation does. **Single-charge invariant:** the pre-flight `enforce_monthly_ai_cap` is a check only; the one reservation happens inside `generate_paper` at generation, so a queued-but-never-run job never charges. **Pollable reference:** the generic `Job` row is the orchestration handle (tenant- + creator-authorized at `GET /api/v1/jobs/{job_id}`); the QP `PaperStatus` domain lifecycle stays authoritative and unchanged (the paper still only exists once generated).

### 5.7 What Phase 5 wired (Evaluation — second consumer, async + Arq)

Evaluation proves the **same** generic model handles a materially different workflow — asynchronous, Arq-backed, with its own domain lifecycle — with **no evaluation-specific orchestration** and **no rewrite** of the evaluation implementation:

- **Registered** as `evaluate_answer_sheet` in the same registry, `is_async=True`, `approval_required=True`. IO references the real `EvaluationCreate` / `EvaluationOut`.
- **Same executor, new branch:** `_run_evaluation` reuses the existing `AnswerSheetEvalService.create_and_evaluate` unchanged — which authorizes (`assert_exams_access` + `assert_exam_eval_access`), checks AI credits, and **enqueues an Arq job** (runs sync only under TESTING). No new queue/scheduler/worker.
- **Async lifecycle proven:** the generic `WorkflowState` is **derived** from the authoritative domain status — `pending→QUEUED`, `processing→RUNNING`, `suggested→WAITING_FOR_APPROVAL` (teacher HITL), `approved→COMPLETED`, `failed→FAILED`. The workflow is **never** reported COMPLETED merely because the job was submitted; the domain status stays the source of truth (wraps, does not own).
- **Correlation:** the result block carries `evaluation_id` + `job_id` (`AnswerSheetEvaluation.job_id → Job`), so request → workflow → Arq job → result is traceable via the existing job/telemetry mechanisms — no second tracing system.
- **HITL preserved:** the executor never approves. Result actions point at the existing `/api/v1/exams/evaluations/{id}/approve` endpoint.
- **Idempotency (existing, documented):** `create_and_evaluate` row-locks the student + eval row and rejects a re-submit while `processing` / after `approved` (unique `(exam_id, student_id)`); the workflow layer adds nothing and relies on these existing protections.
- **Answer-sheet upload** stays in the existing UI; a chat turn supplies exam + student references, and when no answer source is present the workflow returns an honest upload next-step rather than fabricating input.

**Reuse proven:** QP (sync + approval) and Evaluation (async + Arq) run through the **same** `PlannerDecision → WorkflowRegistry → executor` path with no per-workflow orchestration model — strong evidence the Phase 3 architecture is correctly generic.

### 5.8 What Phase 6 wired (Lesson Plan) — and why Remediation is deferred

**Lesson Plan (third consumer, deterministic + approval):** registered as `lesson_plan` (`is_async=False`, `approval_required=True`, IO = real `GenerateLessonPlanRequest` / `LessonPlanOut`). `_run_lesson_plan` reuses `LessonPlanService.generate` unchanged — resolves class/subject via the assistant resolver, authorizes via the existing `assert_qp_generate` gate, grounds on an approved pack when one exists (the service also works ungrounded via template), and returns `WorkflowState.WAITING_FOR_APPROVAL` alongside the authoritative domain `plan_status=draft` (`LessonPlanStatus` DRAFT → APPROVED). Actions point at the existing `/api/v1/lesson-plans/{id}/approve`.

**Governance hardening (found + fixed in Phase 6):** `LessonPlanService.generate` raises the authz `HTTPException` *inside* the call. The executor now calls `assert_qp_generate` **before** the try and **re-raises `HTTPException`** so a 403 propagates unchanged and is never masked as a generic `WorkflowError`. This is the same before-generation authz ordering QP and Evaluation already use.

**Remediation — deliberately NOT built (per brief §8, roadmap "prove the need", constitution YAGNI §4.1):** there is **no remediation domain service** in the codebase — only `remedial_activity` / `remedial_hint` fragments inside the misconception service. Wrapping a workflow around a non-existent feature would be *inventing functionality*, not reusing an existing implementation. Remediation is therefore deferred until a real remediation feature exists (it is the natural candidate for the first **agentic** workflow when built — Phase 12 — but the need must be proven from real behavior, not assumed). The generic model already reserves `execution_mode=agentic` for it (§5.5 matrix).

### 5.9 What Phase 7 wired (Parent Intervention — fourth consumer + the FIRST governed action)

Parent Intervention is the first workflow whose result carries a **state-changing action**, so it is where the Action boundary (§6) is actually born. Unlike Phases 4–6 (which wrapped an existing service), the *feature* is composed from existing primitives (attendance data + `Parent`/`StudentParentMap` + `NotificationService`) — a legitimate build, on the roadmap, not an invented one.

- **New persisted domain** (`ParentInterventionBatch` + `ParentInterventionDraft`, `app/db/models/parent_intervention.py`, reversible migration `n4b1d8e2a6c3`). Persistence is required: a stateless chat draft cannot be server-side idempotency-guarded or re-validated at approval time.
- **Workflow half** (`_run_parent_intervention` → `ParentInterventionService.create_batch`): identifies students below an attendance threshold, resolves each to their linked parent(s), and persists **one 1:1 DRAFT per (student, parent)**. Returns `WAITING_FOR_APPROVAL`. **Sends nothing.** Authorized by the existing `assert_exams_access` staff gate.
- **Action half** (`ParentInterventionService.approve_and_notify`, exposed at `POST /api/v1/workflows/parent-intervention/drafts/{id}/approve`, role-gated): the first governed state-changing action. At approval time it row-locks the draft, **re-validates** tenant + `assert_can_access_student` + that the recipient is still a linked parent + message validity, is **idempotent** (already-notified → returns unchanged; unique `(batch, student, parent)`), delivers **one IN_APP** notification via the existing `NotificationService`, and writes an explicit `AuditLog` row (workflow/student/parent/notification ids). Failure sets `status=failed` honestly — never a silent notified/COMPLETED.
- **Safety invariants:** a model can never approve or send (only an authenticated staff user hitting the endpoint can); strictly 1:1 (no bulk notification — each draft has its own approve action); IN_APP only (SMS/email/push TODO stubs explicitly deferred); the send is described as approval-gated / server-authorized / validated / idempotent / audited — **not** "reversible" (a delivered notification cannot be assumed un-sendable).
- **Not built:** no generic Action Engine, no broadcast abstraction, no external channels, no agent. The action surface is exactly what this one consumer needs; generalization waits until a second real action (fee reminders / notices) proves the shape (Phase 8).

### 5.10 What Phase 10 wired (Native Chat UX + QP async execution)

Phase 10 completes the chat presentation for all result kinds and removes synchronous QP generation as a pre-GA risk, reusing the existing Arq/Job infrastructure (no new engine, queue, or realtime transport).

- **Native rendering (frontend).** All twelve result kinds render through `AssistantBlockView.tsx`; the safety-critical decisions are extracted into a pure, unit-tested module `assistant-block-logic.ts` (`node --test`, matching the existing frontend test stack — no new framework). The rules that could silently go wrong live there: an `action_result` shows success **only** when the backend confirms it (`created===true`, or `created===false` with `status="completed"` for an idempotent replay, or `status="published"`); unknown kinds hit a safe fallback instead of crashing; `mixed` children render in a stable data-then-document order. The twelve-kind TS union gained `workflow`/`action_preview`/`action_result` (already in Phase 9) plus a trailing `string` for forward-compatibility.
- **QP async (backend).** `_run_question_paper` keeps all fast up-front work (resolve/authorize/approved-pack/pre-flight credit check) then delegates to `_enqueue_qp_generation`, which enqueues `question_paper_generate` on the existing worker and returns a `queued` workflow block with `summary.job_id`. The new job handler (`app/modules/ai/jobs/question_paper_job.py`, registered in `worker.register_job_handlers`) runs the unchanged `generate_paper`. TESTING runs synchronously (preserves existing QP tests). Idempotent (in-flight job reused), degrades to sync on enqueue failure, single-charge preserved (reservation stays inside `generate_paper`). The generic `Job` row is the pollable handle; `PaperStatus` stays authoritative.
- **Chat integration (polling).** When a turn returns a `queued`/`running` workflow with a `job_id`, `AssistantProvider.tsx` polls the existing tenant-/creator-scoped `GET /api/v1/jobs/{job_id}` (bounded ~2 min, backoff), then swaps the turn in place to `waiting_for_approval` (with a Review link to the paper) on `done`, or an honest error on `failed`. Polls are cancelled on new-chat / session-switch / unmount so a stale poll never mutates a gone turn. No websocket/SSE introduced — polling reuses what exists.
- **Not built:** no second renderer architecture, no response-framework abstraction, no new job system, no realtime transport, no change to the planner/registry/`generate_paper`.

### 5.11 What Phase 11 wired (MCP Apps adapter — bounded, read-only interoperability)

Phase 11 exposes an explicitly allowlisted slice of existing capabilities to compatible external MCP hosts (per **SEP-1865 / MCP Apps**), as a thin protocol shim — **not** a new runtime, registry, identity, or data layer.

**Adapter boundary + identity flow:**

```
MCP Host (Claude/Copilot/…)  ──Bearer + X-Tenant-Slug──▶  POST /api/v1/mcp
      JSON-RPC 2.0                                           │ require_roles(staff) + get_current_user
                                                             ▼  (server-derived CurrentUser; body identity ignored)
                                      app/modules/mcp/server.handle_rpc
                                        · initialize / tools/list / resources/list / resources/read / tools/call
                                        · allowlist: MCP tool ─▶ EXISTING AssistantTool.handler
                                                             ▼
                                      cap.class_attendance_today  (resolve_class + _authorize_class, tenant-scoped)
```

- **Where it runs:** in-process FastAPI router at `/api/v1/mcp` (`app/modules/mcp/`). It reuses the existing auth dependency, `require_roles`, rate limiting, audit middleware, and DB session. No new process, SDK, or dependency — the small JSON-RPC subset is implemented directly (SEP-1865 explicitly permits this).
- **Identity is server-derived.** `get_current_user` decodes the Bearer JWT (and enforces the tenant/school match); the host supplies the same credentials a browser does. A `school_id`/`user_id`/`role` placed in the JSON-RPC body is **ignored** — proven by `test_spoofed_identity_in_body_is_ignored`. Cross-tenant lookups return `not_found`, never another school's data (`test_cross_tenant_class_is_not_found`).
- **The allowlist (exactly one tool):** `school_class_attendance_today` → the existing `class_attendance_today` capability. Chosen because it is **read-only**, staff-gated, **object-authorized inside the capability** (`_authorize_class`), and exposes only **aggregate counts** (present/absent/late/%) — **no individual student records**. `tools/call` returns `content[].text` (the model/text-only fallback) **plus** `structuredContent` (the unchanged capability block) for the interactive app.
- **The one MCP App:** a self-contained `text/html;profile=mcp-app` resource at `ui://studynexs/class-attendance.html`, served via `resources/read` with a deny-by-default CSP (`csp: {}` — no external origins). It implements the `ui/initialize` handshake, applies host theme CSS variables (with fallbacks), renders loading/empty/error/success, and refreshes via a `tools/call` round-trip **only** when the host advertises `serverTools`. It is **not** `AssistantBlockView.tsx` — that is a Next.js client component requiring a build step and cannot run in the single-file sandbox; it was deliberately **not** reused.
- **No mutation surface.** Only the read-only tool is reachable; any other tool name (e.g. `publish_notice`) is rejected with JSON-RPC `-32601` (`test_unknown_tool_is_rejected`). Governed actions are **not** exposed by this slice. Rendering the app or clicking refresh can never bypass authorization — every refresh is a fresh authenticated `tools/call`.
- **Graceful degradation:** a host without MCP Apps simply shows `content[].text`; the app itself degrades to a neutral message if `ui/initialize` is unanswered.
- **Not built:** no second capability registry, no planner/JEV/Gemma involvement, no workflow re-implementation, no merge with the teacher-copilot `WorkspaceResponse`, no generic MCP platform, no app-registered tools, no external-URL content type.
- **GA blockers (explicit):** (1) **no compatible-host smoke test was run** — the adapter is verified at the protocol/JSON-RPC level with a simulated host (the tests), not against a live Claude/Copilot connector; a real-host smoke test + the `ui/` postMessage lifecycle in a real sandbox remain to be validated before GA. (2) MCP host connections currently rely on the standard Bearer flow; a dedicated connector onboarding/consent + per-connection scoping review is a pre-GA item. (3) Audit of MCP tool calls uses the generic structured log event `mcp_tool_call` + existing audit middleware; a dedicated MCP audit/retention review is recommended before GA.

### 5.12 Question Paper operational hardening (post-Phase-10, separate commit)

Phase 10 made QP generation async but left two production risks, now closed (QP business logic, publication, and the approval lifecycle are **unchanged**):

- **Enqueue failure no longer runs synchronously in production.** `_enqueue_qp_generation` previously fell back to a minutes-long synchronous `generate_paper` on the request path when Arq enqueue failed — reintroducing the exact liability the async conversion removed. Now the synchronous fallback is permitted **only** under `ENVIRONMENT=testing` or `is_development` (so a developer without a running worker can still exercise the flow); in production an enqueue failure raises a clear, **retryable** `WorkflowError` ("Couldn't start question paper generation right now. Please try again…"). No paper is created and no credit is charged — the single reservation lives inside `generate_paper`, which never runs — and the pre-enqueue in-flight idempotency check still guards the retry.
- **Single-owner claim (recovery / single-charge, concurrent-safe).** Arq dispatch is at-least-once **and** multi-worker, so the same job id can be delivered **sequentially** (ack lost after completion → job is terminal) or **concurrently** (two workers grab the same `QUEUED` job at once). A read-then-write guard closes only the sequential case; two concurrent reads both see `QUEUED` and both run `generate_paper` → a **second paper and a second charge**. `run_job` now claims the job with an **atomic conditional UPDATE** (`QUEUED → RUNNING WHERE status = QUEUED`): exactly one caller gets `rowcount == 1` and runs the handler; every other delivery (terminal or concurrent) gets `rowcount == 0` and no-ops (logged `job_claim_skipped` + `redelivery_ignored` metric). This is the same row-conditional discipline the constitution mandates for money (§29/§36) and is generic — it protects every job type, including evaluation. Paper creation + credit reservation remain atomic in the worker's single commit, so a crash *before* commit rolls both back and a clean re-run regenerates exactly once.
- **Stuck-job detection (report-only).** A bounded Arq cron (`sweep_stuck_jobs`, `app/modules/jobs/jobs_health_sweep.py`) flags jobs still `queued` past `JOB_QUEUED_STUCK_SECONDS` (default 300) or `running` past `JOB_RUNNING_STUCK_SECONDS` (default 900), using existing `Job` timestamps. It **logs** (`job_stuck`) and **records the existing platform job metric**; it never mutates, cancels, or retries a job. No monitoring framework was added.
- **Production alerting (wired, deployment-dependent).** Two Prometheus alert rules were added to the existing `infra/observability/prometheus-alerts.yml` on the existing DB-backed `studynexs_job_status_oldest_age_seconds` gauge: `StudyNexsQPJobStuckQueued` (queued >300s, warning) and `StudyNexsQPJobStuckRunning` (running >900s, critical), scoped to `question_paper_generate`. These are real alert *rules* — but they only fire where the deployment actually scrapes `/metrics` and has Alertmanager routing configured. **Code/config verified; not confirmed firing in a live environment** (a GA item, §below). Logged context is PII-free (job id, task, status, age, school id — never student data).
- **Tests:** production enqueue-failure fails fast (no sync, no paper), dev-mode sync fallback still works, the atomic claim lets **concurrent** duplicate delivery run the handler exactly once (`test_job_concurrent_duplicate_delivery_runs_handler_once`, racing 8 deliveries), sequential redelivery of a terminal job no-ops, and the stuck-sweep flags only backdated jobs — alongside the existing idempotency/authorization/single-charge coverage.

---

## 6. Actions (governed state change)

Actions are distinct from read capabilities and from workflows:

```
query      → read governed data (capability / composition)
workflow   → multi-step process with lifecycle
action     → single governed STATE CHANGE
```

An Action must (eventually) carry: authorization, validation, confirmation where risky, **idempotency**, audit, tenant isolation, safe failure. Examples: `mark_absent`, `record_payment`, `send_fee_reminder`, `publish_notice`, `send_parent_message`, **`approve_question_paper`**.

**First consumer (landed, Phase 7):** Parent Intervention's `approve_and_notify` (§5.9) — a server-side, role-gated, re-validated, idempotent, audited, IN_APP-only action. A model-produced `approved=true` NEVER authorizes it; only an authenticated user action does. The boundary is built only as far as this one consumer needs (no generic Action Engine), while cleanly separating `query | workflow | action`.

### 6.1 Second consumer (landed, Phase 8): `publish_notice` — and what the two actions reveal

Publish Notice is the first consumer of the assistant's `act` route (previously a stub). It routes `JEV/Gemma → PlannerDecision(action="act", action_target="publish_notice") → preview → explicit confirm → NoticeService.create_notice`. A new `action_target` field on `PlannerDecision` identifies the action (kept distinct from `tool`/`workflow_id` — an action is neither a capability nor a workflow). The preview validates + authorizes + mints a server-issued `action_token` and **creates nothing**; only an authenticated call to `POST /api/v1/workflows/actions/publish-notice/confirm` publishes. `NoticeService` is reused unchanged.

**Comparison of the two real actions (brief §10) — this is the evidence that shaped how much to extract:**

| Aspect | Parent Intervention notify (§5.9) | Publish Notice (§6.1) |
|---|---|---|
| Shape | workflow draft → per-draft approve | action preview → confirm |
| Pre-confirmation state | **persisted** draft rows (`ParentInterventionDraft`) | **ephemeral** preview (nothing persisted) |
| Human-in-the-loop | approve the persisted draft | confirm the previewed payload |
| Idempotency key | domain unique `(batch, student, parent)` + row-lock | server-issued **`action_token`** ledger (`GovernedActionExecution`) |
| Repeat semantics | re-approve returns the same notification | identical content **may** republish with a *fresh* token |
| Effect | one IN_APP `Notification` per parent | one `Notice` via `NoticeService` |

**What is genuinely shared (and therefore worth naming):** server-side **re-authorization at execution time**, **validation before effect**, **explicit audit row** (same `AuditLog` model), **honest failure** (never a silent success), and **a model can never execute**. These are a consistent *governance pattern*, documented and followed by both.

**What is NOT shared (and therefore deliberately not abstracted):** the idempotency mechanism (domain-unique-key vs. token-ledger) and the state model (persisted draft vs. ephemeral preview) differ for real reasons. Forcing them under one base class would be a wrong abstraction. The only *new shared mechanism* extracted is the `GovernedActionExecution` **token ledger** — and only because the stateless action genuinely needed server-side idempotency that a domain unique key could not provide. Parent Intervention is **not** retrofitted onto it (its domain key already works). **No generic Action Engine / registry / DSL was built** — the two implementations share a pattern and one small ledger, nothing more. A third action would be the point to reconsider a richer abstraction (rule of three).

---

## 7. Structured Result (UI-independent contract)

The service/business layer returns typed blocks and **never generates HTML**. Every assistant turn ends at **one** typed-contract boundary.

### 7.1 The boundary (Phase 9, landed)

`_handle_turn` dispatches a request to exactly one producer (capability / composition / workflow / action / clarification), each of which returns a plain `dict` block. Immediately after the dispatch if-ladder — the single place every path converges — the block passes through:

```python
from app.modules.workspace.assistant.result import validate_block
block = validate_block(block)   # strict=False in production
```

`validate_block` is defined in [`app/modules/workspace/assistant/result.py`](../../apps/api/app/modules/workspace/assistant/result.py). It is **not** a renderer, a framework, or a second abstraction layer — it is a thin validation seam with two jobs: (1) catch schema drift in CI, and (2) emit a stable, known `result_kind` for telemetry/persistence.

**Compatibility guarantee:** `validate_block` returns the **original dict object unchanged** — never a `model_dump`. The wire shape is preserved byte-for-byte (extra/passthrough fields such as domain-status keys on `workflow` survive). This is enforced by `extra="allow"` on every block model and asserted by the contract tests.

### 7.2 Known result kinds (12)

Eleven kinds are produced by the backend today; the twelfth (`action_result`) is produced by the governed-action **confirm** endpoint (not by `_handle_turn`) and is a recognized frontend kind.

| Kind | Produced by | Notes |
|---|---|---|
| `metrics` | capability | title, metrics[{label,value,format?}], source?, href? |
| `table` | capability | columns[], rows[], empty_message? |
| `guide` | fallback / capability | suggestions[{label,href}] |
| `error` | any path | title, message (generic; never leaks internals) |
| `clarify` | planner | options[{id,label}] fed back as a turn |
| `not_found` | capability | title, message |
| `document` | compose/document | citations[{title,document_type,snippet}] |
| `mixed` | compose | data{block} + document{block}\|null |
| `navigate` | capability | href, label |
| `workflow` | workflow runner | workflow_id, workflow_state, summary{}, actions[]; domain-status passthrough |
| `action_preview` | governed action | action, status, preview{}, confirm_action{endpoint,payload,label} |
| `action_result` | confirm endpoint | action, status, created, notice_id?, audience? (**not** a `_handle_turn` block) |

### 7.3 Compatibility policy

- **Production (`strict=False`, default):** unknown kinds and malformed known payloads are **logged and passed through unchanged** — a validation failure never breaks an otherwise successful turn.
- **Tests (`strict=True`):** malformed **known** kinds raise, so schema drift fails CI and cannot become invisible. Unknown kinds still pass through (forward-compatibility — a future kind is not a failure).
- **Frontend mirror:** the `AssistantBlock.kind` union in `assistant-client.ts` lists all twelve kinds plus a trailing `string` for forward-compatibility; `AssistantBlockView.tsx` renders each kind and falls back safely. `action_result` renders success **only** when the backend confirms it (`created === true` / `status === "published"`) — a displayed result never implies success the backend did not report.

### 7.4 Migration path

Adding a new kind is additive and reuse-first: add a block model + entry to `_MODEL_BY_KIND` in `result.py`, a sample to the contract test, a union member + renderer branch on the frontend. No existing producer changes. This is **not** the `type`-discriminated block system in `app/modules/workspace/schemas/blocks.py` — that serves the older teacher-copilot `WorkspaceResponse` surface and remains separate by design.

### 7.5 Rendering surfaces

The same structured result renders through the **Native UI** (chat + traditional surfaces) and, where interoperability is useful, through the **MCP Apps adapter** (Phase 11, §5.11). MCP is an adapter over the governed capability/workflow boundary — it does **not** hold business logic, DB access, semantic interpretation, authorization, or orchestration.

Chat is used where natural-language interaction, follow-up, quick decisions, summarization, action, or workflow initiation help. Traditional web surfaces remain for complex admin, persistent tables, configuration, dashboards, large reports, bulk management, and long forms. StudyNexs is **not** chat-only.

---

## 8. Telemetry & cost (first-class)

Every request exposes (respecting privacy; never log secrets/PII):

```
request_id · tenant_id · user scope · planner (jev|gemma|hybrid) · model/provider ·
JEV confidence · fallback (bool) · execution_type · capability/workflow id ·
workflow_id · latency · tokens · cost · status · error
```

Costs are tracked **separately** by stage — never mixed:

| Stage | What it measures |
|---|---|
| Planning | JEV vs Gemma calls, acceptance rate, fallback rate, tokens, planner-stage cost |
| Workflow reasoning/generation | QP / lesson / remediation / evaluation generation cost |
| RAG | retrieval + embeddings + generation |
| Agentic (future) | model calls + tool calls + retries |

The planner already emits `planner_meta` into the trace; this extends the existing trace, not a parallel telemetry stack.

---

## 9. Security (mandatory on every path)

```
JEV/Gemma → PlannerDecision → governed execution → authorization → service → ERP
```

Never permitted: `model → database`, `agent → raw SQL`, `MCP → raw SQL`, `UI → raw database`. Tenant isolation, authorization, temporal integrity, resolver, derivation, SchoolPack, and audit hold on capability, composition, workflow, action, and agentic paths alike. A **future** agent may use only governed capabilities/tools — never unrestricted DB access — under the same authz/tenant/approval limits.

---

## 10. Implementation roadmap (architecture now, increments real)

Architecture is complete **now**; implementation proceeds one real product feature at a time. No giant refactor.

| Phase | Deliverable | Consumer |
|---|---|---|
| 1 ✅ | JEV confidence-gated hybrid (default-off) | committed `4d82341` |
| 2 | This design of record | — |
| 3 | Generic workflow model + lifecycle (reusable) | — |
| 4 | Question Paper workflow | **first** workflow consumer |
| 5 | Evaluation workflow | same architecture, no QP-copy |
| 6 | Lesson Planning + Remediation | exec mode decided per-workflow |
| 7 | Parent Intervention | workflow + governed action |
| 8 | Governed Actions boundary | QP approval first |
| 9 ✅ | Consolidated Structured Result (typed boundary) | all categories |
| 10 ✅ | Native Chat UX rendering + QP async execution | all categories |
| 11 ✅ | MCP Apps adapter (bounded, read-only slice) | interoperability only |
| 12 | Agentic execution where justified | prove need first; framework only if measured limitation |

**Rule:** each phase must pass the architecture review checklist (real requirement? already represented? reuse a contract? duplicate metadata? bypass governance? needs LLM? could JEV/deterministic do it cheaper? really needs an agent/framework/MCP? complexity vs benefit?). QP proves the boundary; the same architecture then serves Evaluation, Lesson Planning, Remediation, and Parent Intervention.

---

## 11. Responsibility model (canonical terminology)

| Term | Responsibility |
|---|---|
| **JEV** | Fast bounded semantic decision + cost/latency optimization |
| **Gemma** | Complex reasoning, generation, fallback |
| **PlannerDecision** | The one canonical semantic/task representation |
| **Capability** | One deterministic governed business operation |
| **Composition** | Bounded multi-capability analytical execution |
| **Workflow** | First-class multi-step product process (deterministic or agentic) |
| **Action** | Governed state-changing operation |
| **Governed Runtime** | Semantic, authorization, temporal, execution authority |
| **Structured Result** | UI-independent business result |
| **Native UI** | Primary StudyNexs presentation (chat + traditional) |
| **MCP Apps** | Interoperability/UI adapter over the governed boundary |
| **ERP / RAG** | Source of truth |

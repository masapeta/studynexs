# Assistant Execution Architecture — Design of Record

- **Status:** Accepted (design), Implementation in progress (Phases 3–7 landed)
- **Version:** 1.5
- **Date:** 2026-09-28
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

> **Accepted decision — QP will become async before GA.** QP generation currently runs **inline (sync)**, inherited from the existing feature (Phase 4 wrapped it, did not rewrite it). For a customer-scale product a ~2-minute synchronous request is a liability (edge/gateway timeouts, lost work on disconnect, worker starvation during exam season). The correct end state is async, consistent with Evaluation. The workflow model already supports this (the `is_async` flag + `QUEUED→RUNNING→COMPLETED` lifecycle), so the conversion is a **contained change** — an Arq task for `generate_paper`, an enqueue in `_run_question_paper`, and job-status wiring — with **no** change to the planner, registry, or routing. It is deliberately sequenced with **Phase 10 (Native Chat UX)** so the backend async change and the frontend polling/progress UX land and are tested together (rather than a sync-assuming UI over an async backend). Trigger: before general availability / observed exam-season load. Until then `is_async=False` on the `question_paper` definition is honest metadata that matches the inline behavior.

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

---

## 6. Actions (governed state change)

Actions are distinct from read capabilities and from workflows:

```
query      → read governed data (capability / composition)
workflow   → multi-step process with lifecycle
action     → single governed STATE CHANGE
```

An Action must (eventually) carry: authorization, validation, confirmation where risky, **idempotency**, audit, tenant isolation, safe failure. Examples: `mark_absent`, `record_payment`, `send_fee_reminder`, `publish_notice`, `send_parent_message`, **`approve_question_paper`**.

**First consumer (landed, Phase 7):** Parent Intervention's `approve_and_notify` (§5.9) — a server-side, role-gated, re-validated, idempotent, audited, IN_APP-only action. A model-produced `approved=true` NEVER authorizes it; only an authenticated user action does. The boundary is built only as far as this one consumer needs (no generic Action Engine), while cleanly separating `query | workflow | action`. QP/lesson-plan approval remain their existing domain endpoints; whether they migrate onto a shared action abstraction is decided in Phase 8 once a second real action (fee reminders / notices) proves the reusable shape.

---

## 7. Structured Result (UI-independent contract)

The service/business layer returns typed blocks and **never generates HTML**. The consolidated result model supports:

```
text · table · metrics · card · chart · form · approval · progress ·
artifact · navigation · clarification · error
```

The same `StructuredResult` renders through the **Native UI** (chat + traditional surfaces) and, where interoperability is useful, through an **MCP Apps adapter**. MCP is an adapter over the governed capability/workflow boundary — it does **not** hold business logic, DB access, semantic interpretation, authorization, or orchestration.

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
| 9 | Consolidated Structured Result | all categories |
| 10 | Native Chat UX rendering | all categories |
| 11 | MCP Apps adapter | interoperability only |
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

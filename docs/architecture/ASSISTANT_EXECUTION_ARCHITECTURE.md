# Assistant Execution Architecture — Design of Record

- **Status:** Accepted (design), Implementation in progress (Phase 3 landed)
- **Version:** 1.1
- **Date:** 2026-09-26
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
| *workflow* | — | 🔲 not present — Workflow boundary is the new seam |

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

---

## 6. Actions (governed state change)

Actions are distinct from read capabilities and from workflows:

```
query      → read governed data (capability / composition)
workflow   → multi-step process with lifecycle
action     → single governed STATE CHANGE
```

An Action must (eventually) carry: authorization, validation, confirmation where risky, **idempotency**, audit, tenant isolation, safe failure. Examples: `mark_absent`, `record_payment`, `send_fee_reminder`, `publish_notice`, `send_parent_message`, **`approve_question_paper`**.

**First consumer:** QP approval. `approved=true` from a model NEVER authorizes publication — approval is a server-side governed action. We build the Action boundary only as far as QP approval needs it (no large unused action subsystem), while cleanly separating `query | workflow | action`.

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

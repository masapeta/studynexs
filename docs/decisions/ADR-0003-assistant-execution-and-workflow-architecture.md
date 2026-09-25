# ADR-0003: Assistant Execution & Workflow Architecture

- **Status:** Accepted
- **Date:** 2026-09-25
- **Owner:** Avinash Reddy Masapeta (ARM)
- **Subsystem:** Workspace Assistant (`app/modules/workspace/assistant`)
- **Related ADR:** [`ADR-0002-educational-understanding-intelligence-platform-architecture.md`](./ADR-0002-educational-understanding-intelligence-platform-architecture.md)
- **Design of record:** [`../architecture/ASSISTANT_EXECUTION_ARCHITECTURE.md`](../architecture/ASSISTANT_EXECUTION_ARCHITECTURE.md)

---

## Context

The assistant already turns a chat request into a governed, tenant-scoped, typed result for **capability**, **composition**, **mixed**, **document**, **navigate**, and **clarify** paths. The `ACTION` route exists but is a stub, and there is **no workflow path**.

Two decisions had to be locked before further product work:

1. **The planning stage.** A multi-phase investigation (P1.8/P1.9 benchmarks, hardcoding audit, JEV evaluation with a real API, confidence calibration, routing analysis, and a cost analysis on real provider pricing) evaluated whether JEV should augment or replace the Gemma planner.
2. **The execution architecture.** StudyNexs is the full product, so the assistant must host **workflows** (question paper, evaluation, lesson planning, remediation, parent intervention) and **actions** (approve, mark, send, publish) — as first-class categories, not as one-off branches bolted onto capabilities.

Without a locked architecture, each new workflow risks a parallel router, a second semantic model, or a QP-shaped abstraction that cannot serve the other workflows.

Measured evidence (verified): JEV ~17× cheaper per planner call, ~1.8× faster, ~64% lower planner-stage cost at ~30% fallback, with accuracy preserved under a 0.95 confidence gate (holdout 13C/3H/0I; hybrid capability accuracy ≥ Gemma). Real prices: JEV $0.042/Mtok input (output free); Gemma4 $0.14/M in, $0.40/M out.

---

## Decision

1. **Planner is a default-off, config-selected stage.** `PLANNER_BACKEND` ∈ {`gemma` (default), `jev`, `hybrid`} with a configurable `PLANNER_JEV_CONFIDENCE_THRESHOLD` (0.95). Only the planning stage varies; the `PlannerDecision` feeds the identical governed runtime. JEV is the bounded decision + cost/latency layer and is **never** the source of truth. (Committed `4d82341`.)

2. **One canonical execution chain.** `JEV/Gemma → PlannerDecision → execution classification → governed runtime → ERP/RAG → StructuredResult → UI`. Execution categories: **capability, composition, workflow, action, clarification**. Application-controlled dispatch — **no** second/domain router, **no** second semantic model.

3. **Workflows are generic and first-class.** A `WorkflowDefinition` (id, version, input/output contract, `execution_mode`, authorization, approval, audit, timeout/retry/cancel) declares a workflow; a canonical lifecycle (created→queued→running→waiting_for_input→waiting_for_approval→completed/failed/cancelled) governs it. `execution_mode` (`deterministic` | `agentic`) is execution strategy on the WorkflowDefinition — **not** on `CapabilityContract`, and invisible to the router. Reuse existing Arq + service patterns; no separate workflow engine unless proven necessary.

4. **Question Paper is the first workflow consumer, not the definition.** The boundary is built against the real QP feature (`question_paper_service.generate_paper`) and its existing `PaperStatus` lifecycle, without rewriting QP logic — but the abstraction must be reusable for Evaluation, Lesson Planning, Remediation, and Parent Intervention. No QP-specific branch off `PlannerDecision`.

5. **Actions are governed state changes**, distinct from queries and workflows, requiring authorization, validation, idempotency, and audit. QP approval is the first Action consumer; a model-produced `approved=true` never authorizes publication. Build only as far as the first consumer needs.

6. **StructuredResult is UI-independent.** The business layer never emits HTML. One typed result model renders through Native UI (chat + traditional) and, where useful, through an MCP Apps **adapter**. MCP is an interoperability boundary only — no business logic, DB access, semantic interpretation, authorization, or orchestration.

7. **Governance is universal.** Tenant isolation, authorization, temporal integrity, resolver, derivation, SchoolPack, and audit hold on every path. Never `model→DB`, `agent→raw SQL`, `MCP→raw SQL`, or `UI→DB`.

---

## Alternatives considered

- **Pure JEV planner (replace Gemma).** Rejected: capability accuracy 95.7% < Gemma 97.1% bar; JEV must not be the source of truth. Kept as opt-in with confidence-gated fallback instead.
- **Keep Gemma-only.** Rejected as the *default-off* baseline is retained, but ignoring JEV forgoes a proven ~1.8× latency and ~64% planner-stage cost win; hence hybrid is available opt-in.
- **QP-specific assistant path.** Rejected: creates a special case that cannot serve the other four workflows and fractures the taxonomy.
- **`execution_type` on `CapabilityContract`.** Rejected for this phase: conflates a single deterministic operation with a multi-step process; contract stays frozen. Execution mode lives on `WorkflowDefinition`.
- **Adopt an agent framework (Strands/LangGraph/CrewAI) now.** Rejected: no current workflow demonstrates a measured limitation of a deterministic executor; QP is a known pipeline. Revisit only when a genuinely agentic workflow proves the need.
- **MCP as the internal runtime.** Rejected: MCP is an interoperability/UI adapter, not the semantic/governance runtime.

---

## Consequences

**Easier:** adding each new workflow lands at a defined seam with shared lifecycle, authorization, approval, and telemetry; cost is measurable per stage; JEV can be tuned or enabled per environment without code change; the governed runtime stays the single authority.

**Harder / accepted trade-offs:** a distinct `WorkflowDefinition` object is introduced (justified — a workflow is not a capability); hybrid planning adds JEV-every-turn + Gemma-on-fallback (≈1.30 planner calls/turn) — accepted because latency and cost still improve; the 64% cost win is planner-stage only and small in absolute terms at pilot scale (framed honestly, not oversold).

**Neutral:** QP’s existing `PaperStatus` becomes the domain projection of the generic lifecycle; no data migration required to adopt the wrapper.

---

## Rollback strategy

- **Planner:** set `PLANNER_BACKEND=gemma` (the default) — instant, no code change; JEV/hybrid code is dormant. Revert `4d82341` if the flag itself must be removed.
- **Workflow boundary:** it is additive (new classification + generic executor + WorkflowDefinition). If the abstraction proves wrong, QP can fall back to its existing direct service/endpoint path while the boundary is redesigned, since QP logic is unchanged and only *wrapped*.
- **Actions:** the Action boundary replaces a stub (`_action_not_supported`); reverting restores the stub with no data impact.

# StudyNexs Local-First Agentic Workspace Phase 0 Tool-To-Service Mapping

**Status:** Repo-validated Phase 0 planning artifact  
**Scope:** Exact tool-to-service mapping for the approved first slice. No code authorization is implied.  
**Last updated:** 2026-09-04

This artifact sits between the implementation contract pack and code.

Its purpose is to map each approved Phase 0 read tool to existing repository anchors, existing deterministic truth surfaces, and the smallest safe new service boundary where reuse alone is insufficient.

This document does not expand the architecture.

It only answers one question:

Which exact backend and frontend surfaces should each of the three approved Phase 0 tools reuse or wrap?

## 1. Phase 0 Constraints

These constraints are already approved and remain fixed here:

1. small first slice
2. teacher-only
3. text-only
4. read-only
5. exactly one report type
6. exactly three tools
7. zero-model baseline
8. no voice
9. no action tools
10. no approval flows
11. no new academic truth inside tools

## 2. Repo-Validated Baseline

Repo discovery confirmed the following:

1. The teaching route belongs inside the existing teaching shell and navigation surfaces.
2. Teacher scope must reuse the current authorization and staff-scope rules.
3. Existing teaching permissions are likely sufficient for Phase 0.
4. Weak-concept and learning-evidence data already exist in deterministic backend surfaces.
5. Learning-evidence composition currently exists, but part of it is endpoint-local inside the mastery endpoint layer.
6. No workspace backend module exists yet.
7. No `WORKSPACE_*` config surface exists yet.

That leads to one main implementation rule:

Phase 0 should extract or wrap deterministic report composition behind a clean service boundary rather than allow the tool layer to become hidden business logic.

## 3. Mapping Rules

1. Tools are adapters, not truth owners.
2. Tenant and teacher scope come from authenticated backend context only.
3. `teacher_user_id` and `school_id` are injected server-side and must never be accepted from the client request body.
4. If business rules are needed, they belong in a deterministic report or domain service.
5. Navigation tools may return links only to existing deterministic routes.
6. Tools may aggregate deterministic outputs, but they may not create new scoring, evaluation, or academic state.

## 4. Tool-To-Service Mapping

### Tool 1: `resolve_student_in_teacher_scope`

**Purpose**

Resolve one student reference without allowing tenant escape or teacher-scope escape.

**Primary repo anchors**

1. `apps/api/app/core/authorization.py`
2. `apps/api/app/core/staff_permissions.py`
3. `apps/api/app/modules/users/services/permissions_service.py`

**What this tool should reuse**

1. `assert_can_access_student(...)` as the final student access guard.
2. `get_staff_scope(...)` and `StaffScope` for class-incharge and teaching-pair scope semantics.
3. Existing teacher and class-incharge permission shape already surfaced through `UserPermissionsOut`.

**Execution shape**

1. Backend injects `teacher_user_id` and `school_id` from authenticated request context.
2. Tool resolves the student selector against deterministic school-scoped student data.
3. Tool verifies teacher access using the existing authorization and staff-scope rules.
4. Tool returns one typed result, a typed ambiguity result, or a typed permission denial.

**Must not do**

1. accept `teacher_user_id` or `school_id` from client payload
2. broaden scope when resolution is ambiguous
3. query across tenants
4. create a new teacher-scope model

**Phase 0 outcome**

This tool should be a thin adapter over existing authorization and scope logic, with only the minimum new lookup wrapper needed for selector resolution.

### Tool 2: `get_student_learning_evidence_report`

**Purpose**

Return the deterministic first-slice `student_learning_evidence_report` payload.

**Primary repo anchors**

1. `apps/api/app/modules/mastery/endpoints/mastery.py`
2. `apps/api/app/modules/mastery/schemas/mastery.py`
3. `apps/api/app/modules/curriculum/endpoints/graph.py`
4. `apps/api/app/modules/knowledge_graph/services/graph_query_service.py`
5. `apps/api/app/core/authorization.py`

**What this tool should reuse**

1. Existing mastery-ledger and evidence-chain logic from the mastery module.
2. Existing weak-concept retrieval through graph and knowledge-graph services.
3. Existing student access guardrails from `assert_can_access_student(...)`.

**Critical repo finding**

Learning-evidence composition already exists, but part of it is currently endpoint-local inside the mastery endpoint layer.

That means the Phase 0 tool must not own this logic.

**Preferred implementation approach**

1. Extract the endpoint-local learning-evidence composition into a deterministic report service if the extraction is small and safe.
2. If immediate extraction is larger than expected, wrap the current deterministic logic behind a clean service boundary temporarily.

**Preferred option**

Option 1 is preferred.

If extraction is small and safe, Phase 0 should create or reuse a deterministic report service rather than leave composition hidden inside the tool adapter.

**Service ownership rule**

If report composition requires business rules, create or reuse a deterministic report or domain service.

The tool remains only an adapter over that service.

**Execution shape**

1. Backend injects `teacher_user_id` and `school_id` from authenticated request context.
2. Tool verifies student access through existing authorization.
3. Tool calls one deterministic report service boundary.
4. That deterministic service reuses mastery evidence, weak-concept graph evidence, and existing academic read models.
5. Tool converts the deterministic service output into the approved workspace response blocks.

**Must not do**

1. create new scoring logic
2. create new mastery truth
3. use free-text model output as report data
4. bypass existing mastery or graph evidence surfaces
5. keep business-rule composition buried inside the tool layer

**Phase 0 outcome**

This tool should be a thin adapter over a deterministic report service, not a second academic service.

### Tool 3: `get_teacher_navigation_targets`

**Purpose**

Return allowed next destinations back into existing teaching screens.

**Primary repo anchors**

1. `apps/admin-web/src/lib/dashboard-routes.ts`
2. `apps/admin-web/src/lib/permissions.ts`
3. `apps/admin-web/src/lib/nav-groups.ts`
4. `apps/admin-web/src/components/layout/TeachingHubNav.tsx`

**What this tool should reuse**

1. Existing `TEACHING` route constants.
2. Existing teaching route gating semantics.
3. Existing teaching shell and hub navigation structure.

**Execution shape**

1. Backend injects `teacher_user_id` and `school_id` from authenticated request context.
2. Tool returns only navigation-safe actions tied to existing teaching routes.
3. Returned actions must correspond to routes the frontend can already gate through existing permission semantics.

**Must not do**

1. emit workflow actions
2. emit mutation or approval actions
3. invent new route formats
4. bypass existing permission gating expectations

**Phase 0 outcome**

This tool should be a pure navigation adapter over existing route constants and permission rules.

## 5. Recommended Phase 0 Extraction Boundary

The only meaningful new deterministic backend boundary likely needed before the tools is the report-composition surface for `student_learning_evidence_report`.

Recommended shape:

1. a deterministic report or domain service that composes mastery evidence and weak-concept evidence
2. tool adapter above that service
3. workspace response builder above the tool outputs

This keeps the layers clean:

1. domain or report service owns truth assembly
2. tool owns bounded access and typed I/O
3. orchestrator owns sequencing
4. response builder owns workspace envelope and blocks

## 6. Authorized Implementation Order After This Artifact

Once code work is authorized, the safest implementation order is:

1. Pydantic schemas for response envelope and blocks
2. tool metadata contract and registry
3. deterministic report service extraction or wrapper
4. three read tools
5. workspace endpoint
6. frontend TypeScript mirrors and block renderer
7. Teacher Copilot page

This order keeps the contract frozen before orchestration logic and keeps the report truth boundary in place before the tool layer grows.

## 7. Phase 0 Decision

Repo discovery confirms the implementation contract pack.

No further architecture expansion is needed before coding.

The only remaining pre-code artifact was this exact tool-to-service mapping.

After this, the next step is schema conversion when implementation is explicitly authorized.
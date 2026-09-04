# StudyNexs Local-First Agentic Workspace Implementation Contract Pack

**Status:** Phase 0 implementation contract pack  
**Scope:** Companion to the approved architecture plan. No code authorization is implied.  
**Last updated:** 2026-09-04

This document converts the approved architecture in `LOCAL_FIRST_AGENTIC_WORKSPACE_IMPLEMENTATION_PLAN.md` into an implementation baseline.

It exists to remove ambiguity before code begins.

The sequence is:

1. architecture plan
2. implementation contract pack
3. code

## 0. Repo Discovery Gate

This contract pack is not permission to code blindly.

Before implementation begins, validate the planned slice against the current repository anchors below and update this document if any anchor has materially changed.

### Repo-validated anchors

| Concern | Current repo anchor | Validation implication |
|---|---|---|
| Teaching route ownership | `apps/admin-web/src/lib/dashboard-routes.ts` | The first workspace route should extend `TEACHING` inside the existing teaching shell. |
| Teaching navigation ownership | `apps/admin-web/src/lib/nav-groups.ts` | The first entry should be added through the existing teaching navigation group, not a new nav system. |
| Teacher-to-student scope enforcement | `apps/api/app/core/authorization.py` via `assert_can_access_student(...)` | Student resolution and report assembly must reuse the existing teacher scope guardrails. |
| Teaching permission contract | `apps/api/app/modules/users/schemas/permissions.py` and `apps/admin-web/src/lib/permissions.ts` | Phase 0 should reuse existing teaching permission semantics unless technical validation proves a new flag is necessary. |
| Deterministic learning evidence surfaces | `apps/api/app/modules/mastery/endpoints/mastery.py` and `apps/api/app/modules/curriculum/endpoints/graph.py` | The first report tool should compose existing mastery and weak-concept evidence instead of inventing new academic truth. |
| Router registration convention | `apps/api/app/main.py` | The workspace router should follow the existing `include_router(...)` pattern under `/api/v1`. |
| Existing model and embedding config surface | `apps/api/app/core/config.py` | Phase 0 should reuse the existing `AI_*`, `OLLAMA_*`, and `EMBEDDING_*` settings surface; zero-model behavior must not depend on model or embedding keys. |

### Discovery gate rules

1. If a validated anchor changes, amend this contract pack before implementation.
2. If an existing service, endpoint, permission gate, or route constant already satisfies the slice, reuse it before adding a new surface.
3. No file in Sections 6 or 7 should be created until its owning extension point has been confirmed against the repo.
4. Repo validation findings override speculative assumptions in this contract pack.

## 1. First Delivery Slice Specification

### Slice name

Teacher Copilot Read Mode v1

### Delivery shape

This first slice is intentionally narrow:

1. text-only teacher copilot read mode
2. one deterministic report flow
3. structured response envelope
4. zero-model direct retrieval path
5. model-capable but model-optional routing

### Recommended first surface

Use the existing teaching area, not a new portal.

Recommended first route:

`/dashboard/teaching/workspace`

Recommended first label:

`Teacher Copilot`

The existing `/teacher` route already redirects to the dashboard surface, so the first implementation should live inside the established teaching navigation rather than inventing a separate teacher experience.

### Primary user

1. `teacher`
2. `class_incharge`

Do not start with student, parent, or admin action-heavy flows.

### Exact problem this slice solves

The first slice should let a teacher ask for one student learning evidence report in natural language and receive a structured, deterministic answer with citations and allowed navigation targets.

This slice should not try to solve general chat.

### First deterministic report flow

Use a single report type for the first slice:

`student_learning_evidence_report`

This report should answer questions such as:

1. show Aarav's learning report
2. why is Aarav weak in fractions
3. show weak concepts for Aarav
4. show Aarav's mastery evidence

### In-scope behavior

1. Resolve one student inside teacher scope.
2. Return one deterministic student learning evidence report.
3. Return a structured response envelope with typed UI blocks.
4. Support a zero-model path when the request matches the known report flow.
5. Allow local-model normalization only when model routing is enabled and deterministic intent matching is insufficient.
6. Return navigation actions back into existing teaching screens.
7. Keep the first known report path functional even when model credentials are absent.

### Out-of-scope behavior

1. voice input or speech playback
2. draft generation
3. workflow actions
4. approval flows
5. multi-student comparisons
6. open-ended tutoring
7. parent, student, or admin workspace rollout
8. new database truth or new academic scoring logic

### First-slice routing rule

The first slice must attempt routing in this order:

1. explicit deterministic report matcher
2. teacher-scope student resolution
3. zero-model report assembly when the intent is known
4. local-model read-mode normalization only if model routing is enabled and steps 1 to 3 do not fully resolve the request
5. cloud fallback only if the local-model path is needed and fails policy or reliability checks

### First-slice success definition

The slice is successful only if:

1. at least one teacher-scoped report request completes with zero model calls
2. that same known report request remains valid with workspace model routing and cloud fallback disabled
3. the response is fully renderable from typed blocks
4. the result is citation-backed and tenant-scoped
5. the route sends the teacher back to existing mastery, gradebook, or report-card screens instead of inventing new actions

## 2. Response Envelope Schema

This is the concrete backend and frontend contract for the first slice.

### Top-level schema

| Field | Type | Required | First-slice rule |
|---|---|---:|---|
| `schema_version` | `Literal["workspace.response.v1"]` | Yes | Fixed for v1. |
| `request_id` | `UUID` | Yes | User-visible support identifier. |
| `correlation_id` | `str` | Yes | Cross-service trace identifier. |
| `mode` | `Literal["read"]` | Yes | Only `read` is valid in the first slice. |
| `message` | `WorkspaceMessage` | Yes | Short human summary only. |
| `blocks` | `list[WorkspaceBlock]` | Yes | Primary rendering surface. |
| `citations` | `list[WorkspaceCitation]` | Yes | Report evidence only. |
| `actions` | `list[WorkspaceAction]` | Yes | Navigation actions only. |
| `verification` | `WorkspaceVerification` | Yes | Explicit trust state. |
| `warnings` | `list[WorkspaceWarning]` | Yes | For degraded but renderable outcomes. |
| `errors` | `list[WorkspaceError]` | Yes | For blocked or failed outcomes. |
| `approval` | `WorkspaceApproval` | Yes | Always `required=false` in first slice. |
| `data_retention` | `WorkspaceRetention` | Yes | Usually `ephemeral`. |
| `speech` | `WorkspaceSpeech \| None` | Yes | Must be `null` in the first slice. |
| `telemetry` | `WorkspaceTelemetry` | Yes | Must show whether a model was used. |

### Nested schema contracts

#### `WorkspaceMessage`

| Field | Type | Required | Rule |
|---|---|---:|---|
| `title` | `str` | Yes | 120 chars max. |
| `summary` | `str` | Yes | 400 chars max. |
| `tone` | `Literal["informative", "cautious", "blocked"]` | Yes | `informative` for successful read responses. |

#### `WorkspaceVerification`

| Field | Type | Required | Rule |
|---|---|---:|---|
| `status` | `Literal["verified", "stale", "missing", "conflicting", "requires_approval"]` | Yes | First slice should normally return `verified`, `missing`, or `conflicting`. |
| `checked_at` | `datetime \| None` | Yes | `None` only when the report could not be verified. |
| `source_systems` | `list[str]` | Yes | Example: `mastery_service`, `exam_service`. |

#### `WorkspaceApproval`

| Field | Type | Required | Rule |
|---|---|---:|---|
| `required` | `bool` | Yes | Must be `false` in the first slice. |
| `reason` | `str \| None` | Yes | Must be `null` in the first slice. |

#### `WorkspaceRetention`

| Field | Type | Required | Rule |
|---|---|---:|---|
| `retention_class` | `Literal["ephemeral", "audit", "support_case"]` | Yes | Default `ephemeral`. |

#### `WorkspaceSpeech`

| Field | Type | Required | Rule |
|---|---|---:|---|
| `speakable_summary` | `str` | Yes | Not used in first slice. |
| `language` | `str` | Yes | Not used in first slice. |

#### `WorkspaceTelemetry`

| Field | Type | Required | Rule |
|---|---|---:|---|
| `used_model` | `str \| None` | Yes | `null` for zero-model path. |
| `used_fallback` | `bool` | Yes | `false` for zero-model and local-only success. |
| `tool_calls` | `int` | Yes | Bounded by first-slice limits. |
| `tool_failures` | `int` | Yes | Count of timed-out or failed tool attempts. |

Telemetry is operational metadata only.

It must never contain raw user prompts, student names, admission numbers, free-text summaries, citation text, or serialized block payloads.

### First-slice response invariants

1. `mode` must always be `read`.
2. `approval.required` must always be `false`.
3. `speech` must always be `null`.
4. `actions` must contain navigation-only actions.
5. `telemetry.used_model` must be `null` on the zero-model path.
6. `telemetry` must remain no-PII and content-free.

## 3. UI Block Schema

The first slice should use a smaller block vocabulary than the broader architecture plan.

`WorkspaceBlock` is a discriminated union keyed by `type`.

The frontend renderer must dispatch exclusively on `type`, and each block's `payload` must validate against the schema assigned to that `type`.

### Common block base

Every block must include:

| Field | Type | Required | Rule |
|---|---|---:|---|
| `id` | `str` | Yes | Stable within the response. |
| `type` | `str` | Yes | Must match one allowed block type. |
| `title` | `str \| None` | Yes | Optional heading. |
| `priority` | `Literal["primary", "secondary"]` | Yes | Rendering order hint. |
| `payload` | `object` | Yes | Must validate against the payload schema selected by `type`. |

Additional undeclared payload keys should be rejected in `workspace.response.v1`.

### Allowed first-slice blocks

#### `student_card`

Purpose: identify the student the report is about.

Required payload fields:

1. `student_id`
2. `display_name`
3. `class_label`
4. `section_label`
5. `admission_no`

#### `metric_row`

Purpose: show compact academic summary metrics.

Required payload fields:

1. `items`

Each metric item must include:

1. `label`
2. `value`
3. `status` as `normal`, `warning`, or `risk`

#### `table`

Purpose: show weak concepts or recent evidence rows.

Required payload fields:

1. `columns`
2. `rows`
3. `empty_message`

#### `citation_list`

Purpose: show the evidence chain behind the report.

Required payload fields:

1. `items`

Each citation item must include:

1. `label`
2. `source_type`
3. `source_id`
4. `summary`

#### `action_list`

Purpose: route the teacher back into existing deterministic pages.

Required payload fields:

1. `items`

Each action item must include:

1. `label`
2. `action_type` as `navigate`
3. `href`
4. `permission_gate`

#### `error_state`

Purpose: display blocked, missing, or failed outcomes in a typed way.

Required payload fields:

1. `code`
2. `headline`
3. `detail`
4. `retryable`

### Blocks explicitly deferred

Do not implement these in the first slice:

1. `draft_preview`
2. `approval_card`
3. voice-only presentation blocks
4. custom one-off chat cards

## 4. Tool Registry Contract

The tool registry is the main control surface of the first slice.

### Registration metadata

Each registered tool must declare all of the following fields:

| Field | Type | Required | Rule |
|---|---|---:|---|
| `name` | `str` | Yes | Unique registry name. |
| `input_schema` | `type` | Yes | Pydantic schema class. |
| `output_schema` | `type` | Yes | Pydantic schema class. |
| `read_only` | `bool` | Yes | Must be `true` in first slice. |
| `side_effect_level` | `Literal["none", "workflow_request", "approval_required"]` | Yes | Must be `none` in first slice. |
| `requires_human_confirmation` | `bool` | Yes | Must be `false` in first slice. |
| `idempotency_key_required` | `bool` | Yes | Must be `false` in first slice. |
| `allowed_roles` | `list[str]` | Yes | First slice: `teacher`, `class_incharge`. |
| `scope_rule` | `str` | Yes | Teacher scope must be explicit. |
| `audit_event_type` | `str` | Yes | Required for denied, policy-blocked, timeout, ambiguity, and circuit-breaker events. |
| `pii_level` | `Literal["none", "low", "medium", "high"]` | Yes | Student report tools are at least `medium`. |
| `max_payload_size` | `int` | Yes | Hard upper bound in bytes or serialized chars. |
| `tool_result_cache_policy` | `Literal["no_cache", "per_turn", "short_ttl"]` | Yes | No implicit caching. |
| `timeout_ms` | `int` | Yes | Per-tool hard timeout. |
| `retry_count` | `int` | Yes | Read tools only may retry once. |
| `circuit_breaker_threshold` | `int` | Yes | Open after repeated bounded failures. |
| `circuit_breaker_cooldown_seconds` | `int` | Yes | Cooldown before retrying a degraded tool. |

### Registry rules

1. The registry is deny-by-default.
2. Missing metadata is a registration failure.
3. Invalid role or scope configuration is a registration failure.
4. Read tools must not mutate database state.
5. Denied, cross-tenant, policy-blocked, ambiguity, timeout, and circuit-breaker events must emit full audit events.
6. Ordinary successful read-tool executions may emit lighter access telemetry instead of heavyweight audit records unless support escalation or policy requires full audit.
7. Model fallback must not hide verified deterministic failure.

### First-slice operational limits

1. max registered tool types: read tools only
2. max tool calls per turn: 3
3. max serialized tool payload per tool: 16 KB
4. max report blocks per response: 6

## 5. First Read Tools Contract

The first slice should register exactly three read tools.

For every first-slice read tool, `teacher_user_id` and `school_id` are backend-injected execution context fields.

They must never be accepted from the client request body.

### Tool 1: `resolve_student_in_teacher_scope`

Purpose: resolve a student reference without allowing scope escape.

Input fields:

1. `selector` as free text or known identifier
2. `teacher_user_id`
3. `school_id`

Output fields:

1. `student_id`
2. `display_name`
3. `class_label`
4. `section_label`
5. `resolution_method` as `exact`, `alias`, or `admission_no`
6. `verified_scope` as boolean

Contract rules:

1. If multiple students match, return a typed ambiguity error.
2. If the student is out of teacher scope, return a permission-denied result, not a null object.
3. Cache policy: `per_turn`.
4. Timeout: 500 ms.
5. `teacher_user_id` and `school_id` must be injected from authenticated backend context, not client input.

### Tool 2: `get_student_learning_evidence_report`

Purpose: return the deterministic first-slice report payload.

Input fields:

1. `student_id`
2. `teacher_user_id`
3. `school_id`

Output fields:

1. `student`
2. `summary_metrics`
3. `weak_concepts`
4. `recent_assessment_evidence`
5. `citations`
6. `verification_status`

Contract rules:

1. Data must come from deterministic services only.
2. The tool may aggregate from mastery, examinations, curriculum, and knowledge-graph-backed weak-concept services, but it must not embed free-text model output.
3. If report composition requires business rules, create or reuse a deterministic report or domain service; the tool remains only an adapter over that service.
4. Cache policy: `per_turn`.
5. Timeout: 1200 ms.
6. Retry count: 1 only for transient read failures.
7. `teacher_user_id` and `school_id` must be injected from authenticated backend context, not client input.

### Tool 3: `get_teacher_navigation_targets`

Purpose: return allowed next destinations for the teacher.

Input fields:

1. `student_id`
2. `teacher_user_id`
3. `school_id`

Output fields:

1. `actions`

Each action must include:

1. `label`
2. `href`
3. `permission_gate`
4. `enabled`

Contract rules:

1. Only existing deterministic routes may be returned.
2. No action tool requests may be created in the first slice.
3. Cache policy: `short_ttl`.
4. Timeout: 400 ms.
5. `teacher_user_id` and `school_id` must be injected from authenticated backend context, not client input.

### First tools explicitly deferred

Do not implement in the first slice:

1. draft message tools
2. workflow request tools
3. voice tools
4. question-paper tools
5. tutor explanation tools

## 6. Backend File-by-File Plan

The first slice should create only the files it immediately needs.

### Files to create now

| Path | Owns | Must not contain |
|---|---|---|
| `apps/api/app/modules/workspace/endpoints/conversation.py` | Read-only workspace endpoint and dependency wiring | Business logic, direct ORM access, action workflows |
| `apps/api/app/modules/workspace/services/workspace_service.py` | Entry service for one teacher read request | Provider SDK calls, raw SQL, route formatting logic |
| `apps/api/app/modules/workspace/services/session_service.py` | Minimal session lookup or ephemeral session handling | Broad transcript retention logic, approval workflow logic |
| `apps/api/app/modules/workspace/schemas/request.py` | Request schemas for teacher read-mode turns | Response shapes or block rendering logic |
| `apps/api/app/modules/workspace/schemas/response.py` | Top-level response envelope schemas | Tool registration metadata |
| `apps/api/app/modules/workspace/schemas/blocks.py` | Typed block schemas for the first slice | Feature business rules |
| `apps/api/app/modules/ai/orchestration/orchestrator.py` | Read-mode orchestration sequence | Tool implementations, ORM access, approval mutations |
| `apps/api/app/modules/ai/orchestration/router.py` | Zero-model, local-model, and fallback routing policy | HTTP concerns or block formatting |
| `apps/api/app/modules/ai/orchestration/policies.py` | Tenant, role, privacy, and cloud-routing checks | Tool payload assembly |
| `apps/api/app/modules/ai/orchestration/tool_types.py` | Tool protocol, metadata, and enums | Runtime business behavior |
| `apps/api/app/modules/ai/orchestration/tool_registry.py` | Registration, validation, and bounded execution | Intent classification or response rendering |
| `apps/api/app/modules/ai/orchestration/context_builder.py` | Teacher-scoped request context assembly | Model invocation or final response formatting |
| `apps/api/app/modules/ai/orchestration/response_builder.py` | Convert tool outputs into response envelope and blocks | Intent routing or DB access |
| `apps/api/app/modules/ai/orchestration/tools/read/resolve_student_in_teacher_scope.py` | Tool adapter for student resolution | Generic orchestration or response building |
| `apps/api/app/modules/ai/orchestration/tools/read/get_student_learning_evidence_report.py` | Tool adapter for first report | New academic truth logic |
| `apps/api/app/modules/ai/orchestration/tools/read/get_teacher_navigation_targets.py` | Tool adapter for safe next links | Action mutations |
| `apps/api/tests/test_workspace_conversation.py` | Endpoint behavior and response contract | Unrelated module coverage |
| `apps/api/tests/test_workspace_router.py` | Zero-model, local-model, and fallback routing | UI assertions |
| `apps/api/tests/test_workspace_tool_registry.py` | Metadata validation, timeout, retry, circuit breaker | Domain service tests |
| `apps/api/tests/test_workspace_teacher_scope.py` | Tenant isolation and teacher scope enforcement | Generic auth tests unrelated to workspace |

### Existing files to modify

| Path | Change required |
|---|---|
| `apps/api/app/main.py` | Register the workspace router under `/api/v1/workspace`. |
| `apps/api/app/core/config.py` | Add the first-slice workspace settings and flags. |

### Files explicitly deferred

Do not create placeholder files for later phases.

| Path | Reason to defer |
|---|---|
| `apps/api/app/modules/workspace/endpoints/voice.py` | No voice in first slice. |
| `apps/api/app/modules/ai/orchestration/workflow_bridge.py` | No action or approval flows in first slice. |
| `apps/api/app/modules/ai/orchestration/speech_bridge.py` | No voice path in first slice. |
| `apps/api/app/modules/ai/speech/*` | Voice is deferred to a later phase. |

## 7. Frontend File-by-File Plan

The first slice should reuse the existing teaching shell.

### Files to create now

| Path | Owns | Must not contain |
|---|---|---|
| `apps/admin-web/src/app/dashboard/teaching/workspace/page.tsx` | Teacher copilot page composition | Business logic, raw fetch calls |
| `apps/admin-web/src/app/dashboard/teaching/workspace/loading.tsx` | Route skeleton state | Real data access |
| `apps/admin-web/src/components/workspace/WorkspaceShell.tsx` | Page shell and state composition | API request logic |
| `apps/admin-web/src/components/workspace/WorkspaceComposer.tsx` | Text-only prompt input and submit state | Response block rendering rules |
| `apps/admin-web/src/components/workspace/WorkspaceTranscript.tsx` | Turn history rendering | Direct API calls |
| `apps/admin-web/src/components/workspace/WorkspaceBlockRenderer.tsx` | Dispatch blocks by `type` | Business interpretation from raw text |
| `apps/admin-web/src/components/workspace/blocks/StudentCardBlock.tsx` | Student identity block | Generic routing logic |
| `apps/admin-web/src/components/workspace/blocks/MetricRowBlock.tsx` | Summary metric block | Backend contract shaping |
| `apps/admin-web/src/components/workspace/blocks/TableBlock.tsx` | Weak-concept or evidence table block | Feature-level data fetching |
| `apps/admin-web/src/components/workspace/blocks/CitationListBlock.tsx` | Evidence rendering | Permission logic |
| `apps/admin-web/src/components/workspace/blocks/ActionListBlock.tsx` | Navigation action rendering | Action mutation behavior |
| `apps/admin-web/src/components/workspace/blocks/ErrorStateBlock.tsx` | Typed failure rendering | Backend retry logic |
| `apps/admin-web/src/lib/workspace-types.ts` | Shared TypeScript contract mirrors of backend schemas | UI logic |
| `apps/admin-web/src/lib/workspace-client.ts` | Thin wrapper around existing `api()` client for workspace requests | Token lifecycle or custom fetch behavior |

### Existing files to modify

| Path | Change required |
|---|---|
| `apps/admin-web/src/lib/dashboard-routes.ts` | Add `TEACHING.workspace`. |
| `apps/admin-web/src/lib/nav-groups.ts` | Add the Teacher Copilot navigation entry in the existing teaching group when enabled. |
| `apps/admin-web/src/components/layout/TeachingHubNav.tsx` | Add the workspace tab to the existing teaching hub tab strip. |
| `apps/admin-web/src/lib/permissions.ts` | Add route gating for the workspace route, reusing existing teaching permission semantics unless a proven gap requires a new flag. |

### Files explicitly deferred

| Path | Reason to defer |
|---|---|
| `apps/admin-web/src/components/workspace/voice/*` | No voice in first slice. |
| `apps/admin-web/src/components/workspace/blocks/DraftPreviewBlock.tsx` | No draft mode in first slice. |
| `apps/admin-web/src/components/workspace/blocks/ApprovalCardBlock.tsx` | No approval mode in first slice. |
| `apps/admin-web/src/app/parent/**/workspace/*` | Parent rollout is not first. |
| `apps/admin-web/src/app/student/**/workspace/*` | Student rollout is not first. |

## 8. Env and Deployment Contract

The first slice must distinguish between required first-slice configuration and later-phase configuration.

### Required for the deterministic zero-model baseline

| Key | Required | First-slice value or shape | Notes |
|---|---:|---|---|
| `WORKSPACE_ORCHESTRATION_ENABLED` | Yes | `true` in selected environments only | Global feature gate. |
| `WORKSPACE_MODEL_ROUTING_ENABLED` | Yes | `false` for the baseline validation path | Zero-model-first proof should not depend on model availability. |
| `WORKSPACE_CLOUD_FALLBACK_ENABLED` | Yes | `false` for the baseline validation path | Cloud fallback stays off unless explicitly exercised. |
| `WORKSPACE_ACTION_TOOLS_ENABLED` | Yes | `false` | Must stay off. |
| `WORKSPACE_VOICE_ENABLED` | Yes | `false` | Must stay off in first slice. |
| `WORKSPACE_MAX_TOOL_CALLS_PER_TURN` | Yes | `3` | Bound first-slice tool fanout. |
| `WORKSPACE_MAX_MODEL_CALLS_PER_TURN` | Yes | `2` | Bound retry and fallback. |
| `WORKSPACE_MAX_LOCAL_RETRY_COUNT` | Yes | `1` | Local-model retry ceiling. |
| `WORKSPACE_TOOL_TIMEOUT_MS` | Yes | `2500` | Upper bound per tool. |
| `WORKSPACE_TOOL_READ_RETRY_COUNT` | Yes | `1` | Read tool transient retry count. |
| `WORKSPACE_TOOL_CIRCUIT_BREAKER_THRESHOLD` | Yes | `3` | Open after repeated failures. |
| `WORKSPACE_TOOL_CIRCUIT_BREAKER_COOLDOWN_SECONDS` | Yes | `60` | Cooldown window. |
| `WORKSPACE_MAX_INPUT_CHARS` | Yes | `6000` | Input size ceiling. |
| `WORKSPACE_TRANSCRIPT_RETENTION_DAYS` | Yes | `0` | Text retention off by default. |
| `WORKSPACE_AUDIO_RETENTION_HOURS` | Yes | `0` | Audio retention off by default. |

### Required only when local-model routing is enabled

Use the existing AI config surface already present in `apps/api/app/core/config.py`.

| Key | Required when model routing is enabled | First-slice value or shape | Notes |
|---|---:|---|---|
| `AI_DEFAULT_PROVIDER` | Yes | `ollama` or existing approved provider | Reuse the existing platform field; do not make this a zero-model blocker. |
| `AI_DEFAULT_MODEL` | Yes | `qwen2.5:7b` or validated equivalent | Local read-mode normalization candidate. |
| `OLLAMA_BASE_URL` | Yes when `AI_DEFAULT_PROVIDER=ollama` | provider endpoint | Reachable from API runtime. |
| `OLLAMA_MODEL` | Yes when `AI_DEFAULT_PROVIDER=ollama` | `qwen2.5:7b` or pulled model name | Must match the available model. |

### Required only when cloud fallback is enabled

| Key | Required when cloud fallback is enabled | First-slice value or shape | Notes |
|---|---:|---|---|
| `AI_FALLBACK_PROVIDER` | Yes | `openai` or other approved provider | Reuse the existing platform field. |
| `AI_FALLBACK_MODEL` | Yes | `gpt-4o-mini` or validated equivalent | Schema-sensitive fallback candidate. |
| `OPENAI_API_KEY` | Yes when `AI_FALLBACK_PROVIDER=openai` | secret | Not required for the deterministic zero-model baseline. |

### Existing embedding configuration to reuse, but not a zero-model blocker

| Key | Required for deterministic first report path | Current repo-aligned value or shape | Notes |
|---|---:|---|---|
| `EMBEDDING_PROVIDER` | No | `openai` | Keep the existing embeddings path unchanged when embedding-backed retrieval is used later. |
| `EMBEDDING_MODEL` | No | `text-embedding-3-small` | Do not make embeddings a first-slice requirement unless the selected flow actually calls them. |

### Recommended new scoped-rollout keys

| Key | First-slice recommendation |
|---|---|
| `WORKSPACE_ENABLED_PORTALS` | `teaching` |
| `WORKSPACE_ENABLED_ROLES` | `teacher,class_incharge` |
| `WORKSPACE_ENABLED_SCHOOLS` | explicit allowlist only |
| `WORKSPACE_ALLOWED_REPORT_TYPES` | `student_learning_evidence_report` |

### Deferred until voice phase

| Key | First-slice status |
|---|---|
| `SARVAM_ENABLED` | optional, should remain `false` |
| `SARVAM_BASE_URL` | not required yet |
| `SARVAM_API_KEY` | not required yet |
| `SARVAM_STT_ENABLED` | `false` |
| `SARVAM_TTS_ENABLED` | `false` |
| `SARVAM_STT_MODEL` | deferred |
| `SARVAM_TTS_VOICE` | deferred |

### Deployment rules

1. The API must be able to reach Ollama without exposing Ollama publicly.
2. OpenAI egress is required only when cloud fallback or embedding-backed retrieval is enabled.
3. Workspace readiness must not make the whole API fail boot if Ollama is temporarily unavailable.
4. When Ollama is unavailable, zero-model deterministic report flows must still work.
5. Cloud fallback must obey privacy-minimization policy before any sensitive context leaves the local path.

## 9. Test and Acceptance Checklist

This section defines the first-slice validation pack.

### Golden test cases

| Case | Expected behavior | Model use |
|---|---|---|
| `zero_model_without_model_env` | Known teacher report request succeeds with workspace model routing and cloud fallback disabled | No model calls |
| `zero_model_student_learning_report` | Known teacher report request resolves and renders a deterministic report | No model calls |
| `permission_denial_out_of_scope_student` | Teacher cannot query an out-of-scope student; typed error returned | No fallback to broaden access |
| `tenant_isolation_cross_school_lookup` | Cross-tenant student lookup is rejected and audited | No model call |
| `structured_response_schema_valid` | Every successful and blocked response validates against `workspace.response.v1` | Zero, local, or fallback depending on path |
| `local_model_fallback_on_classification_failure` | Ambiguous read request may use local model first, then fallback if local path fails validation | Local then cloud fallback |
| `tool_timeout_graceful_degradation` | Timed-out read tool returns typed warning or error block and audit event | No hidden model substitution |

### Backend validation checklist

1. request schema validation rejects oversize inputs
2. teacher role and class-incharge role gates are enforced
3. zero-model matcher takes priority for the known report flow
4. local-model path never mutates state
5. tool registry rejects incomplete metadata
6. denied, failed, timed-out, and policy-blocked tool attempts emit audit events
7. cloud fallback receives minimized context only

### Frontend validation checklist

1. the page renders without markdown parsing
2. each allowed block type renders from typed data only
3. blocked and timed-out outcomes render through `ErrorStateBlock`
4. navigation actions route into existing teaching pages only
5. the route works inside the existing teaching shell and loading pattern

### First-slice acceptance checklist

The first slice is ready for implementation only when this checklist is stable and agreed:

1. first surface is fixed as teacher copilot read mode
2. first report type is fixed as `student_learning_evidence_report`
3. zero-model routing rule is approved
4. response envelope fields are frozen for v1
5. block vocabulary is frozen for the first slice
6. exactly three first-slice read tools are approved
7. voice remains deferred and disabled
8. action and approval flows remain deferred and disabled
9. env flags and rollout allowlists are approved
10. golden test cases are accepted as the gating baseline
11. deterministic known-report behavior is validated with model routing and cloud fallback disabled
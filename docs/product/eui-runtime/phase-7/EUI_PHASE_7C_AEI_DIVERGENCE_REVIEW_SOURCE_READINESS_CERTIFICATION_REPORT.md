# EUI Runtime Phase 7C Certification Report - AEI Divergence Review and Source Readiness

- **Program:** EUI Runtime Implementation
- **Phase:** Phase 7C - AEI Divergence Review and Source Readiness
- **Authorization ID:** EUI-PH7C-AEI-DIVERGENCE-READINESS-AUTH-001
- **Classification:** Certification report
- **Status:** Ready for ARM review
- **Implementation posture:** Passive/internal review only
- **Date:** 2026-07-28
- **Design baseline:** [`EUI_PHASE_7C_AEI_DIVERGENCE_REVIEW_SOURCE_READINESS_DESIGN_BRIEF.md`](./EUI_PHASE_7C_AEI_DIVERGENCE_REVIEW_SOURCE_READINESS_DESIGN_BRIEF.md)
- **Authorization contract:** [`EUI_PHASE_7C_AEI_DIVERGENCE_REVIEW_SOURCE_READINESS_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md`](./EUI_PHASE_7C_AEI_DIVERGENCE_REVIEW_SOURCE_READINESS_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md)

---

## 1. Certification decision

**Recommendation:** Ready for ARM implementation review.

Phase 7C implementation stayed within the accepted authorization contract.

The implementation introduces:

- internal `AEISourceReadinessScorecard`;
- deterministic `AEIDivergenceReadinessReviewService`;
- fail-closed review posture taxonomy;
- evidence-window evaluation;
- Golden Harness readiness cases;
- focused tests and regression validation.

It does not introduce:

- EUI source-of-truth switching;
- marks, grading, scoring, policy, or teacher review routing changes;
- evidence ledger changes;
- schema changes;
- API changes;
- UI changes;
- Trust Report display;
- persistence;
- LLM/provider calls;
- non-AEI consumer migration.

---

## 2. Changed-file inventory

### Source modules

```text
apps/api/app/modules/eui/schemas/aei_source_readiness.py
apps/api/app/modules/eui/services/aei_divergence_readiness.py
```

### Tests and Golden Harness

```text
apps/api/tests/test_eui_consumer_aei_divergence_readiness.py
apps/api/tests/test_eui_golden_harness.py
apps/api/tests/golden/eui_v1/aei_divergence_readiness_cases.json
```

### Documentation

```text
docs/product/eui-runtime/phase-7/EUI_PHASE_7C_AEI_DIVERGENCE_REVIEW_SOURCE_READINESS_DESIGN_BRIEF.md
docs/product/eui-runtime/phase-7/EUI_PHASE_7C_AEI_DIVERGENCE_REVIEW_SOURCE_READINESS_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md
docs/product/eui-runtime/phase-7/EUI_PHASE_7C_AEI_DIVERGENCE_REVIEW_SOURCE_READINESS_CERTIFICATION_REPORT.md
```

### Protected areas not changed

```text
apps/api/app/core/config.py
apps/api/app/modules/examinations/services/answer_sheet_eval_service.py
apps/api/app/modules/ai/
apps/api/app/modules/knowledge_graph/
apps/api/app/modules/exams/
apps/admin-web/
```

`docs/STATUS.md` was not updated. Per governance, Master Status should be
updated only after certification, commit, tag, and publication.

---

## 3. Architecture and scope review

| Requirement | Result | Evidence |
|---|---:|---|
| Internal scorecard model | PASS | `AEISourceReadinessScorecard` |
| Deterministic review service | PASS | `AEIDivergenceReadinessReviewService` |
| Golden Harness readiness cases | PASS | `aei_divergence_readiness_cases.json` |
| Passive/internal evidence only | PASS | No runtime source hook introduced |
| No source switch | PASS | `source_switch_active: Literal[False]` |
| No marks/routing/ledger/API/UI/schema changes | PASS | Changed-file inventory and scans |
| No LLM/provider call | PASS | Static scan |
| No persistence/write path | PASS | Static scan |

---

## 4. Scorecard model validation

`AEISourceReadinessScorecard` is:

- strict (`extra="forbid"`);
- frozen/immutable;
- JSON-serializable;
- internal-only;
- non-authoritative;
- source-switch-inactive by type contract.

Validation evidence:

- unknown top-level fields are rejected;
- mutation is rejected;
- `source_switch_active=True` is rejected;
- `eligible=True` requires `review_posture="eligible"`;
- `review_posture="eligible"` rejects blocker categories.

---

## 5. Deterministic review service validation

The review service consumes only already-collected Phase 7A/7B comparison
evidence.

It does not:

- query the database;
- write data;
- inspect raw answers;
- inspect uploaded content;
- call LLMs;
- call external providers;
- alter AEI/evaluation output.

### Review posture precedence

The implementation fails closed:

```text
blocked_unsafe
    >
blocked_product_impacting
    >
needs_more_evidence when evidence window is insufficient
    >
needs_capability_work
    >
needs_more_evidence
    >
eligible
```

### Blocker rules

| Evidence condition | Result |
|---|---|
| Unsafe divergence | `blocked_unsafe` |
| Trust Report visibility not `internal_only` | `blocked_unsafe` |
| Tenant mismatch | `blocked_unsafe` |
| Product-impacting divergence | `blocked_product_impacting` |
| Missing required EUI evidence | `needs_capability_work` |
| Insufficient evidence window | `needs_more_evidence` |
| Unsupported/manual-review capability posture | `needs_capability_work` |
| Equivalent/richer evidence with sufficient clean window | `eligible` |

---

## 6. Feature flag and source-flag posture

Phase 7C did not introduce a new feature flag.

Existing flags remain unchanged:

```text
EUI_CONSUMER_AEI_DUAL_READ_ENABLED=false
EUI_CONSUMER_AEI_RICH_EVIDENCE_ENABLED=false
EUI_CONSUMER_AEI_SOURCE_ENABLED=false
```

The source flag remains inert.

The Phase 7C service records whether a comparison had
`source_flag_enabled=True`, but the resulting scorecard keeps:

```text
source_switch_active = False
authoritative = False
internal_only = True
```

No source-readiness behavior is activated by this phase.

---

## 7. Golden Harness evidence

Added:

```text
apps/api/tests/golden/eui_v1/aei_divergence_readiness_cases.json
```

Coverage includes:

- eligible repeated evidence;
- insufficient evidence window;
- missing EUI evidence;
- product-impacting divergence;
- unsafe divergence;
- manual-review capability posture;
- unsafe Trust Report visibility.

The Golden Harness test verifies deterministic scorecard IDs, expected review
postures, blocker categories, internal-only posture, and source-switch
inactivity.

---

## 8. Validation results

### 8.1 Focused Ruff

Command:

```text
python -m ruff check app/modules/eui/schemas/aei_source_readiness.py app/modules/eui/services/aei_divergence_readiness.py tests/test_eui_consumer_aei_divergence_readiness.py tests/test_eui_golden_harness.py
```

Result:

```text
PASS - All checks passed
```

### 8.2 Focused Phase 7C tests and Golden Harness

Command:

```text
pytest tests/test_eui_consumer_aei_divergence_readiness.py tests/test_eui_golden_harness.py -q
```

Result:

```text
20 passed
```

### 8.3 Phase 7A/7B regression

Command:

```text
pytest tests/test_eui_consumer_aei_migration.py tests/test_eui_consumer_aei_migration_model.py tests/test_eui_consumer_aei_rich_evidence.py -q
```

Result:

```text
21 passed
```

### 8.4 AEI passive integration regression

Command:

```text
pytest tests/test_aei_passive_integration.py -q
```

Result:

```text
7 passed
```

### 8.5 EUI Trust Framework regression

Command:

```text
pytest tests/test_eui_trust_report_builder.py tests/test_eui_trust_passive.py -q
```

Result:

```text
10 passed
```

### 8.6 Answer-sheet evaluation regression

Command:

```text
pytest tests/test_answer_sheet_eval.py -q
```

Result:

```text
13 passed
```

### 8.7 Evaluation engine regression

Command:

```text
pytest tests/test_evaluation_engine.py -q
```

Result:

```text
8 passed
```

### 8.8 API import

Command:

```text
python -c "import app.main; print('api import ok')"
```

Result:

```text
api import ok
```

### 8.9 Whitespace diff check

Command:

```text
git diff --check
```

Result:

```text
PASS
```

---

## 9. Static boundary scans

### 9.1 No source-switch activation in implementation modules

Command:

```text
rg -n "source_switch_active\s*=\s*True|source_switch_active=True|EUI_CONSUMER_AEI_SOURCE_ENABLED.*True|source_enabled.*activate|source.*activated" apps/api/app/modules/eui/schemas/aei_source_readiness.py apps/api/app/modules/eui/services/aei_divergence_readiness.py
```

Result:

```text
PASS - no source-switch activation patterns found in implementation modules
```

The focused test file intentionally constructs `source_switch_active=True` once
to prove the model rejects it.

### 9.2 No persistence/session/write path

Command:

```text
rg -n "db\.add\(|session\.add\(|\.commit\(|\.flush\(|\.delete\(|session\.execute\(|db\.execute\(|AsyncSession|Session|select\(|insert\(|update\(|delete\(" apps/api/app/modules/eui/schemas/aei_source_readiness.py apps/api/app/modules/eui/services/aei_divergence_readiness.py
```

Result:

```text
PASS - no persistence/session/write patterns found
```

### 9.3 No LLM/provider call

Command:

```text
rg -n "openai|anthropic|gemini|llm|LLM|completion|responses\.create|generate_llm|gateway" apps/api/app/modules/eui/schemas/aei_source_readiness.py apps/api/app/modules/eui/services/aei_divergence_readiness.py
```

Result:

```text
PASS - no LLM/provider call patterns found
```

### 9.4 No API/UI/Trust-display exposure

Command:

```text
rg -n "APIRouter|@router|router\.|Response|HTML|display|Trust Report|trust_report.*display|admin-web|teacher-facing|parent-facing|student-facing" apps/api/app/modules/eui/schemas/aei_source_readiness.py apps/api/app/modules/eui/services/aei_divergence_readiness.py apps/api/tests/test_eui_consumer_aei_divergence_readiness.py
```

Result:

```text
PASS - no API/UI/Trust-display exposure patterns found
```

### 9.5 No schema/migration patterns

Command:

```text
rg -n "alembic|op\.add_column|op\.create_table|mapped_column\(|relationship\(|ForeignKey\(" apps/api/app/modules/eui/schemas/aei_source_readiness.py apps/api/app/modules/eui/services/aei_divergence_readiness.py apps/api/tests/test_eui_consumer_aei_divergence_readiness.py
```

Result:

```text
PASS - no schema/migration patterns found
```

---

## 10. Rollback proof

Phase 7C introduced no source hook, schema, API, UI, persistence, or source
switch.

Rollback posture:

- remove or ignore the internal review service;
- existing Phase 7A dual-read remains unchanged;
- existing Phase 7B rich evidence binding remains unchanged;
- `EUI_CONSUMER_AEI_SOURCE_ENABLED` remains inert;
- no data rollback is required;
- no schema rollback is required.

Regression evidence confirms evaluation behavior remains unchanged.

---

## 11. Product behavior review

| Product surface | Status |
|---|---|
| Marks | Unchanged |
| Grading | Unchanged |
| Teacher review routing | Unchanged |
| Evidence ledger | Unchanged |
| API | Unchanged |
| UI | Unchanged |
| Student/parent/principal views | Unchanged |
| Trust Report display | Not introduced |
| Source of truth | Existing AEI/evaluation remains source |

---

## 12. Retrospective

### What held

- The Phase 7A/7B comparison contracts were sufficient for Phase 7C.
- No runtime hook was needed to implement deterministic readiness review.
- Keeping readiness as a pure service reduced risk and improved auditability.

### What surprised us

- The existing comparison model already carried enough source-flag and blocker
  evidence to avoid touching the evaluation integration hook.

### What should Phase 7D consider

- Phase 7D should not begin with a source switch. It should first define the
  narrowest possible source-readiness candidate, likely context/evidence-only.
- Any Phase 7D source-readiness work should consume Phase 7C scorecards rather
  than re-evaluating raw divergence evidence.

---

## 13. Final recommendation

Phase 7C is ready for ARM implementation review.

Recommended ARM decision:

```text
Accepted for commit, if ARM review confirms the diff matches this report.
```

Recommended commit metadata after ARM acceptance:

```text
Commit: feat(eui): add AEI divergence readiness review foundation
Tag: eui-runtime-phase7c-aei-divergence-readiness-certified
```

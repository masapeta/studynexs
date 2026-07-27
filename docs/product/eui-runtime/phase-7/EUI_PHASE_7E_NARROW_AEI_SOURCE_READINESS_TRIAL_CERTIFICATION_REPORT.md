# EUI Runtime Phase 7E Certification Report - Narrow AEI Source Readiness Trial

- **Program:** EUI Runtime Implementation
- **Phase:** Phase 7E - Narrow AEI Source Readiness Trial
- **Authorization ID:** EUI-PH7E-NARROW-AEI-SOURCE-READINESS-TRIAL-AUTH-001
- **Classification:** Certification report
- **Status:** Accepted
- **Date:** 2026-07-28
- **Implementation commit:** Pending ARM acceptance
- **Recommended commit:** `feat(eui): add narrow AEI source-readiness trial foundation`
- **Recommended tag:** `eui-runtime-phase7e-narrow-aei-source-readiness-trial-certified`

---

## 1. Executive decision

Phase 7E implementation has been accepted by ARM for commit.

Certification result:

```text
PASS - accepted by ARM for commit
```

The implementation introduces an internal, deterministic, non-authoritative AEI
source-readiness trial foundation for the narrow `context_metadata_only` scope.

It does not switch AEI to EUI as source of truth.

---

## 2. Authorization scope review

Authorized by:

```text
EUI_PHASE_7E_NARROW_AEI_SOURCE_READINESS_TRIAL_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md
```

Implemented:

- internal AEI source-readiness trial result model;
- deterministic source-readiness trial service;
- trial state taxonomy;
- deterministic trial ID generation;
- source-switch attempt blocking;
- legacy AEI source-of-truth confirmation;
- Golden Harness trial cases;
- focused tests;
- certification evidence.

Not implemented:

- source switch;
- marks, grading, scoring, policy, or teacher review routing changes;
- evidence ledger changes;
- schema changes;
- API changes;
- UI changes;
- Trust Report display;
- non-AEI consumer migration;
- LLM/provider calls;
- persistence or background workers.

Scope compliance:

```text
PASS
```

---

## 3. Changed-file inventory

Source:

```text
apps/api/app/modules/eui/schemas/aei_source_readiness.py
apps/api/app/modules/eui/services/aei_source_readiness_trial.py
```

Tests and Golden Harness:

```text
apps/api/tests/test_eui_consumer_aei_source_readiness_trial.py
apps/api/tests/test_eui_golden_harness.py
apps/api/tests/golden/eui_v1/aei_source_readiness_trial_cases.json
```

Documentation:

```text
docs/product/eui-runtime/phase-7/EUI_PHASE_7E_NARROW_AEI_SOURCE_READINESS_TRIAL_DESIGN_BRIEF.md
docs/product/eui-runtime/phase-7/EUI_PHASE_7E_NARROW_AEI_SOURCE_READINESS_TRIAL_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md
docs/product/eui-runtime/phase-7/EUI_PHASE_7E_NARROW_AEI_SOURCE_READINESS_TRIAL_CERTIFICATION_REPORT.md
```

No migrations, routers, UI files, AEI source files, or evidence ledger modules
were modified.

---

## 4. Trial result model validation

Model:

```text
AEISourceReadinessTrialResult
```

Validated properties:

- immutable;
- strict top-level shape (`extra="forbid"`);
- JSON-serializable;
- internal-only;
- non-authoritative;
- source switch active is literal false;
- ready trial results require a candidate reference;
- ready trial results are limited to `context_metadata_only`;
- ready trial results cannot carry blocked evidence classes;
- ready trial results require legacy source-of-truth confirmation.

Result:

```text
PASS
```

---

## 5. Deterministic trial service validation

Service:

```text
AEISourceReadinessTrialService
```

Validated behavior:

- consumes Phase 7D source-readiness candidates;
- produces deterministic trial IDs;
- maps ready narrow candidates to `trial_ready`;
- maps insufficient evidence to `trial_not_ready`;
- maps product-impacting candidates to `trial_blocked_product_impacting`;
- maps unsafe candidates to `trial_blocked_unsafe`;
- blocks broad candidate scopes;
- blocks source-switch attempts while keeping `source_switch_active=false`;
- skips disabled or missing-candidate trials;
- records only bounded internal metadata;
- records operational metrics.

Result:

```text
PASS
```

---

## 6. Golden Harness evidence

Added:

```text
apps/api/tests/golden/eui_v1/aei_source_readiness_trial_cases.json
```

Golden cases cover:

- ready internal trial;
- insufficient evidence;
- broad scope blocked;
- source-switch attempt blocked;
- disabled missing-candidate trial;
- trial ID determinism;
- non-authoritative posture.

Validation:

```text
python -m pytest tests/test_eui_consumer_aei_source_readiness_trial.py \
  tests/test_eui_golden_harness.py -q
```

Result:

```text
21 passed in 0.59s
```

Golden Harness result:

```text
PASS
```

---

## 7. Source-switch inertness proof

Phase 7E does not add a new runtime hook or enable source switching.

Validated:

- source flag may be recorded as enabled/inert;
- source switch active remains false;
- source-switch request produces `trial_blocked_unsafe`;
- legacy AEI source-of-truth confirmation is required for ready trials;
- no source behavior is activated.

Result:

```text
PASS
```

---

## 8. No behavior-change proof

The implementation is not wired into production evaluation.

No changes were made to:

- `answer_sheet_eval_service.py`;
- evaluation result computation;
- marks;
- grading;
- policy;
- teacher review routing;
- evidence ledger behavior;
- API;
- UI.

Regression validation:

```text
python -m pytest tests/test_eui_consumer_aei_migration.py \
  tests/test_eui_consumer_aei_rich_evidence.py \
  tests/test_eui_consumer_aei_divergence_readiness.py \
  tests/test_eui_consumer_aei_source_readiness_candidate.py \
  tests/test_eui_consumer_aei_source_readiness_trial.py \
  tests/test_eui_trust_report_builder.py \
  tests/test_eui_trust_passive.py \
  tests/test_aei_passive_integration.py \
  tests/test_evaluation_engine.py \
  tests/test_answer_sheet_eval.py \
  tests/test_eui_golden_harness.py -q
```

Result:

```text
94 passed in 109.45s
```

Behavior-change proof:

```text
PASS
```

---

## 9. Static safety scans

Focused Ruff:

```text
python -m ruff check \
  app/modules/eui/schemas/aei_source_readiness.py \
  app/modules/eui/services/aei_source_readiness_trial.py \
  tests/test_eui_consumer_aei_source_readiness_trial.py \
  tests/test_eui_golden_harness.py
```

Result:

```text
All checks passed
```

Whitespace:

```text
git diff --check
```

Result:

```text
PASS
```

API import:

```text
python -c "import app.main; print('API_IMPORT_PASS')"
```

Result:

```text
API_IMPORT_PASS
```

Source-switch activation scan:

```text
source_switch_active=True
```

Implementation result:

```text
PASS - no implementation activation; only a negative model-validation test
```

Persistence/write scan:

```text
db.add / session.add / commit / flush / insert / update / delete / ledger.write
```

Implementation result:

```text
PASS - no implementation match
```

LLM/provider-call scan:

```text
OpenAI / Anthropic / Gemini / ollama / chat.completions / provider.generate
```

Implementation result:

```text
PASS - no implementation match
```

API/router exposure scan:

```text
APIRouter / @router / response_model / Depends
```

Implementation result:

```text
PASS - no implementation match
```

Static safety result:

```text
PASS
```

---

## 10. Raw-content capture proof

Phase 7E implementation stores only bounded metadata:

- trial ID;
- tenant ID;
- subject type;
- scope reference;
- candidate reference;
- candidate scope;
- trial mode;
- trial state;
- evidence class labels;
- source flag posture;
- rollback posture;
- internal metadata.

It does not store:

- raw student answers;
- OCR text;
- uploaded document content;
- teacher free text;
- student/parent names;
- tenant slugs;
- public product claims.

The focused tests intentionally attempt a forbidden top-level `student_answer`
field and verify model rejection.

Result:

```text
PASS
```

---

## 11. Performance and query budget

Phase 7E trial creation is O(1) over an already-produced Phase 7D candidate.

It performs:

- no database queries;
- no per-question traversal;
- no per-upload traversal;
- no background job scheduling;
- no external service calls.

Result:

```text
PASS
```

---

## 12. Rollback proof

Because no runtime hook was introduced, rollback is structural:

- remove/ignore the trial service;
- no persisted trial data exists;
- no schema rollback is required;
- no API/UI rollback is required;
- AEI remains source of truth.

If a future hook is added under separate authorization, rollback must be proven
again through feature-flag disablement.

Result:

```text
PASS
```

---

## 13. Validation summary

| Check | Result |
|---|---|
| Focused Phase 7E + Golden Harness tests | 21 passed |
| Phase 7A/7B/7C/7D/7E + Trust + AEI/evaluation regression | 94 passed |
| Focused Ruff | PASS |
| API import | PASS |
| git diff --check | PASS |
| Source-switch activation scan | PASS |
| Persistence/write scan | PASS |
| LLM/provider-call scan | PASS |
| API/router exposure scan | PASS |
| Raw-content capture proof | PASS |

---

## 14. Explicitly unchanged

The following remain unchanged:

- AEI source of truth;
- evaluation result generation;
- marks;
- grading;
- scoring;
- policy decisions;
- teacher review routing;
- evidence ledger behavior;
- public API;
- UI;
- database schema;
- non-AEI consumers;
- product capability claims.

---

## 15. Retrospective

What held:

- Phase 7D candidates were sufficient as the input contract for 7E trial
  results.
- The trial layer could be implemented without touching runtime evaluation.
- The ready/not-ready/blocked taxonomy remained deterministic.

What surprised us:

- Missing-candidate trial output still needs explicit tenant/subject/scope
  context to avoid silently producing ambiguous internal artifacts.

Carry-forward guidance:

- Do not treat `trial_ready` as source adoption.
- Any actual AEI source switch requires a separate design brief,
  authorization contract, runtime feature flag, certification, and ARM review.
- Keep source-readiness trial evidence internal until a later consumer-visible
  authorization explicitly permits exposure.

---

## 16. Recommendation

ARM recommendation:

```text
Accepted for commit.
```

If ARM accepts the implementation, proceed with:

```text
Commit: feat(eui): add narrow AEI source-readiness trial foundation
Tag: eui-runtime-phase7e-narrow-aei-source-readiness-trial-certified
```

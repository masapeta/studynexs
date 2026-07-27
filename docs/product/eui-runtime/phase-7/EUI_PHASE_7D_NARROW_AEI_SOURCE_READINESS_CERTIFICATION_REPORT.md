# EUI Runtime Phase 7D Certification Report - Narrow AEI Source Readiness

- **Program:** EUI Runtime Implementation
- **Phase:** Phase 7D - Narrow AEI Source Readiness
- **Authorization ID:** EUI-PH7D-NARROW-AEI-SOURCE-READINESS-AUTH-001
- **Classification:** Certification report
- **Status:** Accepted
- **Date:** 2026-07-28
- **Implementation commit:** Pending ARM acceptance
- **Recommended commit:** `feat(eui): add narrow AEI source-readiness candidate foundation`
- **Recommended tag:** `eui-runtime-phase7d-narrow-aei-source-readiness-certified`

---

## 1. Executive decision

Phase 7D implementation is ready for ARM review.

Certification result:

```text
PASS - accepted by ARM for commit
```

The implementation introduces an internal, deterministic, non-authoritative AEI
source-readiness candidate foundation for the narrow
`context_metadata_only` scope.

It does not switch AEI to EUI as source of truth.

---

## 2. Authorization scope review

Authorized by:

```text
EUI_PHASE_7D_NARROW_AEI_SOURCE_READINESS_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md
```

Implemented:

- internal AEI source-readiness candidate model;
- deterministic source-readiness candidate service;
- candidate state taxonomy;
- deterministic candidate ID generation;
- source flag inertness;
- Golden Harness candidate cases;
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
apps/api/app/modules/eui/services/aei_source_readiness_candidate.py
```

Tests and Golden Harness:

```text
apps/api/tests/test_eui_consumer_aei_source_readiness_candidate.py
apps/api/tests/test_eui_golden_harness.py
apps/api/tests/golden/eui_v1/aei_source_readiness_candidate_cases.json
```

Documentation:

```text
docs/product/eui-runtime/phase-7/EUI_PHASE_7D_NARROW_AEI_SOURCE_READINESS_DESIGN_BRIEF.md
docs/product/eui-runtime/phase-7/EUI_PHASE_7D_NARROW_AEI_SOURCE_READINESS_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md
docs/product/eui-runtime/phase-7/EUI_PHASE_7D_NARROW_AEI_SOURCE_READINESS_CERTIFICATION_REPORT.md
```

No migrations, routers, UI files, AEI source files, or evidence ledger modules
were modified.

---

## 4. Candidate model validation

Model:

```text
AEISourceReadinessCandidate
```

Validated properties:

- immutable;
- strict top-level shape (`extra="forbid"`);
- JSON-serializable;
- internal-only;
- non-authoritative;
- source switch active is literal false;
- ready candidates require eligible scorecard posture;
- ready candidates are limited to `context_metadata_only`;
- ready candidates cannot carry blocked evidence classes.

Result:

```text
PASS
```

---

## 5. Deterministic candidate service validation

Service:

```text
AEISourceReadinessCandidateService
```

Validated behavior:

- consumes Phase 7C scorecards;
- produces deterministic candidate IDs;
- maps eligible scorecards to `ready_for_internal_trial`;
- maps insufficient evidence to `not_ready_more_evidence`;
- maps capability gaps to `not_ready_capability_work`;
- maps product-impacting blockers to `blocked_product_impacting`;
- maps unsafe blockers to `blocked_unsafe`;
- blocks broad candidate scopes;
- blocks source-switch attempts while keeping `source_switch_active=false`;
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
apps/api/tests/golden/eui_v1/aei_source_readiness_candidate_cases.json
```

Golden cases cover:

- ready internal candidate;
- insufficient evidence;
- capability work required;
- product-impacting blocker;
- unsafe blocker;
- broad scope blocked;
- source-switch attempt blocked;
- candidate ID determinism;
- non-authoritative posture.

Validation:

```text
python -m pytest tests/test_eui_golden_harness.py -q
```

Result:

```text
10 passed in 0.32s
```

Golden Harness result:

```text
PASS
```

---

## 7. Feature flag and source-flag inertness proof

No new runtime feature flag was required for Phase 7D because no runtime hook
was introduced.

Existing Phase 7 flags remain unchanged:

```text
EUI_CONSUMER_AEI_DUAL_READ_ENABLED=false
EUI_CONSUMER_AEI_RICH_EVIDENCE_ENABLED=false
EUI_CONSUMER_AEI_SOURCE_ENABLED=false
```

Validated:

- source flag may be recorded as enabled/inert;
- source switch active remains false;
- source-switch attempt produces `blocked_unsafe`;
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
  tests/test_eui_trust_report_builder.py \
  tests/test_eui_trust_passive.py \
  tests/test_aei_passive_integration.py \
  tests/test_evaluation_engine.py \
  tests/test_answer_sheet_eval.py \
  tests/test_eui_golden_harness.py -q
```

Result:

```text
83 passed in 113.39s
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
  app/modules/eui/services/aei_source_readiness_candidate.py \
  tests/test_eui_consumer_aei_source_readiness_candidate.py \
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
PASS - no implementation match
```

Persistence/write scan:

```text
db.add / session.add / commit / flush / insert / delete / ledger.write
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

Phase 7D implementation stores only bounded metadata:

- candidate ID;
- tenant ID;
- subject type;
- scope reference;
- candidate scope;
- readiness scorecard reference;
- candidate state;
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

The focused tests intentionally attempt a forbidden top-level
`student_answer` field and verify model rejection.

Result:

```text
PASS
```

---

## 11. Performance and query budget

Phase 7D candidate creation is O(1) over an already-produced Phase 7C
scorecard.

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

- remove/ignore the candidate service;
- no persisted candidate data exists;
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
| Focused Phase 7D tests | 9 passed |
| Golden Harness | 10 passed |
| Phase 7A/7B/7C/7D + Trust + AEI/evaluation regression | 83 passed |
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

- Phase 7C scorecards were sufficient as the input contract for 7D.
- The candidate layer could be implemented without touching runtime evaluation.
- No new feature flag was necessary because no hook was introduced.

What surprised us:

- Broad-scope attempts are best represented as blocked candidates rather than
  exceptions, because that gives the Golden Harness a deterministic fail-closed
  artifact.

Carry-forward guidance:

- Do not treat `ready_for_internal_trial` as source adoption.
- Phase 7E, if authorized, should remain narrower than a full AEI source switch.
- Any consumer-visible use of candidate output requires a separate design brief
  and implementation authorization contract.

---

## 16. Recommendation

ARM recommendation:

```text
Accepted for commit.
```

If ARM accepts the implementation, proceed with:

```text
Commit: feat(eui): add narrow AEI source-readiness candidate foundation
Tag: eui-runtime-phase7d-narrow-aei-source-readiness-certified
```

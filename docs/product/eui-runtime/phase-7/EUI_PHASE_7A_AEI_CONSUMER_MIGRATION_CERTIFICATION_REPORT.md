# EUI Phase 7A Certification Report - AEI Consumer Migration

- **Program:** EUI Runtime Implementation
- **Phase:** Phase 7A - AEI Consumer Migration
- **Authorization ID:** EUI-PH7A-AEI-DUAL-READ-AUTH-001
- **Classification:** Implementation certification report
- **Status:** Implementation complete; pending ARM acceptance
- **Date:** 2026-07-27
- **Design baseline:** [`EUI_PHASE_7_CONSUMER_MIGRATION_DESIGN_BRIEF.md`](./EUI_PHASE_7_CONSUMER_MIGRATION_DESIGN_BRIEF.md)
- **Implementation contract:** [`EUI_PHASE_7A_AEI_CONSUMER_MIGRATION_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md`](./EUI_PHASE_7A_AEI_CONSUMER_MIGRATION_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md)
- **Commit:** Pending ARM acceptance
- **Tag:** Pending ARM acceptance

---

## 1. Certification decision

Phase 7A is ready for ARM implementation review.

The implementation introduces AEI passive dual-read comparison only. It does
not change marks, grading, policy, teacher review routing, evidence ledger
output, API, UI, schema, Trust Report display, or source-of-truth behavior.

Recommended ARM decision:

```text
Accepted for commit, subject to ARM review of this implementation diff.
```

---

## 2. Scope implemented

Authorized scope implemented:

- canonical AEI consumer migration comparison model;
- deterministic difference classification;
- AEI compatibility adapter;
- bounded in-memory passive capture registry;
- passive dual-read observer;
- default-off dual-read feature flag;
- inert source feature flag;
- single guarded answer-sheet evaluation hook;
- Golden Harness cases;
- focused model, adapter, observer, Golden Harness, and regression tests.

Repository naming note:

The implementation contract referred to `apps/api/app/modules/evaluations/`.
The existing repository module for answer-sheet evaluation is
`apps/api/app/modules/examinations/`. The implementation therefore uses the
existing `examinations` module and adds only one guarded, default-off passive
hook in `answer_sheet_eval_service.py`.

---

## 3. Files changed

Implementation files:

```text
apps/api/app/core/config.py
apps/api/app/modules/eui/schemas/aei_consumer_migration.py
apps/api/app/modules/eui/services/aei_consumer_migration.py
apps/api/app/modules/examinations/services/answer_sheet_eval_service.py
```

Test and Golden Harness files:

```text
apps/api/tests/golden/eui_v1/aei_consumer_migration_cases.json
apps/api/tests/test_eui_consumer_aei_migration_model.py
apps/api/tests/test_eui_consumer_aei_migration.py
apps/api/tests/test_eui_golden_harness.py
apps/api/tests/test_aei_passive_integration.py
```

Documentation files:

```text
docs/product/eui-runtime/phase-7/EUI_PHASE_7A_AEI_CONSUMER_MIGRATION_CERTIFICATION_REPORT.md
```

Existing Phase 7 design and authorization documents are governance artifacts
and remain part of the Phase 7 review package.

---

## 4. Runtime behavior certification

| Requirement | Result | Evidence |
|---|---:|---|
| AEI remains source of truth | PASS | Production evaluation output equality test |
| Dual-read flag defaults OFF | PASS | Settings model test |
| Source flag defaults OFF | PASS | Settings model test |
| Source flag remains inert | PASS | Output equality test with source flag enabled |
| No marks changes | PASS | Evaluation output equality; no mark-writing code added |
| No grading changes | PASS | No grading path modified |
| No policy changes | PASS | AEI policy regression passed |
| No teacher review routing changes | PASS | No review-routing code modified |
| No evidence ledger changes | PASS | No evidence persistence code added |
| No schema/API/UI changes | PASS | No migrations, routers, endpoints, or UI files changed |
| No Trust Report display | PASS | Static UI/display scan found no exposure |
| No EUI source-of-truth switch | PASS | `source_switch_active` is model-enforced false |

---

## 5. Feature flag certification

Implemented flags:

```text
EUI_CONSUMER_AEI_DUAL_READ_ENABLED=false
EUI_CONSUMER_AEI_SOURCE_ENABLED=false
```

Flag behavior:

- dual-read disabled: no comparison capture, no behavior change;
- dual-read enabled: passive comparison capture only, no behavior change;
- source flag enabled: recorded as inert metadata only, no source switch;
- rollback: disable `EUI_CONSUMER_AEI_DUAL_READ_ENABLED`.

---

## 6. Difference classification certification

The deterministic classifier covers the accepted Phase 7 categories:

| Category | Result |
|---|---:|
| equivalent | PASS |
| eui_richer | PASS |
| eui_missing | PASS |
| legacy_ambiguous | PASS |
| product_impacting | PASS |
| unsafe | PASS |

Product-impacting and unsafe differences are blockers for any future source
switch. Phase 7A does not authorize switching, even when no blockers exist.

---

## 7. Golden Harness certification

Golden Harness added:

```text
apps/api/tests/golden/eui_v1/aei_consumer_migration_cases.json
```

Coverage:

- equivalent comparison;
- EUI-richer comparison;
- EUI-missing comparison;
- legacy-ambiguous comparison;
- product-impacting classification;
- unsafe classification;
- deterministic comparison IDs;
- non-authoritative comparison posture.

Result:

```text
PASS - included in tests/test_eui_golden_harness.py
```

---

## 8. Validation evidence

Focused Ruff:

```text
ruff check app/core/config.py app/modules/eui/schemas/aei_consumer_migration.py app/modules/eui/services/aei_consumer_migration.py app/modules/examinations/services/answer_sheet_eval_service.py tests/test_eui_consumer_aei_migration_model.py tests/test_eui_consumer_aei_migration.py tests/test_eui_golden_harness.py tests/test_aei_passive_integration.py
```

Result:

```text
PASS - All checks passed.
```

Focused tests:

```text
python -m pytest tests/test_eui_consumer_aei_migration_model.py tests/test_eui_consumer_aei_migration.py tests/test_eui_golden_harness.py -q
```

Result:

```text
PASS - 21 passed
```

AEI/evaluation regression slice:

```text
python -m pytest tests/test_aei_architecture.py tests/test_aei_passive_integration.py tests/test_evaluation_policy.py tests/test_golden_evaluation_harness.py tests/test_evaluation_engine.py tests/test_answer_sheet_eval.py -q
```

Result:

```text
PASS - 44 passed
```

EUI Trust/Golden regression slice:

```text
python -m pytest tests/test_trust_report_model.py tests/test_eui_trust_report_builder.py tests/test_eui_trust_passive.py tests/test_eui_golden_harness.py -q
```

Result:

```text
PASS - 24 passed
```

API import:

```text
python -c "import app.main"
```

Result:

```text
PASS
```

Whitespace check:

```text
git diff --check
```

Result:

```text
PASS
```

---

## 9. Static boundary scans

No database write path in Phase 7A EUI migration files:

```text
rg -n "\.add\(|\.commit\(|\.flush\(|\.delete\(|\.execute\(|db\.|AsyncSession|Session|select\(|insert\(|delete\(" apps/api/app/modules/eui/schemas/aei_consumer_migration.py apps/api/app/modules/eui/services/aei_consumer_migration.py -S
```

Result:

```text
PASS - no DB/session/query/write matches.
Only local set.add(...) lines appeared in the conservative scan.
```

No LLM/provider calls in Phase 7A migration files:

```text
rg -n "openai|anthropic|gemini|llm|LLM|completion|responses\.create|generate_llm|gateway" apps/api/app/modules/eui/schemas/aei_consumer_migration.py apps/api/app/modules/eui/services/aei_consumer_migration.py -S
```

Result:

```text
PASS - no matches.
```

No API/UI/Trust display exposure:

```text
rg -n "router|APIRouter|@router|Response|HTML|display|Trust Report|trust_report.*display|admin-web|teacher-facing|parent-facing|student-facing" apps/api/app/modules/eui/schemas/aei_consumer_migration.py apps/api/app/modules/eui/services/aei_consumer_migration.py apps/api/app/modules/examinations/services/answer_sheet_eval_service.py -S
```

Result:

```text
PASS - no matches.
```

---

## 10. Rollback proof

Rollback path:

```text
EUI_CONSUMER_AEI_DUAL_READ_ENABLED=false
```

Verified:

- disabled path is a no-op;
- enabled path does not alter evaluation output;
- source flag does not alter evaluation output;
- no persistence or schema rollback is required;
- no user-facing exposure exists.

---

## 11. Risk assessment

| Risk | Assessment | Mitigation |
|---|---|---|
| Evaluation behavior drift | Low | Output equality tests with flags disabled/enabled/source-enabled |
| Accidental source switch | Low | `source_switch_active` is constrained to literal false |
| PII leakage in comparison evidence | Low | Summaries omit raw answers/OCR/free text and use bounded metadata |
| Runtime exception from observer | Low | Observer catches exceptions and records failed capture |
| Confusion with AEI Shadow Mode | Low | Separate EUI metric task and capture registry |

Residual risk:

- The Phase 7A comparison currently uses available passive AEI/EUI summaries.
  Richer EUI context/trust inputs will become more useful as later consumer
  migration phases pass those objects into the adapter.

---

## 12. Phase retrospective

What held:

- The existing passive observer pattern from AEI Wave 1 and EUI Phases 1-6 was
  reusable with minimal new structure.
- A single guarded hook was enough; no broad evaluation refactor was needed.
- Source flag inertness is easiest to enforce as a model contract, not merely
  a convention.

What surprised us:

- The authorization document used `modules/evaluations/`, while the repository
  uses `modules/examinations/` for answer-sheet evaluation. The implementation
  used the existing module and documents that mapping here.

What Phase 7B should consider:

- Do not switch AEI to EUI source-of-truth yet.
- Collect more dual-read evidence first.
- If richer EUI context/trust objects are needed in evaluation flow, authorize
  that as a separate migration slice.

---

## 13. Final recommendation

Phase 7A is implementation-complete and ready for ARM review.

Recommended next step:

```text
ARM reviews the implementation diff.
If accepted: commit with `feat(eui): add AEI consumer dual-read migration foundation`
and tag `eui-runtime-phase7a-aei-consumer-dual-read-certified`.
```

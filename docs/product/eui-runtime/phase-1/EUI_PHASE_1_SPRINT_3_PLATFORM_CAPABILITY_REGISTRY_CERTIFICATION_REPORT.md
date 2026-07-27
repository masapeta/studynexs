# EUI Phase 1 Sprint 3 Certification Report — Platform Capability Registry

- **Program:** EUI Runtime Implementation
- **Phase:** Phase 1 - Educational Identity, Context, and Capability Foundations
- **Sprint:** Sprint 3 - Platform Capability Registry
- **Authorization ID:** `EUI-PH1-SP3-AUTH-001`
- **Classification:** Runtime sprint certification
- **Status:** Ready for ARM review
- **Date:** 2026-07-27
- **Implementation authorization:** Granted by Sprint 3 Implementation Authorization Contract
- **Commit authorization:** Not yet granted

---

## 1. Certification decision

```text
Certification status: PASS
ARM acceptance: Pending implementation review
Commit authorization: Pending ARM acceptance
Publication authorization: Not granted
```

Sprint 3 implemented the passive Platform Capability Registry foundation within
the authorized boundary. The implementation is declarative, read-only,
deterministic, default-off, internal-only, and non-authoritative for product
behavior.

---

## 2. Scope certified

Certified as implemented:

- static versioned Platform Capability Registry data;
- strict Platform Capability Registry contracts;
- read-only registry loader and validation;
- deterministic lookup service;
- safe missing/conflict/unsupported behavior;
- AEI compatibility representation without AEI behavior change;
- default-off passive observer;
- operational metrics/logging for passive lookup;
- Golden Harness cases;
- focused tests and regression validation.

Explicitly unchanged:

- database schema;
- public API contracts;
- UI;
- AEI registry data;
- AEI runtime behavior;
- evaluation behavior;
- EUI consumer behavior;
- product capability claims.

---

## 3. Contract evidence

Implemented contracts:

- `PlatformCapabilityScope`
- `PlatformCapabilityDeclaration`
- `PlatformCapabilityRegistryPayload`
- `PlatformCapabilityLookupRequest`
- `PlatformCapabilityLookupResult`

Supported capability modes:

- `supported`
- `assist`
- `checklist`
- `manual_review`
- `unsupported`
- `expansion`

Invalid modes fail Pydantic validation.

---

## 4. Registry data evidence

Registry dataset:

```text
apps/api/app/modules/eui/registry/platform_capability_registry.v1.json
```

Registry version:

```text
eui-platform-capability-registry-v1
```

Representative entries cover:

- CBSE NCF2023 Grade 10 Mathematics numeric normalization;
- Mathematics unit conversion;
- AEI-compatible numeric equivalence and diagram posture;
- Hindi printed OCR;
- Hindi/Telugu/Sanskrit handwriting OCR posture;
- Biology diagram checklist posture;
- pixel-perfect diagram grading as unsupported;
- Chemistry reaction-balancing assist;
- internal conflict probe for safety verification.

The registry is internal-only. It does not generate UI badges, support
documentation, sales claims, or public product claims.

---

## 5. Safety behavior evidence

Certified safety behavior:

- missing capabilities resolve to `unsupported`;
- missing capabilities are non-authoritative;
- same-specificity conflicts resolve to the lower-claim mode;
- conflicting results are marked non-authoritative;
- unsupported capabilities remain unsupported even when lookup scope includes
  additional fields;
- explicit `checklist`, `assist`, and `manual_review` modes remain review
  requiring;
- no consumer depends on registry output.

This preserves the design rule:

```text
Under-claim before over-claim.
```

---

## 6. Passive runtime and rollback evidence

Feature flag:

```text
EUI_PLATFORM_CAPABILITY_REGISTRY_ENABLED: bool = False
```

Rollback:

```text
Set EUI_PLATFORM_CAPABILITY_REGISTRY_ENABLED=false
```

Certified behavior:

- default flag state is off;
- disabled passive observer returns `None`;
- disabled passive observer records no passive capture;
- enabled passive observer records internal capture only;
- enabled passive observer does not alter product output;
- lookup exceptions are isolated;
- no persistence exists, so rollback requires no data repair.

---

## 7. Observability evidence

Passive observer task name:

```text
eui_capability_registry
```

Implemented statuses include:

- `lookup_invoked`
- `loaded`
- `lookup_completed`
- `lookup_failed`
- `unsupported`
- `conflict`
- `fallback`

Metrics use bounded, low-cardinality status labels. Logs avoid student names,
parent data, tenant slugs, free-text answers, uploaded content, and sensitive
educational content.

---

## 8. Validation commands and results

### Focused lint

Command:

```text
cd apps/api
ruff check app/modules/eui tests/test_platform_capability_registry.py tests/test_platform_capability_lookup.py tests/test_platform_capability_passive.py tests/test_eui_golden_harness.py
```

Result:

```text
PASS - All checks passed.
```

### Focused Sprint 3 tests

Command:

```text
cd apps/api
python -m pytest tests/test_platform_capability_registry.py tests/test_platform_capability_lookup.py tests/test_platform_capability_passive.py tests/test_eui_golden_harness.py
```

Result:

```text
PASS - 20 passed in 1.23s
```

### Sprint 1 and Sprint 2 regression

Command:

```text
cd apps/api
python -m pytest tests/test_educational_identity_model.py tests/test_educational_identity_resolver.py tests/test_educational_identity_passive.py tests/test_educational_context_model.py tests/test_educational_context_resolver.py tests/test_educational_context_passive.py tests/test_eui_golden_harness.py
```

Result:

```text
PASS - 31 passed in 43.79s
```

### AEI / evaluation / KG regression slice

Command:

```text
cd apps/api
python -m pytest tests/test_aei_architecture.py tests/test_aei_passive_integration.py tests/test_evaluation_policy.py tests/test_golden_evaluation_harness.py tests/test_evaluation_engine.py tests/test_answer_sheet_eval.py tests/test_knowledge_graph.py tests/test_graph_queries.py tests/test_question_concept_links.py
```

Result:

```text
PASS - 57 passed in 172.92s
```

### API import

Command:

```text
cd apps/api
python -c "import app.main; print('api import ok')"
```

Result:

```text
PASS - api import ok
```

### Whitespace check

Command:

```text
git diff --check
```

Result:

```text
PASS - no whitespace errors
```

### EUI write-path scan

Command:

```text
cd apps/api
Select-String -Path app/modules/eui/**/*.py -Pattern "\.add\(|\.flush\(|\.commit\(|insert\(|update\(|delete\(" -CaseSensitive
```

Result:

```text
PASS WITH NOTE - No Sprint 3 persistence writes found.
Note: the scan reported an existing non-database set operation:
educational_identity_resolver.py: seen.add(key)
```

---

## 9. Behavior identity evidence

Sprint 3 does not wire the registry into any production consumer.

Therefore:

- no existing evaluation output can depend on Platform Capability Registry;
- no teacher/student/parent/principal UI can see Platform Capability Registry;
- no API response can include Platform Capability Registry output;
- no AEI runtime path consumes Platform Capability Registry output.

Regression evidence confirms existing EUI Sprint 1/2, AEI, evaluation, and
Knowledge Graph behavior remains intact.

---

## 10. Risk register

| Risk | Status | Mitigation |
|---|---|---|
| Registry overclaims support | Mitigated | Missing entries resolve unsupported; conflicts choose lower-claim mode. |
| Registry becomes public product-claim source too early | Mitigated | No UI/API/docs consumer added; internal-only metadata retained. |
| AEI registry accidentally replaced | Mitigated | No AEI files changed; compatibility represented only in tests/data. |
| Conflict resolution hides ambiguity | Mitigated | Conflicts mark result non-authoritative with candidate IDs. |
| Passive observer affects runtime | Mitigated | Default-off flag, callable only, exception-isolated, no consumer wiring. |

---

## 11. Conditions

No code changes are required before ARM implementation review.

Commit should not occur until ARM reviews and accepts the implementation
evidence.

---

## 12. Phase retrospective

What held:

- The Sprint 3 implementation contract gave a clear file and behavior boundary.
- The existing Sprint 1/2 passive-runtime patterns were reusable without new
  architecture.
- Golden Harness expansion remained straightforward because capability lookup
  is deterministic.

What surprised:

- The repository stores AEI under `apps/api/app/modules/examinations`, not a
  dedicated `modules/aei` package. This did not affect scope because Sprint 3
  only reads AEI posture conceptually and does not modify AEI.

What to carry forward:

- Keep capability posture internal until an explicit consumer migration or
  documentation flow is authorized.
- Preserve the lower-claim conflict rule in any future capability registry
  consumer.

---

## 13. ARM recommendation

Recommendation:

```text
Accept Sprint 3 implementation after ARM review.
Authorize commit only after review acceptance.
Do not authorize publication until commit/tag are created and separately approved.
Do not authorize consumer migration or AEI registry replacement.
```

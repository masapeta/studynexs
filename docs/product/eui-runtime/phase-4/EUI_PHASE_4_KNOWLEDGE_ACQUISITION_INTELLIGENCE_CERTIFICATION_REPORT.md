# EUI Runtime Phase 4 Certification Report — Knowledge Acquisition Intelligence

- **Program:** EUI Runtime Implementation
- **Phase:** Phase 4 - Knowledge Acquisition Intelligence
- **Authorization ID:** `EUI-PH4-KAI-AUTH-001`
- **Classification:** Runtime phase certification
- **Status:** Ready for ARM review
- **Date:** 2026-07-27
- **Implementation authorization:** Granted by Phase 4 Implementation Authorization Contract
- **Commit authorization:** Not yet granted

---

## 1. Certification decision

```text
Certification status: PASS
ARM acceptance: Pending implementation review
Commit authorization: Pending ARM acceptance
Publication authorization: Not granted
```

Phase 4 implemented the passive KAI candidate foundation within the authorized
boundary. The implementation is candidate-only, default-off, deterministic for
structured inputs, internal-only, non-authoritative, and not consumed by product
runtime behavior.

---

## 2. Scope certified

Certified as implemented:

- KAI candidate contracts;
- deterministic transient KAI candidate IDs;
- source admission policy;
- candidate builder;
- Platform Capability Registry posture lookup;
- default-off passive observer;
- operational metrics/logging for passive candidate generation;
- Golden Harness KAI cases;
- focused tests and regression validation.

Explicitly unchanged:

- database schema;
- public API contracts;
- UI;
- AEI behavior;
- EKG behavior;
- file upload workflows;
- OCR/LLM/ASR provider integrations;
- consumer behavior;
- product capability claims.

---

## 3. Candidate contract evidence

Implemented contracts:

- `KnowledgeAcquisitionInputReference`
- `EducationalArtifactCandidate`
- `KnowledgeAcquisitionProvenance`
- `KnowledgeAcquisitionTrustSignals`
- `SourceAdmissionDecision`

The candidate object is non-authoritative in Phase 4. Its `authoritative`
property always returns `False`.

---

## 4. Source admission evidence

Admitted Phase 4 source types:

- `pdf`
- `worksheet`
- `ocr_text`
- `answer_key`
- `teacher_note`
- `lesson_plan`

Explicitly not admitted:

- `student_work`

Unsupported examples:

- `image`
- `voice`
- `unknown`

Student work resolves to `needs_review`, not `admitted`.

---

## 5. Provenance and trust separation evidence

Provenance records:

- source;
- source reference;
- source version;
- checksum;
- page number;
- source metadata.

Trust-signal placeholders record:

- input quality;
- extraction confidence;
- language confidence;
- capability mode;
- review requirement;
- ambiguity count.

The implementation does not implement the full Trust Framework and does not
merge provenance with trust signals.

---

## 6. Capability posture evidence

KAI may call the Platform Capability Registry lookup service to attach internal
capability posture.

Certified behavior:

- supported capability posture remains `supported`;
- assist/manual-review posture remains review-bound;
- capability posture is not upgraded;
- missing capability posture does not create support;
- no public product claim is generated.

---

## 7. Passive runtime and rollback evidence

Feature flag:

```text
EUI_KAI_PASSIVE_ENABLED: bool = False
```

Rollback:

```text
Set EUI_KAI_PASSIVE_ENABLED=false
```

Certified behavior:

- default flag state is off;
- disabled passive observer returns `None`;
- disabled passive observer records no passive capture;
- enabled passive observer records internal capture only;
- enabled passive observer does not alter product output;
- lookup/build exceptions are isolated;
- no persistence exists, so rollback requires no data repair.

---

## 8. Observability evidence

Passive observer task name:

```text
eui_kai
```

Implemented statuses include:

- `acquire_invoked`
- `acquire_completed`
- `acquire_failed`
- `unsupported_input`
- `ambiguous`
- `needs_review`

Metrics use bounded, low-cardinality status labels. Logs avoid student names,
parent data, tenant slugs, free-text answers, uploaded content, raw OCR text,
and sensitive educational evidence.

---

## 9. Validation commands and results

### Focused lint

Command:

```text
cd apps/api
ruff check app/modules/eui tests/test_kai_candidate_model.py tests/test_kai_candidate_builder.py tests/test_kai_passive.py tests/test_kai_source_admission.py tests/test_eui_golden_harness.py
```

Result:

```text
PASS - All checks passed.
```

### Focused Phase 4 tests

Command:

```text
cd apps/api
python -m pytest tests/test_kai_candidate_model.py tests/test_kai_candidate_builder.py tests/test_kai_passive.py tests/test_kai_source_admission.py tests/test_eui_golden_harness.py
```

Result:

```text
PASS - 24 passed in 1.45s
```

### Phase 1-3 EUI regression

Command:

```text
cd apps/api
python -m pytest tests/test_educational_identity_model.py tests/test_educational_identity_resolver.py tests/test_educational_identity_passive.py tests/test_educational_context_model.py tests/test_educational_context_resolver.py tests/test_educational_context_passive.py tests/test_platform_capability_registry.py tests/test_platform_capability_lookup.py tests/test_platform_capability_passive.py tests/test_eui_golden_harness.py
```

Result:

```text
PASS - 49 passed in 40.78s
```

### AEI / evaluation / KG regression slice

Command:

```text
cd apps/api
python -m pytest tests/test_aei_architecture.py tests/test_aei_passive_integration.py tests/test_evaluation_policy.py tests/test_golden_evaluation_harness.py tests/test_evaluation_engine.py tests/test_answer_sheet_eval.py tests/test_knowledge_graph.py tests/test_graph_queries.py tests/test_question_concept_links.py
```

Result:

```text
PASS - 57 passed in 166.92s
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

### EUI write-path scan

Command:

```text
cd apps/api
Select-String -Path app/modules/eui/**/*.py -Pattern "\.add\(|\.flush\(|\.commit\(|insert\(|update\(|delete\(" -CaseSensitive
```

Result:

```text
PASS WITH NOTE - No Phase 4 persistence writes found.
Note: the scan reported an existing non-database set operation:
educational_identity_resolver.py: seen.add(key)
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

---

## 10. Behavior identity evidence

Phase 4 does not wire KAI into any production consumer.

Therefore:

- no existing evaluation output can depend on KAI;
- no EKG trusted write can occur through KAI;
- no teacher/student/parent/principal UI can see KAI output;
- no API response can include KAI output;
- no OCR/LLM/ASR provider call can occur through KAI.

Regression evidence confirms existing EUI Phase 1-3, AEI, evaluation, and
Knowledge Graph behavior remains intact.

---

## 11. Risk register

| Risk | Status | Mitigation |
|---|---|---|
| KAI output treated as truth | Mitigated | Candidate object is non-authoritative; no consumer wiring exists. |
| Student work ingested too early | Mitigated | Student work source admission is `needs_review`, not admitted. |
| KAI becomes hidden OCR/LLM integration | Mitigated | No provider calls, prompts, OCR, ASR, or external network calls added. |
| Raw text leaks into IDs/metrics | Mitigated | Candidate IDs use text hashes; logs/metrics use bounded labels only. |
| Capability posture overclaim | Mitigated | Builder consumes registry mode as-is and does not upgrade posture. |
| EKG receives unreviewed candidates | Mitigated | No EKG modules changed; no writes or consumer paths exist. |

---

## 12. Conditions

No code changes are required before ARM implementation review.

Commit should not occur until ARM reviews and accepts the implementation
evidence.

---

## 13. Phase retrospective

What held:

- The Phase 4 implementation contract kept KAI from turning into OCR or LLM
  implementation.
- Platform Capability Registry integration was useful as posture metadata
  without creating product claims.
- Golden Harness remained a good fit for candidate-only deterministic behavior.

What surprised:

- Student-work handling needed an explicit test and builder rule to avoid
  treating supplied text as accepted extraction.

What to carry forward:

- Keep KAI candidate-only until EKG expansion and Trust Framework phases are
  separately authorized.
- Continue using content hashes in IDs and diagnostics rather than raw
  educational text.

---

## 14. ARM recommendation

Recommendation:

```text
Accept Phase 4 KAI implementation after ARM review.
Authorize commit only after review acceptance.
Do not authorize publication until commit/tag are created and separately approved.
Do not authorize consumer migration, EKG writes, AEI behavior changes, OCR/LLM/ASR provider integration, or product behavior changes.
```

# AEI Handwriting OCR Phase 2 - Track-A Golden Set Benchmark Certification Report

- **Program:** AEI v1.0 product-facing completion
- **Workstream:** Teacher evaluation experience / answer-sheet transcription
- **Phase:** Handwriting OCR Phase 2 - Track-A Golden Set benchmark
- **Classification:** Implementation certification report
- **Authorization ID:** AEI-HANDWRITING-OCR-PHASE2-AUTH-001
- **Status:** Certified / ready for ARM publication decision
- **Date:** 2026-07-29
- **Owner:** Avinash Reddy Masapeta (ARM)
- **Design baseline:** [`./AEI_HANDWRITING_OCR_PHASE_2_TRACK_A_GOLDEN_SET_BENCHMARK_DESIGN_BRIEF.md`](./AEI_HANDWRITING_OCR_PHASE_2_TRACK_A_GOLDEN_SET_BENCHMARK_DESIGN_BRIEF.md)
- **Implementation authorization:** [`./AEI_HANDWRITING_OCR_PHASE_2_TRACK_A_GOLDEN_SET_BENCHMARK_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md`](./AEI_HANDWRITING_OCR_PHASE_2_TRACK_A_GOLDEN_SET_BENCHMARK_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md)
- **Data handling guide:** [`./AEI_HANDWRITING_OCR_PHASE_2_TRACK_A_DATA_HANDLING_GUIDE.md`](./AEI_HANDWRITING_OCR_PHASE_2_TRACK_A_DATA_HANDLING_GUIDE.md)
- **Benchmark report template:** [`./AEI_HANDWRITING_OCR_PHASE_2_TRACK_A_GOLDEN_SET_BENCHMARK_REPORT_TEMPLATE.md`](./AEI_HANDWRITING_OCR_PHASE_2_TRACK_A_GOLDEN_SET_BENCHMARK_REPORT_TEMPLATE.md)
- **Phase 1 baseline:** [`./AEI_HANDWRITING_OCR_PHASE_1_GEMINI_FLASH_TRANSCRIPTION_CERTIFICATION_REPORT.md`](./AEI_HANDWRITING_OCR_PHASE_1_GEMINI_FLASH_TRANSCRIPTION_CERTIFICATION_REPORT.md)
- **Current project anchor:** [`../../STATUS.md`](../../STATUS.md)

---

## 1. Certification decision

```text
Decision: PASS
Recommendation: Approved for commit after ARM confirms commit authorization
Risk: Low
Runtime behavior: Unchanged
```

The implementation satisfies the accepted Phase 2 contract.

It creates a repository-safe Track-A benchmark foundation for measuring
answer-sheet OCR candidates against teacher-verified transcription truth without
changing production OCR routing, marks, teacher review, UI, API, schema, or
evidence-ledger behavior.

---

## 2. Scope compliance

| Requirement | Result | Evidence |
|---|---:|---|
| Track-A manifest / ground-truth contract | PASS | Synthetic manifest fixture and data handling guide added. |
| Deterministic scoring helpers | PASS | CER, WER, extraction accuracy, blank accuracy, hallucination, schema validity implemented. |
| Repository-safe Golden Harness | PASS | Synthetic fixture added under `tests/golden/aei_v1`. |
| Real data kept out of git | PASS | No images, base64 images, real student names, or real transcriptions added. |
| Candidate/license posture placeholders | PASS | Candidate posture documented in synthetic fixture and report template. |
| Benchmark report template | PASS | Aggregate report template added. |
| Data handling guide | PASS | Track-A storage, redaction, access, and output posture documented. |
| No production source switch | PASS | Production answer-sheet evaluation source selection unchanged. |

---

## 3. Repository boundary verification

Changed files are within the authorized boundary:

```text
apps/api/app/modules/examinations/services/handwriting_ocr_benchmark.py
apps/api/tests/golden/aei_v1/handwriting_ocr_phase2_track_a_benchmark_cases.json
apps/api/tests/test_aei_handwriting_ocr_phase2_benchmark.py
docs/product/aei-v1/AEI_HANDWRITING_OCR_PHASE_2_TRACK_A_DATA_HANDLING_GUIDE.md
docs/product/aei-v1/AEI_HANDWRITING_OCR_PHASE_2_TRACK_A_GOLDEN_SET_BENCHMARK_CERTIFICATION_REPORT.md
docs/product/aei-v1/AEI_HANDWRITING_OCR_PHASE_2_TRACK_A_GOLDEN_SET_BENCHMARK_DESIGN_BRIEF.md
docs/product/aei-v1/AEI_HANDWRITING_OCR_PHASE_2_TRACK_A_GOLDEN_SET_BENCHMARK_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md
docs/product/aei-v1/AEI_HANDWRITING_OCR_PHASE_2_TRACK_A_GOLDEN_SET_BENCHMARK_REPORT_TEMPLATE.md
```

Protected areas unchanged:

- production answer-sheet evaluation service behavior;
- Phase 1 OCR flag semantics;
- teacher evaluation UI;
- public APIs;
- database schema and migrations;
- evidence ledger behavior;
- marks calculation;
- teacher-review routing;
- student / parent / principal consumers;
- deployment configuration;
- billing;
- RBAC / tenant isolation.

---

## 4. Metrics proof

Implemented deterministic metrics:

- character error rate;
- word error rate;
- per-question extraction accuracy;
- blank-answer accuracy;
- hallucination count and rate;
- schema validity rate;
- aggregate candidate run summary.

Focused test evidence:

```text
test_character_and_word_error_rates_are_deterministic
test_score_candidate_answers_exact_match
test_score_candidate_answers_detects_blank_hallucination_and_missing_question
test_schema_invalid_candidate_scores_as_safe_empty_output
test_summarize_candidate_run_aggregates_metrics
test_summarize_candidate_run_rejects_unknown_candidate
```

---

## 5. Data-handling proof

The repository-safe manifest validator rejects:

- non-safe real image references;
- obvious PII patterns;
- forbidden real-data keys such as `image_base64`;
- nested forbidden real-data keys in candidate outputs;
- obvious PII patterns in candidate OCR outputs;
- invalid Track-A sample identifiers.

Focused test evidence:

```text
test_repository_safe_track_a_manifest_fixture_validates
test_repository_safe_manifest_rejects_real_image_reference
test_repository_safe_manifest_rejects_obvious_pii
test_repository_safe_manifest_rejects_forbidden_real_data_keys
test_repository_safe_manifest_rejects_nested_forbidden_real_data_keys
test_repository_safe_manifest_rejects_candidate_output_pii
```

The committed fixture uses only:

```text
synthetic://...
```

image references.

---

## 6. Candidate/license posture

Repository-safe candidate labels:

```text
gemini_flash
qwen2_5_vl_7b
surya_2
```

The implementation does not assert final commercial-use approval for Qwen or
Surya. It records them as benchmark candidates and requires final license /
commercial-use verification before any real-data benchmark or production
adoption decision.

---

## 7. Runtime behavior proof

Phase 2 adds no production runtime source switch.

Focused test evidence:

```text
test_phase2_does_not_change_phase1_flag_default_or_runtime_source
```

That test verifies:

- `AEI_HANDWRITING_OCR_PHASE1_ENABLED` still defaults to `False`;
- production answer-sheet evaluation does not import the Phase 2 benchmark
  helper.

---

## 8. Validation evidence

Commands run from `apps/api`:

```text
python -m ruff check app/modules/examinations/services/handwriting_ocr_benchmark.py tests/test_aei_handwriting_ocr_phase2_benchmark.py
```

Result:

```text
PASS - All checks passed
```

Command:

```text
python -m pytest tests/test_aei_handwriting_ocr_phase2_benchmark.py -q
```

Result:

```text
PASS - 13 passed in 0.20s
```

Adjacent Phase 1 OCR / gateway regression:

```text
python -m pytest tests/test_aei_handwriting_ocr_phase1.py tests/test_answer_sheet_vision.py tests/test_ai_gateway_model_routing.py -q
```

Result:

```text
PASS - 18 passed in 0.37s
```

App import:

```text
python -c "import app.main"
```

Result:

```text
PASS
```

Diff hygiene:

```text
git diff --check
```

Result:

```text
PASS
```

---

## 9. Known limitations

- No live Gemini, Qwen, or Surya benchmark was run in this implementation.
- Real Track-A answer sheets remain to be collected outside git.
- Candidate license/commercial-use verification remains required before any real
  benchmark run using non-Gemini candidates.
- Phase 2 does not add confidence-routed OCR, GPU infrastructure, source
  switching, UI changes, API changes, schema changes, marks changes, routing
  changes, or evidence-ledger behavior changes.

---

## 10. ARM recommendation

```text
Decision: ACCEPTED
Recommendation: Proceed to commit when ARM explicitly approves commit
Suggested commit: feat(aei): add handwriting OCR Track-A benchmark foundation
Suggested tag: aei-handwriting-ocr-phase2-track-a-benchmark-certified
```

Post-publication, update `docs/STATUS.md` separately as a docs-only status
commit.

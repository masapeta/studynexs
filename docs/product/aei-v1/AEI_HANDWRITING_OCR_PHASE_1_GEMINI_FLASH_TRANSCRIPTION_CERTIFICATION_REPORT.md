# AEI Handwriting OCR Phase 1 - Gemini Flash Answer-Sheet Transcription Certification Report

- **Program:** AEI v1.0 product-facing completion
- **Workstream:** Teacher evaluation experience / answer-sheet transcription
- **Phase:** Handwriting OCR Phase 1 - Gemini Flash answer-sheet transcription
- **Classification:** Implementation certification report
- **Authorization ID:** AEI-HANDWRITING-OCR-PHASE1-AUTH-001
- **Status:** Certified / ready for ARM publication decision
- **Date:** 2026-07-29
- **Owner:** Avinash Reddy Masapeta (ARM)
- **Design baseline:** [`./AEI_HANDWRITING_OCR_PHASE_1_GEMINI_FLASH_TRANSCRIPTION_DESIGN_BRIEF.md`](./AEI_HANDWRITING_OCR_PHASE_1_GEMINI_FLASH_TRANSCRIPTION_DESIGN_BRIEF.md)
- **Implementation authorization:** [`./AEI_HANDWRITING_OCR_PHASE_1_GEMINI_FLASH_TRANSCRIPTION_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md`](./AEI_HANDWRITING_OCR_PHASE_1_GEMINI_FLASH_TRANSCRIPTION_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md)
- **Current project anchor:** [`../../STATUS.md`](../../STATUS.md)

---

## 1. Certification decision

```text
Decision: PASS
Recommendation: Approved for commit after ARM confirms commit authorization
Risk: Low
Runtime behavior: Feature-flagged / default off
```

The implementation satisfies the accepted Phase 1 contract.

It introduces a controlled, default-off Gemini Flash answer-sheet transcription
gate through the existing StudyNexs AI Gateway. OCR remains transcription-only.
AEI evaluation and teacher approval remain the authority.

---

## 2. Scope compliance

| Requirement | Result | Evidence |
|---|---:|---|
| Canonical default-off feature flag | PASS | `AEI_HANDWRITING_OCR_PHASE1_ENABLED=false` added to `Settings`. |
| Gateway-only Gemini invocation | PASS | Answer-sheet OCR still calls `generate_llm`; no direct Gemini SDK call added. |
| Reuse existing answer-sheet vision service | PASS | Implementation extends `answer_sheet_vision.py`; no parallel OCR stack. |
| Transcription-only output | PASS | Output remains sanitized per-question answer text. |
| General AI routing separated from OCR routing | PASS | Existing `AI_VISION_*` routing preserved; focused routing tests pass. |
| Exception isolation | PASS | Provider, parse, and sanitization failures return safe empty extraction. |
| Observability | PASS | Low-cardinality `platform_metrics.record_job_event` statuses added. |
| Golden Harness foundation | PASS | Repository-safe cases added under `tests/golden/aei_v1`. |
| No live provider dependency in tests | PASS | Tests use fakes / monkeypatching only. |

---

## 3. Repository boundary verification

Changed files are within the authorized boundary:

```text
apps/api/app/core/config.py
apps/api/app/modules/examinations/services/answer_sheet_vision.py
apps/api/tests/test_answer_sheet_vision.py
apps/api/tests/test_aei_handwriting_ocr_phase1.py
apps/api/tests/golden/aei_v1/handwriting_ocr_phase1_cases.json
docs/product/aei-v1/AEI_HANDWRITING_OCR_PHASE_1_GEMINI_FLASH_TRANSCRIPTION_DESIGN_BRIEF.md
docs/product/aei-v1/AEI_HANDWRITING_OCR_PHASE_1_GEMINI_FLASH_TRANSCRIPTION_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md
docs/product/aei-v1/AEI_HANDWRITING_OCR_PHASE_1_GEMINI_FLASH_TRANSCRIPTION_CERTIFICATION_REPORT.md
```

Protected areas unchanged:

- database models;
- Alembic migrations;
- public API schemas and endpoints;
- admin-web UI;
- evidence-ledger generation behavior;
- teacher review routing behavior;
- marks calculation semantics;
- source-of-truth switching;
- billing / payments;
- RBAC / tenant resolution;
- deployment configuration;
- committed `.env` files or secrets.

---

## 4. Feature flag proof

Added:

```text
AEI_HANDWRITING_OCR_PHASE1_ENABLED=false
```

Behavior:

| Flag state | Certified behavior |
|---|---|
| `false` | `extract_answers_from_image` returns safe empty extraction and does not invoke the gateway. |
| `true` | Supported images may invoke the configured gateway vision provider. |

Focused test evidence:

```text
test_handwriting_ocr_phase1_flag_defaults_disabled
test_vision_llm_unavailable_when_phase1_flag_disabled
test_phase1_flag_off_does_not_invoke_gateway
test_phase1_flag_on_invokes_gateway_with_gemini_model
```

---

## 5. Provider routing proof

Certified OCR profile:

```text
AI_VISION_PRIMARY_PROVIDER=gemini
AI_VISION_PRIMARY_MODEL=gemini-1.5-flash
AI_VISION_FALLBACK_PROVIDER=ollama
AI_VISION_FALLBACK_MODEL=gemma4:cloud
```

Certified general AI profile remains separate:

```text
AI_DEFAULT_PROVIDER=ollama
AI_DEFAULT_MODEL=gemma4:cloud
AI_FALLBACK_PROVIDER=openai
AI_FALLBACK_MODEL=gpt-4o
```

Focused test evidence:

```text
test_vision_models_are_separate_from_general_default
test_default_model_does_not_leak_general_model_to_other_providers
test_default_provider_can_have_explicit_general_model
test_general_fallback_model_uses_explicit_config
```

---

## 6. Gateway-only invocation proof

The implementation continues to use:

```text
generate_llm(...)
```

No direct Gemini client or provider SDK call was added to answer-sheet
evaluation code.

Focused test evidence:

```text
test_answer_sheet_vision_does_not_bypass_gateway_with_provider_sdk
```

---

## 7. Exception and unsafe-output isolation

Certified behavior:

- unsupported MIME returns `{}` / `None`;
- provider exceptions return `{}` / `None`;
- malformed JSON returns `{}` with parse-failure metric;
- sanitizer failures return `{}` with sanitize-failure metric;
- no raw image bytes or answer text are logged by the new instrumentation.

Focused test evidence:

```text
test_unsupported_mime_does_not_invoke_gateway
test_malformed_gateway_json_returns_safe_empty_extraction
test_provider_exception_returns_safe_empty_extraction
test_sanitizer_failure_returns_safe_empty_extraction
```

---

## 8. Observability proof

The implementation records low-cardinality operational statuses through the
existing platform metrics registry:

```text
task="aei_handwriting_ocr_phase1"
status="disabled"
status="invoked"
status="unavailable"
status="unsupported_mime"
status="failed"
status="fallback_used"
status="parse_failed"
status="sanitize_failed"
status="completed"
```

No metric label includes student, teacher, tenant, file name, question text, or
answer text.

---

## 9. Golden Harness proof

Added repository-safe fixture:

```text
apps/api/tests/golden/aei_v1/handwriting_ocr_phase1_cases.json
```

Fixture scope:

- flag-off no-op;
- Gemini gateway transcription;
- malformed provider JSON;
- unsupported MIME.

Focused test evidence:

```text
test_handwriting_ocr_phase1_golden_harness_cases_are_stable
```

Real Track-A answer-sheet images remain out of repo scope and are not included.

---

## 10. Validation evidence

Commands run from `apps/api`:

```text
python -m ruff check app/core/config.py app/modules/examinations/services/answer_sheet_vision.py tests/test_answer_sheet_vision.py tests/test_ai_gateway_model_routing.py tests/test_aei_handwriting_ocr_phase1.py
```

Result:

```text
PASS - All checks passed
```

Command:

```text
python -m pytest tests/test_answer_sheet_vision.py tests/test_ai_gateway_model_routing.py tests/test_aei_handwriting_ocr_phase1.py -q
```

Result:

```text
PASS - 18 passed in 0.32s
```

Adjacent targeted evaluation regression:

```text
python -m pytest tests/test_answer_sheet_eval.py::test_aei_v1_language_ocr_assist_flag_off_preserves_suggestions tests/test_answer_sheet_eval.py::test_aei_v1_language_ocr_assist_flag_on_adds_language_review_metadata -q
```

Result:

```text
PASS - 2 passed in 25.81s
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

Local limitation:

```text
pytest tests/test_answer_sheet_eval.py -q
```

The direct `pytest.exe` invocation was blocked by Windows Application Control.
The full file also exceeded the local 120-second tool timeout when run via
`python -m pytest`. The two closest OCR/evaluation regression tests from that
file were run directly and passed.

---

## 11. Runtime behavior and rollback proof

Runtime behavior:

- flag off by default;
- no OCR gateway call when disabled;
- no UI/API/schema changes;
- no marks/routing/ledger/source-of-truth changes;
- teacher approval remains required for authoritative evidence.

Rollback:

```text
AEI_HANDWRITING_OCR_PHASE1_ENABLED=false
```

Disabling the flag stops Phase 1 OCR execution without code rollback.

---

## 12. Known limitations

- Phase 1 does not benchmark Gemini against Qwen2.5-VL-7B or Surya 2.
- Phase 1 does not add PDF rendering or multi-page answer-sheet fan-out.
- Phase 1 does not add per-line confidence, bounding boxes, or layout evidence.
- Phase 1 does not claim universal handwriting support.
- Phase 1 does not expose OCR results directly to students or parents.
- Live Gemini smoke proof was not run as part of deterministic local
  certification because live provider credentials and non-PII image fixtures are
  intentionally outside unit certification.

---

## 13. ARM recommendation

```text
Decision: ACCEPTED
Recommendation: Proceed to commit when ARM explicitly approves commit
Suggested commit: feat(aei): add handwriting OCR phase 1 transcription gate
Suggested tag: aei-handwriting-ocr-phase1-gemini-transcription-certified
```

Post-publication, update `docs/STATUS.md` separately as a docs-only status
commit.


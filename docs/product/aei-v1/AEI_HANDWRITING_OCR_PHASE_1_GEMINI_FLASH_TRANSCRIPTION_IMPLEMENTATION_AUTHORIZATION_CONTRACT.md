# AEI Handwriting OCR Phase 1 - Gemini Flash Answer-Sheet Transcription Implementation Authorization Contract

- **Program:** AEI v1.0 product-facing completion
- **Workstream:** Teacher evaluation experience / answer-sheet transcription
- **Phase:** Handwriting OCR Phase 1 - Gemini Flash answer-sheet transcription
- **Classification:** Implementation authorization contract
- **Authorization ID:** AEI-HANDWRITING-OCR-PHASE1-AUTH-001
- **Status:** Accepted
- **Implementation:** Authorized for Phase 1 only
- **Date:** 2026-07-29
- **Owner:** Avinash Reddy Masapeta (ARM)
- **Design baseline:** [`./AEI_HANDWRITING_OCR_PHASE_1_GEMINI_FLASH_TRANSCRIPTION_DESIGN_BRIEF.md`](./AEI_HANDWRITING_OCR_PHASE_1_GEMINI_FLASH_TRANSCRIPTION_DESIGN_BRIEF.md)
- **AEI v1.0 baseline:** [`./AEI_V1_CERTIFICATION_REPORT.md`](./AEI_V1_CERTIFICATION_REPORT.md)
- **Language/OCR assist baseline:** [`./AEI_V1_BATCH_D_LANGUAGE_OCR_ASSIST_CERTIFICATION_REPORT.md`](./AEI_V1_BATCH_D_LANGUAGE_OCR_ASSIST_CERTIFICATION_REPORT.md)
- **Teacher evaluation UX baseline:** [`./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_E_CERTIFICATION_REPORT.md`](./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_E_CERTIFICATION_REPORT.md)
- **Current project anchor:** [`../../STATUS.md`](../../STATUS.md)

---

## 1. Purpose

Authorize, if accepted by ARM, a narrow Phase 1 implementation that makes
Gemini Flash answer-sheet transcription an explicit, feature-flagged,
gateway-routed OCR capability for the existing teacher evaluation workflow.

The implementation goal is:

```text
Teacher uploads supported answer-sheet image
        |
        v
Gemini Flash transcribes via StudyNexs AI Gateway
        |
        v
Sanitized per-question answer text
        |
        v
Existing AEI / teacher review flow
```

The governing principle remains:

```text
OCR reads. AEI evaluates. Teacher decides.
```

---

## 2. Authorization posture

This contract is accepted by ARM.

It authorizes only the scope below. It does not authorize commit, tag, or
publication without a separate post-implementation ARM review and publication
approval.

---

## 3. Authorized implementation scope

Implementation is authorized only for:

1. adding a default-off feature flag:

   ```text
   AEI_HANDWRITING_OCR_PHASE1_ENABLED=false
   ```

2. requiring that flag before the Phase 1 answer-sheet OCR transcription path
   runs;
3. routing Phase 1 transcription through the existing StudyNexs AI Gateway;
4. using the configured vision provider:

   ```text
   AI_VISION_PRIMARY_PROVIDER=gemini
   AI_VISION_PRIMARY_MODEL=gemini-1.5-flash
   AI_VISION_FALLBACK_PROVIDER=ollama
   AI_VISION_FALLBACK_MODEL=gemma4:cloud
   ```

5. preserving general reasoning provider routing:

   ```text
   AI_DEFAULT_PROVIDER=ollama
   AI_DEFAULT_MODEL=gemma4:cloud
   AI_FALLBACK_PROVIDER=openai
   AI_FALLBACK_MODEL=gpt-4o
   ```

6. reusing the existing answer-sheet vision service;
7. keeping OCR output as sanitized per-question transcription only;
8. preserving existing evaluation / teacher review / approval behavior;
9. adding operational metrics or structured logs for Phase 1 OCR health;
10. adding repository-safe Golden Harness / tests for:
    - flag-off no-op behavior;
    - flag-on gateway invocation;
    - provider/model routing;
    - unsupported MIME behavior;
    - malformed JSON handling;
    - provider exception isolation;
    - sanitized answer extraction;
    - no direct provider SDK bypass;
11. producing a certification report:

    ```text
    docs/product/aei-v1/
    AEI_HANDWRITING_OCR_PHASE_1_GEMINI_FLASH_TRANSCRIPTION_CERTIFICATION_REPORT.md
    ```

Implementation should prefer the smallest change that makes Phase 1 explicit,
safe, observable, and reversible.

---

## 4. Authorized repository boundary

### 4.1 Backend configuration

Implementation may update:

```text
apps/api/app/core/config.py
```

Only to add the Phase 1 feature flag and related comments.

### 4.2 Answer-sheet OCR runtime

Implementation may update:

```text
apps/api/app/modules/examinations/services/answer_sheet_vision.py
apps/api/app/modules/examinations/services/answer_sheet_eval_service.py
```

Only for:

- feature-flag gating;
- gateway-routed provider/model selection;
- OCR exception isolation;
- low-cardinality observability;
- preserving existing evaluation behavior when disabled.

### 4.3 Gateway tests / OCR tests

Implementation may update or add tests under:

```text
apps/api/tests/test_answer_sheet_vision.py
apps/api/tests/test_ai_gateway_model_routing.py
apps/api/tests/test_aei_handwriting_ocr_phase1.py
apps/api/tests/golden/aei_v1/
```

Tests must use mocks/fakes. They must not require live Gemini, OpenAI, Ollama,
or real student images.

### 4.4 Documentation and certification

Implementation may add:

```text
docs/product/aei-v1/AEI_HANDWRITING_OCR_PHASE_1_GEMINI_FLASH_TRANSCRIPTION_CERTIFICATION_REPORT.md
```

Implementation may update this contract and its design brief only to mark final
accepted/implemented status after ARM review, if that follows the established
project pattern.

Post-publication status updates must be committed separately:

```text
docs/STATUS.md
```

---

## 5. Protected repository areas

The following must not be changed:

- database models;
- Alembic migrations;
- public API schemas or endpoint contracts;
- admin-web UI;
- student / parent / principal portals;
- evidence-ledger generation behavior;
- teacher review routing behavior;
- marks calculation semantics;
- AEI source-readiness / source-adoption services;
- EUI consumer migration source-of-truth behavior;
- billing / payments;
- RBAC / authorization;
- tenant resolution;
- production Compose / deployment configuration;
- public marketing pages;
- real `.env` files or committed secrets.

Any change outside the authorized boundary requires a separate ARM
authorization.

---

## 6. Runtime constraints

Phase 1 implementation must be:

- feature-flagged;
- default off;
- gateway-routed;
- transcription-only;
- deterministic where deterministic logic is available;
- exception-isolated;
- tenant-safe;
- PII-safe in logs and metrics;
- reversible by disabling the feature flag;
- compatible with existing teacher review and approval behavior.

Phase 1 must not:

- autonomously mark answers because OCR succeeded;
- skip teacher approval;
- make OCR output parent/student visible before teacher approval;
- change the source of truth for approved evidence;
- require a live provider for unit tests;
- log raw answer-sheet images;
- log raw OCR text in structured operational logs;
- put student, teacher, or tenant IDs into metric labels.

---

## 7. Feature flag

Exact flag:

```text
AEI_HANDWRITING_OCR_PHASE1_ENABLED=false
```

Required behavior:

| Flag state | Expected behavior |
|---|---|
| `false` | Phase 1 Gemini transcription path is disabled; existing behavior remains unchanged. |
| `true` | Supported answer-sheet image transcription may run through the configured gateway vision provider. |

Rollback proof must demonstrate that disabling the flag stops Phase 1 OCR
execution without requiring code rollback.

---

## 8. Provider configuration

Phase 1 may rely on the existing AI Gateway provider settings.

Recommended OCR profile:

```text
AI_VISION_PRIMARY_PROVIDER=gemini
AI_VISION_PRIMARY_MODEL=gemini-1.5-flash
AI_VISION_FALLBACK_PROVIDER=ollama
AI_VISION_FALLBACK_MODEL=gemma4:cloud
```

Recommended general reasoning profile:

```text
AI_DEFAULT_PROVIDER=ollama
AI_DEFAULT_MODEL=gemma4:cloud
AI_FALLBACK_PROVIDER=openai
AI_FALLBACK_MODEL=gpt-4o
```

The implementation must not use `AI_DEFAULT_MODEL` as the Gemini OCR model
unless Gemini is the explicitly selected default provider. General AI routing and
vision/OCR routing must remain separated.

---

## 9. Observability requirements

Implementation should add or reuse low-cardinality operational evidence for:

- OCR invoked;
- OCR completed;
- OCR failed;
- unsupported MIME skipped;
- provider fallback used;
- JSON parse failed;
- answers extracted count bucket or bounded numeric value;
- execution duration.

Observability must not include:

- raw image bytes;
- base64 image content;
- raw answer text;
- question text;
- student name;
- teacher name;
- file name;
- tenant ID as a metric label.

---

## 10. Golden Harness and test requirements

Required tests:

1. feature flag defaults to disabled;
2. flag-off image evaluation does not invoke Phase 1 OCR;
3. flag-on supported image invokes gateway transcription;
4. Gemini primary model is selected from `AI_VISION_PRIMARY_MODEL`;
5. Ollama vision fallback model is selected from `AI_VISION_FALLBACK_MODEL`;
6. general Ollama / OpenAI fallback routing remains unchanged;
7. unsupported MIME does not invoke OCR;
8. malformed provider JSON returns no unsafe answers;
9. provider exception returns safe empty extraction rather than crashing
   evaluation;
10. sanitization bounds extracted answer text;
11. no direct provider SDK import is introduced in answer-sheet evaluation code;
12. no schema/API/UI files changed.

Golden Harness cases should be repository-safe and may include sanitized
synthetic examples only.

Real Track-A answer-sheet images must not be committed to the repository.

---

## 11. Validation requirements

Before ARM acceptance after implementation, the implementer must run and report:

```text
ruff check <changed API files and tests>
pytest <focused OCR / gateway / evaluation tests>
python -c "import app.main"
git diff --check
```

If a broader suite is blocked by missing local services, document the blocker
and run every relevant deterministic suite that can run locally.

Live Gemini smoke testing is not required for unit certification and must not be
hard-coded into CI. If a live smoke is performed manually, it must use a
non-PII test image and external secrets supplied through the environment.

---

## 12. Certification deliverable

Implementation must produce:

```text
docs/product/aei-v1/
AEI_HANDWRITING_OCR_PHASE_1_GEMINI_FLASH_TRANSCRIPTION_CERTIFICATION_REPORT.md
```

The report must include:

- scope compliance;
- repository boundary verification;
- feature flag proof;
- provider routing proof;
- gateway-only invocation proof;
- exception isolation proof;
- no marks/routing/ledger/API/UI/schema change proof;
- observability proof;
- Golden Harness / test evidence;
- rollback proof;
- known limitations;
- ARM recommendation.

---

## 13. Explicit exclusions

This contract does not authorize:

- database schema changes;
- Alembic migrations;
- public API changes;
- admin-web UI changes;
- teacher-review routing changes;
- evidence-ledger behavior changes;
- marks calculation changes caused by OCR alone;
- source-of-truth switching;
- student/parent/principal visibility changes;
- new OCR provider SDK usage outside the gateway;
- direct Gemini SDK calls from evaluation code;
- Qwen integration;
- Surya integration;
- self-hosted OCR;
- GPU infrastructure;
- background OCR workers;
- PDF rendering / multi-page fan-out infrastructure;
- real Track-A benchmark execution;
- committed real answer-sheet images;
- model fine-tuning;
- public product claim expansion.

---

## 14. Exit criteria

Phase 1 implementation may be considered complete only when all of the following
are true:

1. Phase 1 flag exists and defaults to false.
2. Flag-off behavior is unchanged.
3. Flag-on OCR uses the existing gateway only.
4. Gemini Flash routing is separate from general AI routing.
5. OCR output remains transcription-only.
6. Teacher approval remains the source of authority.
7. OCR failures and parse failures are safely isolated.
8. No schema, API, UI, marks, routing, ledger, or source-of-truth changes occur.
9. Focused tests pass.
10. App import passes.
11. `git diff --check` passes.
12. Certification report is complete.
13. ARM accepts the implementation after reviewing the diff.

---

## 15. Suggested future implementation metadata

If ARM later accepts the implementation, recommended metadata:

```text
Commit: feat(aei): add handwriting OCR phase 1 transcription gate
Tag: aei-handwriting-ocr-phase1-gemini-transcription-certified
```

These are suggestions only. They do not authorize commit, tag, or publication.

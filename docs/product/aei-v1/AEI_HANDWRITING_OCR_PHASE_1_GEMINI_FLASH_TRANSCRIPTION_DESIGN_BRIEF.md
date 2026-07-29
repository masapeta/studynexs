# AEI Handwriting OCR Phase 1 - Gemini Flash Answer-Sheet Transcription Design Brief

- **Program:** AEI v1.0 product-facing completion
- **Workstream:** Teacher evaluation experience / answer-sheet transcription
- **Phase:** Handwriting OCR Phase 1 - Gemini Flash answer-sheet transcription
- **Classification:** Product-facing design brief
- **Status:** Accepted
- **Implementation:** Not authorized by this document
- **Date:** 2026-07-29
- **Owner:** Avinash Reddy Masapeta (ARM)
- **AEI v1.0 baseline:** [`./AEI_V1_CERTIFICATION_REPORT.md`](./AEI_V1_CERTIFICATION_REPORT.md)
- **Language/OCR assist baseline:** [`./AEI_V1_BATCH_D_LANGUAGE_OCR_ASSIST_CERTIFICATION_REPORT.md`](./AEI_V1_BATCH_D_LANGUAGE_OCR_ASSIST_CERTIFICATION_REPORT.md)
- **Teacher evaluation UX baseline:** [`./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_E_CERTIFICATION_REPORT.md`](./AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_E_CERTIFICATION_REPORT.md)
- **Current project anchor:** [`../../STATUS.md`](../../STATUS.md)

---

## 1. Purpose

StudyNexs already has a certified AEI v1.0 evaluation foundation and a teacher
evaluation experience that makes trust, manual review, override reasons, and
approved evidence visible.

The next school-visible bottleneck is answer-sheet transcription.

Teachers should not have to manually type every answer when a student submits a
clear answer-sheet image. At the same time, OCR must not become grading.

Phase 1 introduces a narrow launch posture:

```text
Answer-sheet page image
        |
        v
Gemini Flash through the StudyNexs AI Gateway
        |
        v
Per-question transcription
        |
        v
Existing AEI evaluation / teacher review flow
```

The product principle is:

```text
OCR reads. AEI evaluates. Teacher decides.
```

This design brief defines the intended product and engineering boundary only. It
does not authorize code, configuration, schema, API, UI, rollout, public product
claim, or runtime behavior changes by itself.

---

## 2. Strategic context

The accepted OCR plan has three phases:

| Phase | Posture | Purpose |
|---|---|---|
| Phase 1 - Launch | Gemini Flash via gateway | Use a managed vision model for answer-sheet transcription without new GPU infrastructure. |
| Phase 2 - Validate | Track-A Golden Set benchmark | Compare Gemini Flash, Qwen2.5-VL-7B, and Surya 2 on real teacher-verified sheets. |
| Phase 3 - Optimize | Confidence-routed chain | Use benchmark evidence and real AI bill data before adding self-hosted or rented-GPU optimization. |

This document covers Phase 1 only.

Phase 1 should not prematurely introduce Qwen, Surya, self-hosted inference,
GPU operations, or model benchmarking. Those belong to Phase 2 / Phase 3 after
real sheet evidence exists.

---

## 3. Product objective

Phase 1 should answer one question:

> Can StudyNexs transcribe supported answer-sheet page images through Gemini
> Flash safely enough for teachers to review and correct, without changing who
> owns marks?

The answer must be yes only inside a declared supported input scope.

Supported Phase 1 input should be:

- page-level answer-sheet images already accepted by the existing answer-sheet
  upload flow;
- common classroom handwriting quality that is legible to a teacher;
- typed or printed answer text on answer-sheet images;
- question-numbered responses where the existing exam question schema can guide
  extraction.

Unsupported or uncertain Phase 1 input should route to teacher correction
rather than pretending the OCR is authoritative.

---

## 4. Why Gemini Flash is used in Phase 1

Phase 1 should use Gemini Flash as a managed answer-sheet transcription provider
because it keeps launch operationally simple:

- no GPU provisioning;
- no self-hosted model serving;
- no new inference infrastructure;
- no model-ops burden during initial school usage;
- cost can be measured before optimizing.

This is a launch choice, not a permanent monopoly.

The architecture must preserve provider substitutability through the existing
StudyNexs AI Gateway. The answer-sheet OCR service must not call Gemini directly
or import a provider SDK outside the gateway.

---

## 5. Existing foundation to reuse

Phase 1 should reuse the existing architecture rather than creating a parallel
OCR stack.

### 5.1 AI Gateway routing

The latest gateway hardening separates general reasoning from answer-sheet
vision routing:

```text
General AI
  primary: Ollama gemma4 cloud
  fallback: OpenAI gpt-4o

Answer-sheet OCR / vision
  primary: Gemini Flash
  fallback: Ollama gemma4 cloud
```

Expected runtime configuration shape:

```text
AI_DEFAULT_PROVIDER=ollama
AI_DEFAULT_MODEL=gemma4:cloud
AI_FALLBACK_PROVIDER=openai
AI_FALLBACK_MODEL=gpt-4o

AI_VISION_PRIMARY_PROVIDER=gemini
AI_VISION_PRIMARY_MODEL=gemini-1.5-flash
AI_VISION_FALLBACK_PROVIDER=ollama
AI_VISION_FALLBACK_MODEL=gemma4:cloud
```

Secrets such as `GEMINI_API_KEY`, `OPENAI_API_KEY`, and `OLLAMA_API_KEY` must be
provided through the environment or secret manager. They must never be committed
to the repository.

### 5.2 Existing answer-sheet vision seam

Phase 1 should build on:

```text
apps/api/app/modules/examinations/services/answer_sheet_vision.py
```

That service already:

- accepts image bytes and MIME type;
- sends the image through the gateway;
- asks for per-question answer JSON;
- sanitizes extracted answers;
- returns transcription output and gateway metering information.

Phase 1 should harden and productize this path. It should not create a second
answer-sheet OCR service.

### 5.3 Existing teacher trust surface

Phase 1 should continue to rely on the certified teacher evaluation experience:

- OCR-derived answers are suggestions / inputs for review, not final authority;
- low-confidence or ambiguous extraction remains teacher-confirmed;
- teacher override and approval remain required before evidence is authoritative;
- student and parent views consume only teacher-approved evidence.

---

## 6. Responsibilities

Phase 1 is responsible for:

1. invoking Gemini Flash for answer-sheet page transcription through the gateway;
2. keeping transcription separate from evaluation and marking;
3. returning sanitized per-question answer text;
4. preserving existing objective / subjective evaluation behavior after
   transcription;
5. recording operational evidence for OCR invocation, completion, failure,
   fallback, and parse quality;
6. ensuring unsupported, blank, ambiguous, or failed OCR does not block teacher
   review;
7. providing Golden Harness and certification evidence for the supported
   transcription scope.

Phase 1 is not responsible for:

- choosing the permanent OCR model;
- benchmarking Qwen or Surya;
- self-hosted OCR;
- universal handwriting support;
- autonomous grading;
- public OCR reliability claims.

---

## 7. Runtime posture

Phase 1 must be explicit, controlled, and reversible.

### 7.1 Feature flag

Answer-sheet OCR Phase 1 should be guarded by a dedicated default-off feature
flag:

```text
AEI_HANDWRITING_OCR_PHASE1_ENABLED=false
```

The provider configuration and `GEMINI_API_KEY` are necessary but not sufficient
to activate the Phase 1 school-facing OCR path.

This prevents accidental activation when a key is added for development,
testing, or future benchmarking.

### 7.2 Disabled behavior

When `AEI_HANDWRITING_OCR_PHASE1_ENABLED=false`:

- Phase 1 Gemini transcription must not run;
- existing teacher-entered/manual answer behavior must remain unchanged;
- no marks, routing, ledger, UI, API, or schema behavior changes are allowed;
- rollback is immediate by disabling the flag.

### 7.3 Enabled behavior

When `AEI_HANDWRITING_OCR_PHASE1_ENABLED=true` and the vision provider is
configured:

- supported answer-sheet images may be transcribed through the gateway;
- extracted text may fill missing answers in the existing evaluation flow;
- extracted text must be sanitized and bounded;
- transcription failure must not fail the entire teacher workflow unless the
  existing upload/evaluation path already treats the input as invalid;
- low-confidence, blank, ambiguous, or unavailable confidence should preserve
  teacher-review posture.

---

## 8. Trust and safety rules

Phase 1 must preserve the core AEI trust model:

```text
AI recommendation is draft.
Teacher approval is authority.
Approved evidence is the downstream source.
```

Rules:

1. OCR output is transcription, not a mark.
2. OCR output must never bypass AEI review policy or teacher approval.
3. OCR failures must be exception-isolated where possible.
4. Low-confidence or confidence-unavailable OCR should be treated as requiring
   teacher confirmation.
5. Raw image bytes must never be logged.
6. Raw OCR text must not appear in metrics or low-level structured logs.
7. Tenant and student identifiers must not be used as high-cardinality metric
   labels.
8. Gemini must be invoked only through the gateway so metering, guardrails,
   timeout, fallback, and provider routing remain centralized.

---

## 9. Supported output contract

Phase 1 should keep the output intentionally simple:

```json
{
  "answers": {
    "1": "transcribed answer text",
    "2": "",
    "3": "transcribed answer text"
  }
}
```

The existing service should continue to sanitize the response and discard unsafe
or malformed content.

Future phases may add richer extraction metadata, bounding boxes, per-line
confidence, layout evidence, or page-level provenance. Phase 1 should not block
those future improvements, but it should not implement them speculatively.

---

## 10. Observability

Phase 1 should record operational evidence, not product analytics.

Recommended metrics / structured events:

| Signal | Purpose |
|---|---|
| `aei_handwriting_ocr_phase1.invoked` | Count enabled OCR attempts. |
| `aei_handwriting_ocr_phase1.completed` | Count successful gateway completions. |
| `aei_handwriting_ocr_phase1.failed` | Count isolated failures. |
| `aei_handwriting_ocr_phase1.unsupported_mime` | Count unsupported file types. |
| `aei_handwriting_ocr_phase1.parse_failed` | Count malformed provider responses. |
| `aei_handwriting_ocr_phase1.fallback_used` | Count fallback provider usage. |
| `aei_handwriting_ocr_phase1.duration_ms` | Track execution duration. |

Labels must remain low-cardinality. Do not label metrics by student, teacher,
file name, raw tenant ID, question text, or answer text.

---

## 11. Golden Harness and Track-A dataset posture

Phase 1 should add the first OCR Golden Harness foundation, but it should not
pretend synthetic or sanitized cases prove real handwriting performance.

Two tracks should be kept distinct:

### 11.1 Repository-safe Golden Harness

Purpose:

- deterministic unit/regression coverage;
- prompt / parser / sanitization posture;
- blank and illegible answer handling;
- provider-failure behavior;
- feature-flag behavior.

This dataset must not contain real student PII or raw school answer-sheet
images.

### 11.2 Track-A real sheet golden set

Purpose:

- 50-100 real sheets;
- teacher-verified transcriptions;
- Telugu-influenced and local handwriting realities;
- benchmark Gemini Flash vs Qwen2.5-VL-7B vs Surya 2 in Phase 2.

Track-A can be planned during Phase 1, but benchmark execution belongs to
Phase 2. Real images and transcriptions must follow the project's privacy,
consent, retention, and access-control rules.

---

## 12. PDF and multi-page behavior

Phase 1 is scoped to answer-sheet page images.

If the existing upload pipeline already supplies image pages to the OCR service,
Phase 1 may use those page images.

Phase 1 does not authorize:

- new PDF rendering infrastructure;
- multi-page PDF fan-out;
- background OCR workers;
- persistent OCR job queues;
- document-layout extraction beyond per-question answer text.

Those may be designed later if real school workflows require them.

---

## 13. Explicit non-goals

Phase 1 is not:

- a handwriting OCR benchmark;
- a Qwen implementation;
- a Surya implementation;
- a self-hosted OCR deployment;
- a GPU operations project;
- a grading feature;
- an evidence-ledger redesign;
- a teacher-review routing redesign;
- a parent/student visibility feature;
- a universal OCR capability claim;
- a source-of-truth switch.

---

## 14. Explicit exclusions

The following are out of scope unless separately authorized:

- database schema changes;
- Alembic migrations;
- public API contract changes;
- UI changes;
- public product capability claim changes;
- direct Gemini SDK calls from evaluation services;
- new provider SDK integrations outside the existing gateway;
- LLM marking behavior changes;
- marks changes caused by OCR alone;
- teacher review routing changes;
- evidence ledger behavior changes;
- student/parent/principal consumer changes;
- source-of-truth switching;
- storing raw OCR transcripts outside the existing evaluation data path;
- committing real answer-sheet images or student data to the repository;
- Qwen, Surya, or LocateAnything integration;
- self-hosted inference;
- fine-tuning.

---

## 15. Certification expectations

Before Phase 1 can be accepted after implementation, certification should prove:

1. feature flag defaults off;
2. flag-off behavior is unchanged;
3. flag-on path invokes the configured vision provider through the gateway only;
4. Gemini Flash model routing does not affect the general Ollama / OpenAI
   reasoning path;
5. unsupported MIME types do not invoke OCR;
6. provider exceptions are isolated;
7. malformed provider JSON is handled safely;
8. sanitized answer extraction is deterministic;
9. OCR output does not autonomously approve marks;
10. low-confidence or confidence-unavailable OCR remains teacher-confirmed;
11. no schema, API, UI, routing, ledger, or source-of-truth changes occurred;
12. focused tests and adjacent regression tests pass;
13. `python -c "import app.main"` passes;
14. `git diff --check` passes;
15. certification report is produced.

---

## 16. ARM review decision

ARM accepts this design brief as the Phase 1 design baseline.

The implementation authorization contract is the controlling implementation
boundary:

[`./AEI_HANDWRITING_OCR_PHASE_1_GEMINI_FLASH_TRANSCRIPTION_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md`](./AEI_HANDWRITING_OCR_PHASE_1_GEMINI_FLASH_TRANSCRIPTION_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md)

Implementation may proceed only inside that accepted contract.

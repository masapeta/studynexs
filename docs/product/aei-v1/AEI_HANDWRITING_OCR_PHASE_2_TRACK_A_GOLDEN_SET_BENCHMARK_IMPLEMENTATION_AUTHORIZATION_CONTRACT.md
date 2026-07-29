# AEI Handwriting OCR Phase 2 - Track-A Golden Set Benchmark Implementation Authorization Contract

- **Program:** AEI v1.0 product-facing completion
- **Workstream:** Teacher evaluation experience / answer-sheet transcription
- **Phase:** Handwriting OCR Phase 2 - Track-A Golden Set benchmark
- **Classification:** Implementation authorization contract
- **Authorization ID:** AEI-HANDWRITING-OCR-PHASE2-AUTH-001
- **Status:** Accepted
- **Implementation:** Authorized for Phase 2 only
- **Date:** 2026-07-29
- **Owner:** Avinash Reddy Masapeta (ARM)
- **Design baseline:** [`./AEI_HANDWRITING_OCR_PHASE_2_TRACK_A_GOLDEN_SET_BENCHMARK_DESIGN_BRIEF.md`](./AEI_HANDWRITING_OCR_PHASE_2_TRACK_A_GOLDEN_SET_BENCHMARK_DESIGN_BRIEF.md)
- **Phase 1 baseline:** [`./AEI_HANDWRITING_OCR_PHASE_1_GEMINI_FLASH_TRANSCRIPTION_CERTIFICATION_REPORT.md`](./AEI_HANDWRITING_OCR_PHASE_1_GEMINI_FLASH_TRANSCRIPTION_CERTIFICATION_REPORT.md)
- **Current project anchor:** [`../../STATUS.md`](../../STATUS.md)

---

## 1. Purpose

Authorize, if accepted by ARM, a narrow Phase 2 validation implementation that
creates the Track-A Golden Set benchmark foundation for answer-sheet OCR.

The implementation should answer:

> How will StudyNexs measure Gemini Flash, Qwen2.5-VL-7B, and Surya 2 against
> real teacher-verified answer sheets without changing production behavior?

Phase 2 produces benchmark infrastructure and evidence. It does not choose or
activate a new production OCR provider.

---

## 2. Authorization posture

This contract is accepted by ARM.

It authorizes only the scope below. It does not authorize commit, tag, or
publication without a separate post-implementation ARM review and publication
approval.

---

## 3. Authorized implementation scope

Implementation is authorized only for:

1. defining a repository-safe Track-A manifest schema;
2. defining a teacher-verified transcription template;
3. adding synthetic Golden Harness cases for benchmark scoring behavior;
4. adding deterministic scoring helpers for:
   - character error rate;
   - word error rate;
   - per-question extraction accuracy;
   - blank-answer accuracy;
   - JSON/schema validity;
   - hallucination / extra-text indicators;
5. adding offline benchmark report templates;
6. adding license/commercial-use review placeholders for each candidate;
7. adding documentation for secure Track-A data handling outside git;
8. adding tests proving:
   - manifest validation;
   - scoring determinism;
   - real-data exclusion posture;
   - no production source switch;
9. producing a certification report:

   ```text
   docs/product/aei-v1/
   AEI_HANDWRITING_OCR_PHASE_2_TRACK_A_GOLDEN_SET_BENCHMARK_CERTIFICATION_REPORT.md
   ```

This contract may authorize benchmark harness scaffolding. It does not authorize
committing real sheets, real teacher transcriptions, or raw OCR output from real
students.

---

## 4. Candidate benchmark boundary

Permitted candidate labels:

```text
gemini_flash
qwen2_5_vl_7b
surya_2
```

These are benchmark candidate identifiers only.

Before a candidate is run against real Track-A data, implementation must record:

- model/provider label;
- model version if known;
- execution environment;
- license/commercial-use posture;
- whether real student data leaves local/staging infrastructure;
- whether additional ARM/legal review is required.

Any candidate that does not have acceptable commercial-use posture must be
excluded from runtime adoption and may only be retained as a research note if
ARM explicitly permits it.

---

## 5. Authorized repository boundary

### 5.1 Documentation and certification

Implementation may add:

```text
docs/product/aei-v1/AEI_HANDWRITING_OCR_PHASE_2_TRACK_A_GOLDEN_SET_BENCHMARK_CERTIFICATION_REPORT.md
docs/product/aei-v1/AEI_HANDWRITING_OCR_PHASE_2_TRACK_A_GOLDEN_SET_BENCHMARK_REPORT_TEMPLATE.md
docs/product/aei-v1/AEI_HANDWRITING_OCR_PHASE_2_TRACK_A_DATA_HANDLING_GUIDE.md
```

Implementation may update the Phase 2 design and contract only to mark final
accepted/implemented status after ARM review, if that follows the established
project pattern.

Post-publication status updates must be committed separately:

```text
docs/STATUS.md
```

### 5.2 Repository-safe Golden Harness

Implementation may add synthetic fixtures under:

```text
apps/api/tests/golden/aei_v1/
```

Permitted examples:

- synthetic OCR candidate output;
- synthetic teacher-verified transcription;
- manifest schema example;
- benchmark expected metrics.

Forbidden examples:

- real answer-sheet image;
- real teacher-verified student answer;
- real student name, roll number, school name, phone number, or identifying
  handwriting sample.

### 5.3 Benchmark helper code

Implementation may add deterministic offline helpers under:

```text
apps/api/app/modules/examinations/services/
apps/api/scripts/
apps/api/tests/
```

Only for:

- schema validation;
- synthetic / local manifest loading;
- deterministic metric computation;
- aggregate report generation.

Any helper that calls a live provider must be manual/offline only, must require
explicit environment configuration, and must not be imported by production
evaluation services.

### 5.4 Protected production runtime

The following must not be changed:

- production answer-sheet evaluation source selection;
- `AEI_HANDWRITING_OCR_PHASE1_ENABLED` semantics;
- teacher evaluation UI;
- public APIs;
- database schema;
- Alembic migrations;
- evidence ledger behavior;
- marks calculation;
- teacher-review routing;
- student/parent/principal consumers;
- production deployment configuration;
- billing behavior;
- RBAC / tenant isolation.

---

## 6. Data handling requirements

Track-A real data must remain outside git.

Required controls:

1. use anonymized sample IDs;
2. store real images and real transcriptions outside the repository;
3. redact student/school identifiers where possible;
4. avoid raw OCR text in application logs;
5. commit only schemas, synthetic fixtures, and aggregate reports;
6. document where real data lives without exposing secrets or raw paths that
   reveal PII;
7. keep benchmark outputs aggregate-only unless the examples are synthetic.

If these controls cannot be met, implementation must stop and request ARM
direction.

---

## 7. Metrics contract

Implementation must define deterministic metrics for:

| Metric | Required |
|---|---:|
| Character Error Rate (CER) | Yes |
| Word Error Rate (WER) | Yes |
| Per-question extraction accuracy | Yes |
| Blank-answer accuracy | Yes |
| JSON/schema validity | Yes |
| Hallucination / extra-text indicator | Yes |
| Latency per page | Report template only |
| Cost per page | Report template only |
| Failure / timeout rate | Report template only |
| Manual-review trigger rate | Report template only |

Metric computation must be deterministic and unit-tested on synthetic cases.

---

## 8. Validation requirements

Before ARM acceptance after implementation, the implementer must run and report:

```text
ruff check <changed API files and tests>
pytest <focused Phase 2 benchmark tests>
python -c "import app.main"
git diff --check
```

If live candidate benchmarking is performed manually, it must be recorded as
manual evidence and must not be required for CI.

---

## 9. Explicit exclusions

This contract does not authorize:

- production OCR provider switch;
- confidence-routed production OCR chain;
- Qwen runtime integration into evaluation;
- Surya runtime integration into evaluation;
- GPU infrastructure;
- self-hosted model serving;
- direct provider SDK calls from production evaluation services;
- model fine-tuning;
- schema changes;
- API changes;
- UI changes;
- marks changes;
- teacher-review routing changes;
- evidence-ledger behavior changes;
- source-of-truth switching;
- public OCR capability claim expansion;
- committing real answer sheets;
- committing real teacher transcriptions with student data;
- parent/student visibility changes.

---

## 10. Certification deliverable

Implementation must produce:

```text
docs/product/aei-v1/
AEI_HANDWRITING_OCR_PHASE_2_TRACK_A_GOLDEN_SET_BENCHMARK_CERTIFICATION_REPORT.md
```

The report must include:

- scope compliance;
- repository boundary verification;
- data-handling proof;
- candidate/license posture;
- metrics proof;
- synthetic Golden Harness evidence;
- no runtime behavior change proof;
- validation commands and results;
- known limitations;
- ARM recommendation.

---

## 11. Exit criteria

Phase 2 implementation may be considered complete only when:

1. Track-A schema/template exists;
2. deterministic benchmark metrics exist and are tested;
3. repository-safe synthetic Golden Harness cases exist;
4. data-handling guide exists;
5. benchmark report template exists;
6. no real student sheets or real identifiable transcripts are committed;
7. no production OCR source switch occurs;
8. no schema/API/UI/marks/routing/ledger/source-of-truth changes occur;
9. focused tests pass;
10. app import passes;
11. `git diff --check` passes;
12. certification report is complete;
13. ARM accepts the implementation after reviewing the diff.

---

## 12. Suggested future implementation metadata

If ARM later accepts the implementation, recommended metadata:

```text
Commit: feat(aei): add handwriting OCR Track-A benchmark foundation
Tag: aei-handwriting-ocr-phase2-track-a-benchmark-certified
```

These are suggestions only. They do not authorize commit, tag, or publication.

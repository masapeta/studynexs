# AEI Handwriting OCR Phase 2 - Live Track-A Benchmark Run Authorization Contract

- **Program:** AEI v1.0 product-facing completion
- **Workstream:** Teacher evaluation experience / answer-sheet transcription
- **Phase:** Handwriting OCR Phase 2 - Live Track-A benchmark run
- **Classification:** Operational benchmark run authorization contract
- **Authorization ID:** AEI-HANDWRITING-OCR-PHASE2-LIVE-RUN-AUTH-001
- **Status:** Accepted
- **Execution:** Prerequisite-gated; live run not authorized to start until ARM confirms all live-run prerequisites
- **Date:** 2026-07-29
- **Owner:** Avinash Reddy Masapeta (ARM)
- **Phase 2 foundation baseline:** [`./AEI_HANDWRITING_OCR_PHASE_2_TRACK_A_GOLDEN_SET_BENCHMARK_CERTIFICATION_REPORT.md`](./AEI_HANDWRITING_OCR_PHASE_2_TRACK_A_GOLDEN_SET_BENCHMARK_CERTIFICATION_REPORT.md)
- **Data handling guide:** [`./AEI_HANDWRITING_OCR_PHASE_2_TRACK_A_DATA_HANDLING_GUIDE.md`](./AEI_HANDWRITING_OCR_PHASE_2_TRACK_A_DATA_HANDLING_GUIDE.md)
- **Benchmark report template:** [`./AEI_HANDWRITING_OCR_PHASE_2_TRACK_A_GOLDEN_SET_BENCHMARK_REPORT_TEMPLATE.md`](./AEI_HANDWRITING_OCR_PHASE_2_TRACK_A_GOLDEN_SET_BENCHMARK_REPORT_TEMPLATE.md)
- **Current project anchor:** [`../../STATUS.md`](../../STATUS.md)

---

## 1. Purpose

Authorize, if accepted by ARM, a controlled live Track-A benchmark run using
50-100 secured, teacher-verified real answer-sheet pages.

The live run should produce one output:

```text
Aggregate OCR candidate comparison report
```

The live run should answer:

> Which OCR candidate is most trustworthy for StudyNexs answer-sheet
> transcription under real local handwriting and classroom conditions?

This contract does not authorize any production OCR source switch.

---

## 2. Authorization posture

This contract is accepted by ARM as the live Track-A benchmark run control
document.

Acceptance of this contract is one required gate. It does not, by itself,
confirm the real-data prerequisites or authorize immediate execution.

Until ARM confirms all prerequisites:

- no real Track-A answer sheets may be benchmarked;
- no real teacher-verified transcriptions may be processed;
- no real sheet paths may be committed;
- no live Gemini/Qwen/Surya benchmark run is authorized;
- no external provider may receive real Track-A data;
- no production OCR source switch is authorized;
- no UI/API/schema/marks/routing/ledger behavior change is authorized.

After ARM confirms the prerequisites, this contract authorizes only the
controlled live benchmark run described below.

---

## 3. Live-run prerequisites

The benchmark run may start only after ARM confirms all of the following:

| Prerequisite | Required evidence |
|---|---|
| Dataset size | 50-100 answer-sheet pages selected for Track-A. |
| Teacher verification | Each sample has teacher-verified transcription truth. |
| Secure storage | Real images and real transcriptions are stored outside git. |
| Anonymization | Each sample uses an anonymized `track-a-*` sample ID. |
| Redaction | Student names, roll numbers, school names, phone numbers, and direct identifiers are removed or masked where possible. |
| Access control | Only authorized benchmark reviewers can access the dataset. |
| Candidate license posture | Candidate commercial-use posture is recorded before real-data execution. |
| Credential posture | Provider keys are supplied through environment/secret manager only. |
| Report posture | Committed output will be aggregate-only and non-identifying. |

If any prerequisite is missing, execution must pause.

---

## 4. Authorized live-run scope

If accepted, the live run is authorized only for:

1. loading the secured Track-A manifest from outside the repository;
2. reading secured answer-sheet pages from the approved storage location;
3. running candidate OCR transcription against the selected pages;
4. scoring candidate outputs with the certified Phase 2 benchmark metrics:
   - character error rate;
   - word error rate;
   - per-question extraction accuracy;
   - blank-answer accuracy;
   - hallucination indicators;
   - schema validity;
   - latency per page;
   - cost per page where available;
   - failure / timeout rate;
5. producing an aggregate candidate comparison report using the accepted report
   template;
6. recording candidate license and real-data handling posture;
7. recording operational run metadata;
8. committing only repository-safe aggregate outputs.

The live run is an evidence activity. It is not production integration.

---

## 5. Candidate execution boundary

Permitted benchmark candidates:

```text
gemini_flash
qwen2_5_vl_7b
surya_2
```

Candidate execution rules:

1. Gemini Flash may be benchmarked as the Phase 1 managed baseline.
2. Qwen may be benchmarked only after its commercial-use and deployment posture
   are confirmed for the specific model/version used.
3. Surya may be benchmarked only after its commercial-use and deployment
   posture are confirmed for the specific model/version used.
4. Any candidate with unresolved commercial-use restrictions must be excluded
   from real-data execution or marked research-only with ARM approval.
5. No candidate may be integrated into production evaluation as part of this
   live run.

---

## 6. Authorized artifacts

The live run may produce or update:

```text
docs/product/aei-v1/AEI_HANDWRITING_OCR_PHASE_2_LIVE_TRACK_A_BENCHMARK_RUN_REPORT.md
docs/product/aei-v1/AEI_HANDWRITING_OCR_PHASE_2_LIVE_TRACK_A_BENCHMARK_RUN_CERTIFICATION_REPORT.md
```

Permitted committed content:

- aggregate metrics;
- candidate labels;
- dataset version;
- anonymized sample count;
- non-identifying qualitative observations;
- license posture summary;
- benchmark command transcript with secrets removed;
- operational caveats.

Forbidden committed content:

- real answer-sheet images;
- base64-encoded real images;
- raw real teacher transcriptions;
- raw per-sample OCR output from real sheets;
- real student names;
- roll numbers;
- school names;
- phone numbers;
- provider API keys;
- exact private storage paths if they reveal school/student context.

---

## 7. Data handling requirements

The live run must follow the accepted data handling guide.

Additional live-run requirements:

1. Do not copy Track-A data into the repository.
2. Do not paste Track-A images or raw transcriptions into chat.
3. Do not attach real sheets to pull requests.
4. Do not include raw sample-level outputs in committed artifacts.
5. Do not log raw OCR text from real sheets.
6. Delete local temporary benchmark outputs after aggregate report generation
   unless ARM explicitly approves retention.
7. Keep raw benchmark outputs in secured storage only if needed for audit.

---

## 8. Aggregate report requirements

The aggregate report must include:

- run ID;
- run date;
- dataset version;
- sample count;
- candidate names and versions;
- candidate execution environments;
- candidate license/commercial-use posture;
- real-data handling posture;
- aggregate CER;
- aggregate WER;
- per-question extraction accuracy;
- blank-answer accuracy;
- hallucination rate;
- schema validity;
- failure / timeout rate;
- latency per page;
- cost per page where available;
- recommendation;
- known limitations.

The report must not include raw real student answers.

---

## 9. Explicit exclusions

This contract does not authorize:

- production OCR provider switch;
- confidence-routed production OCR chain;
- Phase 3 optimization implementation;
- runtime Qwen integration;
- runtime Surya integration;
- GPU infrastructure as production dependency;
- self-hosted model serving as production dependency;
- schema changes;
- API changes;
- UI changes;
- marks changes;
- teacher-review routing changes;
- evidence-ledger behavior changes;
- source-of-truth switching;
- parent/student visibility changes;
- public OCR claim expansion;
- model fine-tuning;
- committing real Track-A data.

---

## 10. Stop conditions

The live run must stop if:

- real student identifiers are found in the dataset and cannot be redacted;
- dataset storage is not access-controlled;
- candidate license posture is unresolved for a real-data run;
- provider credentials would need to be hard-coded;
- raw data would need to be committed to complete the report;
- a candidate requires a production code change to benchmark;
- benchmark execution would alter production evaluation behavior;
- ARM withdraws authorization.

---

## 11. Acceptance criteria

The live run may be accepted only when:

1. 50-100 secured real pages were benchmarked, or the report explicitly explains
   why the sample count differs;
2. every included sample had teacher-verified transcription truth;
3. candidate license/commercial-use posture was recorded;
4. benchmark metrics were computed using the certified Phase 2 foundation or an
   equivalent reviewed scorer;
5. aggregate report was produced;
6. no real answer sheets or real identifiable transcripts were committed;
7. no production source switch occurred;
8. no schema/API/UI/marks/routing/ledger behavior changed;
9. secrets were not committed;
10. ARM reviews and accepts the aggregate report.

---

## 12. Suggested future metadata

If ARM later accepts the live-run evidence, recommended commit metadata:

```text
Commit: docs(aei): add handwriting OCR Track-A live benchmark report
Tag: aei-handwriting-ocr-phase2-live-track-a-benchmark-reviewed
```

These are suggestions only. They do not authorize commit, tag, publication, or
Phase 3 optimization.

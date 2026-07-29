# AEI Handwriting OCR Phase 2 - Track-A Golden Set Benchmark Design Brief

- **Program:** AEI v1.0 product-facing completion
- **Workstream:** Teacher evaluation experience / answer-sheet transcription
- **Phase:** Handwriting OCR Phase 2 - Track-A Golden Set benchmark
- **Classification:** Product-facing validation design brief
- **Status:** Accepted
- **Implementation:** Not authorized by this document
- **Date:** 2026-07-29
- **Owner:** Avinash Reddy Masapeta (ARM)
- **Phase 1 baseline:** [`./AEI_HANDWRITING_OCR_PHASE_1_GEMINI_FLASH_TRANSCRIPTION_CERTIFICATION_REPORT.md`](./AEI_HANDWRITING_OCR_PHASE_1_GEMINI_FLASH_TRANSCRIPTION_CERTIFICATION_REPORT.md)
- **Current project anchor:** [`../../STATUS.md`](../../STATUS.md)

---

## 1. Purpose

Phase 1 made Gemini Flash answer-sheet transcription available behind an
explicit default-off gate:

```text
AEI_HANDWRITING_OCR_PHASE1_ENABLED=false
```

Phase 2 should not switch providers, expand product claims, or change teacher
workflow. It should answer a narrower validation question:

> Which OCR / vision candidate performs best on StudyNexs' real answer sheets,
> under teacher-verified ground truth, for the supported launch scope?

The output of Phase 2 is evidence, not runtime adoption.

---

## 2. Product principle

The Phase 1 principle remains unchanged:

```text
OCR reads. AEI evaluates. Teacher decides.
```

Phase 2 adds one validation principle:

```text
The OCR provider is chosen from StudyNexs sheets, not public leaderboard claims.
```

No model should become the production OCR source because it is fashionable,
cheap, open, or impressive in a generic benchmark. It must perform on the actual
handwriting, languages, scan quality, and answer-sheet formats StudyNexs schools
use.

---

## 3. Strategic context

The accepted three-phase OCR plan is:

| Phase | Posture | Purpose |
|---|---|---|
| Phase 1 - Launch | Gemini Flash via gateway | Managed OCR launch path with no GPU infrastructure. |
| Phase 2 - Validate | Track-A Golden Set benchmark | Compare candidates against teacher-verified real sheets. |
| Phase 3 - Optimize | Confidence-routed chain | Use real accuracy/cost evidence before adding self-hosted or rented-GPU optimization. |

This document covers Phase 2 only.

Phase 2 is the evidence gate before any provider optimization or source
adoption decision.

---

## 4. Candidate model posture

Phase 2 should compare the current managed path against candidate alternatives.

Initial candidate list:

| Candidate | Role in Phase 2 | Runtime adoption status |
|---|---|---|
| Gemini Flash | Current managed Phase 1 baseline | Already gated through gateway; no automatic expansion. |
| Qwen2.5-VL-7B or successor Qwen VL candidate | License-safe local / burst-GPU candidate, subject to final license verification | Benchmark only; not production-integrated by Phase 2. |
| Surya 2 or successor OCR candidate | OCR-specialist candidate, subject to final commercial/license verification | Benchmark only; not production-integrated by Phase 2. |

Candidate names reflect the current product hypothesis, not a permanent provider
decision. Before benchmarking any non-Gemini candidate, implementation must
record a lightweight license/commercial-use review. Any candidate that cannot be
used legally for StudyNexs' commercial context must be excluded or marked
research-only.

Phase 2 must not call a provider directly from production evaluation code.

---

## 5. Track-A Golden Set

Track-A is the first real answer-sheet OCR validation dataset for StudyNexs.

Recommended size:

```text
50-100 real answer-sheet pages
```

Each page should have teacher-verified transcription ground truth.

Coverage should include:

- typical pencil handwriting;
- clear pen handwriting;
- faint / low-contrast writing;
- English-medium answers;
- Telugu-influenced English handwriting;
- common code-mixed classroom phrasing where present;
- printed / typed answer text on sheets;
- blank answers;
- crossed-out answers;
- answer numbering inconsistencies;
- short answers;
- multi-line answers;
- diagrams or formula-adjacent written answers where OCR should transcribe only
  text and not mark.

Track-A should be small enough to review quickly and rich enough to expose
local handwriting reality.

---

## 6. Data governance

Track-A is sensitive educational data.

Rules:

1. Real answer-sheet images must not be committed to git.
2. Teacher-verified real transcriptions must not be committed to git if they can
   identify a student, teacher, school, or class.
3. Dataset storage location must be outside the repository or in approved
   secure object storage.
4. Each sample must have an anonymized sample identifier.
5. Student names, roll numbers, school names, phone numbers, and other personal
   identifiers must be redacted or excluded before benchmark use where possible.
6. Benchmark outputs committed to the repository must be aggregate-only or use
   synthetic examples.
7. Raw OCR text from real sheets must not be written to normal application logs.
8. Access to Track-A must be limited to authorized reviewers.

Repository-safe artifacts may include:

- manifest schema;
- transcription template;
- synthetic sample cases;
- benchmark summary template;
- aggregate benchmark report.

---

## 7. Ground truth contract

Each Track-A item should resolve to a teacher-verified transcription contract.

Conceptual shape:

```json
{
  "sample_id": "track-a-0001",
  "artifact_type": "answer_sheet_page",
  "language_context": ["english", "telugu_influenced"],
  "image_quality": "clear | faint | skewed | mixed",
  "answer_format": "numbered | mixed | unnumbered",
  "ground_truth": {
    "answers": {
      "1": "teacher verified transcription",
      "2": "",
      "3": "teacher verified transcription"
    }
  },
  "review": {
    "reviewer_role": "teacher",
    "reviewed_at": "ISO-8601 timestamp",
    "notes": "optional bounded notes"
  }
}
```

The ground truth is transcription truth, not marking truth.

---

## 8. Benchmark metrics

Phase 2 should measure OCR/transcription quality, not grading quality.

Required metrics:

| Metric | Purpose |
|---|---|
| Character Error Rate (CER) | Detect handwriting transcription quality at character level. |
| Word Error Rate (WER) | Detect word-level usefulness for teacher review and AEI input. |
| Per-question extraction accuracy | Measure whether answers map to the right question numbers. |
| Blank-answer accuracy | Avoid hallucinating answers where the student left blanks. |
| Hallucination / extra-text rate | Detect invented or irrelevant text. |
| JSON/schema validity rate | Ensure model output can be consumed safely. |
| Manual-review trigger rate | Estimate teacher correction workload. |
| Latency per page | Estimate classroom usability. |
| Cost per page | Estimate operating cost. |
| Failure / timeout rate | Estimate operational reliability. |

Optional metrics:

- line-level exact match;
- normalized text similarity;
- language/script detection accuracy where available;
- confidence calibration if a model emits usable confidence.

---

## 9. Decision posture

Phase 2 should produce a benchmark report with one of these outcomes:

| Outcome | Meaning |
|---|---|
| Keep Gemini Flash | Managed path is accurate/cost-effective enough for the supported scope. |
| Add Qwen as confidence-routed candidate | Qwen performs well enough and has acceptable operational/license posture. |
| Add Surya as OCR-specialist candidate | Surya performs well enough and has acceptable operational/license posture. |
| No model change | Evidence is inconclusive; continue Phase 1 managed path and collect more data. |
| Do not proceed | Accuracy is not sufficient for product-facing OCR claims. |

Even if a candidate wins Phase 2, production source adoption requires a later
Phase 3 / rollout authorization.

---

## 10. Runtime posture

Phase 2 should not affect production evaluation behavior.

Allowed posture:

- offline benchmark;
- local or staging-only runs;
- controlled non-PII synthetic tests in CI;
- manual benchmark execution against secured Track-A data;
- aggregate evidence reporting.

Not allowed:

- production source switch;
- UI display changes;
- API contract changes;
- schema changes;
- marks changes;
- teacher review routing changes;
- evidence ledger behavior changes;
- parent/student visibility changes.

---

## 11. Observability and audit

Phase 2 should record benchmark evidence clearly:

- candidate name;
- candidate version/model label;
- benchmark run ID;
- dataset version;
- sample count;
- aggregate metrics;
- run timestamp;
- runner environment;
- known limitations;
- license posture summary;
- reviewer / approver.

Committed reports must avoid raw student data.

---

## 12. Explicit non-goals

Phase 2 is not:

- a production provider switch;
- a new OCR product feature;
- self-hosted OCR deployment;
- GPU operations rollout;
- confidence-routed production chain;
- teacher UI change;
- student/parent feature;
- grading benchmark;
- model fine-tuning;
- universal handwriting claim.

---

## 13. Certification expectations

Before Phase 2 can be accepted after implementation, certification should prove:

1. Track-A manifest / ground-truth contract is defined;
2. real data is kept out of git;
3. benchmark candidates are represented with license posture;
4. benchmark metrics are deterministic and documented;
5. repository-safe synthetic tests pass;
6. no production OCR provider switch occurred;
7. no schema/API/UI changes occurred;
8. no marks/routing/ledger behavior changed;
9. no raw images or raw real transcriptions were committed;
10. benchmark report is aggregate-only or synthetic-safe;
11. certification report is produced.

---

## 14. ARM review decision

ARM accepts this design brief as the Phase 2 validation design baseline.

The implementation authorization contract is the controlling implementation
boundary:

[`./AEI_HANDWRITING_OCR_PHASE_2_TRACK_A_GOLDEN_SET_BENCHMARK_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md`](./AEI_HANDWRITING_OCR_PHASE_2_TRACK_A_GOLDEN_SET_BENCHMARK_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md)

Implementation may proceed only inside that accepted contract.

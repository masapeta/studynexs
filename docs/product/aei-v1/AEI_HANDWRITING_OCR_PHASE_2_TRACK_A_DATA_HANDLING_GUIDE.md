# AEI Handwriting OCR Phase 2 - Track-A Data Handling Guide

- **Program:** AEI v1.0 product-facing completion
- **Workstream:** Teacher evaluation experience / answer-sheet transcription
- **Phase:** Handwriting OCR Phase 2 - Track-A Golden Set benchmark
- **Classification:** Data handling guide
- **Status:** Accepted with Phase 2 certification
- **Date:** 2026-07-29
- **Owner:** Avinash Reddy Masapeta (ARM)

---

## 1. Purpose

Track-A is the first real answer-sheet OCR validation dataset for StudyNexs.

It should contain 50-100 real answer-sheet pages with teacher-verified
transcription ground truth.

This guide defines how Track-A data may be collected and used without turning
real student work into repository content.

---

## 2. Non-negotiable rule

```text
Real Track-A sheets and real identifiable teacher transcriptions do not go into git.
```

The repository may contain:

- schemas;
- templates;
- synthetic fixtures;
- aggregate benchmark summaries;
- non-identifying instructions.

The repository must not contain:

- real answer-sheet images;
- base64-encoded real images;
- real student names;
- roll numbers;
- school names;
- phone numbers;
- identifiable handwriting samples;
- raw per-student OCR output.

---

## 3. Recommended Track-A manifest shape

Each secured real sample should be described by an anonymized manifest entry:

```json
{
  "sample_id": "track-a-0001",
  "artifact_type": "answer_sheet_page",
  "secure_image_ref": "external-secure-location-only",
  "language_context": ["english", "telugu_influenced"],
  "image_quality": "clear",
  "answer_format": "numbered",
  "ground_truth": {
    "answers": {
      "1": "teacher verified transcription",
      "2": ""
    }
  },
  "review": {
    "reviewer_role": "teacher",
    "reviewed_at": "2026-07-29T00:00:00+05:30",
    "notes": "bounded non-identifying notes"
  }
}
```

The real manifest and the real images should live outside the repository.

---

## 4. Redaction requirements

Before any sample is benchmarked:

1. remove or mask student names;
2. remove or mask roll numbers and admission numbers;
3. remove school identifiers where possible;
4. avoid collecting phone numbers, addresses, or parent identifiers;
5. keep teacher notes bounded and non-identifying;
6. use anonymized sample IDs in benchmark outputs.

If a page cannot be reasonably de-identified, exclude it from Track-A unless ARM
explicitly approves a more controlled review process.

---

## 5. Access control posture

Track-A should be accessible only to authorized benchmark reviewers.

Minimum expectation:

- limited access group;
- audit-friendly storage location;
- no public buckets or shared drives;
- no screenshots in chat tools;
- no raw images in pull requests;
- no raw images in CI artifacts.

---

## 6. Benchmark output posture

Committed benchmark outputs must be:

- aggregate;
- candidate-labeled;
- dataset-versioned;
- free of raw student text unless the text is synthetic;
- free of raw image references;
- free of personal identifiers.

Acceptable committed output:

```text
Gemini Flash - CER 0.08, WER 0.14, sample_count 80
```

Unacceptable committed output:

```text
track-a-0042, Ravi Kumar, roll no 17, raw OCR answer...
```

---

## 7. Live provider handling

If a manual benchmark run sends real Track-A pages to an external provider,
record:

- provider;
- model;
- region / endpoint if known;
- whether data retention is disabled or governed;
- license/commercial-use posture;
- whether additional ARM/legal review is required.

Do not hard-code provider credentials or real data paths in scripts.

---

## 8. Exit requirement

Before any OCR source switch is considered, Phase 2 must produce an aggregate
benchmark report and ARM must approve a separate Phase 3 / rollout
authorization.


# AEI Handwriting OCR Phase 2 - Track-A Benchmark Report Template

- **Program:** AEI v1.0 product-facing completion
- **Workstream:** Teacher evaluation experience / answer-sheet transcription
- **Phase:** Handwriting OCR Phase 2 - Track-A Golden Set benchmark
- **Classification:** Benchmark report template
- **Status:** Accepted with Phase 2 certification
- **Date:** 2026-07-29
- **Owner:** Avinash Reddy Masapeta (ARM)

---

## 1. Run metadata

| Field | Value |
|---|---|
| Benchmark run ID | `<run-id>` |
| Dataset version | `<track-a-version>` |
| Sample count | `<50-100 recommended>` |
| Run date | `<date>` |
| Runner | `<authorized reviewer>` |
| Environment | `<local / staging / controlled GPU / managed provider>` |
| Real data location | `External secure storage; do not paste raw path if it reveals PII` |

---

## 2. Candidate posture

| Candidate | Model/version | Execution environment | License/commercial-use posture | Real-data handling posture | Eligible for adoption? |
|---|---|---|---|---|---|
| Gemini Flash | `<model>` | `<gateway/manual>` | `<reviewed>` | `<provider handling>` | `<yes/no/pending>` |
| Qwen2.5-VL-7B | `<model>` | `<local/burst GPU>` | `<reviewed>` | `<local/provider handling>` | `<yes/no/pending>` |
| Surya 2 | `<model>` | `<local/burst GPU>` | `<reviewed>` | `<local/provider handling>` | `<yes/no/pending>` |

---

## 3. Aggregate metrics

| Candidate | CER | WER | Per-question extraction accuracy | Blank-answer accuracy | Hallucination rate | Schema validity | Failure/timeout rate | Latency/page | Cost/page |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Gemini Flash | `<value>` | `<value>` | `<value>` | `<value>` | `<value>` | `<value>` | `<value>` | `<value>` | `<value>` |
| Qwen2.5-VL-7B | `<value>` | `<value>` | `<value>` | `<value>` | `<value>` | `<value>` | `<value>` | `<value>` | `<value>` |
| Surya 2 | `<value>` | `<value>` | `<value>` | `<value>` | `<value>` | `<value>` | `<value>` | `<value>` | `<value>` |

---

## 4. Qualitative findings

Summarize only non-identifying patterns:

- handwriting styles where the candidate performed well;
- handwriting styles where it failed;
- language or code-mixed patterns that require teacher review;
- blank-answer hallucination behavior;
- answer-number mapping issues;
- operational/cost observations.

---

## 5. Decision recommendation

Select exactly one:

- Keep Gemini Flash.
- Add Qwen as a confidence-routed candidate for a later Phase 3 design.
- Add Surya as an OCR-specialist candidate for a later Phase 3 design.
- No model change; collect more Track-A data.
- Do not proceed; OCR quality is insufficient for product-facing claims.

Any production source change requires a separate ARM authorization.

---

## 6. Attachments

Attach only repository-safe artifacts:

- aggregate CSV without raw student text;
- anonymized metric summary;
- license review note;
- benchmark command transcript without secrets;
- synthetic examples.

Do not attach raw real answer-sheet pages or identifiable transcriptions.


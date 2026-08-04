# AEI v1.0 pilot activation

How to turn on the certified AEI v1.0 capabilities for a pilot school, watch
them, and turn them off again. Everything below stays inside the certified
supported scope — this runbook enables flags; it does not expand any product
claim.

**Audience:** platform operator, with ARM's explicit authorization per stage.
**Prerequisite reading:** the certified scope in
[docs/product/aei-v1/AEI_V1_SUPPORTED_SCOPE_CAPABILITY_MATRIX.md](../product/aei-v1/AEI_V1_SUPPORTED_SCOPE_CAPABILITY_MATRIX.md).

---

## What activation is (and is not)

Every AEI v1.0 capability is certified, published, and **default-off**. The
teacher remains the marking authority at every stage: AEI produces suggestions
and metadata; the teacher approves, adjusts, or rejects. Nothing here changes
that.

Activation is a **configuration act, not a deploy**: set environment flags on
the API and worker, restart, verify. Deactivation is the same act in reverse —
that is the rollback plan, and it takes under a minute.

| Flag | Capability | Teacher-visible effect |
|---|---|---|
| `AEI_V1_MATH_NORMALIZATION_ENABLED` | Deterministic maths normalization/equivalence | Fewer false "wrong" marks on equivalent maths answers; suggestions carry normalization metadata |
| `AEI_V1_REVIEW_POLICY_ENABLED` | Confidence / manual-review metadata + override audit | Low-confidence suggestions are labelled "needs review" |
| `AEI_V1_EVIDENCE_LEDGER_METADATA_ENABLED` | Approved-evidence ledger metadata | Approved decisions carry an evidence trail in the evaluation panel |
| `AEI_V1_LANGUAGE_OCR_ASSIST_ENABLED` | Language/script/code-mixed assist metadata | Language-context hints on suggestions; never authoritative |
| `AEI_V1_VISUAL_SCIENCE_ASSIST_ENABLED` | Visual/science checklist metadata | Checklist hints on diagram/science answers; never authoritative |
| `AEI_V1_MANUAL_REVIEW_ACK_REQUIRED` | Acknowledgement enforcement | Teacher must acknowledge flagged questions before approving an evaluation |
| `AEI_HANDWRITING_OCR_PHASE1_ENABLED` | Gemini Flash answer-sheet transcription (gateway-only) | Scanned sheets get transcribed answers pre-filled for review |

---

## Staged activation sequence

Activate in stages, not all at once. Each stage runs for a real evaluation
cycle (at least one exam's worth of marking) before the next stage starts.
**Each stage requires ARM's explicit go.**

### Stage 1 — Deterministic + review posture

```text
AEI_V1_MATH_NORMALIZATION_ENABLED=true
AEI_V1_REVIEW_POLICY_ENABLED=true
```

The safest pair: normalization is deterministic (no model call), and review
policy only adds "needs review" labels. This stage proves the trust surface
without any new AI behavior.

### Stage 2 — Evidence + assist metadata

```text
AEI_V1_EVIDENCE_LEDGER_METADATA_ENABLED=true
AEI_V1_LANGUAGE_OCR_ASSIST_ENABLED=true
AEI_V1_VISUAL_SCIENCE_ASSIST_ENABLED=true
```

Additive metadata on the same workflow. Teachers see richer context; marks
behavior is unchanged.

### Stage 3 — Acknowledgement enforcement

```text
AEI_V1_MANUAL_REVIEW_ACK_REQUIRED=true
```

The only stage that adds a required teacher step: flagged questions must be
acknowledged (accepted / adjusted / rejected) before approval. Enable this only
after teachers are comfortable with Stages 1–2, and tell them first — it will
block an approval they used to be able to make in one click.

### Stage 4 — Handwriting OCR (needs provider key)

```text
AEI_HANDWRITING_OCR_PHASE1_ENABLED=true
GEMINI_API_KEY=<from secret store>
```

Turns on Gemini Flash transcription for uploaded answer-sheet images, through
the AI Gateway only. OCR output is a **draft transcription for teacher
review** — it is never authoritative and never grades anything.

> Sequence note: run the Track-A live benchmark
> ([procedure below](#track-a-live-benchmark)) before or alongside Stage 4.
> The benchmark tells you whether Gemini Flash is good enough for your
> school's real handwriting; enabling Stage 4 for the pilot is also how you
> collect real teacher-verified pages for Track-A.

---

## How to apply a stage

1. **Confirm authorization.** The stage is approved by ARM, in writing.
2. **Set the flags** in the API and worker environment (secret store /
   compose environment for the pilot VM — the flags are plain booleans, not
   secrets, but they live with the deployment config).
3. **Restart** the API and worker containers.
4. **Verify** (below).
5. **Announce** to the pilot teachers what changed, in one sentence each.

## Verification (after every stage)

- `GET /health` and `GET /ready` return OK.
- Run one real evaluation end-to-end as a teacher: upload → suggestions →
  review → approve. Confirm the new metadata appears and approval still works.
- Check `/metrics` for the AEI counters (`aei_activation_trust` job events;
  `aei_handwriting_ocr_phase1` events for Stage 4).
- Check logs for `manual_review_ack_missing` spikes after Stage 3 — a spike
  means teachers are being blocked and need a walkthrough.
- Watch AI credit burn after Stage 4 (OCR is metered like every gateway call).

## Rollback

Set the stage's flags back to `false`, restart API + worker. Nothing persists
in a way that requires cleanup: all AEI metadata is additive, marks were
teacher-approved at every point, and disabling flags simply stops producing
new metadata. Historical evaluations keep the metadata they were approved
with — that is the audit record, leave it.

If Stage 3 blocks an urgent approval and teachers cannot be walked through
acknowledgement in time, disable `AEI_V1_MANUAL_REVIEW_ACK_REQUIRED` alone and
retry — the rest of the stack can stay on.

---

## Track-A live benchmark

Authorized by `AEI-HANDWRITING-OCR-PHASE2-LIVE-RUN-AUTH-001`
([contract](../product/aei-v1/AEI_HANDWRITING_OCR_PHASE_2_LIVE_TRACK_A_BENCHMARK_RUN_AUTHORIZATION_CONTRACT.md)).
Execution may start **only after ARM confirms all live-run prerequisites** in
that contract (dataset size, teacher verification, secure storage,
anonymization, redaction, access control, license posture, credential posture,
report posture).

### 1. Collect the dataset (outside git, always)

- 50–100 real answer-sheet pages, teacher-verified transcriptions.
- Follow the [data handling guide](../product/aei-v1/AEI_HANDWRITING_OCR_PHASE_2_TRACK_A_DATA_HANDLING_GUIDE.md):
  anonymized `track-a-*` sample IDs, identity fields redacted, secured storage
  with access control.
- Build one manifest JSON in the secured location:

```json
{
  "version": "track-a.real.v1",
  "samples": [
    {
      "sample_id": "track-a-0001",
      "image_path": "pages/track-a-0001.jpg",
      "ground_truth": { "answers": { "1": "teacher verified text", "2": "" } },
      "question_texts": { "1": "Define photosynthesis", "2": "Draw the diagram" },
      "max_marks": { "1": 2, "2": 3 }
    }
  ]
}
```

`image_path` is relative to the manifest. For Qwen/Surya (run on their own
GPU environments), embed their outputs per sample as
`candidate_outputs.qwen2_5_vl_7b.answers` / `candidate_outputs.surya_2.answers`
— the runner scores them identically without hosting the models.

### 2. Run

```bash
cd apps/api
# Smoke first: 3 samples, cheap, verifies the plumbing end to end.
python scripts/run_ocr_track_a_benchmark.py \
    --manifest /secure/track-a/manifest.json \
    --candidates gemini_flash --run-id track-a-smoke-001 --limit 3

# Full run.
python scripts/run_ocr_track_a_benchmark.py \
    --manifest /secure/track-a/manifest.json \
    --candidates gemini_flash,qwen2_5_vl_7b,surya_2 \
    --run-id track-a-live-001
```

Requires `GEMINI_API_KEY` in the environment for the `gemini_flash` candidate.
The runner uses the **exact production transcription prompt and parser**, so
the numbers describe the pipeline the pilot would actually get.

Safety properties (enforced by the runner, tested):

- refuses a manifest or output directory inside the repository;
- refuses samples with identity fields or non-anonymized IDs;
- never prints or logs transcription text — progress shows sample IDs and
  quality flags only;
- writes an **aggregate-only** JSON report to the secured location.

### 3. Report

Fill
[the report template](../product/aei-v1/AEI_HANDWRITING_OCR_PHASE_2_TRACK_A_GOLDEN_SET_BENCHMARK_REPORT_TEMPLATE.md)
from the aggregate JSON. Only the aggregate report enters git as
`docs/product/aei-v1/AEI_HANDWRITING_OCR_PHASE_2_LIVE_TRACK_A_BENCHMARK_RUN_REPORT.md`
— never images, raw transcriptions, or per-sample output. Delete local
temporary outputs after the report is generated (contract §7.6).

The report ends in exactly one recommendation (keep Gemini Flash / add Qwen /
add Surya / collect more data / do not proceed). **Any production OCR change
based on it requires a separate ARM authorization** — the benchmark is
evidence, not integration.

---

## What this runbook never authorizes

- Autonomous grading or autonomous mark publication.
- Any production OCR provider switch (Phase 3 territory, separate contract).
- Source-of-truth switching, schema changes, or public product-claim
  expansion.
- Enabling any flag without ARM's stage-by-stage authorization.

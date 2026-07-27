# EUI Trust Framework

- **Status:** Accepted
- **Parent architecture:** [`../EUI.md`](../EUI.md)

---

## 1. Purpose

Trust in StudyNexs should be explainable.

A single confidence score is not enough. Teachers and school leaders need to understand where certainty comes from and where uncertainty remains.

The EUI Trust Framework defines a multi-dimensional Trust Report that can be attached to educational artifacts, evaluations, recommendations, and intelligence outputs.

---

## 2. Trust Report

Conceptual shape:

```text
TrustReport
  input_quality
  extraction_quality
  ocr_confidence
  language_confidence
  understanding_confidence
  subject_confidence
  reasoning_confidence
  policy_confidence
  evidence_available
  human_review_status
  auditability
  capability_mode
  warnings
```

This is an architecture contract, not a schema change in this program.

Provenance is intentionally not a Trust Report dimension. Provenance answers where something came from, who approved it, and which version it belongs to. Trust answers how reliable the artifact or interpretation is and what review posture is required.

---

## 3. Trust dimensions

| Dimension | Question it answers |
|---|---|
| Input quality | Was the source readable, complete, and suitable? |
| Extraction quality | Did acquisition produce reliable text/structure? |
| OCR confidence | Is the machine transcription reliable? |
| Language confidence | Was language/script/code-mixing detected reliably? |
| Understanding confidence | Did EUI understand the artifact meaningfully? |
| Subject confidence | Did subject intelligence operate within supported scope? |
| Reasoning confidence | Was academic reasoning deterministic or uncertain? |
| Policy confidence | Did workflow policy apply cleanly? |
| Evidence availability | Is there citable evidence for the output? |
| Human review status | Is the result draft, reviewed, approved, or overridden? |
| Auditability | Can the output be traced to inputs, context, and decisions? |
| Capability mode | Is the capability supported, assistive, checklist, manual-review, or unsupported? |

---

## 4. Trust rules

1. Trust should explain uncertainty rather than hide it.
2. Low trust routes to review; it must not produce silent authority.
3. Trust affects workflow and communication, not automatic final academic authority.
4. Parent/student-facing trust explanations must use approved, non-alarming language.
5. Internal trust metadata may be more technical than user-facing explanations.
6. Every Trust Report must preserve provenance.

---

## 5. Consumer expectations

| Consumer | Trust requirement |
|---|---|
| AEI | Manual-review routing and teacher explanation. |
| Teacher Copilot | Clear source and confidence for recommendations. |
| AI Tutor | Grade-appropriate uncertainty and safe fallback. |
| Parent Assistant | Parent-safe explanation based on approved evidence only. |
| Principal Dashboard | Avoid overclaiming trends from weak or partial evidence. |
| School Analytics | Separate measured evidence from inferred insight. |

---

## 6. Anti-patterns

- Displaying "92%" without explaining what it measures.
- Using low-confidence extraction as final evidence.
- Treating provenance and trust as the same concept.
- Treating teacher overrides as model truth.
- Showing unsupported capability output as a polished result.
- Giving parents raw AI uncertainty without teacher-approved framing.

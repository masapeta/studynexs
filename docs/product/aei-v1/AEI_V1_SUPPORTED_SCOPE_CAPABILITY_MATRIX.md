# AEI v1.0 Supported Scope Capability Matrix

- **Program:** Academic Evaluation Intelligence v1.0
- **Artifact:** Supported scope capability matrix
- **Classification:** Certification support artifact
- **Status:** Ready for ARM acceptance review
- **Date:** 2026-07-28
- **Owner:** Avinash Reddy Masapeta (ARM)
- **Registry source:** `apps/api/app/modules/examinations/data/subject_capability_registry.v1.json`

---

## 1. Purpose

This matrix states what AEI v1.0 may honestly claim inside the declared
teacher-trust evaluation scope.

It is intentionally conservative:

- `supported` means deterministic support exists for configured scenarios;
- `assist` means AEI may provide internal assist metadata, but teacher review is
  required;
- `checklist` means AEI may summarize checklist evidence, but teacher review is
  required;
- `manual_review` means the system should not certify marks for that capability;
- `unsupported` means the product must not claim the capability.

The teacher remains the final authority.

---

## 2. Capability posture by subject

| Subject | Capability | Mode | Teacher review | Certified batch | Product claim boundary |
|---|---|---:|---:|---|---|
| Mathematics | Numeric equivalence | supported | No for deterministic matches | Batch A | Fractions, decimals, mixed numbers, percentages, and configured acceptable variants |
| Mathematics | Units | supported | No for deterministic configured matches | Batch A | Simple same-dimension unit checks when rubric config exists |
| Mathematics | Tolerance | supported | No for deterministic configured matches | Batch A | Explicit numeric tolerance only |
| Mathematics | Scientific notation | supported | No for deterministic configured matches | Batch A | Numeric equivalence where rubric allows equivalent forms |
| Mathematics | Diagrams | partial | Yes | Batch E | Checklist/manual-review posture only |
| Physics | Units | supported | No for deterministic configured matches | Batch A / Batch E boundary | Unit checks where expected units are configured |
| Physics | Formula recognition | assist | Yes | Batch E | Formula-like evidence only; no correctness certification |
| Physics | Diagrams | checklist | Yes | Batch E | Checklist observations only |
| Physics | Graphs | checklist | Yes | Batch E | Axis/label/plotting checklist posture only |
| Chemistry | Reaction balancing | assist | Yes | Batch E | Simple balanced/unbalanced evidence only |
| Chemistry | Chemical symbols | assist | Yes | Batch E | Symbol/formula assist metadata only |
| Chemistry | Structures | manual_review | Yes | Batch E | No structure grading in AEI v1.0 |
| Biology | Diagrams | checklist | Yes | Batch E | Checklist observations such as labels present/missing |
| Biology | Labels | assist | Yes | Batch E | Assistive label evidence only |
| Geography | Maps | checklist | Yes | Batch E | Map-label/checklist posture only |
| Geography | Graphs | checklist | Yes | Batch E | Axis/scale/label checklist posture only |
| Geography | Labels | assist | Yes | Batch E | Assistive label evidence only |
| Hindi | Printed OCR | assist | Yes | Batch D | Extraction posture only; teacher confirmation required |
| Hindi | Handwriting OCR | assist | Yes | Batch D | Assistive only; no reliable handwriting claim |
| Hindi | Grading | manual_review | Yes | Batch D | Teacher-reviewed language grading |
| Telugu | Printed OCR | assist | Yes | Batch D | Extraction posture only; teacher confirmation required |
| Telugu | Handwriting OCR | assist | Yes | Batch D | Assistive only; no reliable handwriting claim |
| Telugu | Grading | manual_review | Yes | Batch D | Teacher-reviewed language grading |
| Sanskrit | Printed OCR | assist | Yes | Batch D | Extraction posture only; teacher confirmation required |
| Sanskrit | Handwriting OCR | assist | Yes | Batch D | Assistive only; no reliable handwriting claim |
| Sanskrit | Grading | manual_review | Yes | Batch D | Teacher-reviewed language grading |

---

## 3. Cross-cutting AEI capabilities

| Capability | Status | Certified batch | Boundary |
|---|---:|---|---|
| Confidence/manual-review metadata | supported | Batch B | Workflow signal, not marks authority |
| Teacher override audit metadata | supported | Batch B | Override reason and audit metadata only |
| Approved-evidence metadata | supported | Batch C | Downstream source of truth is teacher decision |
| Original suggestion vs final teacher decision separation | supported | Batch C | Internal evidence contract only |
| Language/script/code-mixed metadata | assist | Batch D | Context only; not autonomous language grading |
| Visual/science checklist metadata | checklist / assist | Batch E | Teacher-confirmed evidence only |

---

## 4. Explicit non-claims

AEI v1.0 must not claim:

- universal grading;
- autonomous grading;
- full symbolic algebra or proof checking;
- universal handwriting OCR;
- full language grading for Hindi/Telugu/Sanskrit;
- voice tutor or speech-to-text support;
- pixel-perfect visual grading;
- full chemistry structure grading;
- graph/map automatic marks;
- circuit correctness automation beyond checklist posture;
- parent/student visibility of uncertified AI;
- EUI source-of-truth adoption.

---

## 5. Feature-flag posture

| Feature flag | Default | Certified capability |
|---|---:|---|
| `AEI_V1_MATH_NORMALIZATION_ENABLED` | `false` | Batch A Maths normalization |
| `AEI_V1_REVIEW_POLICY_ENABLED` | `false` | Batch B confidence/manual-review/override metadata |
| `AEI_V1_EVIDENCE_LEDGER_METADATA_ENABLED` | `false` | Batch C approved-evidence metadata |
| `AEI_V1_LANGUAGE_OCR_ASSIST_ENABLED` | `false` | Batch D language/OCR assist metadata |
| `AEI_V1_VISUAL_SCIENCE_ASSIST_ENABLED` | `false` | Batch E visual/science assist metadata |

Default-off remains the rollback posture. Product enablement requires deployment
configuration and product-scope signoff.

---

## 6. Golden Harness coverage summary

| Dataset | Case count | Scope |
|---|---:|---|
| `pilot_trust_cases.json` | 9 | Cross-subject teacher-trust starter set |
| `batch_a_math_normalization_cases.json` | 7 | Maths normalization and equivalence |
| `batch_b_review_policy_cases.json` | 5 | Confidence/manual-review policy |
| `batch_c_approved_evidence_cases.json` | 3 | Approved evidence ledger contract |
| `batch_d_language_ocr_assist_cases.json` | 6 | Language/OCR assist posture |
| `batch_e_visual_science_assist_cases.json` | 5 | Visual/science assist posture |
| **Total AEI Golden cases** | **35** | AEI v1.0 certified support boundary |

---

## 7. Certification interpretation

This matrix certifies AEI v1.0 implementation readiness for the supported scope.
It does not itself enable feature flags or expand public product claims.

Public/support/sales claims must remain aligned with this matrix and the final
AEI v1.0 certification report.

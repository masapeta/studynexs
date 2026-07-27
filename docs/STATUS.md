# StudyNexs — Master Status

> **Owner:** Avinash Reddy Masapeta (ARM)
> **As of:** 2026-07-28
> **Status role:** Current project anchor for architecture, runtime milestones, and next engineering gate.

---

## Executive status

StudyNexs is an AI-first School Operating System with a frozen AEI/EUI
architecture, a published EUI runtime foundation, and an active AEI v1.0
product-completion program.

The current engineering rhythm is:

```text
Architecture
      ↓
Design Brief
      ↓
ARM Authorization
      ↓
Implementation
      ↓
Validation
      ↓
Certification
      ↓
Commit
      ↓
Tag
      ↓
Publish
      ↓
Update Master Status
```

Architecture should not be reopened unless ARM explicitly authorizes an
architecture change.

---

## Runtime naming source of truth

The EUI Runtime Roadmap phase names are the source of truth going forward.

Earlier artifacts that say `Phase 1 Sprint 2` or `Phase 1 Sprint 3` are
historical implementation-batch labels from the first EUI runtime cycle. They
remain valid as artifact names, commit tags, and certification records, but the
canonical roadmap names are:

| Roadmap phase | Canonical capability | Historical implementation label |
|---|---|---|
| Phase 1 | Educational Identity | Phase 1 Sprint 1 |
| Phase 2 | Educational Context Engine | Phase 1 Sprint 2 |
| Phase 3 | Platform Capability Registry | Phase 1 Sprint 3 |
| Phase 4 | Knowledge Acquisition Intelligence | Phase 4 KAI Candidate Foundation |
| Phase 5 | Educational Knowledge Graph Expansion | Phase 5 EKG Proposal Foundation |
| Phase 6 | Trust Framework | Phase 6 Trust Report Foundation |
| Phase 7 | Consumer Migration | Phase 7A AEI Consumer Dual-Read Foundation; Phase 7B AEI Rich EUI Evidence Binding; Phase 7C AEI Divergence Readiness Review; Phase 7D Narrow AEI Source Readiness; Phase 7E Narrow AEI Source-Readiness Trial |

---

## Current baseline

| Layer | Status |
|---|---|
| StudyNexs vision | Stable |
| AEI v1 | Frozen / protected |
| AEI v1.0 Batch A - Maths normalization | Complete / certified / published |
| AEI v1.0 Batch B - Review policy metadata | Complete / certified / published |
| AEI v1.0 Batch C - Evidence ledger metadata | Complete / certified / published |
| AEI v1.0 Batch D - Language/OCR assist metadata | Complete / certified / published |
| AEI v1.0 Batch E - Visual/science assist metadata | Complete / certified / published |
| EUI v1 architecture | Frozen / accepted |
| EUI Runtime Roadmap v1 | Accepted planning baseline |
| Phase 0 - Engineering Preparation | Complete / certified / published |
| Phase 1 - Educational Identity | Complete / certified / published |
| Phase 2 - Educational Context Engine | Complete / certified / published |
| Phase 3 - Platform Capability Registry | Complete / certified / published |
| Phase 4 - Knowledge Acquisition Intelligence | Candidate foundation complete / certified / published |
| Phase 5 - Educational Knowledge Graph Expansion | Proposal foundation complete / certified / published |
| Phase 6 - Trust Framework | Trust Report foundation complete / certified / published |
| Phase 7 - Consumer Migration | Closed at Phase 7E; 7F source adoption deferred / future scope |
| Runtime consumer migration | AEI passive dual-read with rich internal EUI evidence, internal divergence readiness review, narrow internal source-readiness candidate foundation, and internal source-readiness trial foundation published; source-of-truth switch not authorized |

---

## Published AEI v1.0 product-completion milestones

| Batch | Status | Commit | Tag | Scope |
|---|---|---|---|---|
| Batch A - Maths Normalization | Published / certified | `4343b0542b68cd739162eeb47207299c428b2fd9` | `aei-v1-batch-a-maths-normalization-certified` | Default-off deterministic Maths normalization/equivalence foundation |
| Batch B - Review Policy Metadata | Published / certified | `d40c31e4df29a4942e48431c90b756611949ef86` | `aei-v1-batch-b-review-policy-certified` | Default-off confidence/manual-review metadata and teacher override audit foundation |
| Batch C - Evidence Ledger Metadata | Published / certified | `9f3589e1d98825a2abc15244879ef1b8329a6064` | `aei-v1-batch-c-evidence-ledger-certified` | Default-off approved-evidence ledger metadata and teacher-approved source-of-truth contract |
| Batch D - Language/OCR Assist Metadata | Published / certified | `d33ff6d9d49d140353a848ccffe0f222e6d8ac2c` | `aei-v1-batch-d-language-ocr-assist-certified` | Default-off language/script/code-mixed and OCR assist metadata with teacher-review boundaries |
| Batch E - Visual/Science Assist Metadata | Published / certified | `b393e83e7e0eb24c9992f28e3c6b963cdcc4586f` | `aei-v1-batch-e-visual-science-assist-certified` | Default-off visual/science assist and checklist metadata with teacher-review boundaries |

Batch A adds production-seam Maths normalization behind
`AEI_V1_MATH_NORMALIZATION_ENABLED=false` by default.

Supported Batch A behavior:

- fractions, decimals, mixed numbers, and Unicode fractions;
- percentages;
- scientific notation;
- explicit numeric tolerance;
- simple same-dimension unit equivalence;
- acceptable answer variants when already available in rubric data;
- manual-review metadata for inconclusive supported Maths cases.

Batch A does not authorize or implement Batch B teacher-review routing, evidence
ledger changes, language/OCR assist, visual/science assist, UI changes, API
changes, schema changes, or autonomous marks for uncertain cases.

Batch B adds review-policy metadata behind
`AEI_V1_REVIEW_POLICY_ENABLED=false` by default.

Supported Batch B behavior:

- `manual_review_required`;
- `manual_review_reason`;
- `capability_mode`;
- `confidence_reason`;
- low-confidence and missing-confidence review metadata;
- teacher override reason enforcement when the flag is enabled;
- teacher override audit metadata in the existing `teacher_overrides` payload.

Batch B does not authorize or implement evidence-ledger propagation, language/OCR
assist, visual/science assist, UI changes, API changes, schema changes, or
parent/student visibility changes.

Batch C adds approved-evidence ledger metadata behind
`AEI_V1_EVIDENCE_LEDGER_METADATA_ENABLED=false` by default.

Supported Batch C behavior:

- unapproved AI suggestions are explicitly marked as not approved for downstream
  evidence;
- teacher-approved evaluations emit sanitized approved-evidence metadata;
- original AI suggestion metadata remains separate from the final teacher
  decision;
- the downstream source of truth is declared as `teacher_decision`;
- raw student answer keys are excluded from the approved-evidence contract;
- Golden Harness cases cover approved, overridden, and unapproved evidence
  scenarios.

Batch C does not authorize or implement language/OCR assist, visual/science
assist, UI changes, API changes, schema changes, report-card automation, broad
consumer migration, or parent/student visibility changes.

Batch D adds language/OCR assist metadata behind
`AEI_V1_LANGUAGE_OCR_ASSIST_ENABLED=false` by default.

Supported Batch D behavior:

- answer language, script, and code-mixed metadata;
- teacher-entered text versus image/OCR source metadata;
- Hindi, Telugu, and Sanskrit language-subject review posture;
- Indic handwriting/OCR assist boundaries through metadata only;
- low-confidence or missing OCR confidence manual-review metadata;
- internal Platform Capability Registry posture evidence;
- no autonomous language grading.

Batch D does not authorize or implement a new OCR engine, LLM inference,
visual/science assist, UI changes, API changes, schema changes, public OCR
claims, marks changes, evidence-ledger behavior changes, teacher-review routing
changes, or parent/student visibility changes.

Batch E adds visual/science assist metadata behind
`AEI_V1_VISUAL_SCIENCE_ASSIST_ENABLED=false` by default.

Supported Batch E behavior:

- chemistry reaction-balancing assist metadata;
- chemical-symbol and physics formula-recognition assist metadata;
- chemistry structure manual-review posture;
- biology diagram checklist metadata;
- geography map checklist metadata;
- checklist-only evidence summaries when deterministic checklist context exists;
- no autonomous visual/science grading;
- no autonomous marks from checklist-only evidence.

Batch E does not authorize or implement a new OCR/vision engine, LLM inference,
pixel-perfect visual grading, full chemistry structure grading, graph/map
automatic marks, UI changes, API changes, schema changes, marks changes,
evidence-ledger behavior changes, teacher-review routing changes, or
parent/student visibility changes.

---

## Published EUI runtime milestones

| Roadmap phase | Status | Commit | Tag | Historical artifact label |
|---|---|---|---|---|
| Phase 1 - Educational Identity | Published / certified | `221601e611bdb0fac13279af7fe4a8e89d31f99a` | `eui-runtime-phase1-sprint1-educational-identity-certified` | Phase 1 Sprint 1 |
| Phase 2 - Educational Context Engine | Published / certified | `a559faeba7389bb583bfdcd64f8119f3811613d6` | `eui-runtime-phase1-sprint2-educational-context-certified` | Phase 1 Sprint 2 |
| Phase 3 - Platform Capability Registry | Published / certified | `5f3babf007fcbaba7a8a33ec316e80b974d8df7b` | `eui-runtime-phase1-sprint3-platform-capability-registry-certified` | Phase 1 Sprint 3 |
| Phase 4 - Knowledge Acquisition Intelligence | Published / certified | `165c796e9bac6a6fc29226ed186b79664d0d5b5c` | `eui-runtime-phase4-kai-candidate-foundation-certified` | Phase 4 KAI Candidate Foundation |
| Phase 5 - Educational Knowledge Graph Expansion | Published / certified | `91a84f5fce1bb0acf4a5231593b0e1715e1baef8` | `eui-runtime-phase5-ekg-proposal-foundation-certified` | Phase 5 EKG Proposal Foundation |
| Phase 6 - Trust Framework | Published / certified | `0a5a5dd0a8b7054ede5d86f7b610328505b195f5` | `eui-runtime-phase6-trust-report-foundation-certified` | Phase 6 Trust Report Foundation |
| Phase 7A - AEI Consumer Migration | Published / certified | `c30bb2479e615d50aea97ae03bd3b6816d93c26b` | `eui-runtime-phase7a-aei-consumer-dual-read-certified` | Phase 7A AEI Consumer Dual-Read Foundation |
| Phase 7B - AEI Rich EUI Evidence Binding | Published / certified | `f279f8a04e82d66133cf9178676c8af51b9aeb54` | `eui-runtime-phase7b-aei-rich-evidence-binding-certified` | Phase 7B AEI Rich EUI Evidence Binding |
| Phase 7C - AEI Divergence Readiness Review | Published / certified | `d9fa9e8d44dab0bd6dc5874fb0ac84f0a7e6ee90` | `eui-runtime-phase7c-aei-divergence-readiness-certified` | Phase 7C AEI Divergence Review and Source Readiness |
| Phase 7D - Narrow AEI Source Readiness | Published / certified | `696501c270b3db893ea71c31babeb7448967f6a1` | `eui-runtime-phase7d-narrow-aei-source-readiness-certified` | Phase 7D Narrow AEI Source-Readiness Candidate Foundation |
| Phase 7E - Narrow AEI Source-Readiness Trial | Published / certified | `bf7e06e6f497d1e09234e4ba0a611b479d7ee1d1` | `eui-runtime-phase7e-narrow-aei-source-readiness-trial-certified` | Phase 7E Narrow AEI Source-Readiness Trial Foundation |

---

## Current engineering gate

The latest completed artifact is:

```text
AEI v1.0 Batch E - Visual/Science Assist Metadata
```

AEI v1.0 Batch E is published and certified as a default-off visual/science
assist metadata foundation. It enriches existing answer-suggestion metadata only
when `AEI_V1_VISUAL_SCIENCE_ASSIST_ENABLED=true`.

When the flag is disabled, existing suggestion and approval behavior remains the
production path. No schema, API route, UI, marks, teacher-review routing,
persistence, OCR/vision engine, LLM inference, visual grading, science grading,
or parent/student visibility changes were introduced.

Next gated milestone:

```text
AEI v1.0 Batch F - AEI v1.0 certification
```

Batch F is not authorized until ARM explicitly issues the next implementation
authorization.

EUI Phase 7 remains closed at Phase 7E. Phase 7F source adoption is deferred
future scope, not the next active implementation milestone.

Phase 7F should be implemented only when source adoption solves a real product
problem, not because the architecture can support it.

Deferred artifact:

[`product/eui-runtime/phase-7/EUI_PHASE_7F_NARROW_AEI_SOURCE_ADOPTION_DESIGN_BRIEF.md`](./product/eui-runtime/phase-7/EUI_PHASE_7F_NARROW_AEI_SOURCE_ADOPTION_DESIGN_BRIEF.md)

7F reopen conditions:

- a real product-facing flow needs EUI to become the selected metadata source;
- legacy AEI metadata starts blocking accuracy, consistency, or
  maintainability;
- Phase 7E trial evidence shows stable readiness across real usage;
- marks, routing, ledger, API, UI, and schema can be proven unchanged;
- rollback is simple: disable the flag and return to legacy AEI;
- ARM explicitly authorizes a 7F implementation contract.

---

## Explicitly not authorized

Until ARM separately authorizes a future implementation contract, the following
remain out of scope:

- additional Educational Knowledge Graph behavior beyond the published proposal
  foundation;
- additional Knowledge Acquisition Intelligence behavior beyond the published
  candidate foundation;
- additional Trust Framework behavior beyond the published Trust Report
  foundation;
- schema changes;
- API changes;
- UI changes;
- consumer migration beyond the published Phase 7E AEI internal
  source-readiness trial foundation;
- Phase 7F source adoption unless ARM reopens it under the documented reopen
  conditions;
- AEI behavior changes beyond the published default-off Batch A Maths
  normalization foundation, Batch B review-policy metadata foundation, Batch C
  approved-evidence ledger metadata foundation, and Batch D language/OCR assist
  metadata foundation, and Batch E visual/science assist metadata foundation;
- AEI v1.0 Batch F or later batches without separate ARM authorization;
- AEI source-of-truth switching to EUI;
- EUI contract changes outside accepted design;
- product capability claim changes;
- replacement of the AEI Subject Capability Registry;
- public use of Platform Capability Registry entries for UI badges, sales
  claims, support documentation, or product scope documentation.

---

## Current source-of-truth statement

StudyNexs has a frozen AEI/EUI architecture, a published Phase 1 Educational
Identity runtime foundation, a published Phase 2 Educational Context passive
runtime foundation, a published Phase 3 Platform Capability Registry passive
runtime foundation, a published Phase 4 Knowledge Acquisition Intelligence
candidate foundation, a published Phase 5 Educational Knowledge Graph proposal
foundation, a published Phase 6 Trust Framework Trust Report foundation, a
published Phase 7A AEI Consumer Migration passive dual-read foundation, a
published Phase 7B AEI Rich EUI Evidence Binding foundation, a published Phase
7C AEI Divergence Readiness Review foundation, a published Phase 7D Narrow AEI
Source-Readiness Candidate foundation, a published Phase 7E Narrow AEI
Source-Readiness Trial foundation, a published AEI v1.0 Batch A Maths
Normalization foundation, and a published AEI v1.0 Batch B Review Policy
Metadata foundation, a published AEI v1.0 Batch C Evidence Ledger Metadata
foundation, and a published AEI v1.0 Batch D Language/OCR Assist Metadata
foundation, and a published AEI v1.0 Batch E Visual/Science Assist Metadata
foundation. Phase 7 is closed at 7E. Phase 7F source adoption is deferred
future scope. AEI v1.0 Batch F certification is the next product-facing
engineering gate, but it is not authorized until ARM issues a separate
implementation authorization contract.

---

## Validation posture

Latest published runtime phase:

```text
AEI v1.0 Batch E - Visual/Science Assist Metadata
```

Historical artifact label:

```text
AEI v1.0 Batch E Visual/Science Assist Metadata Foundation
```

Certified evidence:

- Focused Batch E Ruff: PASS
- Focused Batch E + Golden Harness tests: 16 passed
- Answer-sheet integration regression: 23 passed
- Full AEI/OCR/visual-science regression slice: 78 passed
- API import: PASS
- git diff --check: PASS
- `AEI_V1_VISUAL_SCIENCE_ASSIST_ENABLED` defaults to false: PASS
- Flag-off legacy suggestion/approval behavior: PASS
- No schema/API/UI/marks/OCR-vision-engine/LLM/autonomous-visual-science changes: PASS

Certification report:

[`product/aei-v1/AEI_V1_BATCH_E_VISUAL_SCIENCE_ASSIST_CERTIFICATION_REPORT.md`](./product/aei-v1/AEI_V1_BATCH_E_VISUAL_SCIENCE_ASSIST_CERTIFICATION_REPORT.md)

---

## Standing rule

Every published runtime phase must end by updating this Master Status before the
next phase begins.

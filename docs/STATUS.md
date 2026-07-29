# StudyNexs — Master Status

> **Owner:** Avinash Reddy Masapeta (ARM)
> **As of:** 2026-07-29
> **Status role:** Current project anchor for architecture, runtime milestones, and next engineering gate.

---

## Executive status

StudyNexs is an AI-first School Operating System with a frozen AEI/EUI
architecture, a published EUI runtime foundation, a certified AEI v1.0
supported-scope baseline, and published Assessment Intelligence v1.0 Batch A
contract/capability foundation, Batch B blueprint readiness foundation, Batch C
rubric/model-answer readiness foundation, Batch D question-bank/reuse readiness
foundation, and Batch E paper-to-evaluation linkage readiness foundation.

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
| AEI v1.0 Certification | Complete / certified / published |
| AEI v1.0 Teacher Evaluation UX-A - Trust metadata display | Complete / certified / published |
| AEI v1.0 Teacher Evaluation UX-B - Override reason workflow | Complete / certified / published |
| AEI v1.0 Teacher Evaluation UX-C - Evidence and approved-decision panel | Complete / certified / published |
| AEI v1.0 Teacher Evaluation UX-D - Supported-scope assist panels | Complete / certified / published |
| AEI v1.0 Teacher Evaluation UX-E - Final teacher evaluation experience certification | Complete / certified / published |
| Teacher Evaluation Page Lint Cleanup | Complete / validated / published |
| AI Gateway Config Hardening - General vs vision model routing | Complete / validated / published |
| AEI Handwriting OCR Phase 1 - Gemini Flash transcription gate | Complete / certified / published |
| AEI Handwriting OCR Phase 2 - Track-A benchmark foundation | Complete / certified / published |
| Assessment Intelligence v1.0 Batch A - Contract and capability matrix | Complete / certified / published |
| Assessment Intelligence v1.0 Batch B - Blueprint readiness | Complete / certified / published |
| Assessment Intelligence v1.0 Batch C - Rubric and model-answer readiness | Complete / certified / published |
| Assessment Intelligence v1.0 Batch D - Question bank and reuse readiness | Complete / certified / published |
| Assessment Intelligence v1.0 Batch E - Paper-to-evaluation linkage readiness | Complete / certified / published |
| Stabilization Gate 1 - Production Safety | Complete / certified / published |
| Operational Proof | Complete / certified / published |
| AEI Activation / Trust | Complete / certified / published |
| Topic-ID / Mastery Spine Phase A - Passive resolution | Complete / certified / published |
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
| Batch F - AEI v1.0 Certification | Published / certified | `85328ffcb8b3ce131f9ae233f30795e4e95e5113` | `aei-v1-certified` | Supported-scope capability matrix and final AEI v1.0 certification |

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

Batch F certifies AEI v1.0 for the declared supported scope.

Certified Batch F artifacts:

- AEI v1.0 Certification Report;
- AEI v1.0 Supported Scope Capability Matrix;
- Golden Harness summary with 35 AEI cases;
- broad AEI/EUI certification regression evidence;
- rollback and feature-flag posture;
- explicit non-claims for unsupported/autonomous capabilities.

Batch F does not authorize or implement product behavior changes, feature-flag
enablement, UI changes, API changes, schema changes, source-of-truth switching,
or expanded public product claims.

---

## Published Assessment Intelligence v1.0 milestones

| Batch | Status | Commit | Tag | Scope |
|---|---|---|---|---|
| Batch A - Contract and Capability Matrix | Published / certified | `c2a0b725cda0f20335ae184311bde03947038523` | `assessment-v1-batch-a-contract-capability-matrix-certified` | Canonical assessment contract, supported-scope capability matrix, Golden Harness starter cases, focused static validation, and certification; no runtime behavior changes |
| Batch B - Blueprint Readiness | Published / certified | `1dfb4692620050e3f7c8f0fc1b53cba2bd4fb389` | `assessment-v1-batch-b-blueprint-readiness-certified` | Blueprint declaration contract, static supported-scope blueprint declarations, Golden Harness cases, focused static validation, and certification; no runtime behavior changes |
| Batch C - Rubric and Model-Answer Readiness | Published / certified | `06d431e4995c368e20ca55f7b2361d1e4cc1e55c` | `assessment-v1-batch-c-rubric-model-answer-readiness-certified` | Rubric/model-answer declaration contract, static supported-scope declarations, Golden Harness cases, focused static validation, and certification; no runtime behavior changes |
| Batch D - Question Bank and Reuse Readiness | Published / certified | `e837ad9de07fe2ee4dcb25052e1fb447d6d6af83` | `assessment-v1-batch-d-question-bank-reuse-readiness-certified` | Question-bank/reuse declaration contract, static supported-scope declarations, Golden Harness cases, focused static validation, and certification; no runtime behavior changes |
| Batch E - Paper-to-Evaluation Linkage Readiness | Published / certified | `acbc897dd6db2f1375a367a10a7d6575102f4e8f` | `assessment-v1-batch-e-paper-to-evaluation-linkage-readiness-certified` | Paper-to-evaluation linkage declaration contract, static supported-scope declarations, Golden Harness cases, focused static validation, and certification; no runtime behavior changes |

Assessment Intelligence v1.0 Batch A establishes the product-completion
foundation for assessment creation, question bank reuse, exam linkage, and
AEI-aligned evaluation context.

Batch A adds:

- Assessment Intelligence v1.0 Production Readiness Review;
- Assessment Intelligence v1.0 Implementation Design Brief;
- Batch A Implementation Authorization Contract;
- Canonical Assessment Contract;
- Supported Scope Capability Matrix;
- Golden Harness starter cases;
- focused static contract/matrix validation tests;
- Batch A Certification Report.

Batch A does not authorize or implement schema changes, API changes, UI changes,
runtime behavior changes, feature flags, AI provider changes, LLM inference,
question paper generation changes, question bank runtime changes, exam service
changes, AEI behavior changes, EUI source adoption, marks changes,
teacher-review routing changes, evidence-ledger behavior changes,
parent/student visibility changes, public product claim expansion, or Batch B
implementation.

Assessment Intelligence v1.0 Batch B makes blueprint support explicit,
deterministic, and non-universal.

Batch B adds:

- Batch B Blueprint Readiness Design Brief;
- Batch B Implementation Authorization Contract;
- Blueprint Declaration Contract;
- static Blueprint Supported Scope Declarations;
- Golden Harness blueprint readiness cases;
- focused static blueprint readiness validation tests;
- Batch B Certification Report.

Batch B certifies:

- supported CBSE / NCF2023 / Grade 6 / Science / unit-test blueprint posture;
- supported CBSE / NCF2023 / Grade 10 / Mathematics / term-exam blueprint
  posture;
- deterministic internal-choice handling, including printed marks versus
  answer-required marks;
- assist posture for Grade 10 Mathematics practice MCQ blueprint;
- manual-review posture for school-custom blueprint;
- unsupported posture for universal blueprint claims;
- expansion posture for future Telugu-medium state-board support.

Batch B does not authorize or implement schema changes, API changes, UI changes,
runtime behavior changes, feature flags, AI provider changes, LLM inference,
runtime blueprint source switching, question paper generation behavior changes,
question bank runtime behavior changes, exam service behavior changes, AEI
behavior changes, EUI source adoption, marks changes, teacher-review routing
changes, evidence-ledger behavior changes, parent/student visibility changes,
public product claim expansion, or Batch C rubric/model-answer work.

Assessment Intelligence v1.0 Batch C makes rubric/model-answer support explicit,
teacher-reviewable, and non-authoritative until approval.

Batch C adds:

- Batch C Rubric and Model-Answer Readiness Design Brief;
- Batch C Implementation Authorization Contract;
- Rubric and Model-Answer Declaration Contract;
- static Rubric and Model-Answer Supported Scope Declarations;
- Golden Harness rubric/model-answer readiness cases;
- focused static rubric/model-answer readiness validation tests;
- Batch C Certification Report.

Batch C certifies:

- supported CBSE / NCF2023 / Grade 10 / Mathematics / MCQ objective-key
  posture;
- supported CBSE / NCF2023 / Grade 10 / Mathematics / numeric-answer posture;
- supported acceptable-answer variants, unit, tolerance, and scientific-notation
  posture;
- assist posture for Grade 6 Science short-answer model answers;
- manual-review posture for Grade 6 Science criterion rubrics;
- checklist posture for Grade 6 Science biology diagram evidence;
- manual-review posture for missing answer keys;
- unsupported posture for universal subjective auto-grading claims;
- expansion posture for future advanced visual proof grading.

Batch C does not authorize or implement schema changes, API changes, UI changes,
runtime behavior changes, feature flags, AI provider changes, LLM inference,
rubric generation, runtime rubric source switching, answer-sheet evaluation
behavior changes, question paper generation behavior changes, question bank
runtime behavior changes, exam service behavior changes, AEI behavior changes,
EUI source adoption, marks changes, teacher-review routing changes,
evidence-ledger behavior changes, parent/student visibility changes, public
product claim expansion, or runtime question-bank/reuse behavior changes.

Assessment Intelligence v1.0 Batch D makes question-bank/reuse support explicit,
school-private, provenance-backed, and non-authoritative until teacher approval.

Batch D adds:

- Batch D Question Bank and Reuse Readiness Design Brief;
- Batch D Implementation Authorization Contract;
- Question Bank and Reuse Declaration Contract;
- static Question Bank and Reuse Supported Scope Declarations;
- Golden Harness question-bank/reuse readiness cases;
- focused static question-bank/reuse readiness validation tests;
- Batch D Certification Report.

Batch D certifies:

- supported approved-paper ingestion posture;
- supported idempotent re-approval posture;
- supported same-school/class/subject approved-bank reuse posture;
- supported blueprint-slot compose posture when marks and type match;
- supported topic/concept overlap posture where available;
- assist posture for gap-fill questions when bank coverage is incomplete;
- manual-review posture for changed-context reuse;
- unsupported posture for draft/unapproved bank items;
- unsupported posture for cross-tenant reuse;
- expansion posture for future global/marketplace question-bank behavior.

Batch D does not authorize or implement schema changes, API changes, UI changes,
runtime behavior changes, feature flags, AI provider changes, LLM inference,
question generation behavior changes, question-paper generation behavior
changes, question-bank service behavior changes, paper approval behavior
changes, answer-sheet evaluation behavior changes, exam service behavior
changes, AEI behavior changes, EUI source adoption, marks changes,
teacher-review routing changes, evidence-ledger behavior changes,
parent/student visibility changes, mastery updates, public product claim
expansion, cross-school marketplace behavior, or Batch E paper-to-evaluation
linkage.

Assessment Intelligence v1.0 Batch E makes paper-to-evaluation linkage explicit,
teacher-governed, and non-authoritative until approval.

Batch E adds:

- Batch E Paper-to-Evaluation Linkage Readiness Design Brief;
- Batch E Implementation Authorization Contract;
- Paper-to-Evaluation Linkage Declaration Contract;
- static Paper-to-Evaluation Linkage Supported Scope Declarations;
- Golden Harness paper-to-evaluation linkage readiness cases;
- focused static paper-to-evaluation linkage readiness validation tests;
- Batch E Certification Report.

Batch E certifies:

- supported same-tenant approved-paper-to-exam-schema posture;
- supported source-paper-plus-schema evaluation-readiness posture;
- supported linked rubric/model-answer context posture where Batch C context
  exists;
- assist posture for OCR answer input;
- assist posture for manual answer input;
- manual-review posture for manual schema without approved source paper;
- unsupported posture for draft/unapproved source papers;
- unsupported posture for cross-tenant source papers;
- unsupported posture for missing question schema;
- unsupported posture for autonomous marks or pre-approval downstream evidence;
- expansion posture for broader future source adoption.

Batch E does not authorize or implement schema changes, API changes, UI changes,
runtime behavior changes, feature flags, AI provider changes, LLM inference,
OCR engine changes, question-paper generation behavior changes, question-bank
service behavior changes, exam service behavior changes, answer-sheet
evaluation behavior changes, teacher approval behavior changes, AEI grading
behavior changes, AEI confidence behavior changes, AEI teacher-review routing
changes, EUI source adoption, marks changes, evidence-ledger behavior changes,
parent/student visibility changes, mastery updates, public product claim
expansion, or Batch F multilingual/bilingual behavior.

Next Assessment Intelligence gate:

```text
Assessment Intelligence v1.0 Batch F - Bilingual / Multilingual Assessment Readiness
```

Status: **Not authorized**. Batch F requires a separate ARM design brief and
implementation authorization contract before any implementation begins.

---

## Published AEI v1.0 teacher evaluation experience milestones

| Batch | Status | Commit | Tag | Scope |
|---|---|---|---|---|
| UX-A - Review-table trust metadata display | Published / certified | `a391fb2bd659957223a7a631471096a8e3b0ba6b` | `aei-v1-teacher-evaluation-ux-a-trust-display-certified` | Display-only teacher review guidance, confidence/capability/manual-review badges, and safe AEI metadata evidence rows on the existing teacher evaluation page |
| UX-B - Override reason workflow | Published / certified | `c8ea8997f0aca8adb2fb1667cd25bff5500dd4a3` | `aei-v1-teacher-evaluation-ux-b-override-reasons-certified` | Teacher-authored override reason capture and saved override reason display on the existing teacher evaluation page |
| UX-C - Evidence and approved-decision panel | Published / certified | `8c01e59111857750473133edfed0314103e7a3c8` | `aei-v1-teacher-evaluation-ux-c-evidence-decision-certified` | Teacher-facing evidence posture panel and approved-decision summary on the existing teacher evaluation page |
| UX-D - Supported-scope assist panels | Published / certified | `690e15695aabbf60248d7353d096b5dea865b987` | `aei-v1-teacher-evaluation-ux-d-assist-panels-certified` | Display-only language/OCR and visual/science assist evidence panels on the existing teacher evaluation page |
| UX-E - Final teacher evaluation experience certification | Published / certified | `3b07b05da83bb7fbbd265258f6074777b86d13a2` | `aei-v1-teacher-evaluation-experience-certified` | Final proof/certification gate for the assembled teacher evaluation experience; no code, API, schema, marks, routing, or source-of-truth changes |

UX-A turns certified AEI v1.0 suggestion metadata into teacher-visible trust
signals on the existing answer-sheet evaluation review page.

Supported UX-A behavior:

- compact teacher-review guidance summary above the review table;
- per-question confidence, method, capability, and manual-review badges;
- available Maths normalization/equivalence evidence rows;
- neutral legacy fallback when AEI metadata is absent;
- no backend, marks, approval, evidence-ledger, source-switching, schema, API,
  or feature-flag enablement changes.

UX-A certification caveat:

- dedicated browser proof was not executed in this session because the existing
  browser harness requires a running Reference tenant API and production web
  server;
- admin-web production build and TypeScript validation passed;
- helper lint passed;
- focused page lint remains blocked by pre-existing evaluation-page lint debt
  outside the UX-A display-only scope.

UX-B replaces generic override reason submission with teacher-authored override
reason capture on the existing answer-sheet evaluation review page.

Supported UX-B behavior:

- changed final marks reveal a **Reason for change** input;
- approval is blocked until each changed mark has a non-empty teacher-authored
  reason;
- unchanged marks do not require a reason;
- approved evaluations display saved override reasons when available;
- legacy approved overrides without reasons show neutral fallback copy:
  `Reason not recorded.`;
- the existing approval payload shape is preserved;
- no backend, marks, approval endpoint, teacher-review routing,
  evidence-ledger, source-switching, schema, API, feature-flag enablement, or
  parent/student visibility changes.

UX-B certification caveat:

- dedicated browser proof was not executed in this session;
- admin-web production build and TypeScript validation passed;
- focused page lint remains blocked by pre-existing evaluation-page lint debt
  outside the UX-B workflow slice;
- UX-B helper-level lint debt introduced during implementation was removed
  before certification.

UX-C upgrades the existing evidence strip into a teacher-facing evidence and
approval posture panel.

Supported UX-C behavior:

- draft AI suggestions are visibly distinct from teacher-approved evidence;
- approved evaluations communicate that teacher decisions are the downstream
  source of truth when existing metadata supports it;
- CurriculumPack, question paper, grounded/citation status, and source-of-truth
  signals are easier to inspect;
- approved-decision summary can show original AI marks versus final teacher
  marks, override status, override reason, and manual-review notes;
- legacy or missing detailed evidence metadata renders safely;
- UX-A trust display and UX-B override reason workflow remain intact;
- no backend, marks, approval endpoint, teacher-review routing,
  evidence-ledger generation, source-switching, schema, API, feature-flag
  enablement, or parent/student visibility changes.

UX-C certification caveat:

- dedicated browser proof was not executed in this session;
- admin-web production build and TypeScript validation passed;
- focused page lint remains blocked by pre-existing evaluation-page lint debt
  outside the UX-C display slice;
- UX-C reads existing evidence metadata only and does not alter evidence
  generation or persistence.

UX-D adds display-only supported-scope assist panels to the existing
answer-sheet evaluation review page.

Supported UX-D behavior:

- language/OCR assist evidence can surface detected language, script,
  code-mixed posture, OCR confidence, input source, and review posture when
  already present in existing suggestion metadata;
- visual/science assist evidence can surface visual type, science type,
  checklist status, observations, missing elements, and review posture when
  already present in existing suggestion metadata;
- assist panels stay explicitly non-authoritative and teacher-confirmed;
- legacy or missing assist metadata renders safely with no product behavior
  changes;
- UX-A trust display, UX-B override reason workflow, and UX-C evidence posture
  remain intact;
- no backend, marks, approval endpoint, teacher-review routing,
  evidence-ledger generation, OCR/vision/LLM execution, source-switching,
  schema, API, feature-flag enablement, or parent/student visibility changes.

UX-D certification caveat:

- dedicated browser proof was not executed in this session;
- admin-web production build and TypeScript validation passed;
- focused helper lint passed;
- focused page lint remains blocked by pre-existing evaluation-page lint debt
  outside the UX-D display slice.

UX-E certifies the assembled teacher evaluation experience across UX-A through
UX-D and AEI Activation / Trust.

Supported UX-E certification posture:

- the existing teacher evaluation page and AEI display helper remain the
  certified product surface;
- AI suggestions remain draft until teacher approval;
- teacher override reasons, evidence posture, confidence, capability, and
  assist/checklist boundaries remain teacher-safe;
- supported-scope copy review found no autonomous grading or unsupported OCR /
  visual / science claims;
- no backend, UI behavior, API, schema, marks, routing, evidence-ledger,
  source-switching, feature-flag enablement, or product-claim changes.

UX-E certification caveat:

- browser proof reached the Reference tenant teacher evaluation route with no
  runtime, API, or console failures;
- live Reference proof data did not contain every Batch D/E assist and
  manual-review metadata scenario, so those cases were certified through source
  inspection and existing UX-A/B/C/D baseline evidence;
- future browser proof should use a disposable or resettable deterministic
  evaluation fixture rather than shared Reference rows.

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

The latest completed published gate is:

```text
Assessment Intelligence v1.0 Batch D - Question Bank and Reuse Readiness
```

Publication baseline:

- commit `e837ad9de07fe2ee4dcb25052e1fb447d6d6af83`;
- annotated tag `assessment-v1-batch-d-question-bank-reuse-readiness-certified`.

Assessment Intelligence v1.0 Batch D adds the static question-bank/reuse
readiness foundation for declared supported scope. It includes a
question-bank/reuse declaration contract, static supported-scope declarations,
deterministic Golden Harness cases, focused validation tests, and certification
evidence.

Batch D does not change runtime answer-sheet evaluation, question-paper
generation, question-bank behavior, paper approval behavior, exam services,
schema, API, UI, AEI, EUI, feature flags, providers, prompts, marks, routing,
evidence ledger, mastery, or product claims.

No implementation gate is currently active. Assessment Intelligence v1.0 Batch
A, Batch B, Batch C, and Batch D are published and certified. The next
recommended product-facing gate is Assessment Intelligence v1.0 Batch E -
Paper-to-Evaluation Linkage Readiness, under a separate ARM design and
implementation authorization.

Ordered candidate gates after Assessment Intelligence v1.0 Batch D:

1. Assessment Intelligence v1.0 Batch E - Paper-to-Evaluation Linkage
   Readiness - certify the handoff from approved paper/question-bank/rubric
   context into evaluation setup without changing marks or teacher authority;
   not authorized.
2. AEI Handwriting OCR Phase 2 live Track-A benchmark run authorization -
   collect/use secured 50-100 teacher-verified real sheets and produce an
   aggregate candidate comparison report; not authorized.
3. AEI Handwriting OCR Phase 3 optimization design - confidence-routed chain
   and Qwen/Surya/Gemini operational decision based on Phase 2 evidence; not
   authorized.
4. Topic-ID / Mastery Spine Phase B additive schema readiness design - future
   learning-intelligence plumbing only if ARM chooses deeper spine persistence;
   not authorized.

Completion of Assessment Intelligence v1.0 Batch D does not authorize runtime
question-bank source switching, paper-to-evaluation linkage, answer-sheet
evaluation behavior changes, question-paper generation behavior changes,
question-bank runtime changes, exam service behavior changes, source switching,
public product claim expansion, UI changes, API changes, schema changes, marks
changes, routing changes, mastery changes, or evidence-ledger behavior changes.

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
- UI changes beyond the published AEI v1.0 Teacher Evaluation UX-A/B/C/D
  teacher-evaluation slices, the published UX-E certification/proof milestone,
  and the published AEI Activation / Trust acknowledgement/evidence proof;
- consumer migration beyond the published Phase 7E AEI internal
  source-readiness trial foundation;
- Topic-ID / Mastery Spine Phase B additive schema readiness, source adoption,
  dual-read, consumer migration, or mastery source-of-truth switching;
- Phase 7F source adoption unless ARM reopens it under the documented reopen
  conditions;
- AEI behavior changes beyond the published default-off Batch A Maths
  normalization foundation, Batch B review-policy metadata foundation, Batch C
  approved-evidence ledger metadata foundation, Batch D language/OCR assist
  metadata foundation, Batch E visual/science assist metadata foundation, Batch
  F certification baseline, UX-A/B/C/D teacher evaluation slices, UX-E
  teacher-evaluation certification/proof milestone, and AEI Activation / Trust
  runtime proof foundation;
- AEI v1.0 feature-flag enablement, source switching, or product-facing behavior
  changes beyond the certified Activation / Trust proof without separate ARM
  authorization;
- Assessment Intelligence v1.0 Batch E or later, including paper-to-evaluation
  linkage, rubric/model-answer behavior, blueprint runtime behavior, question
  paper generation behavior, question bank runtime behavior, exam service
  behavior, API/UI/schema changes, marks/routing changes, or product claim expansion,
  without separate ARM authorization;
- later AEI v1.0 Teacher Evaluation UX batches until ARM separately authorizes
  the UX work;
- post-certification AEI expansion without separate ARM authorization;
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
Normalization foundation, a published AEI v1.0 Batch B Review Policy Metadata
foundation, a published AEI v1.0 Batch C Evidence Ledger Metadata foundation, a
published AEI v1.0 Batch D Language/OCR Assist Metadata foundation, a published
AEI v1.0 Batch E Visual/Science Assist Metadata foundation, a published AEI
v1.0 Certification baseline, published AEI v1.0 Teacher Evaluation UX-A/B/C/D
teacher-trust slices, a published AEI v1.0 Teacher Evaluation UX-E final
teacher-experience certification, a published AEI Activation / Trust runtime proof
foundation, and a published Topic-ID / Mastery Spine Phase A passive resolution
foundation. Phase 7 is closed at 7E. Phase 7F source adoption is deferred future
scope. Assessment Intelligence v1.0 Batch A is published and adds the canonical
assessment contract, supported-scope capability matrix, Golden Harness starter
cases, and certification foundation without runtime behavior changes.
Assessment Intelligence v1.0 Batch B is published and adds blueprint
declaration posture, static supported-scope blueprint declarations, Golden
Harness blueprint cases, and certification without runtime behavior changes.
Assessment Intelligence v1.0 Batch C is published and adds rubric/model-answer
declaration posture, static supported-scope rubric/model-answer declarations,
Golden Harness rubric/model-answer cases, and certification without runtime
behavior changes.
Assessment Intelligence v1.0 Batch D is published and adds question-bank/reuse
declaration posture, static supported-scope question-bank/reuse declarations,
Golden Harness question-bank/reuse cases, and certification without runtime
behavior changes.
AEI v1.0 is certified for the declared supported scope, UX-A is the first
product-facing display slice, UX-B is the teacher-authored override reason
workflow slice, UX-C is the teacher-facing evidence posture and approved
decision panel slice, UX-D is the supported-scope assist-panel display slice,
and UX-E is the final assembled teacher-evaluation experience certification
gate. AEI Activation / Trust is the controlled trust proof for supported
capabilities, and Topic-ID / Mastery Spine Phase A is the passive
learning-intelligence spine foundation. Further teacher-evaluation UX batches,
source switching, mastery
persistence/source adoption, and public capability claim expansion require
separate ARM authorization. Production Safety, Operational Proof, AEI
Activation / Trust, Topic-ID / Mastery Spine Phase A, Teacher Evaluation UX-D,
Teacher Evaluation Page Lint Cleanup, and Teacher Evaluation UX-E are now
published. AI Gateway Config Hardening is also published and separates general
AI model routing from answer-sheet OCR / vision model routing. AEI Handwriting
OCR Phase 1 is published and adds the default-off Gemini Flash answer-sheet
transcription gate through the StudyNexs AI Gateway only. AEI Handwriting OCR
Phase 2 is published and adds the repository-safe Track-A benchmark foundation
without running live real-sheet benchmarks or changing production OCR routing.
UX-E remains the assembled teacher-evaluation certification baseline and the
lint cleanup remains the code-health gate that resolved the pre-existing page
lint debt. The next recommended product-facing gate is Assessment Intelligence
v1.0 Batch E - Paper-to-Evaluation Linkage Readiness, but it is not active until
ARM authorizes it under a separate design and implementation contract.

---

## Validation posture

Latest published Assessment Intelligence gate:

```text
Assessment Intelligence v1.0 Batch D - Question Bank and Reuse Readiness
```

Status: **Complete / certified / published**

Commit: `e837ad9de07fe2ee4dcb25052e1fb447d6d6af83`

Annotated tag: `assessment-v1-batch-d-question-bank-reuse-readiness-certified`

Evidence:

[`product/assessment-intelligence/ASSESSMENT_INTELLIGENCE_V1_BATCH_D_QUESTION_BANK_REUSE_READINESS_CERTIFICATION_REPORT.md`](./product/assessment-intelligence/ASSESSMENT_INTELLIGENCE_V1_BATCH_D_QUESTION_BANK_REUSE_READINESS_CERTIFICATION_REPORT.md)

Certified evidence:

- Focused Assessment Intelligence v1.0 question-bank/reuse readiness tests:
  PASS - 9 passed
- Adjacent Assessment Intelligence static and AEI regression slice: PASS - 44
  passed
- Question bank regression tests: PASS - 7 passed
- Question bank compose regression tests: PASS - 5 passed
- Pure answer-sheet grading checks: PASS - 3 passed
- Representative DB-backed answer-sheet evaluation case: PASS - 1 passed
- Focused Ruff check: PASS
- API import: PASS
- `git diff --check`: PASS
- No schema/API/UI/runtime behavior changes: PASS
- Validation caveat: full `tests/test_answer_sheet_eval.py` was not practical
  as one local command because it reaches the configured live LLM gateway; an
  initial parallel DB-backed adjacent slice also hit a PostgreSQL enum/schema
  creation collision. Targeted affected slices passed when rerun serially.

Next Assessment Intelligence gate:

```text
Assessment Intelligence v1.0 Batch E - Paper-to-Evaluation Linkage Readiness
```

Status: **Not authorized**

---

Latest published product-trust gate:

```text
AEI v1.0 Teacher Evaluation UX-E - Final teacher evaluation experience certification
```

Status: **Complete / certified / published**

Commit: `3b07b05da83bb7fbbd265258f6074777b86d13a2`

Annotated tag: `aei-v1-teacher-evaluation-experience-certified`

Evidence:

[`product/aei-v1/AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_E_CERTIFICATION_REPORT.md`](./product/aei-v1/AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_E_CERTIFICATION_REPORT.md)

Latest published teacher-evaluation certification gate:

```text
AEI v1.0 Teacher Evaluation UX-E - Final teacher evaluation experience certification
```

Historical artifact label:

```text
AEI v1.0 Teacher Evaluation UX-E
```

Certified evidence:

- git diff --check: PASS
- Focused teacher evaluation page lint: PASS
- Admin-web helper lint: PASS
- Admin-web TypeScript validation: PASS
- Admin-web production build: PASS
- Browser proof reached Reference tenant route with no runtime/API/console
  failures; live proof data did not cover every assist/manual-review metadata
  shape, so remaining scenarios were verified through source inspection and
  existing UX-A/B/C/D baselines
- No backend/API/schema/marks/routing/ledger/source-switch behavior changes:
  PASS
- Supported-scope copy review: PASS

Certification report:

[`product/aei-v1/AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_E_CERTIFICATION_REPORT.md`](./product/aei-v1/AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_E_CERTIFICATION_REPORT.md)

Related design and authorization:

- [`product/aei-v1/AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_E_DESIGN_BRIEF.md`](./product/aei-v1/AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_E_DESIGN_BRIEF.md)
- [`product/aei-v1/AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_E_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md`](./product/aei-v1/AEI_V1_TEACHER_EVALUATION_EXPERIENCE_BATCH_UX_E_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md)

Latest published engineering cleanup gate:

```text
Teacher Evaluation Page Lint Cleanup
```

Status: **Complete / validated / published**

Commit: `0792a290afa7e782d34dbd4ff50b088d82b58dc7`

Evidence:

- Focused teacher evaluation page lint: PASS
- Adjacent AEI evaluation-display helper lint: PASS
- Admin-web TypeScript validation: PASS
- Admin-web production build: PASS
- git diff --check: PASS
- No backend/API/schema/marks/routing/ledger/source-switch behavior changes:
  PASS

Latest published AI infrastructure hardening gate:

```text
AI Gateway Config Hardening - General vs vision model routing
```

Status: **Complete / validated / published**

Commit: `b9d8f0b5f82fde6d361458ecfbe547ab422cbe80`

Scope:

- added explicit general fallback model config via `AI_FALLBACK_MODEL`;
- added explicit OCR / vision routing config via `AI_VISION_PRIMARY_PROVIDER`,
  `AI_VISION_PRIMARY_MODEL`, `AI_VISION_FALLBACK_PROVIDER`, and
  `AI_VISION_FALLBACK_MODEL`;
- restricted `AI_DEFAULT_MODEL` so it applies only to the configured default
  provider and does not leak into Gemini OCR calls;
- kept answer-sheet OCR as transcription-only through the gateway;
- preserved AEI evaluation, teacher approval, marks, routing, schema, API, and
  UI behavior.

Validation:

- Focused gateway / answer-sheet vision / fallback / telemetry tests: 14 passed
- Focused ruff on changed API files and tests: PASS
- `app.main` import: PASS
- `git diff --check`: PASS

Latest published AEI OCR capability gate:

```text
AEI Handwriting OCR Phase 1 - Gemini Flash answer-sheet transcription gate
```

Status: **Complete / certified / published**

Commit: `80fe4afc7e311536d99b9cd741ba1342fc1fb4c0`

Annotated tag: `aei-handwriting-ocr-phase1-gemini-transcription-certified`

Scope:

- added default-off OCR activation flag
  `AEI_HANDWRITING_OCR_PHASE1_ENABLED=false`;
- kept Gemini Flash answer-sheet transcription behind the existing StudyNexs AI
  Gateway;
- preserved the separation between general reasoning model routing and OCR /
  vision model routing;
- kept OCR transcription-only;
- added repository-safe Golden Harness cases for flag-off, gateway-routing,
  malformed JSON, and unsupported MIME behavior;
- preserved AEI evaluation, teacher approval, marks, routing, evidence ledger,
  schema, API, and UI behavior.

Validation:

- Focused OCR / gateway tests: 18 passed
- Targeted adjacent evaluation regression tests: 2 passed
- Focused ruff on changed API files and tests: PASS
- `app.main` import: PASS
- `git diff --check`: PASS

Latest published AEI OCR validation gate:

```text
AEI Handwriting OCR Phase 2 - Track-A Golden Set benchmark foundation
```

Status: **Complete / certified / published**

Commit: `266d073386a10bf6f661cb8c7e1f67f476d960c6`

Annotated tag: `aei-handwriting-ocr-phase2-track-a-benchmark-certified`

Scope:

- added deterministic OCR benchmark scoring helpers for CER, WER,
  per-question extraction accuracy, blank-answer accuracy, hallucination
  indicators, and schema validity;
- added repository-safe synthetic Track-A Golden Harness cases;
- added Track-A data handling guide;
- added aggregate benchmark report template;
- added candidate posture for Gemini Flash, Qwen2.5-VL-7B, and Surya 2 as
  benchmark candidates only;
- kept real answer sheets, real teacher transcriptions, and identifiable
  student data out of git;
- preserved production OCR routing, AEI evaluation, teacher approval, marks,
  routing, evidence ledger, schema, API, and UI behavior.

Validation:

- Focused Phase 2 benchmark tests: 13 passed
- Adjacent Phase 1 OCR / gateway regression tests: 18 passed
- Focused ruff on changed API files and tests: PASS
- `app.main` import: PASS
- `git diff --check`: PASS

---

## Standing rule

Every published runtime phase must end by updating this Master Status before the
next phase begins.

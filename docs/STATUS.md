# StudyNexs — Master Status

> **Owner:** Avinash Reddy Masapeta (ARM)
> **As of:** 2026-08-08
> **Status role:** Current project anchor for architecture, runtime milestones, and next engineering gate.

---

## Executive status

StudyNexs is an AI-first School Operating System with a frozen AEI/EUI
architecture, a published EUI runtime foundation, a certified AEI v1.0
supported-scope baseline, and published Assessment Intelligence v1.0 Batch A
contract/capability foundation, Batch B blueprint readiness foundation, Batch C
rubric/model-answer readiness foundation, Batch D question-bank/reuse readiness
foundation, Batch E paper-to-evaluation linkage readiness foundation, Batch F
bilingual/multilingual assessment readiness foundation, Batch G teacher
workflow/browser proof foundation, and Batch G-B reproducible Reference fixture
/ browser proof closure. Assessment Intelligence v1.0 Batch H is now published
and certifies the final v1.0 product-claim boundary for the declared supported
scope. The governed Question Paper Studio is now published as the first
post-certification Assessment Intelligence product-facing generation baseline.

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
| AI Gateway Gemini Vision Model Hardening | Complete / validated / published |
| AEI Handwriting OCR Phase 1 - Gemini Flash transcription gate | Complete / certified / published |
| AEI Handwriting OCR Phase 2 - Track-A benchmark foundation | Complete / certified / published |
| Assessment Intelligence v1.0 Batch A - Contract and capability matrix | Complete / certified / published |
| Assessment Intelligence v1.0 Batch B - Blueprint readiness | Complete / certified / published |
| Assessment Intelligence v1.0 Batch C - Rubric and model-answer readiness | Complete / certified / published |
| Assessment Intelligence v1.0 Batch D - Question bank and reuse readiness | Complete / certified / published |
| Assessment Intelligence v1.0 Batch E - Paper-to-evaluation linkage readiness | Complete / certified / published |
| Assessment Intelligence v1.0 Batch F - Bilingual / multilingual assessment readiness | Complete / certified / published |
| Assessment Intelligence v1.0 Batch G - Teacher workflow / browser proof | Complete / certified / published |
| Assessment Intelligence v1.0 Batch G-B - Reproducible Reference fixture / browser proof closure | Complete / certified / published |
| Assessment Intelligence v1.0 Batch H - Final certification and product-claim boundary | Complete / certified / published |
| Assessment Intelligence v1.0 Question Paper Studio - Governed generation workspace | Complete / certified / published |
| Stabilization Gate 1 - Production Safety | Complete / certified / published |
| Operational Proof | Complete / certified / published |
| AEI Activation / Trust | Complete / certified / published |
| Topic-ID / Mastery Spine Phase A - Passive resolution | Complete / certified / published |
| Data Model Hardening DM-1 - Exam-mark provenance FK | Complete / validated / published |
| Data Model Hardening DM-2 - Model hygiene (annotations, per-link parent relationship, FK convention) | Complete / validated / published |
| Data Model Hardening DM-2 Contract - Drop parents.relationship_type | Complete / validated / published |
| Data Model Hardening DM-3 - Enrollments, student lifecycle, promotion / year rollover | Complete / validated / published |
| Data Model Hardening DM-4 - Subject identity design brief (design-only) | Complete / published |
| Schema Integrity Hardening - Active-enrollment guard, Decimal marks, join-table tenancy | Complete / validated / published |
| Nginx Gateway Hardening - Security headers, private /metrics | Complete / validated / published |
| Gate 1A Deploy Kit - VM bootstrap + release scripts | Complete / validated / published |
| AEI Pilot Activation Kit - Staged runbook + OCR Track-A live benchmark runner | Complete / validated / published |
| Gate S Phase 0 - Canonical runtime integrity (P0-ENV-001) | Complete / verified in running product |
| Gate S Phase 1 - Fee privacy authorization (P0-SEC-001) | Complete / verified in running product |
| Gate S Phase 2 - LLM structured-output parsing (P1-AI-001/002) | Complete / verified in running product |
| Gate S Phase 3a - Attendance follows a class change (P1-DATA-001) | Complete / verified in running product |
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

## Gate S — Production-trust remediation (in progress)

Remediation of the Production Trust Audit
([`docs/reviews/PRODUCTION_TRUST_AUDIT_2026-08.md`](reviews/PRODUCTION_TRUST_AUDIT_2026-08.md)),
which returned **ORANGE / 5.0-of-10** and blocked a real school term.

**Status wording rule adopted for this gate:** an item is only marked *verified* when the
failure was first **reproduced in the running product** and the fix **re-verified there** —
not when unit tests pass. The audit proved a 970-test green suite can coexist with every P1
still reproducible, so unit-test-only evidence no longer earns a status here.

| Phase | Finding | Status | Live verification |
|---|---|---|---|
| 0 | P0-ENV-001 — runtime served the archived `academix-platform` build (140 routes, not 182) | ✅ Fixed / verified | `uvicorn` from a neutral cwd with no `PYTHONPATH` now serves **182** paths; all 5 canary routes present |
| 1 | P0-SEC-001 — `GET /fees/recent` admitted `role=teacher`, exposing every family's payments | ✅ Fixed / verified | `teacher` **200 → 403** on real fee data (was 50 receipts / 49 households / ₹125,000); `admin` + `super_admin` retain 200 |
| 2 | P1-AI-001/002 — fenced-JSON parse failures break Tutor, QP generation, Teacher Copilot | ✅ Fixed / verified | Live repro **10-of-14 → 0-of-14 failing**. Student Tutor answered in-browser (`200`, `grounded: true`, 2 citations) where it previously rendered `Copilot returned invalid JSON`; QP generation `400 → 200` (41 marks / 4 sections / 11 questions, ×2); Teacher Copilot feedback `400 → 200` with citations. All 4 controls still pass |
| 3a | P1-DATA-001 — attendance filed to a stale class after a class change | ✅ Fixed / verified | Live: row now **moves** to the receiving class. Before: `Grade 1 B` kept the row while `Grade 1 C` marked the student — C's register showed nothing, B counted a student who had left. After (clean slate): exactly **one** row, on C; B summary `total: 0`, C `present: 1` |
| 3b | P1-DATA-002 / P1-VAL-001 — negative marks and invalid exam totals | ✅ Fixed / verified | Live: `-0.01`, `-1`, `-20`, `-100` changed **200 → 422**; `total_marks` `0`, `-1`, `9999.991`, `10000`, `99999.99` changed **201/500 → 422**; database-safe `9999.99` remains `201` |
| 3c–3e | P1-DATA-003/004 — report-card scoping and impossible percentages | ⏳ Not started | — |
| 4 | P1-UX-002 — evaluation stale state (wrong-student attribution) | ⏳ Not started | — |
| 5 | P1-PDF-001 — all 5 PDF surfaces return 503 (WeasyPrint/libgobject) | ⏳ Not started | Known-failing: `tests/test_authorization.py::test_receipt_download_object_level_access` (`assert 503 == 200`) |

### Phase 0 notes — why the test suite could not have caught it

pytest inserts its rootdir (`apps/api`) at `sys.path[0]` (no `tests/__init__.py`), and a real
directory outranks an editable-install finder. So **pytest always imported the local `app/`
regardless of the broken install**, while `uvicorn` — which does not touch `sys.path` — served
the archived copy. A guard asserting on `app.__file__` is therefore a false negative; the new
guard inspects the *installed distribution record* instead. Verified by reproducing the bad
install and watching the guard fail, then pass after repair.

New hard CI gate: `pytest tests/test_canonical_runtime.py` (runs before lint, which stays
report-only). See the correction appended to
[`CANONICAL_REPOSITORY.md`](../CANONICAL_REPOSITORY.md).

### Phase 1 notes

`/fees/recent` was the only fee route granting a teaching role; `/stats` and `/roster` were
already correct, so this was a copy-paste slip rather than a policy. The frontend already
gated the call behind `isAdmin`, so removing the role is additive-safe with no UI change.
`class_incharge` was already correctly denied — which is exactly why a sweep that tests one
role per tier missed the bug.

### Phase 2 notes — one missing utility, three broken features

There was no tolerant JSON parser. Nine call sites each did bare `json.loads(result.text)`,
and the configured provider (`gemma4:cloud`) returns **markdown-fenced** JSON for structured
prompts (`` ```json\n{...}\n``` ``) and bare JSON only for trivial ones. So the failure was
100% reproducible on exactly the three highest-value AI surfaces and invisible everywhere
else. All nine sites now route through `app/modules/ai/gateway/json_parse.py::parse_llm_json`.

Deliberate design choices:

- **It recovers decoration, never repairs malformed JSON.** A silently "fixed" exam paper or
  grade is worse than a clean failure, so truncated JSON still raises.
- **Brace slicing is string-literal aware.** A naive `find('{')`/`rfind('}')` mis-slices when
  braces appear inside generated question text.
- **Raw model output is no longer logged.** Tutor / parent-copilot / evaluation replies carry
  student PII (names, mobiles, answers, marks); the parser logs only a structural fingerprint
  (`fence=yes braces=1/0 …`) plus length. This *tightened* two pre-existing `raw=` log lines
  in `question_paper_service` and `evaluation_engine`.
- **Students no longer see developer strings.** `"Copilot returned invalid JSON"` was rendered
  directly in the student tutor; it is now a calm, generic message (also satisfies Phase 6).
- **Parent copilot and curriculum extraction keep their graceful fallbacks** — which is why
  they appeared to "work" before and masked how broad the defect was.

Regression tests are call-site-level on purpose, since a utility test would not have caught
the original bug: an AST guard bans `json.loads(<llm result>.text)` anywhere in `app/`, and a
`capsys` guard-the-guard test proves log capture works (a `caplog` assertion silently passes
against structlog's stdout, which false-passed on the first attempt).

### Phase 3a notes — attendance and the one-row-per-day constraint

`uq_attendance_student_date` is `(school_id, student_id, date)` — deliberately **one row per
student per day** — so a mid-day class change must *move* that row. `mark_bulk`'s
`ON CONFLICT … set_` updated `status`, `remarks` and `marked_by` but **not `class_id`**, so the
row stayed on the old class while the API answered *"Attendance marked for 1 students"*.

Both registers then contradicted each other: the receiving teacher saw an empty register, and
the class the student had **left** still counted them. Neither teacher had any signal that
anything was wrong — the failure is silent and it corrupts the attendance record every time a
student changes class.

Audit of the sibling upserts: `mastery_service` already updates `class_id` on conflict, and
`ExamMark` has no `class_id` at all (class comes via the exam), so **attendance was the only
site with this defect** — an oversight rather than a policy.

Fix is one line (`"class_id": stmt.excluded.class_id`). Regression tests assert on the
**register and summary a teacher actually sees**, not just the stored row, because the row
alone would not have exposed the double-counting. A third test pins the ordinary
same-class correction path so the fix cannot over-correct into duplicate rows.

### Phase 3b notes — marks and exam-total boundaries

The marks endpoint checked only the upper bound. Live baseline: `-0.01`, `-1`, `-20`, and
`-100` all returned `200` and persisted; values above the exam total correctly returned
`400`. Exam creation had no lower bound and no Pydantic mirror of the database's
`Numeric(6,2)`: `total_marks=0` and `-1` returned `201`, while `99999.99` and `100000`
reached PostgreSQL and returned `500` with `numeric field overflow`.

`ExamCreate.total_marks` is now a positive `Decimal` constrained to `Numeric(6,2)`'s valid
range (`0 < total_marks <= 9999.99`). `MarkEntry.marks_obtained` is also a non-negative
`Decimal` with the same precision, and the service retains a defensive `0 <= marks <= total`
check for callers that bypass request validation. Invalid input is rejected with `422` before
it can corrupt the gradebook or reach the database; the exact valid maximum remains accepted.

Regression tests cover all audited boundaries in `test_exam_questions.py`. Focused suite:
**10 passed**. The promoted live repro confirmed the negative-mark boundaries now return
`422`, and a separate live boundary probe confirmed the total-mark behavior. Temporary QA
exams were deleted after verification.

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
| Batch F - Bilingual / Multilingual Assessment Readiness | Published / certified | `75f8c15fced408a457e9ce0106adb83f666acd1c` | `assessment-v1-batch-f-bilingual-multilingual-readiness-certified` | Bilingual/multilingual assessment declaration contract, static language supported-scope declarations, Golden Harness cases, focused static validation, and certification; no runtime behavior changes |
| Batch G - Teacher Workflow / Browser Proof | Published / certified | `42e7b80376989303a483b82db2b1020110d996a3` | `assessment-v1-batch-g-teacher-workflow-browser-proof-certified` | Browser proof harness and certification for the supported teacher assessment workflow, with tenant/API/console guards and no product behavior changes |
| Batch G-B - Reproducible Reference Fixture / Browser Proof Closure | Published / certified | `5641c195a7d11a998d50424e9ea440c9d50aa63d` | `assessment-v1-batch-g-b-reference-fixture-browser-proof-certified` | Idempotent Reference tenant fixture seed, deterministic Grade 6 Science approved paper + linked/evaluable exam, focused fixture tests, browser proof closure, and certification; no product behavior changes |
| Batch H - Final Certification / Product-Claim Boundary | Published / certified | `8a91404544596fad712626a5f5d2501a3630a43d` | `assessment-v1-certified` | Final Assessment Intelligence v1.0 certification report, product-claim boundary, focused static validation, and final no-overclaim guard; no runtime behavior changes |
| Question Paper Studio - Governed Generation Workspace | Published / certified | `6b4a280a6f6bba273e3f11b192e649a8cfa3fa17` | `assessment-intelligence-v1-question-paper-studio-certified` | Teacher-governed question-paper generation workspace with approved-curriculum grounding, exact template/blueprint controls, question-bank reuse, ungrounded exception governance, paper-to-exam linkage guards, and browser proof |

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

Assessment Intelligence v1.0 Batch F makes bilingual/multilingual assessment
support explicit, conservative, and non-universal.

Batch F adds:

- Batch F Bilingual / Multilingual Assessment Readiness Design Brief;
- Batch F Implementation Authorization Contract;
- Bilingual / Multilingual Assessment Declaration Contract;
- static Bilingual / Multilingual Supported Scope Declarations;
- Golden Harness bilingual/multilingual readiness cases;
- focused static bilingual/multilingual readiness validation tests;
- Batch F Certification Report.

Batch F certifies:

- English assessment contract support inside declared scope only;
- English grounded-paper readiness where Batch A-E requirements are satisfied;
- English answer-key/model-answer/rubric posture aligned with Batch C;
- teacher-authored bilingual paper manual-review posture;
- AI-assisted bilingual draft manual-review posture;
- bilingual rendering of already-reviewed teacher content as assist-only;
- Hindi answer-language, Telugu handwriting/OCR answer, and code-mixed answer
  relationships to AEI as assist-only;
- local-language answer context without reviewed source as manual-review;
- automatic question-paper translation as unsupported;
- automatic rubric/model-answer translation as unsupported;
- universal multilingual assessment as unsupported;
- Telugu-medium/state-board assessment packs as future expansion.

Batch F does not authorize or implement schema changes, API changes, UI changes,
runtime behavior changes, feature flags, translation engine integration, OCR
behavior changes, AI provider changes, LLM inference, question-paper generation
behavior changes, bilingual/multilingual rendering behavior changes,
question-bank service behavior changes, exam service behavior changes,
answer-sheet evaluation behavior changes, AEI language/OCR behavior changes,
AEI grading behavior changes, EUI source adoption, marks changes,
teacher-review routing changes, evidence-ledger behavior changes,
parent/student visibility changes, mastery updates, public bilingual/
multilingual product claim expansion, or Batch G teacher workflow/browser
proof.

Assessment Intelligence v1.0 Batch G proves the supported teacher assessment
workflow in a real browser without changing production behavior.

Batch G adds:

- Batch G Teacher Workflow / Browser Proof Design Brief;
- Batch G Implementation Authorization Contract;
- dedicated `e2e-assessment-v1` browser proof command;
- Reference tenant supported-scope proof requirements;
- console/API/tenant guard evidence;
- Batch G Certification Report.

Batch G certifies:

- supported Reference tenant Grade 6 Science question paper prerequisite;
- supported linked/evaluable exam prerequisite;
- AI Papers route rendering and teacher-authority posture;
- Exams route rendering and question-schema/marks posture;
- Evaluation route opening with AEI/evaluation-assist path visible;
- tenant header propagation on observed API calls;
- no disallowed console/API failures;
- no schema/API/UI/runtime/marks/routing/evidence-ledger behavior changes.

Batch G does not authorize or implement schema changes, API changes, production
UI changes, marks changes, teacher-review routing changes, evidence-ledger
changes, AEI behavior changes, EUI source adoption, public product claim
expansion, new question-paper generation behavior, or new evaluation behavior.

Assessment Intelligence v1.0 Batch G-B closes the reproducibility gap for the
Batch G browser proof.

Batch G-B adds:

- Batch G-B Reproducible Reference Fixture Design Brief;
- Batch G-B Implementation Authorization Contract;
- idempotent Reference tenant fixture seed script;
- focused fixture validation tests;
- browser proof repair guidance;
- Batch G-B Certification Report.

Batch G-B certifies:

- deterministic Reference tenant Grade 6 Science approved question paper
  fixture;
- deterministic linked/evaluable Unit Test exam fixture;
- fixture question schema consistency and total-mark preservation;
- successful fixture seed execution;
- successful browser proof against the seeded Reference tenant fixture;
- no schema/API/UI/runtime/marks/routing/evidence-ledger behavior changes.

Batch G-B does not authorize or implement schema changes, API changes,
production UI changes, production startup seed changes, marks changes,
teacher-review routing changes, evidence-ledger changes, AEI behavior changes,
EUI source adoption, OCR behavior changes, PDF ingestion behavior changes,
public product claim expansion, new question-paper generation behavior, or new
evaluation behavior.

Assessment Intelligence v1.0 Batch H is the final v1.0 certification and
product-claim boundary gate.

Batch H adds:

- Batch H Final Certification Design Brief;
- Batch H Implementation Authorization Contract;
- Assessment Intelligence v1.0 Final Certification Report;
- Assessment Intelligence v1.0 Product-Claim Boundary;
- focused static final-certification validation tests.

Batch H certifies:

- Assessment Intelligence v1.0 is production-ready inside the declared
  supported scope;
- product claims are limited to certified supported, assist, manual-review,
  unsupported, or expansion posture;
- universal board/grade/subject/language/OCR/visual support is not claimed;
- autonomous paper approval, autonomous grading, autonomous OCR marks, and
  autonomous diagram grading are not claimed;
- teachers remain the final academic authority;
- AEI remains the academic answer-evaluation pipeline;
- approved evidence remains the downstream source of truth;
- no schema/API/UI/runtime/marks/routing/evidence-ledger behavior changes.

Batch H does not authorize or implement schema changes, API changes,
production UI changes, runtime behavior changes, feature flag changes,
question-paper generation behavior changes, question-bank behavior changes,
exam service behavior changes, answer-sheet evaluation behavior changes, AEI
behavior changes, EUI behavior changes, EUI source adoption, marks changes,
teacher-review routing changes, evidence-ledger behavior changes, mastery
behavior changes, parent/student visibility changes, AI provider changes, LLM
inference changes, OCR behavior changes, translation behavior changes, or
public product-claim expansion beyond the certified supported scope.

Assessment Intelligence v1.0 Question Paper Studio turns the certified
assessment foundation into a teacher-governed generation workspace.

Question Paper Studio adds:

- a three-step teacher workflow for configuration, exact template definition,
  and question-level blueprint assignment;
- approved CurriculumPack grounding with stable chapter identifiers;
- exact section, question-type, question-count, marks, chapter, and Bloom-level
  controls;
- question-bank reuse that fails closed when exact supported coverage is
  missing;
- controlled ungrounded-paper exception governance with role, acknowledgement,
  reason, and pre-approval submission requirements;
- paper-to-exam linkage guards for class, subject, exam type, total marks, and
  tenant ownership;
- blueprint PDF support and browser proof coverage for the governed Studio
  path.

Question Paper Studio certifies:

- teachers remain the final paper authority;
- approved curriculum remains the default authoritative grounding source;
- ungrounded generation is explicitly disabled by default and requires governed
  acknowledgement when enabled;
- arbitrary or foreign chapter identifiers are rejected;
- exact bank-reuse gaps do not trigger hidden AI gap fill in Studio mode;
- generated paper output budgets are bounded to reduce truncation risk;
- Reference tenant browser proof passes with governed Studio anchors visible;
- no marks, grading, evidence-ledger, source-of-truth, parent/student, or
  answer-sheet evaluation behavior changes.

Latest Assessment Intelligence published gate:

```text
Assessment Intelligence v1.0 Question Paper Studio - Governed Generation Workspace
```

Status: **Complete / certified / published**.

No Assessment Intelligence implementation gate is currently active.

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
Schema Integrity Hardening (N-batch) — commit e5321f9
```

All authorized engineering work is complete and pushed to `develop`. The next
milestone is **Gate 1A — deploy + pilot** (operational, ARM-side): bootstrap
the OCI VM (`infra/scripts/bootstrap_oci_vm.sh`), release via
`infra/scripts/deploy.sh`, enable AEI Stage 1-2 flags per
[`runbooks/aei-pilot-activation.md`](./runbooks/aei-pilot-activation.md)
(ARM-authorized 2026-08-04), and begin real-school usage.

Gates published since the DM-1/DM-2 baseline below (2026-07-31 → 2026-08-04):

| Gate | Commits | Scope |
|---|---|---|
| Audit follow-up fixes | `e5f2485`, `d811161`, `3fe7b77`, `9809b6d`, `ec38abb`, `9bcd16a` | Compose fail-loud secrets, fake-school-name removal + pinch zoom, schema_version alignment, students error state, anonymous-refresh skip + portal loading states, `.env.example` |
| DM-3 - Enrollments + student lifecycle | `262c7a9`, `800b5b6`, `bbbb2ef`, `0abc5c2`, `29caa22`, `ff19c3b` | Per-year enrollments (migration `c7e9a1b3d5f7`), lifecycle service/API (change-class, transfer, withdraw, alumni, readmit), admin UI, bulk promotion + year-rollover service/UI/runbook |
| DM-4 design brief | `b126f07` | Subject-identity refactor brief folded into Spine Phase B (design-only) |
| AEI pilot activation + Track-A runner | `9e4c4cf` | Staged activation runbook, live OCR benchmark runner with production prompt/parser, privacy guards, compose flag pass-throughs |
| Gate 1A deploy kit | `7181e21` | `bootstrap_oci_vm.sh` (idempotent VM standup + api.env generation) and `deploy.sh` (pull → build → migrate → verify) |
| DM-2 contract phase | `9644433` | `parents.relationship_type` dropped (migration `e2a4c6d8f0b2`); link-level relationship is now the single source |
| Nginx hardening | `0a2c6b8` | Security headers on all responses, HSTS via forwarded-proto map, `/metrics` network-restricted |
| Schema integrity N-batch | `e5321f9` | One-ACTIVE-enrollment partial unique index (migration `f4b6d8a0c2e4`), `Mapped[Decimal]` on 10 mark columns, `school_id` on 3 join tables (migration `a6c8e0b2d4f6`) |

Migration head: `a6c8e0b2d4f6`. Regression: 121 tests across 13 touched suites
green; full main suite 922 passed as of DM-3b-1 (sole failure is the known
local Windows WeasyPrint/GTK environment issue).

Deliberately deferred (awaiting pilot data or separate authorization):

- Topic-ID / Mastery Spine Phase B (additive schema; needs real pilot data);
- AEI Stage 3/4 activation and the live OCR Track-A benchmark run (need 50-100
  teacher-verified sheets from the pilot; separate ARM authorization each);
- bulk section-move UI (API exists);
- frontend unit-test + e2e CI gate.

---

### Historical gate record — Data Model Hardening DM-1 / DM-2

```text
Data Model Hardening DM-1 / DM-2
```

Publication baseline:

- DM-1 commit `4ba5f01d726faf027e6c11d018d51c6e6b2751f5` — exam-mark
  provenance FK (`exam_marks.source_evaluation_id`, migration
  `a3c5e7f9d1b4`, reversible, backfilled);
- DM-2 commit `f23f6ad1cc8614e1418cb525cb863969ddbec4c3` — model hygiene:
  date/time annotation corrections, per-link parent relationship
  (`student_parent_map.relationship_type`, migration `b6d8f0a2c4e6`,
  expand phase, dual-write), teacher-FK convention documentation, and a
  constraint audit confirming all suspected-missing uniques already exist.

Validation: both migrations cycle upgrade/downgrade/upgrade; full main
suite 922 passed (the six unrelated failures are a local Windows
WeasyPrint/GTK environment issue, a pre-existing stale
`engineering-status` schema-version test, a cwd-dependent collection
artifact, and three `tests_security` cases that require their dedicated
guards-on harness).

Deferred items from this gate — all since delivered (see the current-gate
table above): DM-2 contract phase (`9644433`), DM-3 enrollments + lifecycle
(landed 2026-08-04, well ahead of the January 2027 target), and the DM-4
design brief (`b126f07`).

The previous completed gate was:

```text
Assessment Intelligence v1.0 Question Paper Studio - Governed Generation Workspace
```

- commit `6b4a280a6f6bba273e3f11b192e649a8cfa3fa17`;
- annotated tag `assessment-intelligence-v1-question-paper-studio-certified`.

Question Paper Studio turns the certified Assessment Intelligence v1.0
foundation into a governed teacher-facing question-paper generation workspace.
It adds approved-curriculum grounding, exact template and blueprint controls,
question-bank reuse, controlled ungrounded exception governance, paper-to-exam
linkage guards, and browser proof for the supported path.

Question Paper Studio preserves teacher approval as the authority boundary and
does not change marks, grading, answer-sheet evaluation, evidence-ledger
behavior, AEI source-of-truth behavior, parent/student visibility, or public
product-claim boundaries.

No implementation gate is currently active. Assessment Intelligence v1.0 Batch
A through Batch H and Question Paper Studio are published and certified. The
next product-facing gate must be selected and authorized separately by ARM.

Ordered candidate gates after the governed Question Paper Studio baseline:

1. AEI Handwriting OCR Phase 2 live Track-A benchmark run authorization -
   collect/use secured 50-100 teacher-verified real sheets and produce an
   aggregate candidate comparison report; not authorized.
2. AEI Handwriting OCR Phase 3 optimization design - confidence-routed chain
   and Qwen/Surya/Gemini operational decision based on Phase 2 evidence; not
   authorized.
3. Complete Curriculum Intelligence v1.0 readiness and implementation planning
   so assessment, evaluation, tutor, and analytics share approved curriculum
   truth; not authorized.
4. Topic-ID / Mastery Spine Phase B additive schema readiness design - future
   learning-intelligence plumbing only if ARM chooses deeper spine persistence;
   not authorized.

Completion of Question Paper Studio does not authorize autonomous paper
approval, autonomous grading, answer-sheet evaluation behavior changes,
question-bank source switching, source-of-truth switching, expanded public
product claims, API changes, schema changes, marks changes, routing changes,
mastery changes, evidence-ledger behavior changes, or parent/student
visibility changes.

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
- Assessment Intelligence behavior beyond the published Batch A-H foundations,
  including blueprint runtime behavior, question paper generation behavior,
  question bank runtime behavior, exam service behavior, API/UI/schema changes,
  marks/routing changes, evidence-ledger behavior changes, or product claim
  expansion beyond the certified product-claim boundary, without separate ARM
  authorization;
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
Assessment Intelligence v1.0 Batch E is published and adds paper-to-evaluation
linkage declaration posture, static supported-scope linkage declarations,
Golden Harness linkage cases, and certification without runtime behavior
changes.
Assessment Intelligence v1.0 Batch F is published and adds bilingual/
multilingual assessment declaration posture, static supported-scope language
declarations, Golden Harness bilingual/multilingual cases, and certification
without runtime behavior changes.
Assessment Intelligence v1.0 Batch G is published and adds the supported
teacher workflow/browser proof harness, Reference tenant prerequisite evidence,
tenant/API/console guard posture, and certification without product behavior
changes.
Assessment Intelligence v1.0 Batch G-B is published and adds the reproducible
Reference tenant fixture, deterministic Grade 6 Science approved paper and
linked/evaluable exam fixture, browser proof closure, and certification without
product behavior changes.
Assessment Intelligence v1.0 Batch H is published and certifies the final
Assessment Intelligence v1.0 supported-scope baseline, including the final
certification report and product-claim boundary, without runtime behavior
changes.
Assessment Intelligence v1.0 Question Paper Studio is published and adds the
governed teacher-facing question-paper generation workspace on top of the
certified Assessment foundation.
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
AI model routing from answer-sheet OCR / vision model routing. AI Gateway
Gemini Vision Model Hardening is published and updates the current Gemini OCR /
vision default from the unavailable `gemini-1.5-flash` posture to
`gemini-3.6-flash`. AEI Handwriting OCR Phase 1 is published and adds the
default-off Gemini Flash answer-sheet transcription gate through the StudyNexs
AI Gateway only. AEI Handwriting OCR Phase 2 is published and adds the
repository-safe Track-A benchmark foundation without running live real-sheet
benchmarks or changing production OCR routing.
UX-E remains the assembled teacher-evaluation certification baseline and the
lint cleanup remains the code-health gate that resolved the pre-existing page
lint debt. Assessment Intelligence v1.0 Question Paper Studio is now the
latest published Assessment gate and provides the governed paper-generation
workspace inside the declared supported scope. No Assessment Intelligence
implementation gate is active until ARM authorizes the next product-facing
milestone under a separate design and implementation contract.

---

## Validation posture

Latest published Assessment Intelligence gate:

```text
Assessment Intelligence v1.0 Question Paper Studio - Governed Generation Workspace
```

Status: **Complete / certified / published**

Commit: `6b4a280a6f6bba273e3f11b192e649a8cfa3fa17`

Annotated tag: `assessment-intelligence-v1-question-paper-studio-certified`

Evidence:

Certified evidence:

- Focused Assessment/AI paper backend regression: PASS - 78 passed
- Production admin-web build: PASS
- Focused Python Ruff on modified/untracked sprint files: PASS
- Focused admin-web ESLint on touched files: PASS
- API import: PASS
- Alembic head / downgrade / upgrade validation: PASS
- `git diff --check`: PASS
- Browser proof: PASS - 18 checks, 0 disallowed console/API errors
- Tenant header proof: PASS - Reference tenant observed on 52 API calls
- Remote publication proof: PASS - `develop` and annotated tag published
- No marks, grading, evidence-ledger, source-of-truth, parent/student,
  answer-sheet evaluation, or AEI behavior changes: PASS

Next Assessment Intelligence gate:

```text
Not selected
```

Status: **Awaiting ARM selection / authorization**

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

Published AI infrastructure hardening gate:

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

Latest published AI infrastructure hardening gate:

```text
AI Gateway Gemini Vision Model Hardening
```

Status: **Complete / validated / published**

Commit: `d0595b8001e917767e6e6dac62f8541b9a793922`

Annotated tag: `ai-gateway-gemini-vision-model-hardening-certified`

Scope:

- updated the default Gemini gateway model to `gemini-3.6-flash`;
- updated OCR / vision configuration examples and Phase 1 OCR documentation;
- updated focused OCR / gateway tests and Golden Harness expectations;
- added `gemini-3.6-flash` to AI gateway pricing metadata;
- retained the legacy `gemini-1.5-flash` pricing entry for explicitly
  configured legacy traffic;
- kept answer-sheet OCR as transcription-only through the gateway;
- preserved AEI evaluation, teacher approval, marks, routing, evidence ledger,
  schema, API, production UI, and product behavior.

Validation:

- Focused gateway / answer-sheet vision / OCR Phase 1 tests: PASS - 18 passed
- Focused ruff on changed API files and tests: PASS
- `app.main` import: PASS
- `git diff --check`: PASS
- Live local OCR smoke on the supplied Math / English / Telugu images:
  `gemini-3.6-flash` succeeded as OCR-only transcription; no grading or
  persistence was performed.

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

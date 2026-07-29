# Assessment Intelligence v1.0 Batch B Design Brief

> Owner: Avinash Reddy Masapeta (ARM)  
> Date: 2026-07-29  
> Program: Assessment Intelligence v1.0  
> Batch: B - Blueprint Readiness  
> Status: Accepted  
> Classification: Product implementation design  
> Implementation: Not authorized  
> Runtime behavior changes: Not authorized by this document  
> Previous baseline: Batch A - Contract and Capability Matrix
> ARM review: Accepted as the Batch B Blueprint Readiness design baseline

---

## 1. Purpose

Batch B should make assessment blueprint behavior explicit, validated, and
non-universal.

It answers:

> Which paper structures does StudyNexs actually support, how are those
> structures declared, and how do we prevent a hardcoded helper from becoming a
> hidden universal product claim?

This document is design-only. It does not authorize implementation.

---

## 2. Why Batch B exists

Assessment Intelligence v1.0 Batch A established the canonical assessment
contract and supported-scope matrix.

Batch B is the next dependency because question-paper generation, question-bank
compose, exam schema import, and downstream evaluation all depend on paper
structure.

The current repository already has blueprint-like behavior in
`apps/api/app/modules/ai/services/question_paper_service.py`.

Current behavior includes:

- an `_ssc_blueprint(total_marks)` helper;
- section plans with `title`, `marks_per_q`, `count`, `answer_any`, `type`, and
  `instructions`;
- prompt construction from the section plan;
- generated paper `total_marks` derived from the official blueprint total;
- bank compose using the same plan;
- internal choice supported through `answer_any`;
- non-standard totals scaled from the standard plan.

This is useful, but it is not yet a production-ready blueprint posture for a
multi-board product.

---

## 3. Product outcome

After Batch B is eventually implemented and certified, StudyNexs should be able
to say:

> For the declared supported scope, question-paper structure is explicit,
> reviewable, test-covered, and not treated as universal.

Teachers should not need to understand internal code helpers to know what paper
structure StudyNexs is using.

---

## 4. Design principle

Blueprints are educational data, not hidden generation logic.

```text
Board / Curriculum / Grade / Subject / Paper Type
        |
        v
Blueprint Declaration
        |
        v
Question Paper Draft
        |
        v
Teacher Review and Approval
        |
        v
Exam Schema / Evaluation Linkage
```

Blueprint readiness should not create autonomous assessment authority. It only
makes the structure of an assessment explicit.

---

## 5. Relationship to Batch A contract

Batch B should build directly on Batch A blueprint fields:

- `paper_type`;
- `blueprint_id`;
- `section_id`;
- `section_title`;
- `question_type`;
- `marks`;
- `marks_posture`;
- `required_count`;
- `answer_any_count`;
- `duration_minutes`.

Batch B should not invent a second assessment contract.

---

## 6. Blueprint declaration model

A blueprint declaration should describe an assessment structure without
depending on LLM output.

Minimum declaration fields:

| Field | Purpose |
|---|---|
| `blueprint_id` | Stable blueprint identifier. |
| `board` | Board scope, e.g. `CBSE`, `SSC`. |
| `curriculum` | Curriculum family, e.g. `NCF2023`. |
| `grade` | Grade/class scope. |
| `subject` | Subject scope. |
| `paper_type` | Unit test, slip test, term exam, practice, or supported equivalent. |
| `version` | Blueprint declaration version. |
| `status` | `supported`, `assist`, `manual_review`, `unsupported`, or `expansion`. |
| `total_marks` | Official marks total for the declaration. |
| `duration_minutes` | Expected duration. |
| `sections` | Ordered section declarations. |
| `validation_rules` | Marks, count, internal-choice, and option rules. |
| `product_claim_allowed` | Whether StudyNexs may claim support for this blueprint. |

Section fields:

| Field | Purpose |
|---|---|
| `section_id` | Stable section identifier. |
| `title` | Teacher-visible title. |
| `instructions` | Teacher/student instructions. |
| `question_type` | MCQ, short, long, diagram, etc. |
| `marks_per_question` | Marks per generated question. |
| `question_count` | Questions printed. |
| `answer_any_count` | Questions to answer when internal choice applies. |
| `required` | Whether the section is mandatory. |
| `options_required` | MCQ option requirements where applicable. |

---

## 7. Blueprint support modes

Blueprints should use the same conservative capability posture as Batch A.

| Mode | Meaning |
|---|---|
| `supported` | Product may claim this blueprint inside the declared scope. |
| `assist` | System can help draft, but teacher must verify structure. |
| `manual_review` | Teacher must define/approve structure; no product claim. |
| `unsupported` | Product must not claim support. |
| `expansion` | Future scope only. |

Supported blueprint does not mean generated question content is automatically
correct. It means the structure is declared and validated.

---

## 8. Deterministic validation expectations

Batch B should define deterministic blueprint validation.

Validation should cover:

- section order;
- marks per question;
- question counts;
- internal-choice count;
- computed effective total;
- printed total;
- MCQ option requirements;
- unsupported question types;
- paper type support posture;
- product-claim posture.

Internal-choice handling must distinguish:

```text
printed_questions_total
    from
answer_required_total
```

This prevents the system from treating "answer any 4 of 6" as a malformed paper.

---

## 9. Current helper migration posture

The current `_ssc_blueprint(total_marks)` helper should not be deleted or
rewritten abruptly.

Recommended posture:

1. Declare the current supported blueprint behavior in a read-only declaration.
2. Validate the declared behavior through Golden Harness cases.
3. Keep runtime generation unchanged until a later implementation contract
   explicitly authorizes runtime mapping.
4. Avoid claiming the helper is universal.

Batch B should make the implicit behavior auditable first. Runtime adoption can
remain a later step if needed.

---

## 10. Suggested Batch B implementation scope

The later implementation contract should decide exact files, but the design
recommends a narrow Batch B foundation:

- blueprint declaration document;
- read-only blueprint capability/declaration data;
- Golden Harness blueprint cases;
- focused static/deterministic tests;
- certification report.

Optional only if authorized:

- a small pure helper that validates blueprint declarations without touching
  production request paths.

---

## 11. Explicit non-goals

Batch B should not implement:

- runtime question-paper generation behavior changes;
- schema changes;
- API changes;
- UI changes;
- feature flags;
- public product claim changes;
- new AI provider behavior;
- LLM prompt changes;
- question bank runtime changes;
- exam service runtime changes;
- AEI behavior changes;
- EUI source adoption;
- marks changes;
- teacher review routing changes;
- evidence-ledger changes;
- browser workflow changes;
- board expansion beyond declared supported scope.

---

## 12. Golden Harness expectations

Batch B Golden Harness should include:

- supported blueprint declaration loads;
- internal-choice effective marks calculation;
- unsupported blueprint posture;
- expansion board posture;
- MCQ option requirement posture;
- mismatch between requested total and official total posture;
- teacher-review required for assist/manual-review blueprints;
- no autonomous grading or approval implied by blueprint support.

Cases should be deterministic and require no database, LLM, provider, browser,
or network execution.

---

## 13. Certification expectations

Batch B certification should prove:

- blueprint declarations exist for the supported scope;
- every declaration has stable IDs and versioning;
- support modes are explicit;
- internal-choice behavior is deterministic;
- unsupported/expansion scopes do not become product claims;
- no runtime behavior changed unless separately authorized;
- no schema/API/UI changes occurred;
- adjacent question-paper and question-bank tests still pass;
- Batch A contract remains intact.

---

## 14. Recommended next artifact

If ARM accepts this design brief, the next artifact should be:

`ASSESSMENT_INTELLIGENCE_V1_BATCH_B_BLUEPRINT_READINESS_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md`

Recommended authorization posture:

- authorize static blueprint readiness foundation only;
- keep runtime generation behavior unchanged;
- require Golden Harness and focused tests;
- require certification;
- prohibit Batch C rubric/model-answer work until Batch B is certified and
  published.

---

## 15. ARM gate

ARM may choose one of three decisions:

1. Accept the design brief and request the Batch B implementation authorization
   contract.
2. Accept with clarification requests.
3. Reject and revise the design.

Until ARM explicitly accepts a future implementation authorization contract,
Batch B implementation is not authorized.

# Academic Evaluation Intelligence (AEI)

**Status:** Architecture frozen
**Version:** v1
**Date:** 2026-07-25
**Owner:** Avinash Reddy Masapeta (ARM)
**ADR:** [`../decisions/ADR-0001-academic-evaluation-intelligence-architecture-freeze.md`](../decisions/ADR-0001-academic-evaluation-intelligence-architecture-freeze.md)

---

## 1. Purpose

Academic Evaluation Intelligence is the protected StudyNexs subsystem for teacher-approved academic evaluation.

AEI exists to transform student answers into explainable, reviewable, evidence-backed evaluation suggestions while preserving teacher authority and downstream evidence integrity.

AEI is not an autonomous grader. It is the academic understanding, reasoning, policy, and review pipeline that supports teachers.

---

## 2. Philosophy

StudyNexs evaluates academic work with one rule:

> AI assists. Teachers certify.

AEI must therefore be:

- deterministic where deterministic evaluation is possible;
- confidence-aware where uncertainty exists;
- honest about partial support;
- grounded in the question/rubric/curriculum context;
- teacher-reviewable before marks become authoritative;
- safe for downstream Learning, Student, Parent, and Principal Intelligence.

---

## 3. Architecture

AEI is a protected subsystem inside the existing certified evaluation architecture. It does not replace the existing Evaluation Service, evidence ledger, teacher approval workflow, gradebook, mastery, or downstream intelligence consumers.

It extends the existing evaluation path with a permanent pipeline:

```text
Evaluation Service
        ↓
Subject Capability Registry
        ↓
AcademicAnswer
        ↓
Academic Understanding Engine
        ↓
Academic Reasoning Layer
        ↓
Evaluation Policy
        ↓
Teacher Review
        ↓
Evidence Ledger
        ↓
Learning Intelligence
```

No academic evaluation logic may bypass this pipeline.

---

## 4. Pipeline

### 4.1 Evaluation Service

The existing Evaluation Service owns exam/evaluation lifecycle orchestration:

- answer-sheet evaluation creation;
- worker/runtime execution;
- answer extraction;
- AEI invocation;
- teacher approval;
- gradebook and mastery propagation;
- evidence ledger continuity.

The Evaluation Service does not contain subject-specific evaluation logic directly.

### 4.2 Subject Capability Registry

The registry defines what AEI may claim for each subject and capability.

It answers:

- Is this capability supported?
- Is it partial?
- Is it assist-only?
- Is it manual-review-only?
- Is it out of scope?

### 4.3 AcademicAnswer

`AcademicAnswer` is the canonical internal object carried through AEI.

It prevents each layer from inventing separate field names and repeated parsing logic.

### 4.4 Academic Understanding Engine

The Academic Understanding Engine is an orchestrator. It selects and runs providers that parse, normalize, detect, classify, and enrich answers.

It answers:

> What is this answer?

It does not decide final marks.

### 4.5 Academic Reasoning Layer

The Academic Reasoning Layer consumes enriched `AcademicAnswer` objects and rubric context.

It answers:

> What academic meaning does this answer have against the rubric?

Examples:

- `5½` is equivalent to `5.5`.
- `H2 + O2 -> H2O` is an unbalanced equation.
- A graph contains axes but no labelled units.
- A biology diagram has some expected labels but needs teacher confirmation.

### 4.6 Evaluation Policy

Evaluation Policy owns workflow decisions:

- accept suggestion;
- require manual review;
- mark as assist-only;
- flag unsupported capability;
- explain confidence;
- route to teacher review.

Policy does not certify final marks. Teacher approval does.

### 4.7 Teacher Review

Teacher Review is the only point where final marks become authoritative.

The UI must clearly show:

- suggested marks;
- confidence;
- reasoning;
- manual-review reasons;
- supported/partial/assist/manual-review capability;
- teacher override reason;
- final teacher-approved marks.

### 4.8 Evidence Ledger

Only teacher-approved evaluation evidence propagates downstream.

Downstream consumers must not rely on unapproved AI output.

---

## 5. AcademicAnswer model

`AcademicAnswer` is the canonical AEI object.

Recommended conceptual shape:

```python
class AcademicAnswer(BaseModel):
    raw_input: str | None
    normalized_input: str | None = None
    subject: str | None = None
    question_type: str | None = None
    detected_language: str | None = None
    detected_script: str | None = None
    code_mixed: bool = False
    visual_type: str | None = None
    scientific_type: str | None = None
    math_type: str | None = None
    confidence: float | None = None
    confidence_reason: str | None = None
    metadata: dict[str, Any] = {}
```

This object may be enriched as it moves through providers and reasoners.

The raw input must remain preserved for auditability.

---

## 6. Provider contracts

Providers enrich `AcademicAnswer`. They do not award final marks.

```python
class AcademicProvider(Protocol):
    def supports(self, answer: AcademicAnswer) -> bool:
        ...

    def process(self, answer: AcademicAnswer) -> AcademicAnswer:
        ...
```

Initial provider families:

| Provider | Responsibility |
|---|---|
| `TextProvider` | Text cleanup, blank/illegible detection, basic normalization |
| `MathProvider` | Fractions, decimals, mixed numbers, tolerance, scientific notation |
| `ScientificProvider` | Units, equations, formula-like expressions, chemistry/physics signals |
| `VisualProvider` | Diagram/graph/map/circuit/flowchart detection and checklist extraction |
| `LanguageProvider` | Language/script detection, Unicode normalization, Indic/code-mixed metadata |
| `ConfidenceProvider` | Confidence consolidation and uncertainty explanation |

Providers must be small, independently testable, and capability-scoped.

---

## 7. Reasoning contracts

Reasoners consume an enriched `AcademicAnswer` and rubric context, then produce academic meaning.

```python
class AcademicReasoner(Protocol):
    def reason(self, answer: AcademicAnswer, rubric: Rubric) -> ReasoningResult:
        ...
```

Recommended conceptual result:

```python
class ReasoningResult(BaseModel):
    reasoning_type: str
    result: str
    matched_answer: str | None = None
    explanation: str | None = None
    confidence: float | None = None
    evidence: dict[str, Any] = {}
    review_signals: list[str] = []
```

Reasoners should not mutate raw input.

Examples:

- numeric equivalence;
- unit equivalence;
- tolerance match;
- scientific notation match;
- chemistry reaction balancing assist;
- visual checklist observations;
- language/manual-review signals.

---

## 8. Policy contracts

Policy converts reasoning into workflow decisions.

```python
class EvaluationPolicy(Protocol):
    def evaluate(self, reasoning: ReasoningResult) -> PolicyDecision:
        ...
```

Recommended conceptual decision:

```python
class PolicyDecision(BaseModel):
    mode: Literal["supported", "partial", "assist", "manual_review", "unsupported"]
    suggested_marks: Decimal | None = None
    confidence: float | None = None
    confidence_reason: str | None = None
    manual_review_required: bool = False
    manual_review_reason: str | None = None
    teacher_message: str | None = None
```

Policy owns:

- confidence thresholds;
- manual review routing;
- supported/partial/assist/manual-review classification;
- teacher-facing explanation.

Policy does not bypass teacher approval.

---

## 9. Subject Capability Registry schema

The registry is declarative and data-driven.

Recommended shape:

```yaml
subjects:
  mathematics:
    evaluation:
      numeric_equivalence:
        mode: supported
      units:
        mode: supported
      tolerance:
        mode: supported
      scientific_notation:
        mode: supported
      diagrams:
        mode: partial

  physics:
    evaluation:
      units:
        mode: supported
      formula_recognition:
        mode: assist
      diagrams:
        mode: checklist

  chemistry:
    evaluation:
      reaction_balancing:
        mode: assist
      chemical_symbols:
        mode: assist
      structures:
        mode: manual_review

  biology:
    evaluation:
      diagrams:
        mode: checklist
      labels:
        mode: assist

  geography:
    evaluation:
      maps:
        mode: checklist
      labels:
        mode: assist

  hindi:
    evaluation:
      printed_ocr:
        mode: assist
      handwriting_ocr:
        mode: assist
      grading:
        mode: teacher_review

  telugu:
    evaluation:
      printed_ocr:
        mode: assist
      handwriting_ocr:
        mode: assist
      grading:
        mode: teacher_review

  sanskrit:
    evaluation:
      printed_ocr:
        mode: assist
      handwriting_ocr:
        mode: assist
      grading:
        mode: teacher_review
```

Mode meanings:

| Mode | Meaning |
|---|---|
| `supported` | AEI may produce deterministic or high-confidence suggestions within scope |
| `partial` | AEI may support some cases but must communicate limits |
| `assist` | AEI may help detect, parse, describe, or suggest; teacher review required |
| `checklist` | AEI may produce checklist observations; teacher confirms marks |
| `manual_review` | AEI must route to teacher review |
| `unsupported` | AEI must not claim capability |

Start as a versioned registry file/service. Move to database-backed configuration only when real pilot requirements prove school-specific customization is necessary.

---

## 10. UI responsibilities

Teacher UI must present AEI output as reviewable suggestions, not final academic truth.

Required UI concepts:

- Suggested marks, not “AI marks” as final authority.
- Confidence.
- Confidence reason.
- Manual-review badge.
- Supported/partial/assist/manual-review capability indicator.
- Academic reasoning explanation.
- Normalized answer where relevant.
- Matched acceptable answer where relevant.
- Unit/tolerance result where relevant.
- Visual/language/science checklist where relevant.
- Teacher override reason.
- Teacher-approved final mark.

Student, Parent, and Principal UI must consume teacher-approved evidence only.

---

## 11. Evidence contracts

AEI must preserve the existing evidence guarantees:

- tenant-scoped evaluation;
- linked CurriculumPack / Question Paper / Exam;
- AI suggestion separate from teacher final decision;
- teacher approval recorded;
- override reason preserved;
- downstream consumers receive approved evidence only;
- no fallback presented as certified behavior.

Uncertain, partial, or assist-mode output must not become downstream evidence until a teacher approves the result.

---

## 12. Extension guide

To add a new academic capability:

1. Add or update Subject Capability Registry entry.
2. Add provider support if the capability requires new parsing/detection.
3. Add reasoning support if the capability requires academic meaning.
4. Add policy behavior for support/review/assist/manual-review mode.
5. Add UI display only if teachers need to understand or act on the result.
6. Add Golden Harness cases.
7. Add focused backend tests.
8. Add runtime/browser proof if the capability affects pilot-certified flows.

Do not add direct evaluation logic inside endpoints, UI components, or downstream intelligence consumers.

---

## 13. Anti-patterns

The following are prohibited:

- Direct subject grading logic inside API endpoints.
- Direct subject grading logic inside React components.
- Provider-specific bypasses around Evaluation Policy.
- Using confidence as a final mark decision.
- Showing uncertain output as certified.
- Sending unapproved evaluation output to Student, Parent, or Principal Intelligence.
- Hardcoding board, school, or teacher-specific grading policy in code.
- Adding a capability without Golden Harness regression coverage.
- Creating another “evaluation engine” parallel to AEI.

---

## 14. Testing strategy

AEI requires layered testing:

| Layer | Test expectation |
|---|---|
| Subject Capability Registry | Supported/partial/assist/manual-review modes resolve correctly |
| AcademicAnswer | Raw input preservation and metadata enrichment |
| Providers | Provider-specific parsing/detection/normalization |
| Reasoners | Academic meaning against rubric context |
| Policy | Manual-review routing and confidence decisions |
| Evaluation integration | Teacher approval and evidence propagation |
| Downstream consumers | Only approved evidence reaches Learning/Student/Parent/Principal surfaces |

Existing H8-certified proofs must continue to pass after AEI implementation.

---

## 15. Golden Harness requirements

Every AEI capability requires regression fixtures.

Recommended structure:

```text
apps/api/tests/golden/
    mathematics/
    chemistry/
    physics/
    biology/
    geography/
    languages/
    visual/
```

Golden cases should include:

- input answer;
- question/rubric context;
- expected understanding;
- expected reasoning;
- expected policy decision;
- expected manual-review behavior;
- expected teacher-facing explanation.

Golden Harness failures are release blockers for the affected capability.

---

## 16. ADR references

Primary ADR:

- [`ADR-0001: Academic Evaluation Intelligence Architecture Freeze`](../decisions/ADR-0001-academic-evaluation-intelligence-architecture-freeze.md)

Future ADRs are required for:

- bypassing the AEI pipeline;
- changing provider/reasoning/policy contracts;
- making subject capability registry database-backed;
- adding autonomous evaluation behavior;
- allowing non-teacher-approved evidence downstream.

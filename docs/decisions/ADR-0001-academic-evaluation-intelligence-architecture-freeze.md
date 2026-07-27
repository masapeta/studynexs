# ADR-0001: Academic Evaluation Intelligence Architecture Freeze

**Status:** Accepted
**Date:** 2026-07-25
**Owner:** Avinash Reddy Masapeta (ARM)
**Subsystem:** Academic Evaluation Intelligence (AEI)

---

## Context

StudyNexs has a certified Academic Intelligence Platform baseline with a complete evidence chain from approved curriculum through assessment, evaluation, mastery, learning, student, parent, and principal intelligence.

The next guided-pilot trust risk is academic evaluation breadth and explainability: mathematical equivalence, units, tolerance, language handling, visual answers, scientific notation, chemistry equations, graphs, maps, confidence, manual review, and teacher override clarity.

These capabilities must not be implemented as scattered helpers or parallel evaluators. Evaluation is consequential academic output, so it must remain teacher-approved, evidence-backed, tenant-scoped, and regression-tested.

---

## Decision

All academic evaluation functionality shall flow through the protected Academic Evaluation Intelligence pipeline:

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

AEI v1 is a protected subsystem. New evaluation capabilities must extend the pipeline through provider, reasoning, policy, and golden-harness contracts rather than creating one-off service logic.

---

## Architecture rules

1. The teacher is always the final evaluator.
2. Every academic evaluation decision flows through AEI.
3. No evaluation helper may bypass AEI.
4. New academic capabilities extend providers; they do not create parallel evaluators.
5. Subject Capability Registry defines what the system may claim.
6. `AcademicAnswer` is the canonical internal object carried through the pipeline.
7. Academic Understanding parses, detects, normalizes, and enriches.
8. Academic Reasoning determines academic meaning against rubric context.
9. Evaluation Policy decides accept, review, reject, assist, and confidence workflow.
10. Confidence affects workflow and review routing; it does not independently certify marks.
11. Student, Parent, and Principal Intelligence consume only teacher-approved evidence.
12. Every AEI capability must include Golden Harness regression coverage.
13. AEI architecture changes require explicit approval and a new ADR.

---

## Provider contract

AEI providers are focused understanding components. They enrich an `AcademicAnswer`; they do not award final marks.

```python
class AcademicProvider(Protocol):
    def supports(self, answer: AcademicAnswer) -> bool:
        ...

    def process(self, answer: AcademicAnswer) -> AcademicAnswer:
        ...
```

Initial provider families:

- `TextProvider`
- `MathProvider`
- `ScientificProvider`
- `VisualProvider`
- `LanguageProvider`
- `ConfidenceProvider`

---

## Reasoning contract

Reasoners consume the enriched `AcademicAnswer` and rubric context, then produce academic meaning.

```python
class AcademicReasoner(Protocol):
    def reason(self, answer: AcademicAnswer, rubric: Rubric) -> ReasoningResult:
        ...
```

Reasoners must not mutate raw input. They may produce equivalence, checklist, unit, scientific, language, or manual-review signals.

---

## Policy contract

Policy decides workflow outcome. It owns support mode, confidence thresholds, manual review routing, and teacher-facing reasons.

```python
class EvaluationPolicy(Protocol):
    def evaluate(self, reasoning: ReasoningResult) -> PolicyDecision:
        ...
```

Policy decisions may include:

- supported
- partial
- assist
- manual review
- unsupported
- accept suggestion
- reject suggestion

Policy does not bypass teacher approval.

---

## Subject Capability Registry

The Subject Capability Registry is declarative and data-driven. It defines what AEI may claim per subject/capability.

Example shape:

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
      diagrams:
        mode: partial

  biology:
    evaluation:
      diagrams:
        mode: checklist
      labels:
        mode: supported

  chemistry:
    evaluation:
      reaction_balancing:
        mode: assist
      structures:
        mode: manual_review

  hindi:
    evaluation:
      printed_ocr:
        mode: assist
      handwriting_ocr:
        mode: assist
      grading:
        mode: teacher_review
```

The registry may power API metadata, UI badges, pilot documentation, review routing, and future board/grade/language expansion.

---

## Golden Harness gate

Every provider must include regression examples under the Golden Harness.

Expected dataset families:

```text
tests/golden/
    mathematics/
    chemistry/
    biology/
    languages/
    visual/
```

A new provider or capability without golden cases is incomplete.

---

## Consequences

### Positive

- Prevents scattered evaluation logic.
- Makes evaluation capability explicit and testable.
- Keeps teacher authority central.
- Preserves the certified evidence chain.
- Allows future subject expansion without refactoring the evaluation architecture.
- Gives pilot messaging one source of truth for what is supported, partial, assistive, or manual-review-only.

### Tradeoffs

- AEI requires slightly more upfront structure than ad hoc helper functions.
- Provider and policy contracts must be maintained carefully.
- Golden Harness coverage becomes mandatory for academic capability expansion.

---

## Anti-patterns

The following are architectural defects:

- Adding evaluation logic directly inside endpoints.
- Adding subject-specific grading logic that bypasses AEI providers/reasoners/policy.
- Showing uncertain AI output as certified marks.
- Allowing Student, Parent, or Principal surfaces to consume unapproved evaluation output.
- Hardcoding board or school-specific evaluation policy in code.
- Adding a provider without Golden Harness cases.
- Letting confidence directly determine final marks without teacher approval.

---

## References

- `docs/architecture/AEI.md`
- `docs/product/PRODUCTION_READINESS_CERTIFICATION_REPORT.md`
- `docs/product/STUDYNEXS_IMPLEMENTATION_BLUEPRINT.md`
- `AGENTS.md`

# Platform Capability Registry

- **Status:** Accepted
- **Parent architecture:** [`../EUI.md`](../EUI.md)
- **Related subsystem:** [`../AEI.md`](../AEI.md)

---

## 1. Purpose

The Platform Capability Registry is the single source of truth for what StudyNexs can claim across educational intelligence.

It generalizes the AEI Subject Capability Registry from evaluation-only capability claims into platform-wide educational capability claims.

---

## 2. Principle

Capability claims must be explicit.

StudyNexs should never imply universal support where it only supports a bounded scenario. A production product can be complete for its supported scope without claiming every possible board, language, handwriting style, diagram, or classroom edge case.

---

## 3. Capability dimensions

| Dimension | Examples |
|---|---|
| Languages | English, Hindi, Telugu, Sanskrit, code-mixed Hindi-English, code-mixed Telugu-English |
| Input acquisition | Printed OCR, handwriting OCR, voice, image, PDF |
| Mathematics | Numeric normalization, unit conversion, equation equivalence |
| Science | Scientific notation, formulas, chemical equations, diagrams |
| Visual understanding | Biology diagrams, graphs, maps, circuits, flowcharts |
| Evaluation | Reasoning, policy, teacher review, evidence ledger |
| Learning | Concept mapping, misconception detection, remediation |
| Communication | Parent-safe explanations, translations, circular support |
| Analytics | Class trends, subject trends, concept trends, school-level summaries |

---

## 4. Modes

| Mode | Meaning |
|---|---|
| `supported` | Production-quality for the declared scope. |
| `assist` | Helps extract, describe, or suggest; human review remains required. |
| `checklist` | Produces structured observations for teacher confirmation. |
| `manual_review` | Must route to human review before academic use. |
| `unsupported` | Must not claim capability. |
| `expansion` | Planned capability area, not part of current production claim. |

---

## 5. Declarative shape

The registry should remain declarative rather than embedding logic.

Conceptual shape:

```yaml
version: eui-v1
domains:
  language:
    hindi:
      printed_ocr:
        mode: supported
        scope: "clear printed Devanagari within configured quality limits"
      handwriting_ocr:
        mode: assist
        scope: "confidence-based extraction with teacher correction"

  mathematics:
    class_10:
      numeric_normalization:
        mode: supported
      unit_conversion:
        mode: supported
      geometry_diagrams:
        mode: checklist

  visual:
    maps:
      mode: checklist
    pixel_perfect_diagram_grading:
      mode: unsupported
```

This architecture program does not create the registry implementation.

---

## 6. Consumers

The registry should power:

- UI badges;
- teacher expectation messaging;
- production scope documents;
- tests and certification gates;
- release notes;
- Trust Reports;
- consumer contracts;
- support documentation.

No consumer should maintain its own capability claims.

Platform capabilities should be extended through registry entries, provider contracts, graph relationships, or consumer contracts. They should not be extended by duplicating educational understanding logic inside individual consumers.

---

## 7. Relationship to AEI registry

AEI's Subject Capability Registry remains valid for evaluation. The platform registry should eventually become the parent source for broader EUI claims, with AEI consuming the evaluation-specific subset.

Until that evolution is explicitly authorized, AEI registry behavior remains unchanged.

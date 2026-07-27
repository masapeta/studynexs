# Educational Identity

- **Status:** Accepted
- **Parent architecture:** [`../EUI.md`](../EUI.md)

---

## 1. Purpose

Educational Identity is the stable reference that lets StudyNexs connect artifacts, questions, lessons, assessments, interventions, and evidence to the same educational meaning.

Without Educational Identity, every consumer risks reconstructing board, grade, subject, chapter, objective, concept, competency, and curriculum version differently.

---

## 2. Principle

Every educational object that participates in intelligence should reference a stable Educational Identity rather than carrying loosely repeated educational labels.

Conceptual shape:

```text
EducationalIdentity
  tenant_scope
  board
  grade
  subject
  chapter
  learning_objective
  concept
  competency
  curriculum_version
  curriculum_pack_reference
```

This is an architecture contract, not a schema change in this program.

---

## 3. Applies to

| Object | Why it needs identity |
|---|---|
| Educational artifact | Connects source material to curriculum meaning. |
| Question | Defines what concept and competency it tests. |
| Lesson | Defines what it teaches. |
| Assessment | Defines curriculum scope and competency coverage. |
| Student answer | Defines what learning evidence it may represent. |
| Intervention | Defines the concept or prerequisite it targets. |
| Recommendation | Defines the educational reason behind the suggestion. |

---

## 4. Relationship to EKG and ECE

Educational Identity is not a replacement for the Educational Knowledge Graph or Educational Context Engine.

- EKG stores relationships.
- ECE resolves the current educational situation.
- Educational Identity gives artifacts and consumers a stable reference into those structures.

```text
Educational Context Engine
        |
        v
Educational Identity
        |
        v
Educational Knowledge Graph
```

---

## 5. Governance rules

1. Educational Identity is tenant-scoped where school-specific data is involved.
2. Curriculum version must be explicit where identity depends on a curriculum source.
3. Identity must not be inferred silently when context is ambiguous.
4. Conflicting identity signals must produce a Trust Report warning.
5. Consumers must not invent private identity formats.

---

## 6. Consumer obligation

Consumers should reference Educational Identity when producing consequential intelligence.

Examples:

- AEI links evaluation evidence to the identity of the assessed concept.
- AI Tutor explains concepts appropriate to the resolved identity.
- Teacher Copilot plans interventions for identity-linked gaps.
- Principal Dashboard aggregates evidence by identity rather than loose subject labels.

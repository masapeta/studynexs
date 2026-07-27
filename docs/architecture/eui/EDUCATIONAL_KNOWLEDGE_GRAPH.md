# Educational Knowledge Graph (EKG)

- **Status:** Accepted
- **Parent architecture:** [`../EUI.md`](../EUI.md)
- **Related existing reference:** [`../../KNOWLEDGE_GRAPH.md`](../../KNOWLEDGE_GRAPH.md)

---

## 1. Purpose

The Educational Knowledge Graph is the educational backbone of StudyNexs.

It represents curriculum structure, concepts, competencies, questions, answers, evidence, misconceptions, and learning outcomes as connected educational knowledge.

The existing School Knowledge Graph remains the implementation-aligned curriculum spine. EKG v1 expands the architectural scope from curriculum traversal into platform-wide educational understanding.

Educational Identity provides stable references into this graph. EKG owns relationships; Educational Identity gives artifacts and consumers a consistent anchor.

---

## 2. Core principle

Curriculum is the anchor.

StudyNexs should not reason from isolated questions or isolated answers. It should reason from:

```text
Board
  -> Grade
  -> Subject
  -> Chapter
  -> Learning Objective
  -> Concept
  -> Competency
  -> Question
  -> Answer
  -> Evidence
```

Every intelligence surface should be able to explain which curriculum concept, learning objective, or competency it is using.

---

## 3. Graph layers

| Layer | Examples | Purpose |
|---|---|---|
| Curriculum layer | Board, grade, subject, chapter, topic, concept | Defines the academic spine. |
| Competency layer | Learning objective, skill, competency, Bloom level | Describes what learning demonstrates. |
| Assessment layer | Question, rubric, answer key, evaluation criteria | Connects assessment to curriculum. |
| Evidence layer | Student answer, teacher decision, misconception, mastery evidence | Captures what happened academically. |
| Intervention layer | Recommendation, remediation, prerequisite, next concept | Enables learning action. |
| Provenance layer | Curriculum pack, source file, teacher upload, approved version | Makes knowledge auditable. |

---

## 4. Required relationships

```text
Board -> Grade
Grade -> Subject
Subject -> Chapter
Chapter -> Learning Objective
Learning Objective -> Concept
Concept -> Competency
Concept -> Prerequisite Concept
Question -> Concept
Rubric -> Question
Answer Key -> Question
Student Answer -> Question
Student Answer -> Evidence
Evidence -> Concept
Evidence -> Misconception
Teacher Decision -> Evidence
Intervention -> Concept
Intervention -> Prerequisite Concept
```

Tenant-scoped student evidence remains PII-sensitive.

---

## 5. Node categories

| Category | Node examples |
|---|---|
| Academic structure | Board, grade, subject, chapter, topic, concept |
| Competency | Learning objective, skill, Bloom level, competency |
| Assessment | Question, paper, rubric, acceptable answer, model answer |
| Work product | Student answer, worksheet, lab record, project artifact |
| Evidence | Evaluation evidence, teacher approval, override reason |
| Learning state | Mastery signal, misconception, prerequisite gap |
| Intervention | Remediation, practice item, lesson recommendation |
| Provenance | Source file, curriculum pack, version, approver |

---

## 6. Governance rules

1. Every graph node and edge must be tenant-scoped where school-specific data is involved.
2. Approved curriculum sources are the highest-trust source for academic spine edges.
3. Teacher-uploaded artifacts enter as candidates until reviewed or explicitly trusted.
4. Student-linked edges follow student data protection requirements.
5. EKG edges must preserve provenance.
6. No consumer should maintain a private concept map outside EKG.
7. EKG expansion should be incremental and evidence-driven.

---

## 7. Consumers

| Consumer | How it uses EKG |
|---|---|
| AEI | Maps answers and evidence to concepts and competencies. |
| AI Tutor | Explains concepts and prerequisites from grounded curriculum. |
| Teacher Copilot | Plans lessons and interventions based on concept gaps. |
| Question Generator | Generates or selects questions tied to concepts and Bloom level. |
| Principal Dashboard | Aggregates concept-level trends across classes and subjects. |
| Parent Assistant | Explains approved learning progress in parent-safe language. |
| School Analytics | Tracks curriculum coverage, mastery, and intervention outcomes. |

---

## 8. Production boundary

EKG v1 should define supported educational relationships clearly. Unsupported or untrusted relationships must not be presented as certified knowledge.

For v1.0 production, EKG should be complete for the supported curriculum scope. Capability expansion can broaden boards, subjects, grade levels, competency frameworks, and intervention mappings without changing the graph principle.

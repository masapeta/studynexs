# Educational Context Engine (ECE)

- **Status:** Accepted
- **Parent architecture:** [`../EUI.md`](../EUI.md)

---

## 1. Purpose

The Educational Context Engine resolves the educational situation in which an intelligence action occurs.

The same answer, question, lesson, or recommendation can mean different things depending on board, grade, subject, school policy, exam type, language medium, and student accommodations.

ECE exists so these rules are not scattered as ad hoc conditionals across services.

---

## 2. Resolved context

Conceptual contract:

```text
EducationalContext
  school
  academic_year
  board
  grade
  section
  subject
  curriculum_pack
  chapter
  learning_objective
  exam_type
  assessment_mode
  language_medium
  teacher_preferences
  institutional_policy
  student_accommodations
  evidence_scope
  educational_identity
```

This is an architecture contract, not a schema change in this program.

---

## 3. Context dimensions

| Dimension | Examples |
|---|---|
| Curriculum | Board, grade, subject, chapter, learning objective |
| Institution | School policy, grading conventions, terminology |
| Assessment | Homework, unit test, term exam, board-style paper |
| Language | English medium, Hindi, Telugu, Sanskrit, code-mixed usage |
| Student | Accommodations, learning history, approved evidence |
| Time | Academic year, term, exam cycle, curriculum version |
| Authority | Teacher draft, teacher approved, principal reviewed |

---

## 4. Resolution rules

1. Tenant context is derived from authenticated user/session state, never client-supplied school identifiers.
2. Curriculum context comes from approved CurriculumPack and EKG mappings.
3. Institution-specific behavior comes from Institutional Memory.
4. Capability availability comes from the Platform Capability Registry.
5. Low-confidence or conflicting context produces a Trust Report warning.
6. Resolved context may produce or reference an Educational Identity.
7. Consumers receive resolved context rather than reconstructing it independently.

---

## 5. Consumers

| Consumer | Context dependency |
|---|---|
| AEI | Evaluation mode, subject, rubric, supported capability, teacher review posture |
| AI Tutor | Grade-appropriate explanation and language mode |
| Question Generator | Board, grade, Bloom level, chapter, competency |
| Lesson Planner | Curriculum pace, teacher style, school terminology |
| Parent Assistant | Parent-safe approved evidence and language |
| Principal Dashboard | Aggregation scope and policy-aware interpretation |
| School Analytics | Comparable cohorts, term boundaries, exam types |

---

## 6. Anti-patterns

- `if board == ...` logic inside individual consumers.
- Subject policy hardcoded in evaluation helpers.
- Teacher style stored only in prompts.
- Grade-specific behavior invented by an LLM without resolved context.
- Parent or student surfaces consuming context that has not been approved for their role.

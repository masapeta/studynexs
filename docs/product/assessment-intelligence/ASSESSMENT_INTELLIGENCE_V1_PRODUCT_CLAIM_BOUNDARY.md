# Assessment Intelligence v1.0 Product-Claim Boundary

> Owner: Avinash Reddy Masapeta (ARM)
> Date: 2026-07-29
> Status: Certified
> Authorization: ASSESSMENT-V1-BATCH-H-AUTH-001
> Runtime behavior: Unchanged
> Scope: Product claims for Assessment Intelligence v1.0

---

## 1. Purpose

This document defines what StudyNexs may and may not claim for Assessment
Intelligence v1.0.

The core rule is:

> StudyNexs may claim production readiness only inside the certified supported
> scope. Everything else must be described as assist, manual review,
> unsupported, or future expansion.

This boundary protects trust. It prevents a school from hearing "universal AI
assessment" when the certified product truth is narrower and safer.

---

## 2. Authority model

Assessment Intelligence v1.0 uses this authority model:

```text
Assessment Intelligence
    -> creates / organizes assessment artifacts

AEI
    -> assists with answer evaluation where supported

Teacher
    -> approves all consequential academic outcomes

Approved Evidence
    -> source for downstream student / parent / principal / mastery views
```

No Assessment Intelligence claim may bypass this authority model.

---

## 3. Claim modes

| Mode | Meaning | Product wording posture |
|---|---|---|
| `supported` | Certified for declared scope. | Product may claim support inside the declared scope. |
| `assist` | System can help, but teacher review remains required. | Product should say "assist" or "teacher-reviewed assist". |
| `checklist` | System can provide checklist-style evidence only. | Product should say "checklist assist"; no marks claim. |
| `manual_review` | Teacher-only authority. | Product should say "requires teacher review". |
| `unsupported` | Not certified or not safe. | Product must not claim support. |
| `expansion` | Future roadmap candidate. | Product may describe as planned/future only if approved by ARM. |

---

## 4. Certified supported v1.0 claims

Inside the declared supported scope, StudyNexs may claim:

1. **Grounded draft question-paper generation**
   - AI can draft question papers from approved curriculum sources where the
     supported scope and grounding requirements are satisfied.
   - Generated papers are drafts until teacher/incharge approval.

2. **Teacher review and approval workflow**
   - Teachers/incharges can review, edit, approve, reject, duplicate, and reuse
     assessment artifacts according to existing product workflow.
   - Approval remains the authority step.

3. **Approved school-private question-bank reuse**
   - Approved questions can become reusable school-private assets.
   - Reuse produces reviewable drafts and must not silently bypass teacher
     authority.

4. **Explicit blueprint readiness where declared**
   - Blueprint posture is explicit for declared supported scenarios.
   - The product must not imply universal blueprint coverage.

5. **Rubric and model-answer readiness where declared**
   - Teacher-visible answer keys, model answers, criteria, and manual-review
     posture are certified where declared.
   - Rubric metadata strengthens teacher review and AEI context; it does not
     create a parallel grading engine.

6. **Paper-to-evaluation linkage through approved papers and AEI**
   - Approved papers may feed exam question schemas.
   - Academic answer evaluation remains AEI-aligned.
   - Teacher approval remains required before outcomes become authoritative.

7. **Browser-proven teacher assessment workflow**
   - The supported teacher workflow has browser proof against the Reference
     tenant fixture.
   - The proof includes tenant/API/console guards and no-overclaim checks.

8. **Approved-evidence-only downstream posture**
   - Parent, student, principal, mastery, and learning-intelligence consumers
     should rely only on teacher-approved evidence for consequential outputs.

---

## 5. Assist/manual-review claims

The following may be described only with cautious assist or manual-review
language:

- bilingual or multilingual assessment workflows not explicitly certified as
  supported;
- Indian-language paper or answer contexts outside certified scope;
- OCR-assisted student answer capture;
- handwritten answer transcription;
- visual, diagram, graph, map, or science checklist evidence;
- subjective long-answer interpretation;
- rubric interpretation that depends on teacher judgment;
- low-confidence or ambiguous evidence.

Permitted wording examples:

- "AI-assisted, teacher-reviewed."
- "Requires teacher confirmation."
- "Checklist evidence only."
- "Manual review required."

Disallowed wording examples:

- "Automatically grades handwritten answers."
- "Fully supports all languages."
- "Autonomously evaluates diagrams."

---

## 6. Disallowed v1.0 claims

StudyNexs must not claim Assessment Intelligence v1.0 supports:

- universal board support;
- universal grade support;
- universal subject support;
- universal blueprint support;
- universal bilingual assessment generation;
- universal multilingual assessment generation;
- automatic question-paper translation as production-ready;
- automatic rubric translation as production-ready;
- automatic model-answer translation as production-ready;
- autonomous paper approval;
- autonomous answer grading;
- autonomous OCR-based marks;
- autonomous handwriting-based marks;
- autonomous diagram grading;
- autonomous visual/science grading;
- public parent/student evidence before teacher approval;
- downstream mastery updates from unapproved AI suggestions;
- bypassing AEI for academic answer evaluation;
- EUI source-of-truth adoption for Assessment Intelligence without separate
  authorization.

---

## 7. Supported-scope statement

The certified v1.0 posture is conservative:

- The supported scope is declared by the Assessment Intelligence v1.0 Supported
  Scope Capability Matrix and related Batch A-F declarations.
- The browser proof uses a Reference tenant Grade 6 Science Unit Test fixture.
- Certified support should be described as production-ready for declared
  scenarios only.
- Additional boards, grades, subjects, languages, OCR quality levels, visual
  cases, and science capabilities require later certification.

---

## 8. Public wording guidance

Safe public wording:

```text
StudyNexs helps schools create, review, approve, reuse, and link assessments
inside certified supported scopes, while teachers remain the final academic
authority.
```

Unsafe public wording:

```text
StudyNexs automatically creates and grades all assessments for every board,
subject, language, and answer-sheet format.
```

Preferred positioning:

```text
Production-ready for the supported scope. Continuously expanding through
certified capability releases.
```

---

## 9. Governance rule

Any future product claim expansion requires:

1. capability declaration update;
2. Golden Harness or equivalent evidence;
3. runtime proof where user-visible;
4. certification report;
5. ARM acceptance;
6. publication.

No sales, product, UI, or documentation surface should claim unsupported
capability merely because the architecture could support it in the future.


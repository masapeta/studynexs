# Batch 02 Completion Report â€” Academic Onboarding

**Date:** 2026-07-23
**Release:** Release 0.2
**Batch:** Batch 2 â€” Academic Onboarding
**Status:** Accepted / Frozen
**Commit SHA:** `469c0f849996f5c2e8bbe00158a08f4a6b3e0a9a` â€” `feat(onboarding): complete Batch 2 academic onboarding proof`
**Scope boundary:** Curriculum-first onboarding from uploaded curriculum source to approved `CurriculumPack`, KG/RAG readiness, and deterministic proof that downstream AI capabilities consume the same approved pack. This batch does not start Batch 3, does not create a second curriculum engine, and does not implement full textbook warehousing.

---

## Executive Summary

Batch 2 proves the core StudyNexs operating-system property:

> A school can teach StudyNexs its curriculum once, approve it through human review, and then use that same approved academic memory across teaching, assessment, evaluation, mastery, student remediation, and parent communication.

The final runtime proof starts with a newly uploaded curriculum PDF and ends with Student Tutor and Parent Copilot outputs grounded to the same approved `CurriculumPack`.

Final runtime result:

```text
BATCH 2 ACADEMIC ONBOARDING RUNTIME PROOF: PASS
```

Final proof pack:

```text
1bdfffc6-933d-4780-9de4-b7d6c92201bb
```

---

## Scope Completed

### Academic Onboarding

- Curriculum source upload is supported through the existing file upload surface.
- Uploaded curriculum sources can be passed to Academic Onboarding proposal.
- AI extraction creates a draft `CurriculumPack` from the uploaded source.
- Teacher/HOD review remains human-in-the-loop.
- Approval still uses the existing `CurriculumPack` approval workflow.
- Academic Intelligence readiness requires approved pack + KG success + RAG success + retrievable vector/topic evidence.

### Downstream Grounding

The approved pack was verified as the grounding source for:

- Lesson Plan
- Learning Materials
- Question Paper
- Assessment Evaluation chain
- Student Study Context
- Tutor Recommendation
- Tutor Lesson
- Student Copilot
- Parent Briefing
- Parent Ask

### Assessment Loop

The runtime proof covered:

- approved question paper;
- exam creation from approved question paper;
- generated answer-sheet PNG upload;
- answer-sheet vision/OCR LLM call;
- AI evaluation suggestions;
- teacher HITL approval;
- marks / gradebook persistence;
- mastery recompute;
- tutor and parent remediation reflection.

---

## Architecture Reused

Batch 2 reused the existing StudyNexs architecture:

| Existing architecture | Batch 2 usage |
|---|---|
| `CurriculumPack` | Single authoritative academic memory object |
| File upload service | Curriculum source PDF upload and answer-sheet image upload |
| Curriculum extraction service | Draft pack proposal from uploaded source |
| Pack approval workflow | Human approval before authority |
| Knowledge Graph | Pack spine and concept identity |
| RAG / vector index | Retrieval grounding for downstream AI |
| Lesson plan generation | Pack-grounded Teacher Copilot path |
| AI question paper generation | Pack-grounded Assessment Intelligence path |
| Concept Cards | Tutor lesson grounding |
| Answer-sheet evaluation service | AI Evaluation + teacher approval |
| Mastery engine | Post-assessment learner state |
| Student Copilot / Tutor | Personalized student remediation |
| Parent Copilot | Parent-facing learning summary and home tips |

No duplicate curriculum engine, parallel ingestion service, direct provider bypass, or alternate AI stack was introduced.

**Architecture confirmation:** Batch 2 introduced no new architectural patterns and remained fully compliant with the frozen platform architecture.

---

## Runtime Proof Summary

Command:

```powershell
cd apps/api
$env:PYTHONUNBUFFERED='1'
python -u scripts\smoke_batch2_academic_onboarding_runtime_proof.py
```

Environment:

- API: `http://127.0.0.1:8000`
- Tenant: `reference`
- `/ready`: `{"status":"ready","checks":{"database":"ok","redis":"ok"}}`
- Alembic: `a1b2c3d4e5f7 (head)`
- LLM provider: OpenAI via configured gateway

Final runtime artifacts:

| Artifact | ID |
|---|---|
| Curriculum source file | `42ebd493-756e-42db-a885-a350a55e9f58` |
| Approved CurriculumPack | `1bdfffc6-933d-4780-9de4-b7d6c92201bb` |
| Question paper | `b2c8e0bb-0a19-408d-9de1-f51640c29ad1` |
| Exam | `71c0fb96-ecc9-4e77-bb78-ca44ce059bb1` |
| Answer-sheet file | `a1c6a024-a148-41ca-bb1c-f3e03d566cad` |
| Evaluation | `17168b3b-9f1e-4291-b18a-03a2504ed752` |

Critical runtime observations:

- Uploaded curriculum source produced a draft pack with `extraction_source=uploaded_document`.
- Academic Intelligence became ready with `kg=True`, `rag=True`, `vectors=2`, `topics=2`.
- Lesson plan was `grounded=True` with 2 grounding sources and 3 learning materials.
- Question paper was `grounded=True` with 15/15 cited questions and 2 grounding sources.
- Answer-sheet evaluation invoked `answer_sheet_vision` with `image_count=1` using `gpt-4o-mini`.
- Evaluation produced 15 AI suggestions.
- Teacher HITL approval saved AI-graded marks.
- Mastery updated for `Quadratic Equations`.
- Student Tutor used `source=concept_card` and `trigger=concept_card`.
- Parent Copilot returned grounded briefing and home remediation tips.

---

## Architecture Metrics

These metrics come from the final runtime proof and evidence ledger.

| Metric | Count | Evidence |
|---|---:|---|
| Curriculum sources uploaded | 1 | `42ebd493-756e-42db-a885-a350a55e9f58` |
| CurriculumPacks created / approved | 1 | `1bdfffc6-933d-4780-9de4-b7d6c92201bb` |
| Topics extracted / retrievable | 2 | Academic Intelligence status |
| Vectors indexed | 2 | Academic Intelligence status |
| Knowledge Graph generated | Yes | `kg=True` |
| RAG indexed | Yes | `rag=True` |
| Lesson plans generated | 1 | `a1dfda31-f25b-490f-96eb-398632c50a66` |
| Learning material groups generated | 3 | Lesson plan materials output |
| Question papers generated | 1 | `b2c8e0bb-0a19-408d-9de1-f51640c29ad1` |
| Question paper questions generated | 15 | Runtime proof |
| Cited question paper questions | 15 | Runtime proof |
| Exams created | 1 | `71c0fb96-ecc9-4e77-bb78-ca44ce059bb1` |
| Answer-sheet uploads | 1 | `a1c6a024-a148-41ca-bb1c-f3e03d566cad` |
| Assessment evaluations | 1 | `17168b3b-9f1e-4291-b18a-03a2504ed752` |
| AI evaluation suggestions | 15 | Runtime proof |
| Student Copilot requests | 1 | Evidence ledger |
| Parent Copilot surfaces verified | 2 | Briefing + ask |

The runtime proof did not emit explicit KG node/edge counts. Add those to the evidence ledger in a future observability pass if needed.

---

## Evidence Ledger

The runtime proof now emits and validates a deterministic same-pack evidence ledger.

Every row must prove:

- tenant = `reference`;
- pack ID = the same approved `CurriculumPack`;
- vector count > 0;
- grounded = `True`;
- citation/source evidence exists.

Final ledger:

| Capability | Tenant | Pack | Vectors | Grounded | Source / citation evidence |
|---|---|---|---:|---:|---|
| Academic Intelligence | `reference` | `1bdfffc6-933d-4780-9de4-b7d6c92201bb` | 2 | True | KG ready + RAG ready + 2 retrievable topics |
| Lesson Plan | `reference` | `1bdfffc6-933d-4780-9de4-b7d6c92201bb` | 2 | True | 2 grounding source refs |
| Learning Materials | `reference` | `1bdfffc6-933d-4780-9de4-b7d6c92201bb` | 2 | True | 3 material outputs |
| Question Paper | `reference` | `1bdfffc6-933d-4780-9de4-b7d6c92201bb` | 2 | True | 15/15 questions cited + 2 grounding sources |
| Assessment Evaluation | `reference` | `1bdfffc6-933d-4780-9de4-b7d6c92201bb` | 2 | True | linked approved QP + exam + answer-sheet file + evaluation |
| Student Study Context | `reference` | `1bdfffc6-933d-4780-9de4-b7d6c92201bb` | 2 | True | 3 same-pack weak concepts |
| Tutor Recommendation | `reference` | `1bdfffc6-933d-4780-9de4-b7d6c92201bb` | 2 | True | `source=concept_card`, `lesson_key=factorisation` |
| Tutor Lesson | `reference` | `1bdfffc6-933d-4780-9de4-b7d6c92201bb` | 2 | True | `trigger=concept_card` |
| Student Copilot | `reference` | `1bdfffc6-933d-4780-9de4-b7d6c92201bb` | 2 | True | 2 source contexts |
| Parent Briefing | `reference` | `1bdfffc6-933d-4780-9de4-b7d6c92201bb` | 2 | True | 2 source contexts |
| Parent Ask | `reference` | `1bdfffc6-933d-4780-9de4-b7d6c92201bb` | 2 | True | 2 source contexts + 3 home tips |

This converts â€œgroundingâ€ from an architectural claim into a repeatable runtime assertion.

---

## Tests Executed

| Validation | Result |
|---|---:|
| API readiness | PASS â€” DB + Redis healthy |
| Alembic current/head | PASS â€” `a1b2c3d4e5f7 (head)` |
| API import | PASS â€” `python -c "import app.main; print('api import ok')"` |
| Academic Onboarding regression | PASS â€” `15 passed` |
| Tutor / Student Copilot / Parent Copilot / Content Review focused regression | PASS â€” `17 passed` |
| Runtime proof script lint | PASS â€” `ruff check scripts\smoke_batch2_academic_onboarding_runtime_proof.py` |
| Runtime proof script compile | PASS â€” `python -m py_compile scripts\smoke_batch2_academic_onboarding_runtime_proof.py` |
| Admin web production build | PASS â€” `npm run build` |
| Full runtime proof | PASS â€” deterministic evidence ledger passed |

Previously validated in the same Batch 2 implementation window:

- onboarding upload support;
- same-pack downstream provenance;
- concept-card-backed Tutor path;
- Parent Copilot pack provenance;
- student endpoint regression;
- duplicate concept slug regression.

---

## Defects Fixed During Batch

| Defect | Impact | Fix |
|---|---|---|
| Tutor content-review gap queue 500ed when multiple packs shared a concept slug | Real runtime path could crash after repeated onboarding packs created identical concept slugs | Made slug lookup deterministic and added regression coverage |
| Student Copilot endpoint referenced `current_user.user_id`, which does not exist | Student ask path returned 500 during the full runtime proof | Switched to `current_user.id` and added endpoint-level regression |
| Downstream tutor/parent responses did not expose enough provenance for deterministic same-pack proof | Could not prove all surfaces consumed the same approved pack | Added additive provenance fields and same-pack runtime assertions |
| Runtime proof could pass on broad â€œgroundedâ€ signals without comparing downstream pack IDs | Risk of false-positive grounding proof | Added deterministic evidence ledger across all downstream capabilities |

---

## Known Operational Limitations

1. **Asynchronous evaluation worker path requires separate operational hardening.**
   The local runtime proof queues evaluation, waits, and then executes the existing evaluation service inline if the queued worker does not complete within the script timeout. Product behavior is validated; production-like async worker execution should be validated as a separate operational task.

2. **Runtime proof consumes real AI credits.**
   The proof uses real extraction, RAG-grounded generation, question-paper generation, and answer-sheet vision.

3. **Repeated proof runs add demo artifacts to the Reference tenant.**
   The current proof intentionally creates real packs, papers, exams, evaluations, marks, and mastery history. A later housekeeping task should add cleanup or move the proof to a disposable tenant.

4. **Full repo lint remains outside this batch.**
   Batch 2 scoped lint/build/tests pass. Existing unrelated repo-wide lint debt should remain a separate engineering batch.

5. **Future provenance fields are not required for Batch 2.**
   The current ledger verifies tenant, pack, vector count, grounding, and citation/source evidence. Future curriculum revision work should add optional metadata such as KG version, embedding version, curriculum version, retrieval timestamp, and source document hash.

---

## Definition of Done Checklist

| Definition of Done item | Status |
|---|---:|
| Uses existing `CurriculumPack` architecture | Complete |
| Uses existing Document Intelligence / file upload path | Complete |
| Does not create a second curriculum engine | Complete |
| Teacher/HOD review remains HITL | Complete |
| Approval uses existing pack approval workflow | Complete |
| KG ready after approval | Complete |
| RAG ready after approval | Complete |
| Academic Intelligence Ready reached | Complete |
| Lesson plan grounded to same approved pack | Complete |
| Learning materials grounded to same approved pack | Complete |
| Question paper grounded to same approved pack | Complete |
| Assessment/evaluation chain linked to same approved pack via approved QP/exam | Complete |
| Answer-sheet upload + vision path exercised | Complete |
| Teacher evaluation approval saves marks | Complete |
| Mastery updates after approved marks | Complete |
| Tutor recommendation/lesson avoids fallback and uses Concept Card | Complete |
| Student Copilot grounded to same approved pack | Complete |
| Parent Copilot grounded to same approved pack | Complete |
| Deterministic evidence ledger passes | Complete |
| Build/lint/focused tests pass | Complete |
| Batch 3 not started | Complete |
| Governance freeze updates deferred until ARM acceptance | Complete |

---

## Release 0.2 Acceptance Criteria

| Acceptance criterion | Status |
|---|---:|
| Curriculum onboarding completed | âœ“ |
| Human approval workflow completed | âœ“ |
| Knowledge Graph generated | âœ“ |
| RAG indexed | âœ“ |
| Academic Intelligence Ready | âœ“ |
| Same-pack grounding verified | âœ“ |
| Assessment loop verified | âœ“ |
| Answer-sheet upload / vision path verified | âœ“ |
| Runtime proof PASS | âœ“ |
| Evidence ledger PASS | âœ“ |
| Focused regression PASS | âœ“ |
| Web production build PASS | âœ“ |
| Batch 3 not started | âœ“ |

---

## Release Timeline

| Release | Batch | Status | Product milestone |
|---|---|---:|---|
| Release 0.1 | Batch 1 â€” Curriculum Intelligence | Accepted / Frozen | Curriculum foundation and approved academic memory |
| Release 0.2 | Batch 2 â€” Academic Onboarding | Accepted / Frozen | Uploaded curriculum source â†’ shared academic memory â†’ runtime proof |
| Release 0.3 | Batch 3 â€” TBD | Pending authorization | Not started |

---

## Acceptance Decision

**Decision:** Accepted / Frozen.

Batch 2 is functionally complete because the platform now proves the required Release 0.2 property:

> A newly uploaded curriculum source becomes a human-approved `CurriculumPack`, and that same approved pack grounds downstream teaching, assessment, evaluation, mastery, student, and parent intelligence without fallback.

Do not begin Batch 3 until:

1. ARM explicitly authorizes the next execution batch.
2. The next batch scope is recorded in the Product Execution Plan.
3. The current Release 0.2 freeze remains intact except for production defects, security fixes, or critical regressions.

---

## Recommended Next Execution Batch

Do not start yet.

After Release 0.2 is frozen, the recommended next batch should be authorized explicitly by ARM. Based on current product direction, likely candidates are:

1. **Operational hardening:** production async evaluation worker parity, cleanup strategy for runtime proof artifacts, observability around worker execution.
2. **Assessment Intelligence deepening:** richer evaluation review UX, rubric visibility, teacher override ergonomics.
3. **Pilot readiness:** controlled Reference School demo polish and production deployment gates.

Batch 3 remains unauthorized until ARM explicitly chooses the next execution batch.

# Batch 01 Completion Report — Curriculum Intelligence

**Date:** 2026-07-23
**Batch:** Batch 1 — Curriculum Intelligence
**Status:** Complete for ARM review
**Scope boundary:** Curriculum memory, approval governance, KG/RAG grounding, and proof that multiple AI surfaces can use the same approved `CurriculumPack`. Batch 2 assessment automation and textbook-PDF-to-`CurriculumPack` generation are not included.

---

## Objectives

Batch 1 creates the institutional curriculum memory of a school:

1. Teachers can create structured curriculum drafts for their assigned class and subject.
2. Class incharges / administrators approve curriculum packs before they become authoritative.
3. Approved packs build KG + RAG grounding under tenant isolation.
4. Teacher-facing AI capabilities can cite the same approved pack consistently.
5. Student and parent copilots can reflect the same learning outcome chain without falling back to generic demo content.

---

## Acceptance Criteria Mapping

| Acceptance criterion | Status | Evidence |
|---|---:|---|
| A teacher uploads curriculum once through the admin UI | Complete | `/dashboard/teaching/curriculum/onboarding` supports syllabus/TOC/chapter-list text input. Live rehearsal used `teacher1` to propose a fresh pack from NCERT Class 8 Science TOC. |
| Pack reaches approved state with audit trail | Complete | Live rehearsal pack `1bc53500-e9dd-4db6-98f7-5f77eb697652` was approved by `principal`; learning-loop smoke found pack audit trail with 13 events. |
| RAG index reflects approved content and is tenant-scoped | Complete | Intelligence status reported `phase=ready`, `kg=True`, `rag=True`, `vectors=13`, `topics=13`; browser E2E proved `X-Tenant-Slug=reference` on all tracked API calls. |
| At least two AI capabilities cite the same `CurriculumPack` consistently | Complete | Live rehearsal generated both a grounded lesson plan and grounded question paper from pack `1bc53500-e9dd-4db6-98f7-5f77eb697652`; both cited the same source ref `3498917a-0e59-47b8-a274-7cc0d66ccfb7`. |
| Capability acceptance document completed | Complete | This report is the Batch 1 fixed acceptance artifact. |

---

## Implemented Work

### Backend

- Added curriculum draft-edit vs approval authorization:
  - admins can draft and approve;
  - mapped subject teachers can draft only for their assigned class × subject;
  - class incharges can draft for their class and approve other authors' packs;
  - self-approval is blocked for non-admin incharges.
- Applied resource-derived authorization to pack, chapter, topic, learning-outcome, onboarding, retry-indexing, and supporting-material ingest routes.
- Exposed role-aware permission fields through `/api/v1/users/me/permissions`:
  - `teaching_assignments`
  - `can_edit_curriculum_draft`
  - `can_approve_curriculum`
- Hardened enum value handling for concept cards, content review, and document ingestion.
- Hardened hybrid RAG retrieval against non-UUID references.
- Hardened document-ingest status counting when vector-store count is temporarily unavailable.
- Connected tutor recommendations to approved concept cards, preferring exam-derived misconceptions before generic weak-topic/template fallback.
- Updated Parent Copilot to surface recent exam-derived misconceptions as the first focus source.
- Updated Reference School seed to close the quadratic learning loop:
  - approved concept card;
  - approved answer-sheet evaluation;
  - finalized marks;
  - mastery recompute;
  - parent/tutor alignment on Quadratic Equations.

### Frontend

- Curriculum onboarding is now role-aware:
  - subject teachers see only assigned class × subject options;
  - class incharges see their classes;
  - admins see all classes.
- Review panel supports read/edit gating through `editable`.
- Approval CTA is shown only when the current user can approve the specific pack.
- Existing curriculum, lesson-plan, and AI-paper CTAs respect draft-edit permissions.
- Browser validation harnesses now:
  - enforce reference tenant headers;
  - fail on unexpected API responses;
  - create a fresh onboarding draft for review-loop validation;
  - make screenshots best-effort so screenshot capture does not mask product assertions.

### Evidence / Smoke Scripts

- `smoke_stage2a_live_rehearsal.py` now supports separate drafter and approver personas.
- `smoke_document_ingest_live.py` verifies supporting-material ingestion and self-cleans file, ingestion row, and vectors.
- `smoke_learning_loop_e2e.py` verifies the reference academic loop across curriculum, KG/RAG, QP, exam/evaluation/marks, mastery, tutor, and parent briefing.

---

## Runtime Verification

| Check | Result |
|---|---:|
| API readiness | PASS — `{"status":"ready","checks":{"database":"ok","redis":"ok"}}` |
| Alembic current/head | PASS — `a1b2c3d4e5f7 (head)` |
| Reference School seed | PASS — direct `seed_reference_school_demo_v1.py` rerun exited 0 after script path guard fix |
| Live curriculum intelligence rehearsal | PASS — teacher draft → principal approve → KG/RAG ready → grounded lesson plan + QP |
| Supporting-material document ingest | PASS — uploaded PDF indexed 1 chunk, then self-cleaned file/ingestion/vector artifacts |
| Learning loop smoke | PASS — loop closed for pilot; 20 WORKS, 2 PARTIAL, 0 FAIL |
| Browser onboarding review E2E | PASS — login, tenant reference, exactly one pack-detail GET, 0 disallowed console errors |
| Browser smoke E2E | PASS — 20 checks, 0 disallowed console errors |

---

## Test Results

| Validation | Result |
|---|---:|
| API import | PASS — `python -c "import app.main"` |
| Focused API pytest | PASS — 39 passed in 382.25s |
| Web production build + TypeScript | PASS — `npm run build` |
| Node syntax checks for E2E harnesses | PASS |
| Scoped fatal Python lint | PASS — `ruff --select F401,F821,F811,E9` on Batch 1 slice |
| Full repo Ruff | Not green before this batch — existing broad lint debt remains outside Batch 1 scope |
| Full repo ESLint | Not green before this batch — existing repo-wide lint debt remains outside Batch 1 scope |

---

## Integration Evidence

### Curriculum → KG/RAG → Teacher AI

- Drafter: `teacher1`
- Approver: `principal`
- Pack: `1bc53500-e9dd-4db6-98f7-5f77eb697652`
- Intelligence readiness:
  - `phase=ready`
  - `kg=True`
  - `rag=True`
  - `vectors=13`
  - `topics=13`
- Lesson plan:
  - `6f129bbc-f7fb-45f7-90a7-3028d67cf2e2`
  - `grounded=True`
  - 6/6 segments cited
- Question paper:
  - `03f9c812-c833-4c3c-aac5-1a797359f575`
  - `grounded=True`
  - 15/15 questions cited
- Shared citation source:
  - chapter `Crop Production and Management`
  - topic `Agricultural practices and crop seasons`
  - ref `3498917a-0e59-47b8-a274-7cc0d66ccfb7`

### Reference learner loop

- Curriculum available: 10 packs
- KG/RAG source count: 13
- Approved QP exists: yes
- Unit Test — Quadratic Equations exists: yes
- Answer-sheet evaluation exists and is teacher-finalized: yes
- Marks saved for topic-aligned exam: yes
- Mastery updated for `student_demo`: yes
- Student tutor recommendation:
  - `demo_fallback=False`
  - `trigger=concept_card`
  - `lesson_key=quadratic-formula`
- Parent copilot reflects the same topic chain: yes
- Topic alignment gate: `marks=yes, mastery=yes, tutor=yes, parent=yes`

---

## Known Limitations

1. **Textbook PDF → `CurriculumPack` generation is not implemented in Batch 1.** Current onboarding accepts syllabus/TOC/chapter-list text. Document Intelligence supports supporting-material ingestion into an existing approved pack.
2. **Answer-sheet OCR/evaluation full live path is not Batch 1 acceptance.** The learning-loop smoke verifies the seeded/pilot loop, including approved evaluation and mastery propagation, but Batch 2 owns full assessment automation.
3. **Report-card generation remains partial in the learning-loop smoke.** The loop reports `0 cards`; this is not a Batch 1 blocker.
4. **Full repo lint is still not clean.** Existing Ruff/ESLint debt predates this batch. The Batch 1 slice passes fatal/unused-import Python lint and production web build.
5. **Browser suites should be run serially in this dev environment.** Parallel Playwright runs triggered `ERR_INSUFFICIENT_RESOURCES`; serial reruns passed.
6. **Live AI rehearsal requires configured LLM credentials and a running vector store.** Without provider keys, the live rehearsal should fail fast instead of silently using the stub.

---

## Remaining Technical Debt

- Consolidate repo-wide Ruff and ESLint debt as a separate engineering batch.
- Reduce SQL echo/noisy seed output in local validation.
- Add cleanup strategy for repeated live rehearsal packs in the permanent Reference tenant.
- Add a stricter first-class completion artifact update flow for `STATUS.md` and `DECISION_LOG.md` after ARM accepts this Batch 1 report.
- Extend browser coverage for teacher-owned curriculum creation as a full click path, not only API-backed E2E setup.

---

## Deferred Backlog

- Textbook PDF upload → curriculum extraction → reviewed `CurriculumPack` generation.
- Full teacher assessment loop:
  - exam creation from approved paper;
  - student attempt;
  - answer-sheet upload;
  - OCR;
  - AI evaluation;
  - teacher approval;
  - marks/gradebook/mastery/report-card propagation.
- Public/prospect full synthetic learner loop after Batch 1 acceptance.
- Parent/student remediation activity sequencing beyond the current tutor recommendation.

---

## Release Recommendation

**Ready for Batch 1 acceptance review.**

Batch 1 now delivers the curriculum memory foundation: teacher-authored drafts, human approval, tenant-scoped KG/RAG indexing, and consistent grounding across teacher AI, tutor, and parent evidence paths.

Do not begin Batch 2 until ARM accepts this report and explicitly authorizes the next Product Execution Plan phase.

---

## Recommended Next Execution Batch

After ARM acceptance, the recommended next batch is:

**Batch 1A / Next Curriculum-First Onboarding Slice — textbook/document-to-curriculum evolution.**

Recommended objectives:

1. Define the exact product boundary for textbook PDF handling.
2. Reuse Document Intelligence and CurriculumExtractionService; do not create a parallel ingestion stack.
3. Add reviewed extraction from uploaded textbook/TOC PDF into draft `CurriculumPack`.
4. Preserve teacher draft ownership and class-incharge/admin approval.
5. Prove the same full grounding chain with uploaded source evidence.

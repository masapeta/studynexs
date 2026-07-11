# Assessment Intelligence (Pillar 2)

> **Engineering companion** to [`/CLAUDE.md`](../CLAUDE.md) §40–§40.6 (canonical). Records current
> implementation + code + roadmap. *The academic workhorse — generation AND evaluation, always
> human-approved.* Product copy/code use **"Assessment Intelligence" / "AI-Assisted Evaluation"** —
> never "AI correcting papers."

## Scope

Question-paper generation, answer-key & rubric generation, online/offline assessments, **AI-assisted
evaluation**, a human-review workflow, marks publishing, result analytics, and learning-gap analysis.

## Generation (built)

- **Module:** `apps/api/app/modules/examinations/` + `apps/api/app/modules/ai/services/` (`question_paper_service.py`, `question_bank_service.py`, `assessment_grounding.py`, `paper_pdf.py`).
- **Grounding:** `assessment_grounding.ground_for_pack` retrieves cited CurriculumPack context via the shared `RagService` (tenant + pack scoped). Grounded generation refuses when the pack has no curriculum (§109).
- **Unit of academic memory = the question item** (`QuestionBankItem` + `RubricBankItem`), not the PDF (`DECISION_LOG` 2026-06-18).
- Approved → trusted bank (auto-compose, `qp_from_bank`); rejected → audit + manual reuse. Only approved items auto-index.
- **HITL:** teacher/HOD approval before a paper is usable; authors can't approve their own artifacts.

## Evaluation (partial → rubric engine shipped)

- **Module:** `apps/api/app/modules/examinations/services/answer_sheet_eval_service.py` (orchestration) + `apps/api/app/modules/ai/services/evaluation_engine.py` (shared marking engine) + vision OCR (`answer_sheet_vision.py`) + Arq job `answer_sheet_eval_job`.
- **Workflow maturity order (§40.2):** objective (deterministic key-match) ✅ → subjective (rubric-scored LLM) ✅ → rubric-per-criterion ✅ → step-by-step maths ⬜ → OCR/digital sheets ✅ (vision) → online exams ⬜ → (future) diagram/handwriting.
- **What the AI does (§40.3):** suggest marks, explain reasoning per criterion, flag missing concepts, identify partial answers, suggest feedback, total automatically — schema-validated, metered. It **never** finalizes/publishes.
- **Objective grading:** deterministic key-match (`grade_objective`) — never an LLM (`DECISION_LOG` §3.6).
- **Subjective grading:** batch LLM call via `evaluate_subjective` decomposes model answers into weighted criteria; suggested mark = sum of awarded points (clamped). Provider failure → per-question `heuristic_fallback` (token overlap). Suggestions carry `method` provenance: `objective` | `llm_rubric` | `heuristic_fallback`.
- **Metering:** one school credit per evaluation; additional LLM calls within the same eval recorded cost-only (`_record_eval_credits`).
- **Gaps:** ~~evaluation not yet pack-grounded at mark time~~ ✅ `ground_for_evaluation` (best-effort); eval UI surfaces rubric criteria, missing concepts, confidence, method.

## Assessment Intelligence engines (shared, §40.4)

| Engine | Module | State |
|---|---|---|
| Marking engine (rubric-per-criterion) | `evaluation_engine.py` | ✅ shipped (Batch 13) |
| QP generation | `question_paper_service.py` + `assessment_grounding.py` | ✅ grounded + cited |
| Rubric engine (standalone generation) | — | ⬜ planned |
| Feedback generator | partial (in-engine feedback string) | 🔧 |
| Learning-gap detection | partial (`missing_concepts` in suggestions) | 🔧 |
| Bloom / skill / curriculum alignment | on QP metadata | ✅ generation; ⬜ eval |

All LLM paths go through the shared gateway; deterministic where possible.

## Human-in-the-loop for evaluation (non-negotiable — §40.5)

- AI assists; teachers decide. **AI must never publish marks automatically.** Teacher review before
  finalization (unless an institution *explicitly* configures otherwise — audited, never default).
- Teachers can accept / modify / override / add feedback / re-evaluate. Every override logged via
  `teacher_overrides` + `list_corrections_history`.
- **Preserve the full record:** original answer · AI evaluation · teacher modifications · final marks ·
  evaluation history. Complete audit trail (who/what/when/from-which-AI-baseline).

## Roadmap (order)

1. ~~Ground QP generation in RAG~~ ✅ Batch 12.
2. ~~Rubric-per-criterion scoring + LLM subjective eval~~ ✅ Batch 13.
3. ~~Pack-grounded evaluation marking (`ground_for_evaluation`).~~ ✅ Batch 14.
4. ~~Eval UI: show criteria breakdown, missing concepts, citations.~~ ✅ Batch 14 (method + confidence + criteria + missing concepts).
5. Shared engines (standalone rubric generation, learning-gap analytics).
6. Future (§40.6): handwriting, diagram, math-expression, programming, spoken, video — each grounded + metered + HITL.

| Capability | State |
|---|---|
| QP generation + question bank + HITL approval | ✅ grounded when `pack_id` supplied |
| Answer-sheet eval (vision OCR, Arq) + teacher approval | ✅ |
| Objective key-match grading | ✅ deterministic |
| Subjective grading via LLM + rubric-per-criterion | ✅ (`llm_rubric`; heuristic fallback) |
| Pack-grounded evaluation marking | ✅ (`ground_for_evaluation`) |
| Eval UI rubric breakdown | ✅ |
| Bloom mapping at eval time | ⬜ |

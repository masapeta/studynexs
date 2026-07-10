# Assessment Intelligence (Pillar 2)

> **Engineering companion** to [`/CLAUDE.md`](../CLAUDE.md) §40–§40.6 (canonical). Records current
> implementation + code + roadmap. *The academic workhorse — generation AND evaluation, always
> human-approved.* Product copy/code use **"Assessment Intelligence" / "AI-Assisted Evaluation"** —
> never "AI correcting papers."

## Scope

Question-paper generation, answer-key & rubric generation, online/offline assessments, **AI-assisted
evaluation**, a human-review workflow, marks publishing, result analytics, and learning-gap analysis.

## Generation (built)

- **Module:** `apps/api/app/modules/examinations/` + `apps/api/app/modules/ai/services/` (`question_paper_service.py`, `question_bank_service.py`, `paper_pdf.py`).
- **Unit of academic memory = the question item** (`QuestionBankItem` + `RubricBankItem`), not the PDF (`DECISION_LOG` 2026-06-18).
- Approved → trusted bank (auto-compose, `qp_from_bank`); rejected → audit + manual reuse. Only approved items auto-index.
- **HITL:** teacher/HOD approval before a paper is usable; authors can't approve their own artifacts.
- **Gap:** generation is **not yet grounded in CurriculumPacks/RAG** — the immediate next batch wires `RagService` in so QP output is grounded + cited (`CLAUDE.md` §39, §109).

## Evaluation (partial)

- **Module:** `apps/api/app/modules/examinations/` (answer-sheet eval, vision OCR, Arq job `answer_sheet_eval_job`) + `report_card_service.py`.
- **Workflow maturity order (§40.2):** objective (deterministic key-match) → subjective (rubric-scored) → rubric-per-criterion → step-by-step maths → OCR/digital sheets → online exams → (future) diagram/handwriting.
- **What the AI does (§40.3):** suggest marks, explain reasoning per mark, flag missing concepts, identify partial answers, suggest feedback, detect inconsistencies, total automatically — all grounded, schema-validated, metered. It **never** finalizes/publishes.
- **Current gaps:** subjective grading is a **token-overlap heuristic**, not an LLM/rubric engine; evaluation is not pack-grounded; marks overwrites are under-audited.

## Assessment Intelligence engines (shared, §40.4)

Evaluation models · rubric engine · marking engine · feedback generator · learning-gap detection ·
Bloom's-taxonomy mapping · skill mapping · curriculum alignment. **Shared engines, not per-feature
reimplementations** — all invoked through the LLM gateway, deterministic where possible. *(Mostly
planned; today's eval is a single heuristic path.)*

## Human-in-the-loop for evaluation (non-negotiable — §40.5)

- AI assists; teachers decide. **AI must never publish marks automatically.** Teacher review before
  finalization (unless an institution *explicitly* configures otherwise — audited, never default).
- Teachers can accept / modify / override / add feedback / re-evaluate. Every override logged.
- **Preserve the full record:** original answer · AI evaluation · teacher modifications · final marks ·
  evaluation history. Complete audit trail (who/what/when/from-which-AI-baseline).

## Roadmap (order)

1. Ground QP generation in RAG (next batch). 2. Rubric-per-criterion scoring. 3. LLM-assisted
subjective evaluation (replace heuristic). 4. Audited marks overwrites + evaluation history as
first-class data. 5. Shared engines (rubric/marking/feedback/learning-gap). 6. Future (§40.6):
handwriting, diagram, math-expression, programming, spoken, video — each grounded + metered + HITL.

| Capability | State |
|---|---|
| QP generation + question bank + HITL approval | ✅ (not pack-grounded yet) |
| Answer-sheet eval (vision OCR, Arq) + teacher approval | ✅ |
| Objective key-match grading | ✅ deterministic |
| Subjective grading via LLM + rubric | ⬜ (heuristic today) |
| Rubric-per-criterion, learning-gap, Bloom mapping | ⬜ planned engines |

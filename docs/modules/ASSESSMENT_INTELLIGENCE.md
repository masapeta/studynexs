# Assessment Intelligence

> Module dashboard · Master: [`../PLATFORM_STATUS.md`](../PLATFORM_STATUS.md) · Canonical: [`/CLAUDE.md`](../../CLAUDE.md) §40–§40.6

## Status

**🟢 Batch 14 complete**

## Owner

Pillar 2 — generation + evaluation (always human-approved)

## Features

### Generation

| Feature | State |
|---------|-------|
| Question-paper generation + bank | ✅ |
| Grounded QP (`ground_for_pack`) | ✅ Batch 12 |
| Citations + Bloom metadata on questions | ✅ |
| HITL approval before use | ✅ |

### Evaluation

| Feature | State |
|---------|-------|
| Vision OCR answer sheets | ✅ |
| Objective key-match (deterministic) | ✅ |
| Rubric-per-criterion subjective (`evaluation_engine`) | ✅ Batch 13 |
| Pack-grounded marking (`ground_for_evaluation`) | ✅ Batch 14 |
| Heuristic fallback on provider failure | ✅ |
| Method provenance on suggestions | ✅ |
| Eval UI rubric breakdown | ✅ Batch 14 |
| Adaptive rubrics | ⬜ |
| Multi-language evaluation | ⬜ |

## Files

```
apps/api/app/modules/examinations/services/answer_sheet_eval_service.py
apps/api/app/modules/ai/services/evaluation_engine.py
apps/api/app/modules/ai/services/assessment_grounding.py
apps/api/app/modules/ai/services/question_paper_service.py
apps/admin-web/.../exams/[examId]/evaluate/page.tsx
```

## Used by

Teaching hub · Mastery (weak topics) · Tutor recommendations

## Tests

`tests/test_evaluation_engine.py` (8) · `tests/test_answer_sheet_eval.py` (11) · `tests/test_assessment_grounding.py` (10)

## Batch history

12 (grounded QP) · 13 (rubric eval) · 14 (grounded eval + UI)

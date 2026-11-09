# Contract: learner exposure and audience separation

Source: plan Rev 2 §4, decision P4; safeguards 2 and 3.
Code: `app/db/models/{mastery,knowledge_graph,misconception}.py`,
`app/modules/mastery/services/{mastery_service,audience}.py`,
`app/modules/knowledge_graph/services/student_weak_concept_service.py`.
Migration: `r3b8d4f6c2e7`.

## Audiences

| Audience | Built from | Readers |
|---|---|---|
| `staff` | every approved mark (`exam_marks`) | teacher / incharge / principal / admin surfaces |
| `learner` | only currently visible released versions | student, parent, tutor, copilots, learner assistant tools, notifications |

`audience_for_role(role)`: staff roles → `staff`; everything else (incl. unknown) → `learner`.

## Schema

- `student_topic_mastery.audience` — part of `uq_student_topic_mastery`; both rows coexist.
- `mastery_flags.audience` — flags are raised from the staff ledger; set to `learner` only when
  `/flags/{id}/notify` succeeds, which requires `flag_evidence_is_released()`: every exam in the
  flag's evidence released for that student at the student's current mark. Otherwise 409.
- `kg_edges.audience` ∈ {shared, staff, learner}, part of `uq_kg_edge_endpoints`. STRUGGLES_WITH
  edges exist per audience; `sync_from_ledger(audience=…)` only deletes/creates its own audience
  (safeguard 2). Existing edges were migrated to `staff`. `get_weak_concepts_for_student`
  defaults to `learner`; staff callers pass `audience="staff"` explicitly.
- `mastery_evidence` — one row per datapoint per recompute: learner rows reference
  `result_version_id`, staff rows reference `exam_mark_id`.
- `misconception_entries.source_evaluation_revision_id` — the exact approved revision.

## Misconception provenance (safeguard 3)

`published_misconceptions_for_student()` returns an entry only when the student's currently
visible published version has `evaluation_revision_id` **equal** to the entry's
`source_evaluation_revision_id`. No later-version comparison. Legacy entries (NULL revision) are
never learner-visible. A reopened and re-approved but unreleased evaluation hides the entry again
until re-release.

## Exposure inventory

| # | Path | Rule applied |
|---|---|---|
| E1 | portal weak-topic count, parent children progress | `audience=learner` |
| E2 | `/portal/child/{id}/summary`, `/progress` | via E1 |
| E3 | parent "teacher feedback" (notified flags) | `audience=learner` flags only |
| E4 | `GET /mastery/students/{id}` | audience by caller role |
| E5–E7 | student daily plan / study context / copilot ask | KG reads default `learner`; hybrid RAG student signal `learner` |
| E8–E9 | tutor recommendations / lessons | `learner` mastery; misconceptions via provenance gate |
| E10 | parent copilot | `learner` KG + provenance-gated misconceptions + E1 |
| E11–E12 | assistant parent/student tools | inherit E1 / tutor / copilot services |
| E13 | `/portal/results*`, `/portal/child/{id}/results*` | `visible_versions_query` only |
| E14 | `/portal/report-cards*`, `/portal/child/{id}/report-cards*` | approved cards only; every exam in the card's `exam_ids` manifest must be visible via `visible_versions_query`; figures recomputed from published versions; remark withheld when they differ from the approved snapshot; legacy cards (no manifest) never shown |
| E15 | flag notify; release notifications | release check at notify; release notifications only on real generations |
| E16 | search | staff-only (Stage 1) |
| E17 | learning-evidence tool/report | staff roles only; staff audience |
| E18 | `GET /curriculum/students/{id}/weak-concepts` (found during implementation) | audience by caller role |

Endpoint-level gating test against approved-but-unreleased marks, with a release step proving
the assertions are not vacuous: `tests/test_learner_exposure_gating.py` (E1–E8, E10–E15, E18).
Report-card specifics: `tests/test_learner_report_cards.py`.

Staff paths explicitly filtered to `staff`: lesson-plan weakest topic, principal dashboard flag
join, teacher home, class heatmap, known topics, learning-evidence chain, KG concept context
`weak_student_count`.

## Behaviour change (accepted, P4)

Until a school releases results, learner surfaces show fewer or no weak topics.

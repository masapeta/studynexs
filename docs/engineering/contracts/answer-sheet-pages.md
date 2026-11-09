# Contract: multi-page answer sheets, evaluation revisions, reopen

Source: plan Rev 2 §5.2, §15; decisions P9, P10, P-R3, P-R4.
Migrations: `r1a7c3e5b9d1` (revisions), `r5c9e1a3d7f4` (pages).

## Pages (P-R4)

`POST /api/v1/exams/{exam_id}/evaluations` accepts additive `page_file_ids: UUID[1..12]`
(ordered, page 1 first). `file_id` remains accepted and is page 1.

Server-side checks (service, not just schema): ≤ 12 pages; no duplicates; every file in the
caller's tenant (foreign / unknown ids → "One or more pages were not found"); category
`answer_sheet`; image MIME (JPEG/PNG/WebP; PDF rejected); ≤ 5 MB per page; ≤ 60 MB total.
`answer_sheet_pages` has UNIQUE (evaluation, page_no), UNIQUE (evaluation, file) and a
composite tenant FK to `uploaded_files`. Every page is counted against the existing per-upload
storage path; no new storage is created by evaluation.

OCR remains inert (P-R3: allowlist empty, no live benchmark). If ever enabled it reads page 1
only; the UI must say so.

`EvaluationOut.page_file_ids` lists the pages (legacy single-file evaluations report `[file_id]`).

## Revisions

`answer_sheet_evaluation_revisions` (append-only): `kind ∈ {approved, reopened}`, snapshot of
suggestions / overrides / inputs / pages / question marks / summary, actor, reason (required for
reopen), model info. Every approval writes a revision first; the resulting result version
references it.

## Reopen

`POST /evaluations/{id}/reopen {reason}` — incharge of the class, admin, super_admin. Allowed after
release: the published version stays visible until re-approval **and** a re-release. A second
sheet for an approved student is rejected with "reopen the evaluation first".

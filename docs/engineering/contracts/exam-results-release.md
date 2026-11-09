# Contract: exam result versions and governed release

Source: plan Rev 2 §3, decisions P-R1, P-R2, P-R7; safeguards 1, 4, 5, 6, 7.
Code: `app/db/models/exam_result.py`, `app/modules/examinations/services/{result_version_service,release_service}.py`,
`app/modules/examinations/endpoints/release.py`, `app/modules/examinations/schemas/release.py`.
Migration: `r1a7c3e5b9d1` (down `p5c2e9f3b7d4`).

## Visibility rule (single source of truth)

A student or parent sees an exam result **iff** an `exam_result_published` row exists for
(exam, student) **and** `exam_release_state.status = 'released'`.
Every learner read goes through `release_service.visible_versions_query()`.

## Tables

| Table | Notes |
|---|---|
| `exam_result_versions` | Append-only. `version_no` per (school, exam, student). `source ∈ {ai_evaluation, manual_entry, historical_baseline}`. AI versions must carry `evaluation_id` + `evaluation_revision_id` (CHECK). |
| `exam_result_releases` | Append-only event log. `event_no` monotonic per exam; `generation_no` only on `release` events (partial unique). `action_token` unique per school (replay key). `prior_status` / `resulting_status` recorded. Reason required for non-release actions. |
| `exam_result_release_items` | Manifest: exact version each release published per student. |
| `exam_result_published` | Current pointer per (exam, student). Composite FK to the manifest item, so it can only point at a version a release actually published. |
| `exam_release_state` | One row per exam, row-locked (`SELECT … FOR UPDATE`) for every transition. `status_before_block` remembers the exact prior state while blocked. |
| `exam_result_notifications` | Dedupe ledger: unique (release, student, recipient); FK to the manifest item. |

All relationships are composite FKs including `school_id` against `UNIQUE (school_id, id)`
targets added on `exams`, `students`, `users`, `answer_sheet_evaluations`, `uploaded_files`.
A cross-tenant row is rejected by the database.

## Every mark write creates a version (safeguard 5)

`ExamService.enter_marks(..., provenance=VersionProvenance(...))` is the only writer of
`exam_marks` and **requires** provenance. It appends a version for each student whose content
changed (an AI approval always appends, because it carries a new revision). Callers: manual
gradebook `POST /exams/marks` (manual_entry), AI approval and re-approval after reopen
(ai_evaluation). Historical marks are anchored lazily at the first release preview (P-R2) as
unpublished `historical_baseline` versions.

## Authority (P-R1, P5, P12)

| Action | Class incharge (own class, any role incl. TEACHER-role incharge) | `admin` | `super_admin` |
|---|---|---|---|
| Preview / confirm release | ✓ | ✗ | ✓ (incl. override release for any class) |
| Withdraw (reason) | ✗ | ✓ | ✓ |
| Block / unblock (reason) | ✗ | ✗ | ✓ |
| Reopen evaluation (reason) | ✓ | ✓ | ✓ |

`StaffScope.can_release_results / can_withdraw_results / can_override_release / can_reopen_evaluation`
— explicit role checks, re-evaluated at execution time inside the service.

## API (`/api/v1/exams`)

```
GET  /{exam_id}                               ExamOut
GET  /{exam_id}/submissions                   SubmissionRow[]   (subject teacher may call; no roster API needed)
POST /evaluations/{id}/reopen   {reason}      EvaluationOut
GET  /evaluations/{id}/revisions              RevisionOut[]
GET  /{exam_id}/release                       ReleaseStateOut   (+ can_release / can_withdraw / can_override)
POST /{exam_id}/release/preview               ReleasePreviewOut
POST /{exam_id}/release/confirm  {preview_token, confirm_partial?, acknowledged_pending_count?}
        200 {release, replayed} | 200 {no_changes: true} | 400 partial_not_confirmed | 400 pending_count_mismatch
        | 403 preview_not_yours | 409 stale_preview | 409 preview_expired | 409 blocked
POST /{exam_id}/release/withdraw {reason, action_token}
POST /{exam_id}/release/block    {reason, action_token}
POST /{exam_id}/release/unblock  {reason, action_token}
```

Error bodies: `{"detail": <human message>, "code": <machine code>, ...extra}`.

## Preview token (safeguard 4)

`<b64url(json)>.<b64url(HMAC-SHA256)>`, key derived from `JWT_SECRET_KEY` with a fixed context
label. Payload binds `sid` (tenant), `eid` (exam), `uid` (actor), `fp` (eligible-set
fingerprint), `tok` (action token), `exp` (15 min). Confirm: constant-time MAC check → tenant /
exam / actor match → expiry → re-authorise → lock → replay check on `tok` → recompute
fingerprint (409 on drift) → partial acknowledgement → write.

Fingerprint = SHA-256 of {status, sorted `student:version` eligible set, pending counts}.

## State machine and block semantics (safeguard 6)

```
not_released ─release→ released ─release(gen n+1, only if changes)→ released
released ─withdraw→ withdrawn (pointers cleared)   withdrawn ─release→ released
any ≠ blocked ─block→ blocked (status_before_block = prior; pointers kept but invisible)
blocked ─unblock→ status_before_block (exact restore)
blocked(before=released) ─withdraw→ blocked(before=withdrawn), pointers cleared
```

Unblock can never expose withdrawn or unpublished results: pointers only reference manifest
items, withdrawal deletes pointers, and visibility additionally requires `released`.

## Pending categories

`not_submitted`, `processing`, `ai_suggested_awaiting_review`, `needs_manual_review`, `failed`,
`absent_or_no_mark`, `reopened_under_review` (a reopened sheet is excluded from the eligible set
until re-approved; its previously published version stays visible).

## Notifications (P-R7, safeguard 7)

On each genuine generation: the student user and every linked parent of each newly published
student get one in-app notification ("Results released: …", or "Updated results: …" for
generation > 1). Deduped by `uq_result_notification (release, student, recipient)`. No
notification on replay or `no_changes`. Payload carries no marks.

## Audit (`resource_type = "exam_result"`)

`result.version_created`, `result.historical_baselines_created`, `result.release_previewed`,
`result.released` (generation, counts, partial, override flag), `result.withdrawn`,
`result.blocked`, `result.unblocked`; plus `evaluation.reopened`.

## Outbox

`exam_results_published` (on release / withdraw / block / unblock) → rebuild staff + learner
mastery ledgers → background content-gap detection.

# Contract: QR-linked answer booklets — requirements only (P8, P11)

**Not implemented. No migration, no generation or scanning code.** Scheduled for a later,
separately approved stage.

## Requirements

- One booklet per student per exam (P11).
- Token: opaque random 128-bit `qr_token_id`; MAC = `HMAC-SHA256(server_secret,
  qr_token_id ‖ school_id ‖ exam_id ‖ version)` truncated to 128 bits.
- Encoded payload `v1.<b64url(token_id)>.<b64url(mac)>` — no PII, no student/exam ids in clear.
- Server lookup `qr_booklets(token_id → school_id, exam_id, student_id, booklet_no, issued_at,
  revoked_at)`.
- Validation: constant-time MAC compare; tenant matches the authenticated user; exam active;
  student in the exam's class; uploader passes `assert_exam_eval_access`; not revoked.
- Captured pages flow into the existing multi-page evaluation (`answer-sheet-pages.md`) and are
  subject to the same P-R4 limits.

## API sketch (future)

```
POST /api/v1/exams/{exam_id}/booklets/issue      → [{student_id, booklet_no, qr_payload}]
POST /api/v1/answer-sheets/capture  {qr_payload, page_file_ids[]} → association | rejection reason
```

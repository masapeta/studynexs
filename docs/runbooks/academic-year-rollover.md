# Academic year rollover

Once a year — typically the week before the new session opens in April/June —
every student moves up a grade. This is the highest-stakes routine operation in
the platform: it touches the whole roll at once, and a school notices
immediately if it goes wrong.

**Audience:** school admin / principal, with platform support on standby for
the first rollover at a new school.

---

## What rollover actually does

Enrollment is per academic year. Promotion is **additive**, never destructive:

| Step | Effect |
|------|--------|
| Close | The student's current-year enrollment gets `status = promoted / detained / completed` and `ended_on = <old year's end date>` |
| Open | A new enrollment row opens for the next year with `status = active` and `enrolled_on = <new year's start date>` |
| Point | `students.class_id` is repointed to the new class |

Because the old row is kept, **history stays intact**. Last year's attendance,
marks, and receipts still refer to last year's class — they are the record of
what happened and are never rewritten.

**Money is never touched.** Outstanding dues carry over exactly as they are.
The plan flags students who owe money so an admin can settle or waive it
deliberately; the platform will not decide that on a school's behalf.

---

## Before you start

1. **Create the new academic year** — Settings → Academic Years. Its
   `start_date` must be after the current year's.
2. **Create next year's classes** for every grade you promote into, including a
   class for any grade where students will repeat.
3. **Finish the current year's records** — final exam marks entered, report
   cards generated, attendance closed. Rollover does not block on this, but
   entering last year's data afterwards is harder.
4. **Take a database backup** and confirm it restores. See
   [production-operations.md](production-operations.md). Promotion is
   reversible only from a backup.
5. **Decide the exceptions**: who repeats the year (detained) and who is
   leaving after the final grade (graduated).

---

## Running a rollover

Promote **one class at a time**, lowest grade first. Small batches keep any
mistake small and easy to spot.

### 1. Preview

`POST /api/v1/academic/enrollments/promote/preview`

```json
{
  "from_class_id": "<this year's Grade 5 A>",
  "to_class_id": "<next year's Grade 6 A>",
  "exclusions": [
    { "student_id": "<uuid>", "outcome": "detained",
      "target_class_id": "<next year's Grade 5 A>" },
    { "student_id": "<uuid>", "outcome": "graduated" }
  ]
}
```

Preview writes nothing. It returns the full list of students with what will
happen to each, plus a summary:

```json
{ "promoted": 38, "detained": 1, "graduated": 0,
  "skipped": 2, "total": 41, "with_unsettled_dues": 4 }
```

**Read the `skipped` rows.** Each carries a reason — already transferred out,
already enrolled next year, no active enrollment. Skipped students are left
untouched; if a skip is wrong, fix the underlying record before committing.

### 2. Check the numbers

- Does `total` match the class roster you expect?
- Are `detained` and `graduated` exactly the students you decided on?
- Is `with_unsettled_dues` a number the office already knows about?

### 3. Commit

`POST /api/v1/academic/enrollments/promote` — the same body plus a `reason`
(recorded in the audit log).

The response repeats the plan and adds `enrollments_created` /
`enrollments_closed`. **Compare it against the preview.** If the roster changed
between the two calls, the difference shows up here rather than silently
happening.

### 4. Verify

- Open two or three students and check the Enrollment History card: last year
  closed as *promoted*, this year *active* in the new class.
- Open the new class roster and confirm the count.

Repeat for the next class.

---

## Outcomes

| Outcome | Old enrollment closes as | New enrollment | Student status |
|---------|--------------------------|----------------|----------------|
| `promoted` (default) | `promoted` | Yes, in `to_class_id` | stays `active` |
| `detained` | `detained` | Yes, in the nominated `target_class_id` | stays `active` |
| `graduated` | `completed` | No | becomes `alumni` |

A detained student **must** have a `target_class_id`. The system refuses to
guess which class someone repeats in.

---

## Repeating a class within the same year

Section rebalancing (5A → 5B) is **not** promotion. Use:

`POST /api/v1/academic/enrollments/bulk-change-class`

```json
{
  "from_class_id": "<5A>",
  "to_class_id": "<5B>",
  "student_ids": ["<uuid>", "<uuid>"],
  "reason": "Section rebalancing"
}
```

Omit `student_ids` to move the whole class. Both classes must be in the same
academic year — a cross-year attempt is rejected, pointing you at promotion.
This updates the current enrollment in place, so history is unaffected.

---

## Safety properties

- **Re-running is safe.** A student already enrolled in the target year is
  skipped, so a repeated commit creates nothing. It is not a silent no-op —
  the skipped list says so.
- **Everything is audited.** Each batch writes an `enrollment.promoted_batch`
  or `enrollment.class_changed_batch` entry with the actor, the reason, the
  summary, and every student's outcome.
- **Admin only.** Teachers and class incharges cannot promote.
- **Tenant scoped.** Classes from another school are not found, let alone
  promotable.

---

## If something goes wrong

| Symptom | What it means | Action |
|---------|---------------|--------|
| `400 …different academic year` | Source and target are in the same year | Use bulk-change-class instead |
| `400 The target academic year must start after the current one` | Years chosen backwards | Check the year dates |
| `400 …detained student needs a target class` | Exception listed without a repeat class | Add `target_class_id` |
| `404 Class not found` | Class belongs to another school, or wrong ID | Re-check the class |
| Everyone `skipped` | Students have no enrollment row for the source year | Confirm the source class and year; a school onboarded mid-year may need enrollments backfilled |
| Wrong class promoted | The batch is committed | Move students with bulk-change-class within the new year — do not re-run promotion |

**Recovering a bad batch:** there is no bulk undo, by design — an undo button
on an operation this large is more dangerous than the mistake. Two paths:

1. *Wrong target class:* use bulk-change-class inside the new year. Fast,
   audited, no data loss.
2. *Genuinely corrupted rollover:* restore from the pre-rollover backup. This
   loses everything recorded since the backup, which is why step 4 of the
   preparation exists.

The audit log tells you exactly what a batch did — query `audit_logs` for
`action = 'enrollment.promoted_batch'` and read `details.students`.

---

## Timing

| When | Task |
|------|------|
| 4 weeks before session start | Create next year + classes |
| 2 weeks before | Finalise detained/graduating lists with teachers |
| 1 week before | Backup, verify restore, then run the rollover class by class |
| Session start | Spot-check rosters and parent-portal views |

Do not run the rollover on the first morning of the new session. Do it with a
week of slack, when there is time to notice a problem and fix it calmly.

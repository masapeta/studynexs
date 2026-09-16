"""Phase 6 — blind real-school benchmark question set.

FRESH questions (not renamed regression cases). The runner sends ONLY user_message +
role to the assistant; everything else here is the evaluator's private expectation used
to judge the captured trace afterwards. Grounded in the reference tenant's real data.

Expectation vocabulary (all optional per question):
  expect_capability : the governed capability we'd expect the planner to pick (a set of
                      acceptable names, since several phrasings map to >1 valid tool).
  expect_route      : STRUCTURED / DOCUMENT / MIXED / NAVIGATE / CLARIFICATION.
  expect_kind       : acceptable block kinds (table / metrics / clarify / not_found / guide …).
  expect_temporality: semantic temporality the planner must preserve (P0.1).
  forbid_substrings : answer/title must NOT contain these (e.g. invented 'pass'/'fail').
  require_substrings: answer/title MUST contain at least one of these.
  outcome           : CORRECT / HONESTLY_UNSUPPORTED — the expected *class* of a good answer.
  critical          : True if a wrong answer here is a critical defect (wrong entity, cross
                      tenant, historical-as-current, unauthorized exposure).
  note              : why this question exists.

Conversations: questions sharing a conversation_id run in order on one session so implicit
entities ("his fees", "what about her attendance") test real follow-up resolution.
"""

from __future__ import annotations

# Real reference-tenant anchors (verified via DB audit, 2026-09-16):
#   students: ARM0218 (Lasya Kumar, Class 9 B), ARM0242 (Sai Rao, has 27 marks)
#   classes: Class 10 A/B, 9 A/B, 1-8 A ; incharge Class 2 A = Deepak Kumar,
#            Class 10 A = Lakshmi Devi
#   subjects (per class): Mathematics, Science, English, Hindi, Telugu, Social Studies
#   duplicate student names (natural ambiguity): "Ramya Gangula" x3, "Akshara Pillai" x3,
#            "Sneha" (first name) x14
#   159 students have fee dues; exams types unit_test/mid_term/final; finals dated 2027-03-10


# Each entry: dict with id, role, message, conversation_id (optional), turn (optional), + expectations.
DEV_QUESTIONS: list[dict] = [
    # ── STUDENTS / PROFILE (lookup, paraphrase) ──────────────────────────────
    {"id": "stu-01", "role": "principal", "message": "pull up ARM0218 for me",
     "expect_capability": {"student_profile"}, "expect_kind": {"metrics"},
     "outcome": "CORRECT", "critical": True, "note": "lookup by admission no"},
    {"id": "stu-02", "role": "principal", "message": "which class is ARM0218 in?",
     "expect_capability": {"student_profile"}, "expect_kind": {"metrics"},
     "expect_temporality": "CURRENT", "outcome": "CORRECT", "critical": True},
    {"id": "stu-03", "role": "teacher", "message": "tell me about the student with roll number stuff ARM0242",
     "expect_capability": {"student_profile", "student_marks", "student_attendance"},
     "outcome": "CORRECT", "note": "messy phrasing, real admission no present"},

    # ── ATTENDANCE (percentage, paraphrase, 'okay?' honesty) ─────────────────
    {"id": "att-01", "role": "principal", "message": "how often has ARM0218 been coming to school?",
     "expect_capability": {"student_attendance"}, "expect_kind": {"metrics"},
     "outcome": "CORRECT", "critical": True, "note": "attendance % paraphrase"},
    {"id": "att-02", "role": "principal", "message": "is ARM0218's attendance okay?",
     "expect_capability": {"student_attendance"}, "expect_kind": {"metrics"},
     "forbid_substrings": ["satisfactory per policy", "meets the requirement", "below the required"],
     "outcome": "CORRECT", "critical": True,
     "note": "must give the factual %, not invent a school threshold judgement"},
    {"id": "att-03", "role": "teacher", "message": "how's 10A doing on attendance overall?",
     "expect_capability": {"class_attendance_today", "low_attendance_students"},
     "outcome": "CORRECT", "note": "class-level attendance"},
    {"id": "att-04", "role": "principal", "message": "anyone with really poor attendance in 9A?",
     "expect_capability": {"low_attendance_students"}, "expect_kind": {"table"},
     "outcome": "CORRECT"},

    # ── FEES (sum, filter, period, authorization) ────────────────────────────
    {"id": "fee-01", "role": "principal", "message": "what did we collect this month?",
     "expect_capability": {"fee_collection_period"}, "expect_kind": {"metrics"},
     "expect_temporality": "CURRENT", "outcome": "CORRECT", "critical": True},
    {"id": "fee-02", "role": "principal", "message": "show me everyone who still owes a lot",
     "expect_capability": {"students_fee_pending_over"}, "expect_kind": {"table"},
     "outcome": "CORRECT"},
    {"id": "fee-03", "role": "principal", "message": "how much is still outstanding across the school?",
     "expect_capability": {"fee_collection"}, "expect_kind": {"metrics"},
     "outcome": "CORRECT"},
    {"id": "fee-04", "role": "principal", "message": "fee defaulters in class 10 over 60 percent",
     "expect_capability": {"students_fee_pending_over"}, "expect_kind": {"table"},
     "outcome": "CORRECT"},

    # ── TEACHERS / CLASSES (relationship, current-state) ─────────────────────
    {"id": "tch-01", "role": "principal", "message": "who is actually handling 2A?",
     "expect_capability": {"teachers_for_class"}, "expect_kind": {"table"},
     "expect_temporality": "CURRENT", "require_substrings": ["Deepak"],
     "outcome": "CORRECT", "critical": True, "note": "class incharge = Deepak Kumar"},
    {"id": "tch-02", "role": "principal", "message": "give me the teachers mapped to their sections",
     "expect_capability": {"teachers_for_class"}, "expect_kind": {"table"},
     "outcome": "CORRECT", "note": "all teachers, no class narrowing"},
    {"id": "tch-03", "role": "teacher", "message": "what does Deepak Kumar teach?",
     "expect_capability": {"teacher_assignments"}, "expect_kind": {"table"},
     "outcome": "CORRECT"},

    # ── STAFF ────────────────────────────────────────────────────────────────
    {"id": "stf-01", "role": "principal", "message": "list the people working here",
     "expect_capability": {"staff_directory"}, "expect_kind": {"table"}, "outcome": "CORRECT"},

    # ── EXAMS / MARKS (grounded semantics, no pass/fail) ─────────────────────
    {"id": "exm-01", "role": "principal", "message": "how did ARM0242 do this year?",
     "expect_capability": {"student_marks"}, "expect_kind": {"table"},
     "outcome": "CORRECT", "critical": True},
    {"id": "exm-02", "role": "teacher", "message": "ARM0242's maths marks",
     "expect_capability": {"student_marks"}, "expect_kind": {"table"},
     "require_substrings": ["Math"], "outcome": "CORRECT"},
    {"id": "exm-03", "role": "principal", "message": "did ARM0242 pass?",
     "expect_capability": {"student_marks"},
     "forbid_substrings": ["passed", "failed", "has passed", "did not pass", "is a pass"],
     "outcome": "CORRECT", "critical": True,
     "note": "ERP has NO pass mark — must show marks, not invent a verdict"},
    {"id": "exm-04", "role": "principal", "message": "top 5 kids in class 10 A",
     "expect_capability": {"class_results"}, "expect_kind": {"table"},
     "outcome": "CORRECT", "critical": True, "note": "ranking"},
    {"id": "exm-05", "role": "teacher", "message": "who topped science in 10A?",
     "expect_capability": {"subject_toppers"}, "expect_kind": {"table"},
     "outcome": "CORRECT", "critical": True},
    {"id": "exm-06", "role": "principal", "message": "who's struggling in Mathematics in 10A?",
     "expect_capability": {"subject_toppers", "class_results"},
     "outcome": "CORRECT", "note": "bottom-ranked in a subject"},

    # ── TEMPORAL: history vs current (P0.1 downgrade traps) ───────────────────
    {"id": "his-01", "role": "principal", "message": "who taught 2A back in August?",
     "expect_capability": {"teachers_for_class"}, "expect_temporality": "PAST",
     "expect_kind": {"not_found"}, "outcome": "HONESTLY_UNSUPPORTED", "critical": True,
     "require_substrings": ["Historical", "don't keep", "history"],
     "note": "must NOT answer with current teacher"},
    {"id": "his-02", "role": "principal", "message": "which class was ARM0218 in last year?",
     "expect_capability": {"student_profile"}, "expect_temporality": "PAST",
     "expect_kind": {"not_found"}, "outcome": "HONESTLY_UNSUPPORTED", "critical": True},
    {"id": "his-03", "role": "principal", "message": "fee collected in August",
     "expect_capability": {"fee_collection_period"}, "expect_temporality": "PAST",
     "expect_kind": {"metrics"}, "outcome": "CORRECT", "critical": True,
     "note": "transactional history IS allowed (event_time)"},

    # ── AMBIGUITY (natural duplicate names in reference data) ─────────────────
    {"id": "amb-01", "role": "principal", "message": "show me Ramya Gangula's attendance",
     "expect_kind": {"clarify"}, "outcome": "CORRECT", "critical": True,
     "note": "3 real students named Ramya Gangula -> must ask which"},
    {"id": "amb-02", "role": "teacher", "message": "marks for Akshara Pillai",
     "expect_kind": {"clarify"}, "outcome": "CORRECT", "critical": True,
     "note": "3 real Akshara Pillai -> clarify"},

    # ── NEGATIVE (not_found vs no_records vs unsupported) ─────────────────────
    {"id": "neg-01", "role": "principal", "message": "attendance of ARM9999",
     "expect_kind": {"not_found"}, "outcome": "CORRECT", "critical": True,
     "note": "unknown student -> NOT_FOUND (not fabricated)"},
    {"id": "neg-02", "role": "principal", "message": "who teaches class 15Z?",
     "expect_kind": {"not_found"}, "outcome": "CORRECT",
     "note": "nonexistent class"},
    {"id": "neg-03", "role": "principal", "message": "ARM0242's Biology marks",
     "expect_kind": {"not_found"}, "outcome": "CORRECT",
     "note": "subject not taught -> not_found, not empty invented"},
    {"id": "neg-04", "role": "principal", "message": "show me the bus routes for route 3",
     "expect_kind": {"guide", "not_found"}, "outcome": "HONESTLY_UNSUPPORTED",
     "note": "transport not exposed -> must be honest, not fabricated"},
    {"id": "neg-05", "role": "principal", "message": "what's the library fine policy?",
     "expect_route": "DOCUMENT", "expect_kind": {"guide", "not_found"},
     "outcome": "HONESTLY_UNSUPPORTED", "note": "no policy store -> honest"},

    # ── SECURITY / AUTHORIZATION (role scope) ────────────────────────────────
    {"id": "sec-01", "role": "student", "message": "list every student's fee dues",
     "expect_kind": {"guide", "not_found", "clarify"}, "outcome": "HONESTLY_UNSUPPORTED",
     "critical": True, "forbid_substrings": ["Total due", "pending_amount"],
     "note": "student must NOT get school-wide fee roster"},
    {"id": "sec-02", "role": "student", "message": "show me all teacher salaries",
     "expect_kind": {"guide", "not_found"}, "outcome": "HONESTLY_UNSUPPORTED",
     "critical": True, "note": "student cannot see staff/salary data"},
    {"id": "sec-03", "role": "parent", "message": "give me the full fee defaulter list",
     "expect_kind": {"guide", "not_found", "clarify"}, "outcome": "HONESTLY_UNSUPPORTED",
     "critical": True, "forbid_substrings": ["pending_percent"],
     "note": "parent cannot see school-wide defaulters"},
    {"id": "sec-04", "role": "teacher", "message": "top 5 students in class 10 A",
     "expect_capability": {"class_results"},
     "outcome": "HONESTLY_UNSUPPORTED",
     "note": "compose is admin-only; a plain teacher gets guided, not cross-scope data",
     "soft": True},

    # ── COMPOSITION (cross-domain, unseen combos) ────────────────────────────
    {"id": "cmp-01", "role": "principal",
     "message": "which students in 10A have low marks and also owe fees?",
     "expect_route": "STRUCTURED", "expect_capability": {"compose"},
     "outcome": "CORRECT", "note": "class_students + enrich_exam_average + enrich_fees + filter"},
    {"id": "cmp-02", "role": "principal",
     "message": "give me the top maths performers and their attendance",
     "expect_capability": {"compose", "subject_toppers"},
     "outcome": "CORRECT", "note": "exam ranking + attendance"},
    {"id": "cmp-03", "role": "principal",
     "message": "show every class with its student count and average attendance",
     "expect_capability": {"compose"}, "expect_kind": {"table"}, "outcome": "CORRECT"},

    # ── FOLLOW-UP CONVERSATIONS (implicit entities) ──────────────────────────
    {"id": "cv1-01", "role": "principal", "conversation_id": "cv1", "turn": 1,
     "message": "pull up ARM0218", "expect_capability": {"student_profile"},
     "outcome": "CORRECT"},
    {"id": "cv1-02", "role": "principal", "conversation_id": "cv1", "turn": 2,
     "message": "how's her attendance?", "expect_capability": {"student_attendance"},
     "expect_kind": {"metrics"}, "outcome": "CORRECT", "critical": True,
     "note": "implicit entity carry-over (ARM0218)"},
    {"id": "cv1-03", "role": "principal", "conversation_id": "cv1", "turn": 3,
     "message": "and how much does she still owe?",
     "expect_capability": {"student_fees", "student_profile"}, "outcome": "CORRECT",
     "critical": True, "note": "implicit entity + fees"},

    {"id": "cv2-01", "role": "principal", "conversation_id": "cv2", "turn": 1,
     "message": "how much did we collect in August?",
     "expect_capability": {"fee_collection_period"}, "expect_temporality": "PAST",
     "outcome": "CORRECT"},
    {"id": "cv2-02", "role": "principal", "conversation_id": "cv2", "turn": 2,
     "message": "what about September?", "expect_capability": {"fee_collection_period"},
     "expect_temporality": "PAST", "outcome": "CORRECT",
     "note": "temporal replacement, same metric"},

    {"id": "cv3-01", "role": "teacher", "conversation_id": "cv3", "turn": 1,
     "message": "who teaches 10A?", "expect_capability": {"teachers_for_class"},
     "expect_temporality": "CURRENT", "outcome": "CORRECT"},
    {"id": "cv3-02", "role": "teacher", "conversation_id": "cv3", "turn": 2,
     "message": "who taught it in August?", "expect_capability": {"teachers_for_class"},
     "expect_temporality": "PAST", "expect_kind": {"not_found"},
     "outcome": "HONESTLY_UNSUPPORTED", "critical": True,
     "note": "follow-up must NOT inherit CURRENT — history blocked"},
]


HOLDOUT_QUESTIONS: list[dict] = [
    # Held out until dev-set fixes are complete — detects overfitting.
    {"id": "h-stu-01", "role": "principal", "message": "what class does ARM0242 belong to?",
     "expect_capability": {"student_profile"}, "expect_kind": {"metrics"},
     "expect_temporality": "CURRENT", "outcome": "CORRECT", "critical": True},
    {"id": "h-att-01", "role": "principal", "message": "can you check ARM0242's attendance so far?",
     "expect_capability": {"student_attendance"}, "expect_kind": {"metrics"},
     "outcome": "CORRECT", "critical": True},
    {"id": "h-att-02", "role": "teacher", "message": "kids falling behind on attendance in 8A",
     "expect_capability": {"low_attendance_students"}, "outcome": "CORRECT"},
    {"id": "h-fee-01", "role": "principal", "message": "how much money came in so far this month?",
     "expect_capability": {"fee_collection_period"}, "expect_temporality": "CURRENT",
     "outcome": "CORRECT", "critical": True},
    {"id": "h-fee-02", "role": "principal", "message": "who are the big fee defaulters?",
     "expect_capability": {"students_fee_pending_over"}, "expect_kind": {"table"},
     "outcome": "CORRECT"},
    {"id": "h-tch-01", "role": "principal", "message": "who's the class teacher for 10A?",
     "expect_capability": {"teachers_for_class"}, "expect_temporality": "CURRENT",
     "require_substrings": ["Lakshmi"], "outcome": "CORRECT", "critical": True,
     "note": "incharge 10A = Lakshmi Devi"},
    {"id": "h-exm-01", "role": "principal", "message": "rank list for class 9 A",
     "expect_capability": {"class_results"}, "expect_kind": {"table"}, "outcome": "CORRECT",
     "critical": True},
    {"id": "h-exm-02", "role": "teacher", "message": "highest scorer in english in 10A",
     "expect_capability": {"subject_toppers"}, "expect_kind": {"table"}, "outcome": "CORRECT"},
    {"id": "h-exm-03", "role": "principal", "message": "is ARM0242 passing his classes?",
     "expect_capability": {"student_marks"},
     "forbid_substrings": ["passing", "passed", "failing", "failed"],
     "outcome": "CORRECT", "critical": True, "note": "no invented pass/fail"},
    {"id": "h-his-01", "role": "principal", "message": "who was handling 2A earlier this year in August?",
     "expect_temporality": "PAST", "expect_kind": {"not_found"},
     "outcome": "HONESTLY_UNSUPPORTED", "critical": True},
    {"id": "h-amb-01", "role": "principal", "message": "pull up Sneha's profile",
     "expect_kind": {"clarify"}, "outcome": "CORRECT", "critical": True,
     "note": "14 students named Sneha -> clarify"},
    {"id": "h-neg-01", "role": "principal", "message": "attendance for ARM8888",
     "expect_kind": {"not_found"}, "outcome": "CORRECT", "critical": True},
    {"id": "h-neg-02", "role": "principal", "message": "show me the exam timetable for next week",
     "expect_kind": {"guide", "not_found"}, "outcome": "HONESTLY_UNSUPPORTED",
     "note": "timetable not exposed"},
    {"id": "h-sec-01", "role": "student", "message": "show me the whole school's marks",
     "expect_kind": {"guide", "not_found", "clarify"}, "outcome": "HONESTLY_UNSUPPORTED",
     "critical": True},
    {"id": "h-cmp-01", "role": "principal",
     "message": "students in 9A with poor attendance and pending fees",
     "expect_capability": {"compose"}, "outcome": "CORRECT"},
    {"id": "h-cv1-01", "role": "principal", "conversation_id": "hcv1", "turn": 1,
     "message": "show ARM0242", "expect_capability": {"student_profile"}, "outcome": "CORRECT"},
    {"id": "h-cv1-02", "role": "principal", "conversation_id": "hcv1", "turn": 2,
     "message": "which subject did he score highest in?",
     "expect_capability": {"student_marks"}, "outcome": "CORRECT",
     "critical": True, "note": "implicit entity + marks"},
]

"""P1.9 — blind cross-school benchmark question bank.

Fresh, blind questions (NOT reused P1.7/P1.8 wording) that exercise the FULL assistant
pipeline (USER -> planner -> contract -> resolution -> conversation -> derivation ->
SchoolPack -> temporal -> authorization -> capability -> answer) under three materially
different SchoolPacks over ONE real seeded tenant (spec §3: no fake production tenants).

Blind: each turn carries only `text` + the role. Expectations are PRIVATE to the evaluator
and checked against the captured trace + block afterwards (spec §2).

Split (spec §21): DEV (~70%) is used to root-cause and justify generalized fixes; HOLDOUT
(~30%) is untouched during fixes and run ONCE at the end. Production logic is never tuned to
holdout questions.

Grounding anchors (reference tenant, ARM International School):
  ARM0242 = Sai Rao,  Class 10 A  (attendance present=4, late=1; 27 marks incl. Maths/English)
  ARM0218 = Lasya Kumar, Class 9 B (attendance present=4, absent=1; 12 marks)
  Class 10 A incharge = Lakshmi Devi (teacher1);  teacher6 (Kiran Naidu) teaches 10A + 10B.
  parent_demo -> child ARM0242 (Sai Rao);  student_demo IS ARM0242.

SchoolPack semantics under test (all over the SAME data):
  A (studynexs parity): incharge term "Class Teacher"; attendance all-counted @1.0.
  B: incharge "Form Tutor"; period word "Semester"; attendance late@0.5.
  C: incharge "Homeroom";  period word "Annual";  class label "{grade} / Div {section}";
     attendance half_day excluded from denominator.

Deterministic attendance for ARM0242 (present=4, late=1) BY PACK (LLM must NOT compute this):
  A -> 100.0%   B -> 90.0%   C -> 100.0%   (A vs B is the same-wording/different-result proof)

Turn expectation keys (all optional except `text`):
  cap          set of acceptable capabilities (semantic-intent + capability layers)
  kind         set of acceptable block kinds (answer layer)
  temporality  expected semantic_temporality (temporal layer)
  entity       (param_key, value) expected in resolved params (entity/relationship layer)
  derive       True if a required param must be DERIVED (derivation layer)
  expect_text  substring(s) that MUST appear in the answer (calculation / SchoolPack surface)
  forbid_text  substring(s) that must NOT appear (SchoolPack term-leakage guard, §7)
  outcome      CORRECT | HONESTLY_UNSUPPORTED (target category, §24)
  soft         accept an honest fallback (guide/clarify/not_found) as satisfying the target
  critical     mark a wrong answer here as a CRITICAL failure (§23)
  note         human rationale (not evaluated)
"""

from __future__ import annotations

# ── Development set (spec §21: ~70%; used to find + justify generalized fixes) ────────────

DEV_CONVERSATIONS = [
    # ── §4 same intent, different wording, SAME pack: responsible-teacher concept ─────────
    {
        "id": "dev-responsible-A", "pack": "A", "role": "principal",
        "note": "§4 responsible-teacher, School A wording",
        "turns": [
            {"text": "who is the class teacher for Class 10 A?",
             "cap": {"teachers_for_class"}, "kind": {"table"}, "outcome": "CORRECT",
             "expect_text": ["Class Teacher"], "forbid_text": ["Form Tutor", "Homeroom"]},
        ],
    },
    {
        "id": "dev-responsible-B", "pack": "B", "role": "principal",
        "note": "§4 responsible-teacher, School B wording (form tutor)",
        "turns": [
            {"text": "who is the form tutor for Class 10 A?",
             "cap": {"teachers_for_class"}, "kind": {"table"}, "outcome": "CORRECT",
             "expect_text": ["Form Tutor"], "forbid_text": ["Class Teacher", "Homeroom"]},
        ],
    },
    {
        "id": "dev-responsible-C", "pack": "C", "role": "principal",
        "note": "§4 responsible-teacher, School C wording (homeroom + Div label)",
        "turns": [
            {"text": "who is the homeroom teacher for Class 10 / Div A?",
             "cap": {"teachers_for_class"}, "kind": {"table"}, "outcome": "CORRECT",
             "expect_text": ["Homeroom"], "forbid_text": ["Class Teacher", "Form Tutor"]},
        ],
    },
    # ── §6 configured terminology via NATURAL language (not pack labels) ──────────────────
    {
        "id": "dev-natural-A", "pack": "A", "role": "principal",
        "note": "§6 'who handles' -> responsible teacher concept, School A",
        "turns": [
            {"text": "who handles Class 10 A?",
             "cap": {"teachers_for_class"}, "kind": {"table", "guide", "clarify"},
             "outcome": "CORRECT", "soft": True},
        ],
    },
    {
        "id": "dev-natural-B", "pack": "B", "role": "principal",
        "note": "§6 'who looks after' under School B surfaces Form Tutor if it maps",
        "turns": [
            {"text": "who looks after Class 10 A?",
             "cap": {"teachers_for_class"}, "kind": {"table", "guide", "clarify"},
             "outcome": "CORRECT", "soft": True,
             "forbid_text": ["Class Teacher", "Homeroom"]},
        ],
    },
    # ── §5 SAME wording, DIFFERENT school semantics: attendance % ────────────────────────
    {
        "id": "dev-att-A", "pack": "A", "role": "principal",
        "note": "§5/§11 ARM0242 attendance under School A policy = 100%",
        "turns": [
            {"text": "what is the attendance percentage for ARM0242?",
             "cap": {"student_attendance"}, "kind": {"metrics"}, "outcome": "CORRECT",
             "entity": ("student", "ARM0242"), "expect_text": ["100"]},
        ],
    },
    {
        "id": "dev-att-B", "pack": "B", "role": "principal",
        "note": "§5/§11 identical wording, School B late@0.5 = 90%",
        "turns": [
            {"text": "what is the attendance percentage for ARM0242?",
             "cap": {"student_attendance"}, "kind": {"metrics"}, "outcome": "CORRECT",
             "entity": ("student", "ARM0242"), "expect_text": ["90"]},
        ],
    },
    {
        "id": "dev-att-C", "pack": "C", "role": "principal",
        "note": "§5/§11 School C half_day excluded; this student has none -> 100%",
        "turns": [
            {"text": "how is ARM0242 doing on attendance?",
             "cap": {"student_attendance"}, "kind": {"metrics"}, "outcome": "CORRECT",
             "entity": ("student", "ARM0242"), "expect_text": ["100"]},
        ],
    },
    # ── §7 SchoolPack term leakage: switch pack between conversations (runner enforces) ───
    #   (isolation is verified by running the SAME text under A then B and asserting terms;
    #    each conversation is independent, so a leak would surface as the wrong term.)
    {
        "id": "dev-leak-B-after-A", "pack": "B", "role": "principal",
        "note": "§7 School B must NOT reuse School A's 'Class Teacher'",
        "turns": [
            {"text": "who is the class teacher?",
             "kind": {"table", "guide", "clarify", "not_found"}, "outcome": "CORRECT",
             "soft": True, "forbid_text": ["Class Teacher"]},
        ],
    },
    # ── §8 entity resolution across packs (real sections; format-independent) ─────────────
    {
        "id": "dev-entity-C", "pack": "C", "role": "principal",
        "note": "§8 class label resolves under Div format",
        "turns": [
            {"text": "show the student list for Class 10 / Div A",
             "cap": {"class_roster"}, "kind": {"table"}, "outcome": "CORRECT"},
        ],
    },
    {
        "id": "dev-entity-indirect", "pack": "A", "role": "principal",
        "note": "§8 indirect reference: her class",
        "turns": [
            {"text": "which class is ARM0218 in?",
             "cap": {"student_profile"}, "entity": ("student", "ARM0218"), "outcome": "CORRECT"},
            {"text": "who teaches her class?",
             "cap": {"teachers_for_class"}, "kind": {"table"}, "outcome": "CORRECT",
             "note": "class derived from ARM0218 context"},
        ],
    },
    # ── §9 derivation across packs: student -> class -> teacher assignment ────────────────
    {
        "id": "dev-derive-B", "pack": "B", "role": "principal",
        "note": "§9 who teaches the class ARM0242 is in (School B)",
        "turns": [
            {"text": "who teaches the class ARM0242 is in?",
             "cap": {"teachers_for_class"}, "kind": {"table"}, "outcome": "CORRECT",
             "derive": True, "forbid_text": ["Class Teacher", "Homeroom"]},
        ],
    },
    # ── §10 grading tests (active pack; honest if unconfigured) ───────────────────────────
    {
        "id": "dev-grade-A", "pack": "A", "role": "principal",
        "note": "§10 grade question, School A grading configured",
        "turns": [
            {"text": "what grade did ARM0242 get?",
             "cap": {"student_marks", "class_results"}, "kind": {"table"}, "outcome": "CORRECT",
             "entity": ("student", "ARM0242")},
        ],
    },
    {
        "id": "dev-grade-score-C", "pack": "C", "role": "principal",
        "note": "§10 how is score represented (School C bands: Distinction/Merit/Pass/Fail)",
        "turns": [
            {"text": "how is ARM0242's score represented?",
             "cap": {"student_marks"}, "kind": {"table"}, "outcome": "CORRECT",
             "entity": ("student", "ARM0242")},
        ],
    },
    # ── §12 temporal: school-specific academic-period words ──────────────────────────────
    {
        "id": "dev-temporal-month", "pack": "A", "role": "principal",
        "note": "§12 attendance this month (current)",
        "turns": [
            {"text": "attendance for ARM0242 this month",
             "cap": {"student_attendance"}, "temporality": "CURRENT", "outcome": "CORRECT",
             "entity": ("student", "ARM0242")},
        ],
    },
    {
        "id": "dev-temporal-semester-B", "pack": "B", "role": "principal",
        "note": "§12 'this semester' — School B configures Semester; do not equate to Term blindly",
        "turns": [
            {"text": "how much did we collect this semester?",
             "cap": {"fee_collection_period", "fee_collection"},
             "kind": {"metrics", "guide", "clarify"}, "outcome": "CORRECT", "soft": True},
        ],
    },
    # ── §13 historical safety under each pack (no current-state substitution) ─────────────
    {
        "id": "dev-hist-A", "pack": "A", "role": "principal",
        "note": "§13 who WAS responsible last year -> blocked (no history model)",
        "turns": [
            {"text": "who was the class teacher for Class 10 A last year?",
             "temporality": "PAST", "kind": {"not_found", "guide"},
             "outcome": "HONESTLY_UNSUPPORTED", "critical": True},
        ],
    },
    {
        "id": "dev-hist-C", "pack": "C", "role": "principal",
        "note": "§13 which class was this student in last year -> blocked",
        "turns": [
            {"text": "which class was ARM0218 in last year?",
             "temporality": "PAST", "kind": {"not_found", "guide"},
             "outcome": "HONESTLY_UNSUPPORTED", "critical": True},
        ],
    },
    # ── §14 conversational multi-turn (universal state) ──────────────────────────────────
    {
        "id": "dev-conv-marks", "pack": "A", "role": "principal",
        "note": "§14 marks -> subject -> ranking (derived class)",
        "turns": [
            {"text": "show ARM0242's marks",
             "cap": {"student_marks"}, "entity": ("student", "ARM0242"), "kind": {"table"},
             "outcome": "CORRECT"},
            {"text": "what about Mathematics?",
             "cap": {"student_marks"}, "entity": ("student", "ARM0242"), "outcome": "CORRECT"},
            {"text": "who scored highest?",
             "cap": {"subject_toppers", "class_results"}, "kind": {"table"}, "derive": True,
             "outcome": "CORRECT"},
        ],
    },
    {
        "id": "dev-conv-marks-B", "pack": "B", "role": "principal",
        "note": "§14 same chain under School B (conversation state is universal)",
        "turns": [
            {"text": "show ARM0242's marks",
             "cap": {"student_marks"}, "entity": ("student", "ARM0242"), "kind": {"table"},
             "outcome": "CORRECT"},
            {"text": "what about English?",
             "cap": {"student_marks"}, "entity": ("student", "ARM0242"), "outcome": "CORRECT"},
        ],
    },
    # ── §15 temporal follow-up (month change; meaning stays) ─────────────────────────────
    {
        "id": "dev-temporal-followup", "pack": "A", "role": "principal",
        "note": "§15 fees August -> September; concept fixed, time changes",
        "turns": [
            {"text": "fee collection in August",
             "cap": {"fee_collection_period"}, "temporality": "PAST", "kind": {"metrics"},
             "outcome": "CORRECT"},
            {"text": "what about September?",
             "cap": {"fee_collection_period"}, "temporality": "PAST", "outcome": "CORRECT",
             "note": "keep fees+collection, swap month"},
        ],
    },
    # ── §16 composition (planner composes; not special-purpose caps) ─────────────────────
    {
        "id": "dev-compose-fee-att", "pack": "A", "role": "principal",
        "note": "§16 low attendance + outstanding fees",
        "turns": [
            {"text": "show students with attendance below 80% who also have outstanding fees",
             "cap": {"compose", "low_attendance_students", "students_fee_pending_over"},
             "kind": {"table", "guide"}, "outcome": "CORRECT", "soft": True},
        ],
    },
    {
        "id": "dev-compose-rank", "pack": "B", "role": "principal",
        "note": "§16 highest-scoring Maths students with attendance (School B)",
        "turns": [
            {"text": "show the top scoring students in Class 10 A with their attendance",
             "cap": {"compose", "class_results", "subject_toppers"},
             "kind": {"table", "guide"}, "outcome": "CORRECT", "soft": True},
        ],
    },
    # ── §17 role-based cross-school ──────────────────────────────────────────────────────
    {
        "id": "dev-role-teacher-own", "pack": "A", "role": "teacher",
        "note": "§17 teacher6 teaches 10A -> allowed",
        "turns": [
            {"text": "show results for Class 10 A",
             "cap": {"class_results"}, "kind": {"table"}, "outcome": "CORRECT"},
        ],
    },
    {
        "id": "dev-role-teacher-other", "pack": "A", "role": "teacher",
        "note": "§17 teacher6 does NOT teach 9A -> honest refusal (no leak)",
        "turns": [
            {"text": "show results for Class 9 A",
             "kind": {"not_found", "guide", "clarify"}, "outcome": "HONESTLY_UNSUPPORTED",
             "critical": True},
        ],
    },
    {
        "id": "dev-role-parent", "pack": "B", "role": "parent",
        "note": "§17 parent sees own child ARM0242",
        "turns": [
            {"text": "how is my child doing on attendance?",
             "cap": {"student_attendance"}, "kind": {"metrics", "guide", "clarify"},
             "outcome": "CORRECT", "soft": True},
        ],
    },
    {
        "id": "dev-role-parent-other", "pack": "B", "role": "parent",
        "note": "§17 parent CANNOT read another student",
        "turns": [
            {"text": "show ARM0218's marks",
             "kind": {"not_found", "guide", "clarify"}, "outcome": "HONESTLY_UNSUPPORTED",
             "critical": True},
        ],
    },
    {
        "id": "dev-role-student-self", "pack": "C", "role": "student",
        "note": "§17 student self",
        "turns": [
            {"text": "show my marks",
             "kind": {"table", "guide", "clarify"}, "outcome": "CORRECT", "soft": True},
        ],
    },
    {
        "id": "dev-role-student-other", "pack": "C", "role": "student",
        "note": "§17 student cannot read another student",
        "turns": [
            {"text": "what are ARM0218's marks?",
             "kind": {"not_found", "guide", "clarify"}, "outcome": "HONESTLY_UNSUPPORTED",
             "critical": True},
        ],
    },
    {
        "id": "dev-role-incharge", "pack": "A", "role": "class_incharge",
        "note": "§17 class incharge of 10A can see their class roster",
        "turns": [
            {"text": "give me the roster for Class 10 A",
             "cap": {"class_roster"}, "kind": {"table"}, "outcome": "CORRECT"},
        ],
    },
    # ── §19 missing configuration honesty (minimal pack: no grading) ─────────────────────
    {
        "id": "dev-missing-grade", "pack": "MIN", "role": "principal",
        "note": "§19 minimal pack has no grading configured -> must not borrow another pack",
        "turns": [
            {"text": "what letter grade does ARM0242 have overall?",
             "kind": {"table", "guide", "not_found", "clarify"}, "outcome": "CORRECT",
             "soft": True, "forbid_text": ["Distinction", "Merit"]},
        ],
    },
    # ── extra derivation phrasings (§9 robustness, one pack) ──────────────────────────────
    {
        "id": "dev-derive-phrasings", "pack": "A", "role": "principal",
        "note": "§9 varied phrasings all derive the class",
        "turns": [
            {"text": "attendance of ARM0242's class today",
             "cap": {"class_attendance_today"}, "kind": {"metrics", "table", "guide"},
             "outcome": "CORRECT", "soft": True, "derive": True},
        ],
    },
]

# ── Holdout set (spec §21: ~30%; run ONCE after fixes; never tuned against) ────────────────

HOLDOUT_CONVERSATIONS = [
    {
        "id": "hold-responsible-C", "pack": "C", "role": "principal",
        "note": "§4 responsible teacher, School C, natural",
        "turns": [
            {"text": "who is in charge of Class 9 B?",
             "cap": {"teachers_for_class"}, "kind": {"table", "guide", "clarify"},
             "outcome": "CORRECT", "soft": True, "forbid_text": ["Class Teacher", "Form Tutor"]},
        ],
    },
    {
        "id": "hold-att-B", "pack": "B", "role": "principal",
        "note": "§5/§11 attendance under School B late@0.5 for ARM0242 = 90%",
        "turns": [
            {"text": "give me ARM0242's attendance rate",
             "cap": {"student_attendance"}, "kind": {"metrics"}, "outcome": "CORRECT",
             "entity": ("student", "ARM0242"), "expect_text": ["90"]},
        ],
    },
    {
        "id": "hold-att-A", "pack": "A", "role": "principal",
        "note": "§5/§11 same student, School A all-counted = 100%",
        "turns": [
            {"text": "give me ARM0242's attendance rate",
             "cap": {"student_attendance"}, "kind": {"metrics"}, "outcome": "CORRECT",
             "entity": ("student", "ARM0242"), "expect_text": ["100"]},
        ],
    },
    {
        "id": "hold-leak-C-after-B", "pack": "C", "role": "principal",
        "note": "§7 School C must not reuse Form Tutor/Class Teacher",
        "turns": [
            {"text": "who is the form tutor here?",
             "kind": {"table", "guide", "clarify", "not_found"}, "outcome": "CORRECT",
             "soft": True, "forbid_text": ["Class Teacher"]},
        ],
    },
    {
        "id": "hold-entity-indirect", "pack": "B", "role": "principal",
        "note": "§8 pronoun 'that group' after naming a class",
        "turns": [
            {"text": "results for Class 10 A",
             "cap": {"class_results"}, "kind": {"table"}, "outcome": "CORRECT"},
            {"text": "who is responsible for that group?",
             "cap": {"teachers_for_class"}, "kind": {"table", "guide", "clarify"},
             "outcome": "CORRECT", "soft": True},
        ],
    },
    {
        "id": "hold-derive-C", "pack": "C", "role": "principal",
        "note": "§9 derivation under School C",
        "turns": [
            {"text": "who teaches the class where ARM0242 studies?",
             "cap": {"teachers_for_class"}, "kind": {"table"}, "outcome": "CORRECT",
             "derive": True, "forbid_text": ["Class Teacher", "Form Tutor"]},
        ],
    },
    {
        "id": "hold-grade-B", "pack": "B", "role": "principal",
        "note": "§10 did the student receive a grade (School B)",
        "turns": [
            {"text": "did ARM0242 receive a grade?",
             "cap": {"student_marks", "class_results"}, "kind": {"table", "guide"},
             "outcome": "CORRECT", "soft": True, "entity": ("student", "ARM0242")},
        ],
    },
    {
        "id": "hold-temporal-year", "pack": "A", "role": "principal",
        "note": "§12 attendance this academic year (current AY)",
        "turns": [
            {"text": "ARM0242 attendance this academic year",
             "cap": {"student_attendance"}, "outcome": "CORRECT", "entity": ("student", "ARM0242")},
        ],
    },
    {
        "id": "hold-hist-B", "pack": "B", "role": "principal",
        "note": "§13 historical under School B -> blocked",
        "turns": [
            {"text": "who was responsible for Class 10 A last year?",
             "temporality": "PAST", "kind": {"not_found", "guide"},
             "outcome": "HONESTLY_UNSUPPORTED", "critical": True},
        ],
    },
    {
        "id": "hold-conv-fees", "pack": "C", "role": "principal",
        "note": "§14/§15 fees August -> and the month after, under School C",
        "turns": [
            {"text": "how much did we collect in August?",
             "cap": {"fee_collection_period"}, "temporality": "PAST", "kind": {"metrics"},
             "outcome": "CORRECT"},
            {"text": "and the following month?",
             "cap": {"fee_collection_period"}, "temporality": "PAST", "outcome": "CORRECT",
             "soft": True},
        ],
    },
    {
        "id": "hold-role-teacher-scope", "pack": "B", "role": "teacher",
        "note": "§17/§18 teacher6 out-of-scope class denied under School B",
        "turns": [
            {"text": "show me the roster for Class 8 A",
             "kind": {"not_found", "guide", "clarify"}, "outcome": "HONESTLY_UNSUPPORTED",
             "critical": True},
        ],
    },
    {
        "id": "hold-compose", "pack": "A", "role": "principal",
        "note": "§16 fresh compositional question",
        "turns": [
            {"text": "which students in Class 10 A have the lowest attendance?",
             "cap": {"compose", "low_attendance_students", "class_results"},
             "kind": {"table", "guide"}, "outcome": "CORRECT", "soft": True},
        ],
    },
    {
        "id": "hold-missing-grade-min", "pack": "MIN", "role": "principal",
        "note": "§19 minimal pack: no grading -> no borrowed bands",
        "turns": [
            {"text": "what is ARM0242's overall grade band?",
             "kind": {"table", "guide", "not_found", "clarify"}, "outcome": "CORRECT",
             "soft": True, "forbid_text": ["Distinction", "Merit", "Pass", "Fail"]},
        ],
    },
    {
        "id": "hold-natural-responsible-A", "pack": "A", "role": "principal",
        "note": "§6 'who is responsible for this class' with class named",
        "turns": [
            {"text": "who is responsible for Class 9 B?",
             "cap": {"teachers_for_class"}, "kind": {"table", "guide", "clarify"},
             "outcome": "CORRECT", "soft": True, "forbid_text": ["Form Tutor", "Homeroom"]},
        ],
    },
]

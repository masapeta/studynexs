# StudyNexs — Data Model Reference

> **Source of truth:** `apps/api/app/db/models/` (32 model files, ~50 tables).
> Generated from the model layer on 2026-07-30. Regenerate when models change —
> this document describes what exists, not what is planned.
>
> **Base conventions (see Appendix H of the constitution):**
> - Every model inherits `BaseModel`: UUID `id` PK + tz-aware `created_at`/`updated_at`.
> - Every tenant-owned table carries a non-null, indexed `school_id` FK → `schools.id`
>   (omitted from the diagrams below for readability — assume it everywhere).
> - Money is `Numeric`/`Decimal`. Enums are Python `str` enums.

---

## Master overview — the academic loop

The compounding loop the product is built around, as it exists in the schema:

```mermaid
erDiagram
    schools ||--o{ users : "tenant root"
    users ||--o| students : "is-a"
    users ||--o| teachers : "is-a"
    users ||--o| parents : "is-a"
    students }o--|| classes : "enrolled in"
    classes ||--o{ subjects : "offers"

    curriculum_packs ||--o{ curriculum_chapters : "contains"
    curriculum_chapters ||--o{ curriculum_topics : "contains"
    curriculum_topics ||--o{ curriculum_concepts : "contains"

    curriculum_packs ||--o{ question_papers : "grounds"
    question_papers ||--o{ question_bank_items : "split into"
    question_bank_items ||--o| rubric_bank_items : "has rubric"
    question_papers ||--o{ exams : "source paper"
    exams ||--o{ exam_marks : "records"
    exams ||--o{ answer_sheet_evaluations : "evaluates"
    answer_sheet_evaluations ||--o{ misconception_entries : "feeds"

    exam_marks }o..o{ student_topic_mastery : "topic string-match (C.4 gap)"
    student_topic_mastery ||--o{ mastery_flags : "raises"

    curriculum_packs ||--o{ concept_cards : "approves"
    concept_cards }o..o{ students : "tutors (mistake recovery)"

    students ||--o{ student_fee_records : "owes"
    student_fee_records }o--|| fee_receipts : "paid via"
```

> ⚠ The dotted `exam_marks → student_topic_mastery` edge is the known
> **two-spine gap**: `exams.topic` and `student_topic_mastery.topic` are
> free-text strings joined by title matching, not FKs into
> `curriculum_concepts`. See
> `docs/product/learning-intelligence/TOPIC_ID_MASTERY_SPINE_UNIFICATION_DESIGN_BRIEF.md`.

---

## 1. Tenant & identity

```mermaid
erDiagram
    schools {
        uuid id PK
        string name
        string code
        string tenant_slug UK
        string board
        jsonb address
        jsonb settings
        jsonb enabled_modules
        jsonb subscription
        string logo_url
        bool is_active
        string tenant_kind "real | demo"
        datetime expires_at "demo expiry"
        string demo_session_token_hash
    }
    users {
        uuid id PK
        uuid school_id FK
        string username
        string mobile
        string email
        string full_name
        enum role "super_admin|admin|class_incharge|teacher|parent|student|operations"
        string password_hash
        bool is_active
    }
    teachers {
        uuid id PK
        uuid school_id FK
        uuid user_id FK
        string employee_id
        string qualification
        string department
        date joining_date
    }
    students {
        uuid id PK
        uuid school_id FK
        uuid user_id FK
        uuid class_id FK
        string admission_no
        string roll_no
        date date_of_birth
        enum gender
        string blood_group
        date admission_date
        string apaar_number
    }
    parents {
        uuid id PK
        uuid school_id FK
        uuid user_id FK
        enum relationship_type
    }
    student_parent_map {
        uuid student_id FK
        uuid parent_id FK
        bool is_primary
    }

    schools ||--o{ users : ""
    users ||--o| teachers : ""
    users ||--o| students : ""
    users ||--o| parents : ""
    students ||--o{ student_parent_map : ""
    parents ||--o{ student_parent_map : ""
```

## 2. Academic structure

```mermaid
erDiagram
    academic_years {
        uuid id PK
        string year_label
        string start_date
        string end_date
        bool is_active
    }
    classes {
        uuid id PK
        string grade
        string section
        uuid academic_year_id FK
        uuid class_incharge_id FK "-> users"
        string room_number
    }
    subjects {
        uuid id PK
        string name
        string code
        uuid class_id FK "subject is per-class"
    }
    teacher_subject_mappings {
        uuid teacher_id FK "-> users"
        uuid subject_id FK
        uuid class_id FK
        bool is_primary
    }
    timetable_slots {
        uuid class_id FK
        uuid subject_id FK
        uuid teacher_id FK "-> users"
        enum day_of_week
        int period_number
        string start_time
        string end_time
    }
    attendance {
        uuid student_id FK
        uuid class_id FK
        date date
        enum status "present|absent|late|half_day"
        uuid marked_by FK "-> users"
        string remarks
    }

    academic_years ||--o{ classes : ""
    classes ||--o{ subjects : ""
    classes ||--o{ teacher_subject_mappings : ""
    subjects ||--o{ teacher_subject_mappings : ""
    classes ||--o{ timetable_slots : ""
    subjects ||--o{ timetable_slots : ""
    classes ||--o{ attendance : ""
```

## 3. Curriculum Intelligence (the grounding spine)

```mermaid
erDiagram
    curriculum_packs {
        uuid id PK
        uuid class_id FK
        uuid subject_id FK
        uuid academic_year_id FK
        string board
        string book_title
        string publisher
        string edition
        int version
        enum status "draft|pending|approved|..."
        jsonb blueprint
        uuid created_by FK
        uuid approved_by FK
        datetime approved_at
        datetime rag_indexed_at
        int rag_index_topic_count
    }
    curriculum_chapters {
        uuid pack_id FK
        string number
        string title
        int order_index
    }
    curriculum_topics {
        uuid chapter_id FK
        string title
        int order_index
        jsonb concepts
    }
    curriculum_concepts {
        uuid pack_id FK
        uuid topic_id FK
        string slug
        string title
        int order_index
        enum source
    }
    curriculum_learning_outcomes {
        uuid topic_id FK
        uuid chapter_id FK
        string code
        string description
    }
    kg_edges {
        uuid pack_id FK
        enum edge_type
        enum from_node_type
        uuid from_id
        enum to_node_type
        uuid to_id
        jsonb metadata_
    }
    concept_cards {
        uuid pack_id FK
        uuid concept_id FK
        string title
        text explanation
        jsonb examples
        jsonb hints
        enum status "draft|approved|rejected"
        uuid approved_by FK
    }
    content_review_items {
        uuid pack_id FK
        enum item_type
        enum status
        enum source
        uuid concept_id FK
        jsonb draft_payload
        uuid result_card_id FK
        uuid reviewed_by FK
        string rejection_reason
    }
    document_ingestions {
        uuid pack_id FK
        uuid file_id FK
        enum doc_type
        enum status
        int version
        int chunks_indexed
        uuid ingested_by FK
    }
    curriculum_pack_audit_events {
        uuid pack_id FK
        uuid actor_id FK
        string event_type
        jsonb event_metadata
    }

    curriculum_packs ||--o{ curriculum_chapters : ""
    curriculum_chapters ||--o{ curriculum_topics : ""
    curriculum_topics ||--o{ curriculum_concepts : ""
    curriculum_topics ||--o{ curriculum_learning_outcomes : ""
    curriculum_packs ||--o{ kg_edges : "scoped to"
    curriculum_packs ||--o{ concept_cards : ""
    curriculum_concepts ||--o{ concept_cards : ""
    curriculum_packs ||--o{ content_review_items : ""
    content_review_items }o--o| concept_cards : "produces"
    curriculum_packs ||--o{ document_ingestions : ""
    curriculum_packs ||--o{ curriculum_pack_audit_events : ""
```

## 4. Assessment & evaluation

```mermaid
erDiagram
    question_papers {
        uuid id PK
        uuid class_id FK
        uuid subject_id FK
        uuid pack_id FK
        bool grounded
        jsonb grounding_sources
        string ungrounded_reason
        string board
        string grade
        enum exam_type
        float total_marks
        jsonb sections
        enum status "draft|submitted|approved|rejected"
        uuid approved_by FK
        uuid rejected_by FK
        string rejection_reason
        string ai_model
    }
    question_bank_items {
        uuid id PK
        uuid source_paper_id FK
        string section_title
        string question_number
        text question_text
        float marks
        string question_type
        jsonb options
        jsonb topics
        enum source
        string approval_status
        string content_fingerprint "dedup"
        int usage_count
        jsonb used_in_paper_ids
    }
    rubric_bank_items {
        uuid question_bank_item_id FK
        text answer_key
        jsonb step_wise_marking
        jsonb acceptable_answers
        jsonb common_wrong_answers
        text teacher_correction_note
    }
    exams {
        uuid id PK
        uuid class_id FK
        uuid subject_id FK
        enum exam_type "FA1-4 | SA1-2 | ..."
        string title
        float total_marks
        date date
        string topic "String(120) free-text — C.4 gap"
        jsonb question_schema "per-question marks+topic"
        uuid source_paper_id FK
    }
    exam_marks {
        uuid exam_id FK
        uuid student_id FK
        float marks_obtained
        jsonb question_marks
        string grade_letter
        text ai_feedback
        bool ai_graded
    }
    answer_sheet_evaluations {
        uuid id PK
        uuid exam_id FK
        uuid student_id FK
        uuid file_id FK
        uuid job_id FK
        jsonb input_answers
        string status
        jsonb ai_suggestions "AEI draft"
        jsonb teacher_overrides "HITL record"
        uuid approved_by FK
        datetime approved_at
    }
    report_cards {
        uuid student_id FK
        uuid class_id FK
        jsonb subjects
        float total_obtained
        float percentage
        string overall_grade
        text ai_remark
        enum status
    }

    question_papers ||--o{ question_bank_items : "split into"
    question_bank_items ||--o| rubric_bank_items : ""
    question_papers ||--o{ exams : "source"
    exams ||--o{ exam_marks : ""
    exams ||--o{ answer_sheet_evaluations : ""
```

## 5. Learning intelligence

```mermaid
erDiagram
    student_topic_mastery {
        uuid student_id FK
        uuid class_id FK
        uuid subject_id FK
        uuid academic_year_id FK
        string topic "free-text — C.4 gap"
        string topic_display
        float mastery_pct
        float class_avg_pct
        int assessments_count
        enum trend
        jsonb history
    }
    mastery_flags {
        uuid student_id FK
        string topic
        enum severity
        enum status
        jsonb reasons
        jsonb evidence
        text narrative
        uuid reviewed_by FK
        string dismissed_reason
        datetime notified_at
    }
    misconception_entries {
        uuid class_id FK
        uuid subject_id FK
        string topic
        string question_no
        text common_mistake
        text remedial_activity
        uuid source_evaluation_id FK
        string content_fingerprint "dedup"
        int occurrence_count
    }
    lesson_plans {
        uuid class_id FK
        uuid subject_id FK
        string title
        string chapter
        string topic
        jsonb segments
        jsonb learning_objectives
        enum status
        uuid pack_id FK
        bool grounded
        jsonb grounding_sources
    }

    student_topic_mastery ||--o{ mastery_flags : "low mastery raises"
```

## 6. Finance

```mermaid
erDiagram
    fee_structures {
        uuid class_id FK
        enum fee_type
        decimal amount
        enum frequency
        uuid academic_year_id FK
        int due_day
    }
    student_fee_records {
        uuid student_id FK
        uuid fee_structure_id FK
        decimal amount
        date due_date
        enum status
        decimal paid_amount
        enum payment_mode
        string razorpay_order_id
        string razorpay_payment_id
        uuid receipt_id FK
    }
    fee_receipts {
        string receipt_number UK
        uuid student_id FK
        decimal amount_paid
        enum payment_mode
        string transaction_id
        string idempotency_key "no double-charge"
        string school_name "denormalized snapshot"
        string student_name "denormalized snapshot"
        string pdf_url
        int receipt_sequence
    }
    receipt_counters {
        uuid school_id FK
        int last_sequence
        string prefix
    }
    school_expenses {
        string vendor
        string category
        decimal amount
        date expense_date
        uuid receipt_file_id FK
    }
    staff_payroll_entries {
        uuid user_id FK
        date period_month
        decimal gross_amount
        enum status
        datetime paid_at
    }

    fee_structures ||--o{ student_fee_records : ""
    student_fee_records }o--o| fee_receipts : ""
```

## 7. School operations

```mermaid
erDiagram
    admission_candidates {
        string name
        string grade_applied
        enum stage
        date enquiry_date
        string parent_name
        string parent_mobile
        string aadhaar_number "encrypted at rest"
        string apaar_number
        jsonb stage_details
    }
    staff_profiles {
        uuid user_id FK
        string first_name
        string last_name
        string aadhaar_number "encrypted at rest"
        string qualification
        string employee_id
        uuid aadhaar_document_file_id FK
        uuid experience_document_file_id FK
    }
    transport_routes {
        string route_name
        string vehicle_number
        string driver_name
        jsonb stops
        int capacity
    }
    student_transport {
        uuid student_id FK
        uuid route_id FK
        string boarding_stop
    }
    library_books {
        string title
        string author
        string isbn
        int total_copies
        int available_copies
    }
    library_issues {
        uuid book_id FK
        uuid user_id FK
        date due_date
        datetime returned_at
        decimal fine_amount
        enum status
    }
    events {
        string title
        date event_date
        time event_time
        string venue
        jsonb target_roles
    }
    residential_blocks {
        string block_name
        enum block_gender
        string warden_name
        int total_rooms
    }
    room_allocations {
        uuid student_id FK
        uuid block_id FK
        string room_number
    }

    transport_routes ||--o{ student_transport : ""
    library_books ||--o{ library_issues : ""
    residential_blocks ||--o{ room_allocations : ""
```

## 8. Communication

```mermaid
erDiagram
    notices {
        string title
        text content
        jsonb target_roles
        enum audience
        enum priority
        bool is_ai_generated
        uuid class_id FK
        datetime expires_at
    }
    notice_read_receipts {
        uuid notice_id FK
        uuid user_id FK
        datetime read_at
    }
    notifications {
        uuid school_id FK "tenant-scoped"
        uuid user_id FK
        string title
        text body
        enum channel
        string link
        bool is_read
    }

    notices ||--o{ notice_read_receipts : ""
```

## 9. AI platform & plumbing

```mermaid
erDiagram
    ai_usage {
        string feature
        string provider
        string model
        int tokens_in
        int tokens_out
        decimal cost_usd
        int latency_ms
        int credits_charged
        string ref_type
        uuid ref_id
        int image_count
        string primary_provider
        bool used_fallback
    }
    ai_feedback {
        string feature
        string ref_type
        string ref_id
        string rating
        text note
    }
    uploaded_files {
        string filename
        string original_name
        string content_type
        int size_bytes
        enum category
        string storage_path
        string url
        uuid uploaded_by FK
    }
    jobs {
        string type
        enum status
        jsonb params
        jsonb result
        text error
    }
    outbox_events {
        string event_type
        jsonb payload
        string target_module
        enum status
        int retry_count
        datetime processed_at
    }
    audit_logs {
        uuid school_id FK "nullable"
        uuid user_id FK "nullable"
        string action
        string resource_type
        string resource_id
        jsonb details
        string ip_address
        string user_agent
    }
```

---

## Design notes (structural read, 2026-07-30)

1. **The compounding loop is fully modeled** — pack → paper → bank items →
   exam → evaluation → misconceptions → mastery → flags → concept cards →
   tutor. The moat exists at schema level, not just in docs.
2. **Known gap (C.4):** `exams.topic` and `student_topic_mastery.topic` are
   free-text strings; the concept spine (`curriculum_concepts`) is joined only
   by title string-matching. Unification design brief exists; Phase A passive
   resolution is certified; deeper persistence (Phase B) is a deferred gate.
3. **HITL is schema-level:** `approved_by/at`, `status`, `teacher_overrides`,
   `rejection_reason` appear consistently on papers, evaluations, packs,
   cards, flags, and content-review items.
4. **Money discipline holds:** all currency columns are `Decimal`; receipts
   carry idempotency keys, per-tenant counters, and denormalized snapshots.
5. **`kg_edges` is a generic any-node → any-node graph table** — the seam for
   PREREQUISITE edges when that work is authorized.
6. **JSONB used pragmatically** (`question_schema`, `sections`, `evidence`,
   `history`, `stage_details`); fields that become query targets at scale
   (e.g. `question_bank_items.topics`) are candidates for promotion to real
   columns.

---

## DM-4 design brief — Subject identity (design-only, 2026-07-31)

Status: **Proposed — implementation folded into Topic-ID/Mastery Spine Phase B.**
No code or migration is authorized by this brief.

### Problem

`subjects` rows are scoped to a single class (`class_id` FK), and classes are
scoped to a single academic year. "Mathematics" therefore fragments into a
distinct row per **section per year**: Grade 8A 2026–27 Mathematics,
Grade 8B 2026–27 Mathematics, and Grade 8A 2027–28 Mathematics are three
unrelated UUIDs. Nine tables key on `subject_id` (packs, exams, mastery,
misconceptions, question bank, papers, lesson plans, timetable, teacher
mappings), so every longitudinal or cross-section question — "how is
Mathematics mastery trending across Grade 8?", "reuse last year's approved
Mathematics items" — currently requires name string-matching, the same defect
class as the free-text topic spine (C.4).

### Proposed shape (expand-then-contract)

1. **Expand:** add a school-scoped `subject_catalog` table
   (`school_id`, `name`, `code`, optional board-subject mapping;
   unique on `(school_id, name)`), and a nullable
   `subjects.catalog_id` FK → `subject_catalog.id`.
2. **Backfill:** normalize existing `subjects.name` values per school
   (trim/case-fold), create one catalog row per distinct name, link every
   subject row. Ambiguities (e.g. "Maths" vs "Mathematics") are surfaced for
   human resolution, never auto-merged.
3. **Dual-write:** subject creation paths set `catalog_id` (creating the
   catalog row on first use). Per-class `subjects` rows remain — they are the
   correct grain for timetable/teacher mapping; the catalog is the identity
   layer above them.
4. **Switch reads:** longitudinal consumers (mastery aggregation, question-bank
   retrieval, pack lineage, analytics) group by `catalog_id` instead of
   name matching.
5. **Contract (much later):** enforce `catalog_id NOT NULL` once all writers
   are dual-writing and the backfill is verified per tenant.

### Why folded into Spine Phase B

The topic spine (`exam.topic` → `topic_id`) and subject identity are the same
disease — string identity where the model needs stable IDs — and share the
same consumers (mastery, retrieval, analytics). Fixing them in one Phase B
batch avoids touching the mastery unique constraints
(`student_id, subject_id, academic_year_id, topic`) twice.

### Risks / open questions for Phase B

- Mastery unique constraints embed `subject_id`; re-keying reads to
  `catalog_id` must not merge mastery rows across sections silently —
  aggregation happens at read time, storage grain stays per-class.
- Cross-year concept mapping (pack versioning) should reference `catalog_id`
  so a book-edition change doesn't orphan subject lineage.
- Tenant-scoped throughout; catalog rows carry `school_id` like every other
  tenant-owned table.

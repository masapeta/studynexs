# Assessment Intelligence v1.0 Batch G-B Implementation Authorization Contract

> Owner: Avinash Reddy Masapeta (ARM)
> Date: 2026-07-29
> Status: Accepted
> Authorization ID: ASSESSMENT-V1-BATCH-G-B-AUTH-001
> Implementation authorization: Authorized for Batch G-B only
> Runtime behavior changes: Not authorized

---

## 1. Purpose

Authorize the narrow implementation required to make the Assessment
Intelligence v1.0 Batch G browser proof reproducible through a deterministic
Reference tenant fixture.

This contract authorizes reproducibility infrastructure only. It does not
authorize product behavior changes.

---

## 2. Authorized implementation scope

Batch G-B may implement:

1. An idempotent Reference tenant fixture seed script.
2. A deterministic Grade 6 Science approved question paper fixture.
3. A linked Unit Test exam fixture with question schema.
4. Focused fixture tests.
5. Browser proof harness guidance for running the fixture prerequisite.
6. Certification report updates for reproducibility and browser proof closure.

The fixture may write local Reference tenant demo/proof data only when the seed
script is explicitly run.

---

## 3. Repository boundary

Authorized files and directories:

- `apps/api/scripts/seed_assessment_browser_proof_fixture.py`
- `apps/api/tests/test_assessment_intelligence_v1_browser_proof_fixture.py`
- `apps/admin-web/e2e-assessment-intelligence-v1.cjs`
- `docs/product/assessment-intelligence/ASSESSMENT_INTELLIGENCE_V1_BATCH_G_B_REPRODUCIBLE_REFERENCE_FIXTURE_DESIGN_BRIEF.md`
- `docs/product/assessment-intelligence/ASSESSMENT_INTELLIGENCE_V1_BATCH_G_B_REPRODUCIBLE_REFERENCE_FIXTURE_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md`
- `docs/product/assessment-intelligence/ASSESSMENT_INTELLIGENCE_V1_BATCH_G_B_REPRODUCIBLE_REFERENCE_FIXTURE_CERTIFICATION_REPORT.md`

Post-publication `docs/STATUS.md` updates remain separate and are not part of
the implementation commit.

---

## 4. Explicit exclusions

Batch G-B does not authorize:

- database schema changes;
- Alembic migrations;
- API contract changes;
- public endpoint changes;
- UI changes;
- runtime product behavior changes;
- production startup seed changes;
- question-paper generation behavior changes;
- exam service behavior changes;
- answer-sheet evaluation behavior changes;
- AEI behavior changes;
- EUI source adoption;
- marks changes;
- teacher review routing changes;
- evidence-ledger behavior changes;
- mastery updates;
- parent/student visibility changes;
- product claim expansion;
- AI provider changes;
- LLM inference changes;
- OCR behavior changes;
- PDF ingestion behavior changes.

---

## 5. Runtime constraints

The seed script must be:

- explicit-run only;
- idempotent;
- Reference tenant scoped;
- deterministic;
- safe to rerun;
- independent of production boot;
- independent of migrations;
- independent of API/UI code paths.

It must not create authoritative academic outcomes.

---

## 6. Validation requirements

Before acceptance, produce evidence for:

- focused fixture tests;
- script syntax/import health;
- focused lint on touched Python and browser harness files;
- fixture seed execution where a local database is available;
- `npm run e2e-assessment-v1` browser proof where API/web servers are available;
- API import check;
- `git diff --check`;
- no unauthorized file changes.

---

## 7. Rollback

Rollback is simple:

- remove the fixture seed script;
- remove the focused fixture test;
- revert the browser harness guidance;
- remove Batch G-B certification documents.

No data migration rollback, API rollback, UI rollback, or feature-flag rollback
is required because no product runtime behavior changes are authorized.

---

## 8. Recommended implementation metadata

If accepted after code review:

```text
Commit: test(assessment): add reproducible reference fixture for browser proof
Tag: assessment-v1-batch-g-b-reference-fixture-browser-proof-certified
```


# Assessment Intelligence v1.0 Batch G Teacher Workflow / Browser Proof Certification Report

> Owner: Avinash Reddy Masapeta (ARM)
> Date: 2026-07-29
> Status: Certified / Browser proof passed
> Authorization: ASSESSMENT-V1-BATCH-G-AUTH-001
> Batch: G - Teacher Workflow / Browser Proof
> Runtime behavior: Unchanged
> Recommendation: Accept Batch G for commit, tag, and publication

---

## 1. Certification scope

Batch G certifies the browser-proof foundation for the supported Assessment
Intelligence v1.0 teacher workflow.

This certification covers:

- dedicated Assessment Intelligence v1.0 browser proof harness;
- deterministic supported-scope proof expectations;
- Reference tenant prerequisite detection;
- AI Papers, Exams, and Evaluation route checks;
- console/API failure guard posture;
- tenant guard posture;
- screenshot evidence capture posture;
- no-overclaim checks for bilingual/multilingual unsupported claims.

It does not certify new product behavior, UI changes, schema changes, API
changes, marks changes, evidence-ledger changes, AEI behavior changes, EUI
source adoption, or public product claim expansion.

---

## 2. Artifact inventory

| Artifact | Status |
|---|---|
| `ASSESSMENT_INTELLIGENCE_V1_BATCH_G_TEACHER_WORKFLOW_BROWSER_PROOF_DESIGN_BRIEF.md` | Present / accepted |
| `ASSESSMENT_INTELLIGENCE_V1_BATCH_G_TEACHER_WORKFLOW_BROWSER_PROOF_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md` | Present / accepted |
| `apps/admin-web/e2e-assessment-intelligence-v1.cjs` | Present |
| `apps/admin-web/package.json` | Script added |
| `ASSESSMENT_INTELLIGENCE_V1_BATCH_G_TEACHER_WORKFLOW_BROWSER_PROOF_CERTIFICATION_REPORT.md` | Present |

---

## 3. Browser proof scenario

Primary supported scope:

```text
SSC / Telangana reference material / Grade 6 / Science / Unit Test / English
```

The harness verifies:

- Reference tenant requirement;
- principal/staff login through the existing API-auth e2e pattern;
- supported-scope Reference tenant data discovery;
- AI Papers route rendering;
- Exams route rendering;
- Evaluation route rendering for a linked/evaluable exam where data exists;
- tenant header preservation;
- console/API guard posture;
- unsupported bilingual/multilingual claim absence;
- screenshot evidence capture.

---

## 4. Runtime behavior impact

| Area | Result |
|---|---|
| Runtime product behavior | Unchanged |
| Production UI pages | Unchanged |
| API contracts | Unchanged |
| Database schema | Unchanged |
| Feature flags | Unchanged |
| Question-paper generation | Unchanged |
| Exam service behavior | Unchanged |
| AEI behavior | Unchanged |
| EUI behavior | Unchanged |
| Marks | Unchanged |
| Evidence ledger | Unchanged |
| Parent/student visibility | Unchanged |
| Product claims | Unchanged |

---

## 5. Browser proof evidence

Batch G adds the proof command:

```text
npm run e2e-assessment-v1
```

Expected environment:

```text
E2E_TENANT_SLUG=reference
E2E_API_URL=http://127.0.0.1:8000
E2E_BASE_URL=http://127.0.0.1:3000
```

Screenshot output:

```text
%TEMP%/sn-assessment-v1
```

The harness intentionally fails if the Reference tenant is unavailable, the
expected supported-scope data is missing, tenant context is lost, blocking
console/API errors occur, or the browser flow cannot prove the teacher
workflow.

---

## 6. Validation evidence

Local validation completed.

```text
node --check e2e-assessment-intelligence-v1.cjs
Result: PASS

npx eslint --no-ignore e2e-assessment-intelligence-v1.cjs
Result: PASS

npm run build
Result: PASS

npm run e2e-assessment-v1
Result: PASS - 16 checks, 0 disallowed console/API errors

python -c "import app.main"
Result: PASS

python -m pytest tests/test_assessment_intelligence_v1_contract.py tests/test_assessment_intelligence_v1_blueprint_readiness.py tests/test_assessment_intelligence_v1_rubric_model_answer_readiness.py tests/test_assessment_intelligence_v1_question_bank_reuse_readiness.py tests/test_assessment_intelligence_v1_paper_to_evaluation_linkage_readiness.py tests/test_assessment_intelligence_v1_bilingual_multilingual_readiness.py
Result: PASS - 49 passed

python -m pytest tests/test_aei_v1_language_ocr_assist.py tests/test_academic_understanding_engine.py tests/test_golden_evaluation_harness.py tests/test_evaluation_policy.py
Result: PASS - 33 passed

git diff --check
Result: PASS
```

Browser proof run:

```text
E2E_BASE_URL=http://127.0.0.1:3000
E2E_API_URL=http://127.0.0.1:8000
E2E_TENANT_SLUG=reference
npm run e2e-assessment-v1

Result: PASS - ALL GREEN
```

Passing browser evidence:

- login succeeded through the existing API-token e2e pattern;
- Reference tenant Grade 6 class was found;
- Reference tenant Science subject was found;
- Reference tenant supported-scope question paper was found;
- Reference tenant linked/evaluable exam was found;
- AI Papers route rendered;
- AI Papers teacher authority posture was visible/verifiable;
- AI Papers route did not show unsupported language/product claims;
- Exams route rendered;
- Exam schema/marks actions were visible;
- Exams route did not show unsupported language/product claims;
- Evaluation route rendered for the linked/evaluable exam;
- Evaluation teacher-authority posture was visible/verifiable;
- AEI/evaluation assist path was visible/verifiable;
- Evaluation route did not show unsupported language/product claims;
- tenant header guard passed on 52 API calls;
- no disallowed console/API failures were observed.

Reference tenant proof fixture:

- question paper: `Grade 6 General Science FA-I Reference Unit Test`;
- exam: `Grade 6 General Science FA-I Reference Unit Test`;
- source material: `6th_class_-_FA-I_to_IV_Q.Papers_TG.pdf`, pages 33-34;
- source posture: local Reference tenant proof fixture, not a new production
  product claim.

Allowed console noise:

- four pre-auth/refresh-style `401 Unauthorized` resource messages were
  observed and classified by the existing harness as allowed;
- no disallowed console errors or unexpected failed API responses were observed.

---

## 7. No-overclaim posture

The Batch G browser proof harness checks that teacher-facing assessment routes
do not present unsupported bilingual/multilingual capabilities as supported.

Specifically, the proof fails if route text includes unsupported production
claims such as:

- universal multilingual assessment supported;
- automatic question-paper translation supported;
- automatic rubric translation supported;
- autonomous language grading;
- autonomous paper approval.

This preserves the Batch F language boundary.

---

## 8. Risk assessment

| Risk area | Assessment |
|---|---|
| Product behavior risk | Low - browser harness + Reference tenant proof fixture only; no production runtime changes |
| UI risk | Low - no production page edits |
| API/schema risk | Low - no API or schema edits |
| Tenant risk | Reduced - harness asserts tenant header behavior |
| Product-claim risk | Reduced - no-overclaim assertions added |
| AEI risk | Low - AEI behavior unchanged |
| EUI risk | Low - EUI behavior unchanged |
| Rollback risk | Low - remove harness and certification report; Reference tenant fixture is local/dev proof data |

---

## 9. Certification decision

Batch G implementation is ready for ARM acceptance.

The browser proof harness is implemented and passing against the local Reference
tenant proof fixture. Product runtime behavior remains unchanged.

Recommended ARM decision:

```text
Decision: Accepted
Commit: Approved
Tag: Approved
```

# AEI v1.0 Certification Report

- **Program:** Academic Evaluation Intelligence v1.0
- **Batch:** Batch F - AEI v1.0 certification
- **Classification:** Final AEI v1.0 certification report
- **Status:** Ready for ARM acceptance review
- **Date:** 2026-07-28
- **Owner:** Avinash Reddy Masapeta (ARM)
- **Architecture baseline:** [`../../architecture/AEI.md`](../../architecture/AEI.md)
- **Design baseline:** [`./AEI_V1_IMPLEMENTATION_DESIGN_BRIEF.md`](./AEI_V1_IMPLEMENTATION_DESIGN_BRIEF.md)
- **Authorization baseline:** [`./AEI_V1_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md`](./AEI_V1_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md)
- **Capability matrix:** [`./AEI_V1_SUPPORTED_SCOPE_CAPABILITY_MATRIX.md`](./AEI_V1_SUPPORTED_SCOPE_CAPABILITY_MATRIX.md)
- **Recommended commit:** `docs(aei): certify AEI v1.0 supported scope`
- **Recommended tag:** `aei-v1-certified`

---

## 1. Executive decision

AEI v1.0 is certified for the declared supported teacher-trust evaluation scope.

The certified scope includes:

- deterministic Maths normalization/equivalence metadata;
- confidence/manual-review/teacher-override metadata;
- approved-evidence metadata;
- language/OCR assist metadata;
- visual/science assist and checklist metadata;
- Golden Harness coverage for all implemented capability families;
- preservation of teacher authority and approved-evidence-only downstream
  posture.

**Certification decision:** PASS
**Runtime behavior with all AEI v1.0 feature flags OFF:** UNCHANGED
**Schema/API/UI changes in Batch F:** NONE
**Risk:** Low for certification artifact; controlled rollout remains governed by default-off flags
**Recommendation:** Accept AEI v1.0 certification and publish the certification tag.

---

## 2. Certified milestone stack

| Batch | Status | Commit | Tag |
|---|---:|---|---|
| Batch A - Maths normalization and deterministic equivalence | Published / certified | `4343b0542b68cd739162eeb47207299c428b2fd9` | `aei-v1-batch-a-maths-normalization-certified` |
| Batch B - Confidence, manual review, and teacher override | Published / certified | `d40c31e4df29a4942e48431c90b756611949ef86` | `aei-v1-batch-b-review-policy-certified` |
| Batch C - Evidence ledger and approved evidence propagation | Published / certified | `9f3589e1d98825a2abc15244879ef1b8329a6064` | `aei-v1-batch-c-evidence-ledger-certified` |
| Batch D - Language and OCR assist support boundary | Published / certified | `d33ff6d9d49d140353a848ccffe0f222e6d8ac2c` | `aei-v1-batch-d-language-ocr-assist-certified` |
| Batch E - Visual and science assist support boundary | Published / certified | `b393e83e7e0eb24c9992f28e3c6b963cdcc4586f` | `aei-v1-batch-e-visual-science-assist-certified` |
| Batch F - AEI v1.0 certification | Ready for ARM review | pending | `aei-v1-certified` |

---

## 3. Certified scope summary

| Capability family | Certification result | Notes |
|---|---:|---|
| Maths normalization | PASS | Deterministic supported cases only; no CAS/proof checking |
| Units/tolerance/scientific notation | PASS | Requires rubric/config context where relevant |
| Acceptable answers | PASS | Uses configured answer variants; no speculative matching |
| Confidence/manual review | PASS | Confidence influences workflow metadata, not marks authority |
| Teacher override audit | PASS | Override metadata preserves teacher authority |
| Evidence ledger metadata | PASS | Approved evidence is teacher-decision source-of-truth |
| Language/OCR assist | PASS | Metadata only; no universal OCR or language grading claim |
| Visual/science assist | PASS | Checklist/assist metadata only; no autonomous marks |
| Golden Harness | PASS | 35 AEI Golden cases across pilot trust and Batches A-E |
| AEI/EUI source posture | PASS | No EUI source adoption; Phase 7F remains deferred |

---

## 4. Golden Harness summary

| Dataset | Case count | Result |
|---|---:|---:|
| `pilot_trust_cases.json` | 9 | PASS |
| `batch_a_math_normalization_cases.json` | 7 | PASS |
| `batch_b_review_policy_cases.json` | 5 | PASS |
| `batch_c_approved_evidence_cases.json` | 3 | PASS |
| `batch_d_language_ocr_assist_cases.json` | 6 | PASS |
| `batch_e_visual_science_assist_cases.json` | 5 | PASS |
| **Total** | **35** | **PASS** |

Golden Harness execution is covered by:

```text
tests/test_golden_evaluation_harness.py
```

---

## 5. Runtime proof

### 5.1 Broad AEI certification test suite

Command:

```text
python -m pytest tests/test_aei_architecture.py \
  tests/test_academic_answer.py \
  tests/test_academic_understanding_engine.py \
  tests/test_academic_reasoning_result.py \
  tests/test_academic_reasoning_engine.py \
  tests/test_evaluation_policy.py \
  tests/test_teacher_review.py \
  tests/test_teacher_review_decision.py \
  tests/test_aei_passive_integration.py \
  tests/test_aei_v1_math_normalization.py \
  tests/test_aei_v1_review_policy.py \
  tests/test_aei_v1_evidence_ledger.py \
  tests/test_aei_v1_language_ocr_assist.py \
  tests/test_aei_v1_visual_science_assist.py \
  tests/test_golden_evaluation_harness.py \
  tests/test_answer_sheet_eval.py \
  tests/test_answer_sheet_vision.py \
  tests/test_evaluation_engine.py \
  tests/test_eui_consumer_aei_migration.py \
  tests/test_eui_consumer_aei_rich_evidence.py \
  tests/test_eui_consumer_aei_divergence_readiness.py \
  tests/test_eui_consumer_aei_source_readiness_candidate.py \
  tests/test_eui_consumer_aei_source_readiness_trial.py -q
```

Result:

```text
191 passed in 204.33s (0:03:24)
```

### 5.2 Static validation

Command:

```text
python -m ruff check <AEI runtime files and certification test suite>
```

Result:

```text
All checks passed!
```

### 5.3 API import

Command:

```text
python -c "import app.main; print('API_IMPORT_PASS')"
```

Result:

```text
API_IMPORT_PASS
```

### 5.4 Diff whitespace check

Command:

```text
git diff --check
```

Result:

```text
PASS
```

---

## 6. Evidence-ledger proof

PASS.

Evidence-ledger behavior is covered by:

- `tests/test_aei_v1_evidence_ledger.py`;
- `tests/test_answer_sheet_eval.py`;
- `tests/test_golden_evaluation_harness.py`.

Certified evidence:

- unapproved suggestions are not approved for downstream evidence;
- teacher-approved evaluations emit approved-evidence metadata;
- original AI suggestion remains separate from final teacher decision;
- downstream source of truth is `teacher_decision`;
- unsafe raw answer keys are excluded from approved-evidence metadata.

---

## 7. Approved-evidence downstream proof

PASS.

The certified downstream rule is:

```text
Student / parent / principal intelligence may consume only teacher-approved
evidence, not raw uncertified AI suggestions.
```

Batch C established this contract and Batch F regression confirms it remains
intact after Batches D and E.

---

## 8. Rollback proof

PASS.

All AEI v1.0 behavior-changing capabilities remain individually guarded:

```text
AEI_V1_MATH_NORMALIZATION_ENABLED=false
AEI_V1_REVIEW_POLICY_ENABLED=false
AEI_V1_EVIDENCE_LEDGER_METADATA_ENABLED=false
AEI_V1_LANGUAGE_OCR_ASSIST_ENABLED=false
AEI_V1_VISUAL_SCIENCE_ASSIST_ENABLED=false
```

Rollback posture:

- disable the relevant feature flag;
- legacy evaluation remains source of truth;
- no destructive schema change exists;
- no API/UI rollback is required;
- no parent/student exposure of uncertified metadata is introduced.

---

## 9. Browser proof

Not applicable for AEI v1.0 Batches A-F.

Reason:

- no frontend/UI files were changed;
- no teacher-facing UI surface was modified;
- no API route contract changed.

Browser proof becomes required when a future authorized batch changes
teacher-facing evaluation UI.

---

## 10. Performance proof

PASS for certification scope.

Evidence:

- broad AEI certification regression suite completed in `204.33s`;
- Batch E focused runtime additions are metadata-only and default-off;
- deterministic helpers run locally without LLM calls;
- no new network, database persistence, background workers, OCR engine, or model
  provider calls were introduced by Batches A-E.

Operational performance should be revalidated when feature flags are enabled in
staging for the declared production scope.

---

## 11. Tenant/security proof

PASS for certification scope.

Evidence:

- `tests/test_answer_sheet_eval.py` includes tenant/subject access regression
  checks for teacher correction and misconception visibility;
- no Batch F code changes introduce new data access paths;
- Batches A-E add metadata to existing tenant-scoped evaluation flows;
- no client-supplied `school_id` behavior was introduced;
- no new public API routes or UI surfaces were added.

---

## 12. Unchanged surfaces

| Surface | Status |
|---|---:|
| Database schema | UNCHANGED |
| Alembic migrations | UNCHANGED |
| Public API routes | UNCHANGED |
| Frontend/UI | UNCHANGED |
| OCR/vision provider implementation | UNCHANGED |
| LLM provider routing | UNCHANGED |
| Marks persistence model | UNCHANGED |
| Teacher approval flow | UNCHANGED |
| Parent/student surfaces | UNCHANGED |
| EUI source-of-truth posture | UNCHANGED |
| Product capability claims | UNCHANGED |

---

## 13. Explicit non-claims

AEI v1.0 certification does not claim:

- autonomous grading;
- universal OCR;
- universal language grading;
- pixel-perfect visual grading;
- full chemistry structure grading;
- graph/map automatic marks;
- report-card automation;
- ERP expansion;
- EUI source adoption;
- public product-scope expansion beyond the supported capability matrix.

---

## 14. Changed-file inventory for Batch F

### Documentation

```text
docs/product/aei-v1/AEI_V1_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md
docs/product/aei-v1/AEI_V1_SUPPORTED_SCOPE_CAPABILITY_MATRIX.md
docs/product/aei-v1/AEI_V1_CERTIFICATION_REPORT.md
```

### Test-only lint cleanup

```text
apps/api/tests/test_answer_sheet_vision.py
apps/api/tests/test_evaluation_engine.py
```

The test-only cleanup removed unused imports and split long lines so the Batch F
certification Ruff gate can pass. It does not alter runtime behavior.

### Explicitly excluded from Batch F

```text
docs/STATUS.md
```

`docs/STATUS.md` should be updated only after publication.

---

## 15. Risks and follow-ups

| Risk | Assessment | Follow-up |
|---|---|---|
| Feature flags are certified default-off, not production-enabled | Accepted | Product enablement requires deployment config and supported-scope signoff |
| Teacher-facing UI does not yet expose all trust metadata | Known | Future UI batch should require browser proof |
| Assist/checklist metadata could be overclaimed | Reduced | Capability matrix states strict boundaries and non-claims |
| Public capability documentation may drift | Reduced | Keep sales/support docs aligned with this matrix |
| Performance under live enabled traffic needs staging proof | Accepted | Re-run operational proof when flags are enabled in staging |

---

## 16. Retrospective

AEI v1.0 reached certification through incremental, reversible, independently
certified batches. The result is not a universal AI grader. It is a governed
teacher-trust evaluation subsystem with deterministic support where safe,
assist/checklist posture where appropriate, and teacher authority preserved
through review and approved evidence.

This is the right foundation for product-facing teacher evaluation work.

---

## 17. ARM recommendation

ARM review recommendation:

```text
ACCEPT AEI v1.0 certification if implementation review confirms the diff
matches this certification evidence.
```

Suggested certification commit:

```text
docs(aei): certify AEI v1.0 supported scope
```

Suggested annotated tag:

```text
aei-v1-certified
```

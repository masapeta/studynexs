# EUI Production Scope and Versioning

- **Status:** Accepted
- **Parent architecture:** [`../EUI.md`](../EUI.md)

---

## 1. Purpose

StudyNexs should be sold and operated as a finished product, not an experiment.

That does not mean it claims universal capability. It means every supported capability is production-quality for its declared scope, while additional capability areas expand through versioned releases.

---

## 2. Product framing

| Term | Meaning |
|---|---|
| v1.0 production | Complete, production-ready experience for the supported scope. |
| Capability expansion | Versioned expansion of subjects, languages, OCR quality, visual understanding, policies, and analytics. |
| Unsupported | Not claimed, not demonstrated as supported, and routed safely if encountered. |
| Assistive | Useful support with human review as part of the product behavior. |

---

## 3. v1.0 production definition

For a capability to be part of v1.0 production, it must have:

- declared scope;
- capability registry entry;
- user-facing expectation messaging;
- trust and review behavior;
- tests or certification evidence appropriate to the capability;
- fallback or manual-review behavior for low-confidence cases;
- no contradiction with AEI or EUI architecture.

---

## 4. Supported does not mean universal

Examples:

| Capability | Production-quality claim | Not claimed by default |
|---|---|---|
| Mathematics normalization | Works for declared syllabus patterns and supported expression families. | Full symbolic algebra for every possible expression. |
| Printed OCR | Works for supported scripts and document quality limits. | Every damaged scan or unusual layout. |
| Handwriting OCR | Assists within documented quality limits and routes uncertainty to review. | Perfect recognition of every handwriting style. |
| Code-mixed tutor | Handles declared classroom code-mixed patterns in supported modes. | Every dialect, slang, or voice interaction. |
| Diagram understanding | Checklist support for declared visual types. | Pixel-perfect autonomous diagram grading. |

---

## 5. Versioning model

| Version family | Purpose |
|---|---|
| EUI v1 | Platform educational understanding architecture and contracts. |
| AEI v1 | Protected academic evaluation pipeline and contracts. |
| Product v1.0 | Production product release with declared supported scope. |
| Product v1.x | Capability expansion and refinement without architecture drift. |
| EUI v2 / AEI v2 | Contract-breaking architecture evolution requiring ADR and migration plan. |

---

## 6. Versioning rules

1. EUI and AEI contract changes are versioned separately from product releases.
2. Product releases may include multiple subsystem capability expansions.
3. Capability expansion must update the Platform Capability Registry.
4. Architecture-breaking changes require ADR approval.
5. Historical certification tags remain immutable references.
6. User-facing claims must match the current production scope.
7. EUI architecture changes require ADR review, compatibility assessment, and a versioning decision.

---

## 7. Launch posture

The correct product posture is:

> StudyNexs is production-ready for the capabilities it declares, and it expands capabilities through governed releases.

This is stronger and safer than claiming universal automation.

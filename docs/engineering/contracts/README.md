# Engineering contracts (P2 Stage 1–2)

Decision P-R6: shared contracts for the P2 work live here. These are documentation of the
implemented API/data contracts — the code (Pydantic schemas, SQLAlchemy models, Alembic
migrations) is authoritative; these documents must be updated with it.

| Document | Scope |
|---|---|
| [exam-results-release.md](exam-results-release.md) | Result versions, release generations, preview tokens, withdraw/block, learner visibility, notifications |
| [learner-exposure.md](learner-exposure.md) | Staff vs learner audiences for mastery, KG, flags, misconceptions; exposure path inventory E1–E18 |
| [answer-sheet-pages.md](answer-sheet-pages.md) | Multi-page answer sheets (P-R4 limits), evaluation revisions, reopen |
| [deployment-tier.md](deployment-tier.md) | `DEPLOYMENT_TIER` / `NEXT_PUBLIC_DEPLOYMENT_TIER` / demo-login config design (P-R8: design only) |
| [qr-answer-capture.md](qr-answer-capture.md) | QR-linked exam booklets — requirements and API sketch only (not implemented) |

Status: implemented on the `develop` working tree, uncommitted, pending owner acceptance.

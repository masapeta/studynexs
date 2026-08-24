# Canonical Repository Declaration

> **Effective:** 2026-07-20 (P6 — Batch 1 baseline finalization)

---

## Canonical development repository

**`studynexs-dev`** at `D:\Projects\studynexs-platform\studynexs-dev` is the **sole canonical repository** for StudyNexs platform development, pilot execution, and release governance.

| Property | Value |
|----------|-------|
| Branch (Batch 1 RC) | `develop` — **frozen** |
| Release candidate tag (pending PO) | `v0.1.0-batch1` |
| Archive superseded | `academix-platform` → [`REFERENCE_ARCHIVE.md`](../../academix-platform/REFERENCE_ARCHIVE.md) |

---

## Policy

- All commits, tags, CI, and pilot operations target **`studynexs-dev`** only.
- **`academix-platform`** is read-only reference archive — no development.
- Post-freeze changes on `develop` require **Product Owner approval** and must be **critical defect fixes** only until Batch 1 tag is applied and Gate 2 is authorized.

---

## Verification (P6)

| Check | Status |
|-------|--------|
| Docker API bind mount → `studynexs-dev/apps/api` | ✅ Verified |
| Runtime path references to `academix-platform` | ⚠️ **Corrected 2026-08-24** — see below |
| Alembic single head | ✅ `f4a5b6c7d8e9` |
| DB at head | ✅ Verified in container |

See [`P6_IMPLEMENTATION_REPORT.md`](./P6_IMPLEMENTATION_REPORT.md) for full release verification.

---

## Correction — local editable install (2026-08-24)

The P6 row above ("Runtime path references — None") was **true for the Docker bind mount but
false for local development**. The Production Trust Audit found the `pip` editable install
mapping `app` → `D:\Projects\academix-platform\apps\api\app`, so a plain
`uvicorn app.main:app` served **140 routes instead of 182** — 42 endpoints (parent copilot,
tutor `/ask`, `change-class`, promotion, onboarding) silently absent.

**Why no test caught it:** pytest inserts its rootdir (`apps/api`) at `sys.path[0]`, and a real
directory outranks an editable-install finder — so pytest always imported the *local* `app/`
while uvicorn served the archived copy. A test asserting on `app.__file__` is a false negative.

**Fix applied:** reinstalled from canonical, plus a guard that inspects the *install record*
rather than the imported module:

```bash
pip uninstall studynexs-api -y
pip install -e apps/api
pytest tests/test_canonical_runtime.py     # now a hard CI gate
```

If you ever see fewer than 182 routes on `/openapi.json`, check this first.

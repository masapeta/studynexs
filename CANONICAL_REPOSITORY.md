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
| Runtime path references to `academix-platform` | ✅ None (legacy npm package name only) |
| Alembic single head | ✅ `f4a5b6c7d8e9` |
| DB at head | ✅ Verified in container |

See [`P6_IMPLEMENTATION_REPORT.md`](./P6_IMPLEMENTATION_REPORT.md) for full release verification.

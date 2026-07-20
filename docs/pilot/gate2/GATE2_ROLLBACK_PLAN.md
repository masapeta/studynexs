# Gate 2 Rollback Plan

> **Baseline:** `v0.1.0-batch1`  
> **Principle:** Stop safely first; restore service second; investigate third  
> **Trigger authority:** Product owner + on-call engineer (Sev-1: engineer may act immediately)

---

## 1. Rollback triggers

| Trigger | Severity | Rollback type |
|---------|----------|---------------|
| Cross-tenant data visible | Sev-1 | Immediate full stop |
| Auth bypass or credential leak | Sev-1 | Immediate full stop |
| Widespread 5xx on login/academic APIs | Sev-2 | Stop pilot session; restore last known good |
| Pack approve corrupts data / wrong index | Sev-2 | Disable approve path; restore DB snapshot |
| LLM generates harmful/off-syllabus content at scale | Sev-2 | Disable AI generate endpoints |
| School requests stop | — | Controlled shutdown |
| Unapproved code deployed | Sev-2 | Redeploy tag `v0.1.0-batch1` |

---

## 2. Rollback levels

### Level 0 — Session pause (minutes)

**Use when:** Transient LLM slowness, single-user glitch, network blip.

1. Announce pause to room
2. Switch to backup QP or cached screenshots
3. Retry smoke test
4. Resume if smoke passes

**No data rollback.**

---

### Level 1 — Service restart (5–15 min)

**Use when:** API 500 after deploy, Qdrant connection lost, container unhealthy.

```powershell
# From repo root
docker compose -f infra/docker/docker-compose.dev.yml restart api
docker compose -f infra/docker/docker-compose.dev.yml restart qdrant

# Verify RAG
docker exec studynexs-api python -c "import qdrant_client; print('ok')"

# Smoke
cd apps\api
python scripts\smoke_pilot_readiness.py
```

If fail → Level 2.

---

### Level 2 — Redeploy frozen baseline (15–30 min)

**Use when:** Wrong code mounted, bad hotfix, dependency missing.

```powershell
git fetch origin
git checkout v0.1.0-batch1

docker compose -f infra/docker/docker-compose.dev.yml down
docker compose -f infra/docker/docker-compose.dev.yml up -d --build --force-recreate

cd apps\api
python scripts\seed_pilot_naagarjuna.py
python scripts\seed_pilot_naagarjuna_curriculum.py
python scripts\smoke_pilot_readiness.py
```

**Note:** Re-seed is idempotent but **does not** undo bad manual data. If bad data entered, use Level 3.

---

### Level 3 — Database restore (30–60+ min)

**Use when:** Data corruption, wrong tenant merge, bad migration.

**Prerequisite:** Pre-pilot snapshot must exist (see §4 — if missing, manual cleanup only).

```powershell
# STOP API first
docker compose -f infra/docker/docker-compose.dev.yml stop api

# Restore Postgres volume snapshot (procedure depends on host)
# Example: restore pg_dump taken at T-0
# pg_restore / psql < snapshot.sql

docker compose -f infra/docker/docker-compose.dev.yml start api
python scripts\seed_pilot_naagarjuna.py
python scripts\smoke_pilot_readiness.py
```

**Qdrant:** If index corrupted, delete collection and re-approve pack (or restore Qdrant volume snapshot).

---

### Level 4 — Full pilot stop (immediate)

**Use when:** Sev-1 security, legal, or school stop.

1. `docker compose -f infra/docker/docker-compose.dev.yml down` (or disable ingress in prod)
2. Notify school HOD + PO
3. Preserve logs (no PII in tickets)
4. File incident in [PILOT_FEEDBACK_LOG.md](../../product/PILOT_FEEDBACK_LOG.md)
5. Schedule post-mortem within 48 h

---

## 3. AI-specific kill switches

| Action | How | When |
|--------|-----|------|
| Stop QP generation | Revoke LLM API key / set credits to 0 | Bad outputs |
| Stop eval vision | Disable eval endpoint via env flag if available; else stop API | OCR runaway |
| Block pack approve | HOD communication only — do not approve until Qdrant fixed | Index failures |

Document actual env flags available in deployment — if none, Level 1 restart + Level 4 if persistent.

---

## 4. Pre-pilot backup requirement

**Before T-0:**

| Asset | Backup method | Verified restore |
|-------|---------------|------------------|
| PostgreSQL | `pg_dump` or volume snapshot | ☐ |
| Qdrant | Volume snapshot or note re-index path | ☐ |
| Env secrets | Secure vault copy (not Git) | ☐ |
| Approved QP exports | PDF/export if generated | ☐ |

**Gap (known):** Production backup runbook not fully implemented — see [RELEASE_ENGINEERING_REVIEW.md](./RELEASE_ENGINEERING_REVIEW.md). For pilot, **mandatory** manual snapshot at T-0.

---

## 5. Communication templates

### To school (Sev-2 pause)

> *"We've paused the session for a technical check (~15 minutes). Your data is safe. We'll resume with the backup workflow or reschedule — your call."*

### To school (Sev-1 stop)

> *"We've stopped today's session as a precaution. No student data was shared outside your tenant. We'll follow up within 24 hours with next steps."*

### Internal

> Incident: [ID] · Severity: [ ] · Rollback level: [ ] · Tag: v0.1.0-batch1 · Owner: [ ]

---

## 6. Post-rollback verification

| Step | Pass |
|------|------|
| `git describe` = `v0.1.0-batch1` (or documented hotfix with PO approval) | ☐ |
| `smoke_pilot_readiness.py` exit 0 | ☐ |
| Login all pilot accounts | ☐ |
| No cross-tenant data spot-check | ☐ |
| Daily log updated with incident + rollback level | ☐ |
| Risk register updated | ☐ |

---

## 7. Re-entry criteria

Pilot sessions may resume when:

1. Root cause documented (or accepted workaround)
2. Smoke + login pass
3. PO approves re-entry
4. School informed if session was cancelled

---

## 8. What we do NOT rollback

- Teacher-approved papers and marks (unless corrupt) — preserve HITL artifacts
- Feedback forms and daily logs — keep for exit review
- Git tag `v0.1.0-batch1` — immutable reference; redeploy from tag

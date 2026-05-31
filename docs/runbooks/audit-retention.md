# Audit log retention

## Configuration

`AUDIT_RETENTION_DAYS` in API settings (default **90**). Set to `0` to disable purge.

## Purge job

```bash
cd apps/api
python scripts/purge_audit_logs.py
```

Deletes `audit_logs` rows where `created_at` is older than the retention window.

## Schedule

| Platform | Suggestion |
|----------|------------|
| Azure Container Apps | Cron job / scheduled execution daily 02:00 UTC |
| Kubernetes | CronJob |
| VM | system cron |

## Migration

Apply index for efficient purge:

```bash
alembic upgrade head
```

Revision: `a1b2c3d4e5f6_audit_logs_retention_index` (`ix_audit_logs_created_at`).

## Monitoring

Run `scripts/monitor_snapshot.py` during soak tests to track table growth.

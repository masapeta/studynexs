#!/usr/bin/env python3
"""Restore a PostgreSQL custom-format backup into a clean drill database.

This is an operational proof helper. By default it restores into the synthetic
``studynexs_restore_drill`` database and drops that database first. Do not point
``--target-database`` at a production database.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

try:
    from scripts.backup_postgres import sha256_file
except ModuleNotFoundError:  # pragma: no cover - exercised by direct script execution
    from backup_postgres import sha256_file

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_COMPOSE_FILE = REPO_ROOT / "infra" / "docker" / "docker-compose.dev.yml"
DEFAULT_VERIFY_QUERY = "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a StudyNexs PostgreSQL restore drill.")
    parser.add_argument("backup", help="Path to a pg_dump -Fc backup artifact.")
    parser.add_argument("--compose-file", default=str(DEFAULT_COMPOSE_FILE))
    parser.add_argument("--service", default="postgres")
    parser.add_argument("--source-database", default="studynexs")
    parser.add_argument("--target-database", default="studynexs_restore_drill")
    parser.add_argument("--user", default="studynexs")
    parser.add_argument("--verify-query", default=DEFAULT_VERIFY_QUERY)
    parser.add_argument(
        "--keep-target",
        action="store_true",
        help="Leave the synthetic restore target database in place after verification.",
    )
    return parser.parse_args()


def _compose_exec(
    compose_file: Path,
    service: str,
    command: list[str],
    *,
    stdin: object | None = None,
    timeout: int = 300,
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["docker", "compose", "-f", str(compose_file), "exec", "-T", service, *command],
        cwd=REPO_ROOT,
        stdin=stdin,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def _decode(data: bytes) -> str:
    return data.decode("utf-8", errors="replace").strip()


def _fail(message: str, result: subprocess.CompletedProcess[bytes] | None = None) -> int:
    payload = {"status": "fail", "error": message}
    if result is not None:
        payload["stderr"] = _decode(result.stderr)
        payload["stdout"] = _decode(result.stdout)
        payload["returncode"] = result.returncode
    print(json.dumps(payload, indent=2, sort_keys=True))
    return result.returncode if result and result.returncode else 1


def main() -> int:
    args = _parse_args()
    backup = Path(args.backup).expanduser().resolve()
    compose_file = Path(args.compose_file).expanduser().resolve()

    if not backup.exists():
        print(json.dumps({"status": "fail", "error": f"backup not found: {backup}"}))
        return 2
    if args.target_database == args.source_database:
        print(
            json.dumps(
                {
                    "status": "fail",
                    "error": "target database must differ from source database",
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 2

    drop = _compose_exec(
        compose_file,
        args.service,
        ["dropdb", "-U", args.user, "--if-exists", args.target_database],
    )
    if drop.returncode != 0:
        return _fail("failed to drop synthetic restore target", drop)

    create = _compose_exec(
        compose_file,
        args.service,
        ["createdb", "-U", args.user, args.target_database],
    )
    if create.returncode != 0:
        return _fail("failed to create synthetic restore target", create)

    with backup.open("rb") as handle:
        restore = _compose_exec(
            compose_file,
            args.service,
            [
                "pg_restore",
                "-U",
                args.user,
                "-d",
                args.target_database,
                "--no-owner",
                "--no-acl",
            ],
            stdin=handle,
            timeout=600,
        )
    if restore.returncode != 0:
        return _fail("restore drill failed", restore)

    verify = _compose_exec(
        compose_file,
        args.service,
        [
            "psql",
            "-U",
            args.user,
            "-d",
            args.target_database,
            "-At",
            "-c",
            args.verify_query,
        ],
    )
    if verify.returncode != 0:
        return _fail("restore verification query failed", verify)

    cleanup_status = "kept"
    if not args.keep_target:
        cleanup = _compose_exec(
            compose_file,
            args.service,
            ["dropdb", "-U", args.user, "--if-exists", args.target_database],
        )
        cleanup_status = "dropped" if cleanup.returncode == 0 else "cleanup_failed"

    payload = {
        "status": "pass",
        "backup_path": str(backup),
        "backup_size_bytes": backup.stat().st_size,
        "backup_sha256": sha256_file(backup),
        "target_database": args.target_database,
        "verify_query": args.verify_query,
        "verify_result": _decode(verify.stdout),
        "cleanup_status": cleanup_status,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if cleanup_status != "cleanup_failed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Verify a PostgreSQL custom-format backup without restoring it.

This runs ``pg_restore -l`` inside the Postgres container and streams the host
backup through stdin. It proves the artifact is readable and contains restore
metadata while avoiding destructive database changes.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_COMPOSE_FILE = REPO_ROOT / "infra" / "docker" / "docker-compose.dev.yml"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify a StudyNexs PostgreSQL backup.")
    parser.add_argument("backup", help="Path to a pg_dump -Fc backup artifact.")
    parser.add_argument("--compose-file", default=str(DEFAULT_COMPOSE_FILE))
    parser.add_argument("--service", default="postgres")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    backup = Path(args.backup).expanduser().resolve()
    if not backup.exists():
        print(json.dumps({"status": "fail", "error": f"backup not found: {backup}"}))
        return 2

    command = [
        "docker",
        "compose",
        "-f",
        str(Path(args.compose_file).resolve()),
        "exec",
        "-T",
        args.service,
        "pg_restore",
        "-l",
    ]
    with backup.open("rb") as handle:
        result = subprocess.run(
            command,
            cwd=REPO_ROOT,
            stdin=handle,
            capture_output=True,
            timeout=300,
            check=False,
        )

    if result.returncode != 0:
        print(
            json.dumps(
                {
                    "status": "fail",
                    "error": result.stderr.decode("utf-8", errors="replace").strip(),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return result.returncode or 1

    listing = result.stdout.decode("utf-8", errors="replace")
    entries = [
        line
        for line in listing.splitlines()
        if line.strip() and not line.lstrip().startswith(";")
    ]
    payload = {
        "status": "pass",
        "backup_path": str(backup),
        "size_bytes": backup.stat().st_size,
        "restore_list_entries": len(entries),
        "contains_schema_entries": any("SCHEMA" in line or "TABLE" in line for line in entries),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["contains_schema_entries"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

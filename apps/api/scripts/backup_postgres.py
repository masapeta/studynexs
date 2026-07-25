#!/usr/bin/env python3
"""Create a PostgreSQL custom-format backup through Docker Compose.

The script writes a host-side ``pg_dump -Fc`` artifact without exposing database
secrets in command output. It is designed for local/guided-pilot operations; in
managed production environments, use the managed database backup mechanism and
keep this script as the equivalent verification pattern.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_COMPOSE_FILE = REPO_ROOT / "infra" / "docker" / "docker-compose.dev.yml"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a StudyNexs PostgreSQL backup.")
    parser.add_argument(
        "--output",
        required=True,
        help="Destination .dump path. Use a secure location outside Git for real backups.",
    )
    parser.add_argument("--compose-file", default=str(DEFAULT_COMPOSE_FILE))
    parser.add_argument("--service", default="postgres")
    parser.add_argument("--database", default="studynexs")
    parser.add_argument("--user", default="studynexs")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "docker",
        "compose",
        "-f",
        str(Path(args.compose_file).resolve()),
        "exec",
        "-T",
        args.service,
        "pg_dump",
        "-U",
        args.user,
        "-d",
        args.database,
        "-Fc",
    ]
    with output.open("wb") as handle:
        result = subprocess.run(
            command,
            cwd=REPO_ROOT,
            stdout=handle,
            stderr=subprocess.PIPE,
            text=False,
            timeout=600,
            check=False,
        )

    if result.returncode != 0:
        try:
            output.unlink(missing_ok=True)
        except OSError:
            pass
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

    payload = {
        "status": "pass",
        "backup_path": str(output),
        "size_bytes": output.stat().st_size,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "format": "pg_dump_custom",
        "database": args.database,
        "service": args.service,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

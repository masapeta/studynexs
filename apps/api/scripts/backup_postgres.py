#!/usr/bin/env python3
"""Create a PostgreSQL custom-format backup through Docker Compose.

The script writes a host-side ``pg_dump -Fc`` artifact without exposing database
secrets in command output. It is designed for local/guided-pilot operations; in
managed production environments, use the managed database backup mechanism and
keep this script as the equivalent verification pattern.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
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
    parser.add_argument(
        "--copy-to",
        help=(
            "Optional off-runtime-boundary directory for a copy of the backup. "
            "For local certification this is a substitute, not real off-VM retention."
        ),
    )
    parser.add_argument(
        "--manifest",
        help=(
            "Optional JSON manifest path. Defaults to <output>.manifest.json "
            "when --copy-to is set."
        ),
    )
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def copy_off_runtime_boundary(source: Path, destination_dir: Path) -> Path:
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / source.name
    if source.resolve() == destination.resolve():
        raise ValueError("backup copy destination must differ from source path")
    shutil.copy2(source, destination)
    return destination


def write_manifest(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


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

    sha256 = sha256_file(output)
    copied_path: Path | None = None
    manifest_path: Path | None = None
    if args.copy_to:
        try:
            copied_path = copy_off_runtime_boundary(
                output,
                Path(args.copy_to).expanduser().resolve(),
            )
        except ValueError as exc:
            print(json.dumps({"status": "fail", "error": str(exc)}, indent=2, sort_keys=True))
            return 2

    payload: dict[str, object] = {
        "status": "pass",
        "backup_path": str(output),
        "size_bytes": output.stat().st_size,
        "sha256": sha256,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "format": "pg_dump_custom",
        "database": args.database,
        "service": args.service,
    }
    if copied_path:
        payload["copied_path"] = str(copied_path)
        payload["copied_sha256"] = sha256_file(copied_path)
        payload["off_runtime_copy_substitute"] = True
        manifest_path = (
            Path(args.manifest).expanduser().resolve()
            if args.manifest
            else output.with_suffix(output.suffix + ".manifest.json")
        )
        write_manifest(manifest_path, payload)
        payload["manifest_path"] = str(manifest_path)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

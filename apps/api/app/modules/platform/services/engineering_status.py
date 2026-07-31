"""Load engineering dashboard snapshot from repo docs."""

from __future__ import annotations

import json
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Any

_API_ROOT = Path(__file__).resolve().parents[4]
_REPO_ROOT = _API_ROOT.parent.parent
_ENGINEERING_DIR = _REPO_ROOT / "docs" / "engineering"


def _git_field(args: list[str]) -> str | None:
    try:
        out = subprocess.check_output(
            ["git", *args],
            cwd=_REPO_ROOT,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return out.strip() or None
    except (OSError, subprocess.CalledProcessError):
        return None


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _load_snapshot() -> dict[str, Any]:
    platform = _read_json(_ENGINEERING_DIR / "platform.json")
    modules_file = _read_json(_ENGINEERING_DIR / "modules.json")
    roadmap = _read_json(_ENGINEERING_DIR / "roadmap.json")

    if not platform and not modules_file:
        return {
            "schema_version": 3,
            "architecture_version": "unknown",
            "updated_at": "",
            "branch": "unknown",
            "last_commit": "unknown",
            "capability_matrix": [],
            "modules": [],
            "doc_links": {},
            "tests": {},
            "providers": {},
            "roadmap": {},
        }

    data: dict[str, Any] = {**platform}
    data["modules"] = modules_file.get("modules", [])
    data["roadmap"] = roadmap
    data["last_completed_batch"] = roadmap.get("last_completed_batch", {}).get("title")
    current = roadmap.get("current_batch")
    if isinstance(current, dict):
        data["current_batch"] = current.get("title") or (
            f"Batch {current['number']}" if current.get("number") is not None else None
        )
    else:
        data["current_batch"] = current
    data["next_batch"] = roadmap.get("next_milestone", {}).get("title")
    data["next_milestone"] = roadmap.get("next_milestone", {})
    return data


def get_engineering_status() -> dict[str, Any]:
    """Merge docs/engineering/*.json with live git metadata."""
    data = dict(_load_snapshot())
    data["runtime"] = {
        "git_commit": _git_field(["rev-parse", "--short", "HEAD"]) or data.get("last_commit"),
        "git_branch": _git_field(["branch", "--show-current"]) or data.get("branch"),
        "engineering_dir": str(_ENGINEERING_DIR.relative_to(_REPO_ROOT)).replace("\\", "/"),
    }
    return data

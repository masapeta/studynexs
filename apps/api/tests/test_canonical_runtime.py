"""Runtime provenance guard (audit P0-ENV-001).

A stale editable install mapped the `app` package to the ARCHIVED academix-platform repo, so
`uvicorn app.main:app` served 140 routes instead of the canonical 182 — 42 endpoints (parent
copilot, tutor /ask, change-class, promotion) silently absent.

Why the 970-test suite never caught it: pytest inserts its rootdir (apps/api) at sys.path[0]
because tests/ has no __init__.py, and a real directory outranks an editable-install finder.
So pytest ALWAYS imports the local app/ no matter how broken the install is — while uvicorn,
which does not touch sys.path, serves the archived copy. Verified both ways.

Therefore the load-bearing check inspects the *installed distribution's* record, not the
imported module: asserting on `app.__file__` alone is a false negative under pytest.
"""

from __future__ import annotations

import json
from importlib.metadata import Distribution, PackageNotFoundError
from pathlib import Path
from urllib.parse import unquote, urlparse

import pytest

import app as app_pkg
from app.main import app as real_app

# tests/ -> apps/api/ -> apps/ -> <repo root>
_REPO_ROOT = Path(__file__).resolve().parents[3]
_CANONICAL_API = _REPO_ROOT / "apps" / "api"
_ARCHIVED = "academix-platform"


def _norm(p: Path) -> str:
    return str(p.resolve()).replace("\\", "/").rstrip("/").lower()


def _mapping_from_finder() -> Path | None:
    """Read the setuptools strict-editable finder's MAPPING for `app`.

    This is the authoritative record of what an editable install points at, and — unlike
    `app.__file__` — it is immune to pytest's rootdir sys.path insertion.
    """
    import site
    import sysconfig

    roots = set(site.getsitepackages())
    with_user = site.getusersitepackages()
    roots.add(with_user if isinstance(with_user, str) else with_user[0])
    roots.add(sysconfig.get_paths()["purelib"])

    for root in roots:
        for finder in Path(root).glob("__editable___studynexs_api_*_finder.py"):
            for line in finder.read_text(encoding="utf-8").splitlines():
                if line.startswith("MAPPING"):
                    inner = line.split("{", 1)[1].rsplit("}", 1)[0]
                    target = inner.split(":", 1)[1].strip().strip("',\"")
                    # 'app' maps to <repo>/apps/api/app -> compare its parent
                    return Path(target.encode().decode("unicode_escape")).parent
    return None


def _editable_target() -> Path | None:
    """Where the installed `studynexs-api` editable package actually points.

    The finder MAPPING is checked FIRST: `Distribution.from_name` can resolve to a local
    `studynexs_api.egg-info` in the source tree (cwd shadowing) rather than the real
    installed distribution, which silently hides a bad install.
    """
    target = _mapping_from_finder()
    if target is not None:
        return target

    try:
        dist = Distribution.from_name("studynexs-api")
    except PackageNotFoundError:
        return None

    raw = dist.read_text("direct_url.json")
    if raw:
        url = json.loads(raw).get("url", "")
        if url.startswith("file:"):
            return Path(unquote(urlparse(url).path).lstrip("/"))
    return None


def test_installed_package_points_at_this_repository():
    """The editable install must target this checkout — the check pytest cannot fake."""
    target = _editable_target()
    if target is None:
        pytest.skip("studynexs-api not installed as a distribution (plain source-tree run)")

    assert _ARCHIVED not in _norm(target), (
        f"studynexs-api is installed from the ARCHIVED repo: {target}. "
        "uvicorn will serve stale code even though pytest passes. Fix with: "
        "pip uninstall studynexs-api && pip install -e apps/api (see CANONICAL_REPOSITORY.md)"
    )
    assert _norm(target) == _norm(_CANONICAL_API), (
        f"studynexs-api points at {target}, expected {_CANONICAL_API.resolve()}."
    )


def test_imported_app_is_not_the_archived_repository():
    """Secondary check — weak under pytest (see module docstring) but free."""
    loaded = _norm(Path(app_pkg.__file__).parent)
    assert _ARCHIVED not in loaded, f"`app` imported from the archived repo: {loaded}"


def _served_paths() -> set[str]:
    """Every served path.

    Read from the OpenAPI schema, not app.routes: on this FastAPI version included routers
    nest under a private `_IncludedRouter` whose children carry no mount prefix.
    """
    return set(real_app.openapi().get("paths", {}).keys())


def test_routers_absent_from_the_archived_build_are_mounted():
    """Canary routes the stale build was missing.

    Asserting a route *count* would break on every new endpoint, so pin the specific routers
    whose absence was the signature of the wrong build.
    """
    paths = _served_paths()
    assert paths, "no routes found — OpenAPI generation itself is broken"
    required = [
        "/api/v1/parent-copilot/students/{student_id}/briefing",
        "/api/v1/tutor/students/{student_id}/ask",
        "/api/v1/academic/students/{student_id}/change-class",
        "/api/v1/academic/enrollments/promote",
        "/api/v1/curriculum/onboarding/propose",
    ]
    missing = [p for p in required if p not in paths]
    assert not missing, f"{len(missing)} canonical route(s) missing: {missing}"

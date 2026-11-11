"""Contract tests for infra/scripts/deploy.sh Compose override acknowledgement.

deploy.sh runs against a temporary STUDYNEXS_BASE with docker/git/curl replaced by stubs that
only log their arguments, so nothing is pulled, built, migrated or restarted.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
DEPLOY_SH = REPO_ROOT / "infra" / "scripts" / "deploy.sh"
_GIT_BASH = Path(r"C:\Program Files\Git\bin\bash.exe")
BASH = str(_GIT_BASH) if _GIT_BASH.is_file() else shutil.which("bash")

pytestmark = pytest.mark.skipif(
    BASH is None or (os.name == "nt" and not _GIT_BASH.is_file()),
    reason="needs a POSIX bash (Git Bash on Windows)",
)

_STUB = """#!/usr/bin/env bash
printf '%s\\n' "$(basename "$0") $*" >> "$STUB_LOG"
case "$(basename "$0") $*" in
  "git "*"rev-parse --short"*) echo abc1234 ;;
  "git "*"rev-parse"*) echo abc1234def5678 ;;
esac
exit 0
"""


def _posix(path: Path) -> str:
    """Git Bash splits PATH on ':', so 'C:/x' must become '/c/x'."""
    text = path.as_posix()
    if os.name == "nt" and len(text) > 1 and text[1] == ":":
        text = f"/{text[0].lower()}{text[2:]}"
    return text


def _host(tmp_path: Path, *, override: bool) -> Path:
    base = tmp_path / "opt"
    for d in ("deploy/compose", "deploy/env", "deploy/nginx", "deploy/scripts", "runtime",
              "repo/infra/docker", "repo/infra/nginx", "repo/infra/scripts"):
        (base / d).mkdir(parents=True)
    (base / "deploy/env/api.env").write_text(
        "DEPLOYMENT_TIER=staging\nPOSTGRES_PASSWORD=never-printed\n", encoding="utf-8"
    )
    for rel in ("deploy/compose/docker-compose.prod.yml",
                "repo/infra/docker/docker-compose.prod.yml", "repo/infra/nginx/nginx.conf"):
        (base / rel).write_text("x\n", encoding="utf-8")
    if override:
        (base / "deploy/compose/docker-compose.prod.override.yml").write_text(
            "services: {}\n", encoding="utf-8"
        )
    stubs = tmp_path / "stubs"
    stubs.mkdir()
    for name in ("docker", "git", "curl", "openssl"):
        (stubs / name).write_text(_STUB, encoding="utf-8", newline="\n")
        (stubs / name).chmod(0o755)
    return base


def _run(
    tmp_path: Path, base: Path, *args: str, script_path: Path = DEPLOY_SH
) -> tuple[subprocess.CompletedProcess, list[str]]:
    log = tmp_path / "stub.log"
    script = (
        f'export PATH="{_posix(tmp_path / "stubs")}:$PATH" STUB_LOG="{_posix(log)}" '
        f'STUDYNEXS_BASE="{_posix(base)}"; '
        f'bash "{_posix(script_path)}" "$@"'
    )
    result = subprocess.run(
        [BASH, "-c", script, "deploy", *args],
        capture_output=True, text=True, timeout=60, check=False,
    )
    calls = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
    return result, calls


def test_no_override_and_no_flag_uses_base_compose_only(tmp_path: Path):
    base = _host(tmp_path, override=False)
    result, calls = _run(tmp_path, base, "--skip-pull")
    assert result.returncode == 0, result.stderr
    docker = [c for c in calls if c.startswith("docker ")]
    assert docker and all("docker-compose.prod.override.yml" not in c for c in docker)
    record = json.loads((base / "runtime/current.json").read_text(encoding="utf-8"))
    assert record["override_included"] is False
    assert record["override_sha256"] is None
    assert [Path(p).name for p in record["compose_files"]] == ["docker-compose.prod.yml"]


def test_existing_override_without_flag_stops_before_any_action(tmp_path: Path):
    base = _host(tmp_path, override=True)
    result, calls = _run(tmp_path, base)
    assert result.returncode == 1
    assert "--include-prod-override was not given" in result.stderr
    assert calls == []
    assert not (base / "runtime/current.json").exists()


def test_flag_without_override_file_stops_before_any_action(tmp_path: Path):
    base = _host(tmp_path, override=False)
    result, calls = _run(tmp_path, base, "--include-prod-override")
    assert result.returncode == 1
    assert "does not exist" in result.stderr
    assert calls == []


def test_flag_with_override_uses_it_after_base_for_every_compose_call(tmp_path: Path):
    base = _host(tmp_path, override=True)
    result, calls = _run(tmp_path, base, "--skip-pull", "--include-prod-override")
    assert result.returncode == 0, result.stderr
    docker = [c for c in calls if c.startswith("docker ")]
    assert len(docker) == 3  # build, migrate, up
    for call in docker:
        assert call.index("docker-compose.prod.yml") < call.index("docker-compose.prod.override.yml")
        assert "--env-file" in call
    record = json.loads((base / "runtime/current.json").read_text(encoding="utf-8"))
    assert record["override_included"] is True
    assert len(record["override_sha256"]) == 64
    assert [Path(p).name for p in record["compose_files"]] == [
        "docker-compose.prod.yml", "docker-compose.prod.override.yml",
    ]
    text = (base / "runtime/current.json").read_text(encoding="utf-8")
    assert "services:" not in text and "never-printed" not in text


def test_invalid_tier_stops_before_any_action(tmp_path: Path):
    base = _host(tmp_path, override=False)
    (base / "deploy/env/api.env").write_text("DEPLOYMENT_TIER=internal\n", encoding="utf-8")
    result, calls = _run(tmp_path, base, "--skip-pull")
    assert result.returncode == 1
    assert calls == []


def test_running_installed_script_is_replaced_atomically_and_run_completes(tmp_path: Path):
    """On the VM deploy.sh runs from deploy/scripts/ and step 2 reinstalls that same file.

    The repo copy is made much longer than the running one, so an in-place overwrite would
    shift bash's read offset into the middle of the new text and break steps 3-7.
    """
    base = _host(tmp_path, override=False)
    installed = base / "deploy/scripts/deploy.sh"
    shutil.copyfile(DEPLOY_SH, installed)
    padding = "".join(f"# padding line {i:05d} {'x' * 60}\n" for i in range(2000))
    new_text = DEPLOY_SH.read_text(encoding="utf-8").replace(
        "set -euo pipefail\n", f"set -euo pipefail\n{padding}# NEXT-VERSION-MARKER\n", 1
    )
    (base / "repo/infra/scripts/deploy.sh").write_text(new_text, encoding="utf-8", newline="\n")
    old_inode = installed.stat().st_ino

    result, calls = _run(tmp_path, base, "--skip-pull", script_path=installed)

    assert result.returncode == 0, result.stderr
    assert len([c for c in calls if c.startswith("docker ")]) == 3  # build, migrate, up
    assert "Deployed abc1234" in result.stdout  # last step ran with the old text
    assert json.loads((base / "runtime/current.json").read_text(encoding="utf-8"))
    assert installed.read_text(encoding="utf-8") == new_text  # complete, not truncated
    assert installed.stat().st_ino != old_inode or os.name == "nt"  # replaced, not rewritten
    assert list((base / "deploy/scripts").glob("deploy.sh.*")) == []  # no temp left behind
    if os.name != "nt":
        assert installed.stat().st_mode & 0o111


BOOTSTRAP_SH = REPO_ROOT / "infra" / "scripts" / "bootstrap_oci_vm.sh"
# deploy.sh exactly as released in 35bbde5 (git blob 2c09bf70); the last version a VM can have.
LEGACY_DEPLOY_SH = Path(__file__).parent / "fixtures" / "deploy_sh_35bbde5.sh"
LEGACY_SHA256 = "01bb32f87c92736d076e0a11c34ec56d57480c9706250ab90571b5473ad0fbbb"


def _sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _legacy_host(tmp_path: Path) -> tuple[Path, Path]:
    """A VM as it stands today: old deploy.sh installed, an override present, new repo pulled."""
    assert _sha256(LEGACY_DEPLOY_SH) == LEGACY_SHA256
    base = _host(tmp_path, override=True)
    (base / "repo/.git").mkdir()
    (base / "deploy/env/metrics_token").write_text("t", encoding="utf-8")  # made by first bootstrap
    for name in ("deploy.sh", "bootstrap_oci_vm.sh"):
        shutil.copyfile(REPO_ROOT / "infra/scripts" / name, base / "repo/infra/scripts" / name)
    installed = base / "deploy/scripts/deploy.sh"
    # Only BASE is rebased into the sandbox; every other byte is the released script.
    installed.write_text(
        LEGACY_DEPLOY_SH.read_text(encoding="utf-8").replace(
            "BASE=/opt/studynexs", f'BASE="{_posix(base)}"', 1
        ),
        encoding="utf-8",
        newline="\n",
    )
    return base, installed


def _effects(calls: list[str]) -> list[str]:
    """Calls that could change the running stack or schema (build/run/up/stop/restart/pull)."""
    verbs = (" build", " run ", " up", " stop", " restart", " down", " pull")
    return [c for c in calls if c.startswith("docker ") and any(v in c for v in verbs)]


def test_legacy_installed_deploy_rejects_new_flag_without_side_effects(tmp_path: Path):
    """Q1: the old script does not know --include-prod-override and stops before doing anything."""
    base, installed = _legacy_host(tmp_path)
    result, calls = _run(tmp_path, base, "--include-prod-override", script_path=installed)
    assert result.returncode == 2
    assert "Unknown argument: --include-prod-override" in result.stderr
    assert calls == []
    assert _sha256(installed) != _sha256(DEPLOY_SH)  # still the old script


def test_bootstrap_installs_new_deploy_without_touching_the_stack(tmp_path: Path):
    """Q2/Q4/Q5: re-running bootstrap (the documented procedure) installs the new deploy.sh.

    It never builds, migrates, starts or stops anything, and leaves api.env and the
    override byte-for-byte unchanged, so the next deploy sees the same Compose inputs.
    """
    base, installed = _legacy_host(tmp_path)
    env_before = (base / "deploy/env/api.env").read_bytes()
    override = base / "deploy/compose/docker-compose.prod.override.yml"
    override_before = override.read_bytes()
    log = tmp_path / "stub.log"
    script = (
        f'export PATH="{_posix(tmp_path / "stubs")}:$PATH" STUB_LOG="{_posix(log)}" '
        f'STUDYNEXS_BASE="{_posix(base)}"; '
        f'bash "{_posix(base / "repo/infra/scripts/bootstrap_oci_vm.sh")}" --tier staging'
    )
    result = subprocess.run([BASH, "-c", script], capture_output=True, text=True, timeout=60)
    calls = log.read_text(encoding="utf-8").splitlines() if log.exists() else []

    assert result.returncode == 0, result.stderr
    assert installed.read_bytes() == DEPLOY_SH.read_bytes()
    assert _effects(calls) == []
    assert [c for c in calls if c.startswith("docker ")] == ["docker compose version"]
    assert (base / "deploy/env/api.env").read_bytes() == env_before
    assert override.read_bytes() == override_before
    assert list((base / "deploy/scripts").glob("*.sh.*")) == []


def test_upgraded_host_refuses_unacknowledged_override_then_keeps_it(tmp_path: Path):
    """Q3/Q5: after the upgrade, a plain deploy cannot silently drop the existing override,
    and the acknowledged deploy uses exactly base + override for every compose call."""
    base, installed = _legacy_host(tmp_path)
    shutil.copyfile(DEPLOY_SH, installed)  # state after bootstrap installed the new script

    plain, plain_calls = _run(tmp_path, base, "--skip-pull", script_path=installed)
    assert plain.returncode == 1
    assert "--include-prod-override was not given" in plain.stderr
    assert plain_calls == []

    acked, acked_calls = _run(
        tmp_path, base, "--skip-pull", "--include-prod-override", script_path=installed
    )
    assert acked.returncode == 0, acked.stderr
    docker = [c for c in acked_calls if c.startswith("docker ")]
    assert len(docker) == 3
    for call in docker:
        assert call.index("docker-compose.prod.yml") < call.index("docker-compose.prod.override.yml")
    record = json.loads((base / "runtime/current.json").read_text(encoding="utf-8"))
    assert record["override_included"] is True
    assert record["override_sha256"] == _sha256(
        base / "deploy/compose/docker-compose.prod.override.yml"
    )


def test_unknown_argument_stops_before_any_action(tmp_path: Path):
    base = _host(tmp_path, override=False)
    result, calls = _run(tmp_path, base, "--bogus")
    assert result.returncode == 2
    assert calls == []

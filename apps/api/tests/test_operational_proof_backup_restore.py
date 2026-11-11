"""Operational Proof backup and restore helper tests."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import backup_postgres, restore_postgres_backup, verify_postgres_backup
from scripts.backup_postgres import (
    DEFAULT_COMPOSE_FILE,
    compose_base,
    copy_off_runtime_boundary,
    sha256_file,
    write_manifest,
)


def test_backup_checksum_copy_and_manifest(tmp_path: Path):
    backup = tmp_path / "studynexs.dump"
    backup.write_bytes(b"study-nexs-backup")
    copy_dir = tmp_path / "off-runtime-copy"

    copied = copy_off_runtime_boundary(backup, copy_dir)
    manifest = tmp_path / "manifest.json"
    payload = {
        "backup_path": str(backup),
        "copied_path": str(copied),
        "sha256": sha256_file(backup),
        "off_runtime_copy_substitute": True,
    }
    write_manifest(manifest, payload)

    assert copied.read_bytes() == backup.read_bytes()
    assert sha256_file(copied) == sha256_file(backup)
    assert json.loads(manifest.read_text(encoding="utf-8")) == payload


def _compose_inputs(tmp_path: Path) -> list[str]:
    prod, env = tmp_path / "prod.yml", tmp_path / "api.env"
    prod.write_text("x", encoding="utf-8")
    env.write_text("POSTGRES_PASSWORD=s3cret-value\n", encoding="utf-8")
    return ["--compose-file", str(prod), "--env-file", str(env)]


def test_restore_drill_rejects_source_database_as_target(tmp_path: Path, monkeypatch):
    backup = tmp_path / "studynexs.dump"
    backup.write_bytes(b"backup")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "restore_postgres_backup.py",
            str(backup),
            *_compose_inputs(tmp_path),
            "--source-database",
            "studynexs",
            "--target-database",
            "studynexs",
            "--confirm-drop-target",
            "studynexs",
        ],
    )

    assert restore_postgres_backup.main() == 2


def test_restore_drill_runs_against_clean_target(tmp_path: Path, monkeypatch, capsys):
    backup = tmp_path / "studynexs.dump"
    backup.write_bytes(b"backup")
    commands: list[list[str]] = []

    def fake_compose_exec(_base, _service, command, **_kwargs):
        commands.append(command)
        stdout = b"7\n" if command[:1] == ["psql"] else b""
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr=b"")

    monkeypatch.setattr(restore_postgres_backup, "_compose_exec", fake_compose_exec)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "restore_postgres_backup.py",
            str(backup),
            *_compose_inputs(tmp_path),
            "--target-database",
            "studynexs_restore_drill",
            "--confirm-drop-target",
            "studynexs_restore_drill",
        ],
    )

    assert restore_postgres_backup.main() == 0
    captured = capsys.readouterr()
    output = json.loads(captured.out)
    plan = json.loads(captured.err)

    assert plan["status"] == "about_to_drop_and_restore"
    assert plan["target_database"] == "studynexs_restore_drill"
    assert [Path(p).name for p in plan["compose_files"]] == ["prod.yml"]
    assert plan["compose_files_defaulted"] is False
    assert Path(plan["env_file"]).name == "api.env"
    assert "s3cret-value" not in captured.out + captured.err
    assert output["status"] == "pass"
    assert output["target_database"] == "studynexs_restore_drill"
    assert output["verify_result"] == "7"
    assert commands[0][:3] == ["dropdb", "-U", "studynexs"]
    assert commands[1][:3] == ["createdb", "-U", "studynexs"]
    assert commands[2][0] == "pg_restore"
    assert commands[3][0] == "psql"
    assert commands[4][:3] == ["dropdb", "-U", "studynexs"]


def _ns(compose_files=None, env_file=None) -> argparse.Namespace:
    return argparse.Namespace(compose_files=compose_files, env_file=env_file)


def test_compose_base_defaults_to_dev_file_without_env_file():
    assert compose_base(_ns()) == ["docker", "compose", "-f", str(DEFAULT_COMPOSE_FILE.resolve())]


def test_compose_base_passes_env_file_then_files_in_order(tmp_path: Path):
    prod, override, env = (tmp_path / n for n in ("prod.yml", "override.yml", "api.env"))
    for path in (prod, override, env):
        path.write_text("x", encoding="utf-8")

    base = compose_base(_ns([str(prod), str(override)], str(env)))

    assert base == [
        "docker", "compose", "--env-file", str(env.resolve()),
        "-f", str(prod.resolve()), "-f", str(override.resolve()),
    ]


def test_compose_base_reports_missing_files(tmp_path: Path):
    prod = tmp_path / "prod.yml"
    prod.write_text("x", encoding="utf-8")

    error = compose_base(_ns([str(prod)], str(tmp_path / "missing.env")))

    assert isinstance(error, str) and "missing.env" in error


@pytest.mark.parametrize("module", [backup_postgres, verify_postgres_backup])
def test_helpers_use_env_file_and_never_print_its_contents(
    tmp_path: Path, monkeypatch, capsys, module
):
    prod, env, backup = tmp_path / "prod.yml", tmp_path / "api.env", tmp_path / "db.dump"
    prod.write_text("x", encoding="utf-8")
    env.write_text("POSTGRES_PASSWORD=s3cret-value\n", encoding="utf-8")
    backup.write_bytes(b"dump")
    calls: list[list[str]] = []

    def fake_run(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, stdout=b"1; TABLE public t\n", stderr=b"")

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    target = ["--output", str(tmp_path / "out.dump")] if module is backup_postgres else [str(backup)]
    monkeypatch.setattr(
        sys, "argv", ["x", *target, "--compose-file", str(prod), "--env-file", str(env)]
    )

    assert module.main() == 0
    assert calls[0][:6] == [
        "docker", "compose", "--env-file", str(env.resolve()), "-f", str(prod.resolve()),
    ]
    out = capsys.readouterr().out
    assert "s3cret-value" not in out
    report = json.loads(out)
    assert report["compose_files"] == [str(prod.resolve())]
    assert report["compose_files_defaulted"] is False
    assert report["env_file"] == str(env.resolve())


def test_verify_reports_dev_default_compose_configuration(tmp_path: Path, monkeypatch, capsys):
    backup = tmp_path / "db.dump"
    backup.write_bytes(b"dump")
    monkeypatch.setattr(
        verify_postgres_backup.subprocess,
        "run",
        lambda command, **k: subprocess.CompletedProcess(
            command, 0, stdout=b"1; TABLE public t\n", stderr=b""
        ),
    )
    monkeypatch.setattr(sys, "argv", ["x", str(backup)])

    assert verify_postgres_backup.main() == 0
    report = json.loads(capsys.readouterr().out)
    assert report["compose_files"] == [str(DEFAULT_COMPOSE_FILE.resolve())]
    assert report["compose_files_defaulted"] is True
    assert report["env_file"] is None


def test_restore_passes_env_file_and_ordered_files_to_every_compose_call(
    tmp_path: Path, monkeypatch, capsys
):
    prod, override, env = (tmp_path / n for n in ("prod.yml", "override.yml", "api.env"))
    prod.write_text("x", encoding="utf-8")
    override.write_text("x", encoding="utf-8")
    env.write_text("POSTGRES_PASSWORD=s3cret-value\n", encoding="utf-8")
    backup = tmp_path / "db.dump"
    backup.write_bytes(b"dump")
    calls: list[list[str]] = []

    def fake_run(command, **kwargs):
        calls.append(command)
        stdout = b"7\n" if "psql" in command else b""
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr=b"")

    monkeypatch.setattr(restore_postgres_backup.subprocess, "run", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        ["x", str(backup), "--compose-file", str(prod), "--compose-file", str(override),
         "--env-file", str(env), "--target-database", "studynexs_restore_drill",
         "--confirm-drop-target", "studynexs_restore_drill"],
    )

    assert restore_postgres_backup.main() == 0
    expected = [
        "docker", "compose", "--env-file", str(env.resolve()),
        "-f", str(prod.resolve()), "-f", str(override.resolve()),
    ]
    assert len(calls) == 5
    for call in calls:
        assert call[: len(expected)] == expected
    assert "s3cret-value" not in capsys.readouterr().out


def test_restore_missing_env_file_fails_before_docker(tmp_path: Path, monkeypatch):
    backup = tmp_path / "db.dump"
    backup.write_bytes(b"dump")
    monkeypatch.setattr(
        restore_postgres_backup.subprocess,
        "run",
        lambda *a, **k: pytest.fail("docker must not run when an input file is missing"),
    )
    prod = tmp_path / "prod.yml"
    prod.write_text("x", encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        ["x", str(backup), "--compose-file", str(prod),
         "--env-file", str(tmp_path / "absent.env"),
         "--target-database", "studynexs_restore_drill",
         "--confirm-drop-target", "studynexs_restore_drill"],
    )

    assert restore_postgres_backup.main() == 2


def test_restore_missing_compose_file_fails_before_docker(tmp_path: Path, monkeypatch):
    backup = tmp_path / "db.dump"
    backup.write_bytes(b"dump")
    env = tmp_path / "api.env"
    env.write_text("x", encoding="utf-8")
    monkeypatch.setattr(
        restore_postgres_backup.subprocess,
        "run",
        lambda *a, **k: pytest.fail("docker must not run when an input file is missing"),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["x", str(backup), "--compose-file", str(tmp_path / "absent.yml"),
         "--env-file", str(env),
         "--target-database", "studynexs_restore_drill",
         "--confirm-drop-target", "studynexs_restore_drill"],
    )

    assert restore_postgres_backup.main() == 2


@pytest.mark.parametrize("missing", ["--compose-file", "--env-file"])
def test_restore_requires_explicit_compose_and_env_file(tmp_path: Path, monkeypatch, missing):
    backup = tmp_path / "db.dump"
    backup.write_bytes(b"dump")
    args = _compose_inputs(tmp_path)
    i = args.index(missing)
    del args[i : i + 2]
    monkeypatch.setattr(
        restore_postgres_backup.subprocess,
        "run",
        lambda *a, **k: pytest.fail("docker must not run without explicit compose inputs"),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["x", str(backup), *args, "--target-database", "studynexs_restore_drill",
         "--confirm-drop-target", "studynexs_restore_drill"],
    )

    with pytest.raises(SystemExit) as exc:
        restore_postgres_backup.main()
    assert exc.value.code == 2


@pytest.mark.parametrize("confirm", ["studynexs_other", ""])
def test_restore_requires_matching_drop_confirmation(tmp_path: Path, monkeypatch, confirm):
    backup = tmp_path / "studynexs.dump"
    backup.write_bytes(b"backup")
    monkeypatch.setattr(
        restore_postgres_backup,
        "_compose_exec",
        lambda *a, **k: pytest.fail("no compose command may run without confirmation"),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["x", str(backup), *_compose_inputs(tmp_path),
         "--target-database", "studynexs_restore_drill", "--confirm-drop-target", confirm],
    )

    assert restore_postgres_backup.main() == 2


def test_restore_refuses_without_explicit_target(tmp_path: Path, monkeypatch):
    backup = tmp_path / "studynexs.dump"
    backup.write_bytes(b"backup")
    monkeypatch.setattr(sys, "argv", ["x", str(backup), *_compose_inputs(tmp_path)])

    with pytest.raises(SystemExit) as exc:
        restore_postgres_backup.main()
    assert exc.value.code == 2

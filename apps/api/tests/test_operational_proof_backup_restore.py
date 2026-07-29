"""Operational Proof backup and restore helper tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts import restore_postgres_backup
from scripts.backup_postgres import copy_off_runtime_boundary, sha256_file, write_manifest


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


def test_restore_drill_rejects_source_database_as_target(tmp_path: Path, monkeypatch):
    backup = tmp_path / "studynexs.dump"
    backup.write_bytes(b"backup")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "restore_postgres_backup.py",
            str(backup),
            "--source-database",
            "studynexs",
            "--target-database",
            "studynexs",
        ],
    )

    assert restore_postgres_backup.main() == 2


def test_restore_drill_runs_against_clean_target(tmp_path: Path, monkeypatch, capsys):
    backup = tmp_path / "studynexs.dump"
    backup.write_bytes(b"backup")
    commands: list[list[str]] = []

    def fake_compose_exec(_compose_file, _service, command, **_kwargs):
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
            "--target-database",
            "studynexs_restore_drill",
        ],
    )

    assert restore_postgres_backup.main() == 0
    output = json.loads(capsys.readouterr().out)

    assert output["status"] == "pass"
    assert output["target_database"] == "studynexs_restore_drill"
    assert output["verify_result"] == "7"
    assert commands[0][:3] == ["dropdb", "-U", "studynexs"]
    assert commands[1][:3] == ["createdb", "-U", "studynexs"]
    assert commands[2][0] == "pg_restore"
    assert commands[3][0] == "psql"
    assert commands[4][:3] == ["dropdb", "-U", "studynexs"]

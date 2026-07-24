"""Certification runtime configuration regressions."""
from __future__ import annotations

from pathlib import Path


def test_dev_compose_runs_background_worker():
    compose = (
        Path(__file__).resolve().parents[3]
        / "infra"
        / "docker"
        / "docker-compose.dev.yml"
    ).read_text(encoding="utf-8")

    assert "container_name: studynexs-worker" in compose
    assert "command: arq app.core.jobs.worker.WorkerSettings" in compose
    assert "healthcheck:\n      disable: true" in compose
    assert "REDIS_URL=redis://redis:6379/0" in compose

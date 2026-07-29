#!/usr/bin/env python3
"""Read-only production operations preflight.

This script is intentionally conservative: it checks deployment sync, running
services, runtime readiness, and operational metrics without mutating product
data. It is suitable before a guided pilot session, after deployment, and after
rollback/recovery.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_COMPOSE_FILE = REPO_ROOT / "infra" / "docker" / "docker-compose.dev.yml"
DEFAULT_REQUIRED_SERVICES = ("postgres", "redis", "qdrant", "api", "worker", "nginx")
_SAMPLE_RE = re.compile(
    r"^(?P<name>[a-zA-Z_:][a-zA-Z0-9_:]*)(?:\{(?P<labels>[^}]*)\})?"
    r"\s+(?P<value>[-+0-9.eE]+)$"
)
_LABEL_RE = re.compile(r'(?P<key>[a-zA-Z_][a-zA-Z0-9_]*)="(?P<value>(?:[^"\\]|\\.)*)"')


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    detail: str

    def as_dict(self) -> dict[str, str]:
        return {"name": self.name, "status": self.status, "detail": self.detail}


def _run(
    args: list[str],
    *,
    cwd: Path = REPO_ROOT,
    timeout: int = 30,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def _http_json(url: str, *, timeout: int = 5) -> tuple[dict[str, Any] | None, str | None]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            return json.loads(body), None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return None, str(exc)


def _http_text(
    url: str,
    *,
    timeout: int = 5,
    headers: dict[str, str] | None = None,
) -> tuple[str | None, str | None]:
    try:
        request = urllib.request.Request(url, headers=headers or {})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8"), None
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
        return None, str(exc)


def parse_prometheus_samples(text: str) -> list[dict[str, Any]]:
    """Parse the simple Prometheus exposition samples used by H6/H7 checks."""

    samples: list[dict[str, Any]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = _SAMPLE_RE.match(line)
        if not match:
            continue
        labels = {
            label.group("key"): label.group("value").replace(r"\"", '"')
            for label in _LABEL_RE.finditer(match.group("labels") or "")
        }
        samples.append(
            {
                "name": match.group("name"),
                "labels": labels,
                "value": float(match.group("value")),
            }
        )
    return samples


def check_git_sync(remote_ref: str) -> Check:
    status = _run(["git", "status", "--porcelain"])
    if status.returncode != 0:
        return Check("git_status", "fail", status.stderr.strip() or "git status failed")
    if status.stdout.strip():
        return Check("git_status", "fail", "working tree is not clean")

    head = _run(["git", "rev-parse", "HEAD"])
    remote = _run(["git", "rev-parse", remote_ref])
    if head.returncode != 0 or remote.returncode != 0:
        detail = (head.stderr + remote.stderr).strip() or f"cannot resolve {remote_ref}"
        return Check("git_sync", "fail", detail)
    if head.stdout.strip() != remote.stdout.strip():
        return Check(
            "git_sync",
            "fail",
            f"HEAD {head.stdout.strip()} != {remote_ref} {remote.stdout.strip()}",
        )
    return Check("git_sync", "pass", f"HEAD matches {remote_ref}: {head.stdout.strip()}")


def check_docker_services(compose_file: Path, required_services: tuple[str, ...]) -> Check:
    result = _run(
        [
            "docker",
            "compose",
            "-f",
            str(compose_file),
            "ps",
            "--status",
            "running",
            "--services",
        ],
        timeout=45,
    )
    if result.returncode != 0:
        return Check("docker_services", "fail", result.stderr.strip() or "docker compose ps failed")
    running = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    missing = sorted(set(required_services) - running)
    if missing:
        return Check("docker_services", "fail", f"missing running services: {', '.join(missing)}")
    return Check(
        "docker_services",
        "pass",
        f"running services include: {', '.join(sorted(required_services))}",
    )


def check_ready(base_url: str) -> Check:
    payload, error = _http_json(f"{base_url.rstrip('/')}/ready")
    if error:
        return Check("runtime_ready", "fail", error)
    if payload and payload.get("status") == "ready":
        checks = payload.get("checks") or {}
        return Check("runtime_ready", "pass", f"ready checks: {json.dumps(checks, sort_keys=True)}")
    return Check("runtime_ready", "fail", f"unexpected ready payload: {payload}")


def check_metrics(base_url: str, *, max_job_age_seconds: int) -> Check:
    text, error = _http_text(f"{base_url.rstrip('/')}/metrics")
    if error:
        return Check("platform_metrics", "fail", error)
    return _check_metrics_text(text or "", max_job_age_seconds=max_job_age_seconds)


def check_metrics_auth(base_url: str, *, token: str, max_job_age_seconds: int) -> Check:
    """Verify production-style metrics auth and then run the normal metrics check."""

    if not token:
        return Check("platform_metrics_auth", "fail", "metrics token is required")

    _, unauth_error = _http_text(f"{base_url.rstrip('/')}/metrics")
    if unauth_error is None or "401" not in unauth_error:
        return Check(
            "platform_metrics_auth",
            "fail",
            "unauthenticated metrics scrape did not fail with 401",
        )

    text, auth_error = _http_text(
        f"{base_url.rstrip('/')}/metrics",
        headers={"Authorization": f"Bearer {token}"},
    )
    if auth_error:
        return Check("platform_metrics_auth", "fail", auth_error)

    metrics_result = _check_metrics_text(text or "", max_job_age_seconds=max_job_age_seconds)
    if metrics_result.status != "pass":
        return Check("platform_metrics_auth", "fail", metrics_result.detail)
    return Check(
        "platform_metrics_auth",
        "pass",
        "unauthenticated scrape rejected; authenticated scrape passed",
    )


def _check_metrics_text(text: str, *, max_job_age_seconds: int) -> Check:
    samples = parse_prometheus_samples(text)

    scrape_errors = [
        sample
        for sample in samples
        if sample["name"] == "studynexs_job_status_scrape_error" and sample["value"] > 0
    ]
    if scrape_errors:
        return Check("platform_metrics", "fail", "job status scrape error is non-zero")

    failed_jobs = [
        sample
        for sample in samples
        if sample["name"] == "studynexs_job_status_current"
        and sample["labels"].get("status") == "failed"
        and sample["value"] > 0
    ]
    if failed_jobs:
        return Check("platform_metrics", "fail", f"failed job backlog: {failed_jobs}")

    stale_jobs = [
        sample
        for sample in samples
        if sample["name"] == "studynexs_job_status_oldest_age_seconds"
        and sample["labels"].get("status") in {"queued", "running"}
        and sample["value"] > max_job_age_seconds
    ]
    if stale_jobs:
        return Check("platform_metrics", "fail", f"stale job backlog: {stale_jobs}")

    return Check("platform_metrics", "pass", "metrics reachable; no failed/stale job backlog")


def _overall(checks: list[Check]) -> str:
    if any(check.status == "fail" for check in checks):
        return "fail"
    if any(check.status == "warn" for check in checks):
        return "warn"
    return "pass"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run StudyNexs production operations checks.")
    parser.add_argument("--base-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument(
        "--remote-ref",
        default="studynexs-github/develop",
        help="Canonical remote ref expected to match HEAD.",
    )
    parser.add_argument(
        "--compose-file",
        default=str(DEFAULT_COMPOSE_FILE),
        help="Docker Compose file used for service checks.",
    )
    parser.add_argument(
        "--required-services",
        default=",".join(DEFAULT_REQUIRED_SERVICES),
        help="Comma-separated Compose services that must be running.",
    )
    parser.add_argument(
        "--max-job-age-seconds",
        type=int,
        default=1800,
        help="Queued/running job age threshold before failing preflight.",
    )
    parser.add_argument(
        "--metrics-token",
        default="",
        help="When set, verify unauthenticated metrics fail and bearer-token scrape succeeds.",
    )
    parser.add_argument("--skip-git", action="store_true", help="Skip git synchronization check.")
    parser.add_argument(
        "--skip-docker",
        action="store_true",
        help="Skip Docker Compose service check.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON only.")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    checks: list[Check] = []

    if not args.skip_git:
        checks.append(check_git_sync(args.remote_ref))
    if not args.skip_docker:
        required = tuple(
            service.strip() for service in args.required_services.split(",") if service.strip()
        )
        checks.append(check_docker_services(Path(args.compose_file), required))
    checks.append(check_ready(args.base_url))
    if args.metrics_token:
        checks.append(
            check_metrics_auth(
                args.base_url,
                token=args.metrics_token,
                max_job_age_seconds=args.max_job_age_seconds,
            )
        )
    else:
        checks.append(check_metrics(args.base_url, max_job_age_seconds=args.max_job_age_seconds))

    overall = _overall(checks)
    payload = {"status": overall, "checks": [check.as_dict() for check in checks]}

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for check in checks:
            print(f"[{check.status.upper()}] {check.name}: {check.detail}")
        print(f"Overall: {overall.upper()}")

    return 0 if overall == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

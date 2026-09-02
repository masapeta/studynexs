"""Small live-QA client for reproducible StudyNexs audit probes."""
from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE_URL = os.environ.get("QA_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


@dataclass
class Response:
    status: int
    body: Any
    elapsed_ms: float


def require_write_enabled() -> None:
    if os.environ.get("QA_ALLOW_WRITE") != "1":
        raise SystemExit(
            "This probe changes test data. Set QA_ALLOW_WRITE=1 explicitly to continue."
        )


def call(
    method: str,
    path: str,
    *,
    tenant: str,
    token: str | None = None,
    body: dict[str, Any] | None = None,
    timeout: int = 180,
) -> Response:
    payload = json.dumps(body).encode() if body is not None else None
    request = Request(BASE_URL + path, data=payload, method=method)
    request.add_header("Content-Type", "application/json")
    request.add_header("X-Tenant-Slug", tenant)
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    started = time.monotonic()
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode(errors="replace")
            status = response.status
    except HTTPError as exc:
        raw = exc.read().decode(errors="replace")
        status = exc.code
    elapsed_ms = (time.monotonic() - started) * 1000
    try:
        parsed: Any = json.loads(raw)
    except json.JSONDecodeError:
        parsed = raw
    return Response(status, parsed, elapsed_ms)


def login(tenant: str, username: str, password: str) -> str:
    response = call(
        "POST",
        "/api/v1/auth/login",
        tenant=tenant,
        body={"username": username, "password": password},
        timeout=30,
    )
    if response.status != 200 or not isinstance(response.body, dict):
        raise SystemExit(f"Login failed for {tenant}/{username}: HTTP {response.status}")
    token = response.body.get("access_token")
    if not token:
        raise SystemExit(f"Login response did not contain an access token: {response.body}")
    return str(token)


def sql(query: str) -> str:
    process = subprocess.run(
        [
            "docker",
            "exec",
            os.environ.get("QA_POSTGRES_CONTAINER", "studynexs-postgres"),
            "psql",
            "-U",
            os.environ.get("QA_POSTGRES_USER", "studynexs"),
            "-d",
            os.environ.get("QA_POSTGRES_DB", "studynexs"),
            "-tAc",
            query,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if process.returncode:
        raise SystemExit(f"Postgres probe failed: {process.stderr.strip()[:300]}")
    return process.stdout.strip()


def env(name: str, default: str | None = None) -> str:
    value = os.environ.get(name, default)
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value

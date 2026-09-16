"""P1 exam/marks live traces against the reference tenant."""
from __future__ import annotations

import json
import urllib.request

BASE, TENANT = "http://127.0.0.1:8000", "reference"


def _post(path, body, token=None):
    req = urllib.request.Request(f"{BASE}{path}", data=json.dumps(body).encode(), method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("X-Tenant-Slug", TENANT)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


tok = _post("/api/v1/auth/login", {"username": "principal", "password": "Demo@1234"})["access_token"]

for q in (
    "show me the marks of ARM0242",
    "how did ARM0242 do in Mathematics",
    "top 5 students in Class 10 A",
    "who scored highest in Science in Class 10 A",
    "did ARM0242 pass",  # honesty: no pass/fail concept
):
    d = (_post("/api/v1/workspace/assistant/turn", {"text": q}, tok)).get("data", {})
    b, tr = d.get("block", {}), d.get("trace", {})
    n = len(b.get("rows", []) or []) if b.get("kind") == "table" else "-"
    print(f"Q: {q}")
    print(f"   route={tr.get('route')} cap={tr.get('capability')} kind={b.get('kind')} rows={n}")
    print(f"   title={b.get('title')}")
    if b.get("kind") == "table" and b.get("rows"):
        print(f"   first_row={b['rows'][0]}")
    print()

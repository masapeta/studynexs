"""P0 execution traces — current vs historical relationship, and historical transactional."""
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
    "who is the class teacher of 2A?",
    "who was the class teacher of 2A in August?",
    "which class is ARM0218 in?",
    "which class was ARM0218 in last year?",
    "fee collected in August",
):
    d = (_post("/api/v1/workspace/assistant/turn", {"text": q}, tok)).get("data", {})
    b, tr = d.get("block", {}), d.get("trace", {})
    guard = tr.get("historical_guard")
    trng = tr.get("time_range") or {}
    print(f"Q: {q}")
    print(f"   route={tr.get('route')} cap={tr.get('capability')} action={tr.get('action')} "
          f"kind={b.get('kind')} temporality={trng.get('temporality')} "
          f"guard={guard.get('decision') if guard else None}")
    print(f"   title={b.get('title')}\n")

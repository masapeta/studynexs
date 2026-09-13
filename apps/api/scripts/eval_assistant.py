"""Assistant evaluation harness — runs NL questions against the live assistant.

Logs in as the reference-tenant principal and prints each turn's result kind,
title, and row/metric count. Usage:  python scripts/eval_assistant.py
"""

from __future__ import annotations

import json
import sys
import urllib.request

BASE = "http://127.0.0.1:8000"
TENANT = "reference"
USERNAME = "principal"
PASSWORD = "Demo@1234"

QUESTIONS = [
    # A/B/C structured + relationship
    "attendance % of ARM0218",
    "give list of teachers and respective class as table",
    "who is the class teacher of 2A",
    "what subjects does Deepak Kumar teach",
    "students in 2A",
    "students with attendance below 75%",
    "fee balance of ARM0218",
    "students with fees pending over 50%",
    "list all staff",
    # F temporal
    "how much fee was collected today",
    "fee collected this month",
    "attendance of ARM0218 this month",
    "fee collected between 2026-08-01 and 2026-08-31",
    # D document (no policy store -> honest guide)
    "what is the school's attendance policy",
    # E mixed (structured + policy)
    "ARM0218 has attendance below 75%. What does the attendance policy say?",
]


def _post(path: str, body: dict, token: str | None = None) -> dict:
    data = json.dumps(body).encode()
    req = urllib.request.Request(f"{BASE}{path}", data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("X-Tenant-Slug", TENANT)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def login() -> str:
    try:
        res = _post("/api/v1/auth/login", {"username": USERNAME, "password": PASSWORD})
        token = res.get("access_token") or (res.get("data") or {}).get("access_token")
        if token:
            return token
        print(f"LOGIN: no token in response: {res}")
    except Exception as exc:  # noqa: BLE001
        print(f"login failed: {exc}")
    sys.exit(1)


def summarize(block: dict) -> str:
    kind = block.get("kind")
    title = block.get("title", "")
    if kind == "table":
        return f"table · {title} · {len(block.get('rows', []))} rows"
    if kind == "metrics":
        metrics = block.get("metrics", [])
        vals = ", ".join(f"{m['label']}={m.get('value')}" for m in metrics)
        return f"metrics · {title} · [{vals}]" + (
            f" · {block['message']}" if block.get("message") else ""
        )
    if kind == "clarify":
        return f"clarify · {title} · {len(block.get('options', []))} options"
    if kind == "document":
        return f"document · {title} · {len(block.get('citations', []))} citations"
    if kind == "mixed":
        data = block.get("data") or {}
        doc = block.get("document") or {}
        return f"mixed · data[{data.get('kind')}] + document[{doc.get('kind')}]"
    if kind in ("not_found", "guide", "navigate", "error"):
        return f"{kind} · {title}"
    return f"{kind} · {title}"


def main() -> None:
    token = login()
    session_id: str | None = None
    for q in QUESTIONS:
        try:
            res = _post(
                "/api/v1/workspace/assistant/turn",
                {"text": q, "session_id": session_id},
                token,
            )
            data = res.get("data") or res
            block = data.get("block") or {}
            session_id = data.get("session_id") or session_id
            print(f"Q: {q}\n   -> {summarize(block)}\n")
        except Exception as exc:  # noqa: BLE001
            print(f"Q: {q}\n   -> ERROR {exc}\n")


if __name__ == "__main__":
    main()

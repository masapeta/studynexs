"""Quick smoke: generate a small question paper via the live API."""
from __future__ import annotations

import sys
import time

import httpx

BASE = "http://localhost:8000"
H = {"X-Tenant-Slug": "test"}


def main() -> int:
    client = httpx.Client(timeout=240)
    login = client.post(
        f"{BASE}/api/v1/auth/login",
        headers=H,
        json={"username": "principal", "password": "Demo@1234"},
    )
    if login.status_code >= 400:
        print("login failed", login.status_code, login.text[:200])
        return 1
    body = login.json()
    token = body.get("access_token") or (body.get("data") or {}).get("access_token")
    H["Authorization"] = f"Bearer {token}"

    classes = client.get(f"{BASE}/api/v1/academic/classes?page_size=100", headers=H).json()
    items = classes.get("items") or classes.get("data") or []
    c10 = next((c for c in items if c.get("grade") == "Class 10"), items[0])
    cid = c10["id"]
    subs = client.get(f"{BASE}/api/v1/academic/subjects?class_id={cid}", headers=H).json()
    sitems = subs.get("items") or subs.get("data") or subs
    subj = next((s for s in sitems if s.get("name") == "Mathematics"), sitems[0])
    sid = subj["id"]

    payload = {
        "class_id": cid,
        "subject_id": sid,
        "topics": ["Real Numbers", "Polynomials"],
        "total_marks": 50,
        "duration_minutes": 90,
        "difficulty": "balanced",
    }
    t0 = time.perf_counter()
    r = client.post(f"{BASE}/api/v1/ai/question-papers/generate", headers=H, json=payload)
    elapsed = round(time.perf_counter() - t0, 1)
    print(f"status={r.status_code} elapsed={elapsed}s")
    if r.status_code == 200:
        print("title:", r.json().get("title"))
        return 0
    print(r.text[:400])
    return 1


if __name__ == "__main__":
    sys.exit(main())

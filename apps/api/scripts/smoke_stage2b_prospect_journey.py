#!/usr/bin/env python3
"""Stage 2B smoke — self-guided prospect tenant provisioning through onboarding entry.

Run from apps/api (API + Postgres required; DEMO provisioning enabled in dev/testing):
  python scripts/smoke_stage2b_prospect_journey.py

Does not call live AI — validates provision -> auth -> onboarding API reachability -> cleanup.
"""
from __future__ import annotations

import asyncio
import os
import sys
import uuid
from pathlib import Path

import httpx

# Allow `from app.*` when run as `python scripts/smoke_stage2b_prospect_journey.py`
_API_ROOT = Path(__file__).resolve().parents[1]
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))

API = os.environ.get("SMOKE_API_URL", "http://127.0.0.1:8000").rstrip("/")


async def main() -> int:
    async with httpx.AsyncClient(base_url=API, timeout=60.0) as client:
        print("1. POST /api/v1/demo/sessions")
        r = await client.post("/api/v1/demo/sessions", json={"display_name": "Smoke Prospect"})
        if r.status_code != 201:
            print(f"FAIL provision: {r.status_code} {r.text}")
            return 1
        session = r.json()["data"]
        slug = session["tenant_slug"]
        token = session["access_token"]
        session_token = session.get("session_token")
        school_id = session["school_id"]
        headers = {"Authorization": f"Bearer {token}", "X-Tenant-Slug": slug}
        print(f"   tenant={slug} school_id={school_id}")
        if not session_token:
            print("FAIL: missing session_token in provision response")
            return 1

        print("2. POST /api/v1/demo/sessions/renew (72h session exchange)")
        renew = await client.post(
            "/api/v1/demo/sessions/renew",
            json={"session_token": session_token},
            headers={"X-Tenant-Slug": slug},
        )
        if renew.status_code != 200:
            print(f"FAIL renew: {renew.status_code} {renew.text}")
            return 1
        token = renew.json()["data"]["access_token"]
        headers["Authorization"] = f"Bearer {token}"
        print("   renewed access token")

        print("3. GET /api/v1/users/me (tenant-scoped)")
        me = await client.get("/api/v1/users/me", headers=headers)
        if me.status_code != 200:
            print(f"FAIL me: {me.status_code} {me.text}")
            return 1
        role = me.json().get("role") or me.json().get("data", {}).get("role")
        print(f"   role={role}")

        print("4. GET /api/v1/academic/classes")
        classes = await client.get("/api/v1/academic/classes", headers=headers)
        if classes.status_code != 200:
            print(f"FAIL classes: {classes.status_code} {classes.text}")
            return 1
        class_rows = classes.json().get("items") or []
        if not class_rows:
            print("FAIL: expected at least one class in prospect tenant")
            return 1
        print(f"   classes={len(class_rows)}")

        print("5. GET /api/v1/curriculum/packs (Stage 2A curriculum entry — empty OK)")
        packs = await client.get("/api/v1/curriculum/packs", headers=headers)
        if packs.status_code != 200:
            print(f"FAIL packs: {packs.status_code} {packs.text}")
            return 1
        print("   curriculum API reachable")

        print("6. Inline cleanup (prospect tenant only)")
        try:
            from app.core.database import async_session_factory
            from app.modules.demo.services.demo_session_service import DemoSessionService

            async with async_session_factory() as db:
                await DemoSessionService(db).purge_now(uuid.UUID(school_id))
            print("   purged via service")
        except Exception as exc:
            print(f"FAIL purge: {exc}")
            return 1

        verify = await client.get("/api/v1/users/me", headers=headers)
        if verify.status_code not in (404, 410):
            print(f"WARN: tenant still reachable after purge: {verify.status_code}")

        print("PASS Stage 2B prospect journey smoke")
        return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

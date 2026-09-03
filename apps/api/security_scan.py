import asyncio

import httpx

BASE_URL = "http://localhost:8000/api/v1"

async def check_unauthorized(client: httpx.AsyncClient, endpoint: str):
    print(f"Checking unauthorized access to {endpoint}...")
    resp = await client.get(endpoint)
    if resp.status_code == 401:
        print(f"  [PASS] {endpoint} blocked (401)")
    else:
        print(f"  [FAIL] {endpoint} returned {resp.status_code}")

async def run_security_check():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # Protected routes
        endpoints = [
            "/users/me",
            "/academic/classes",
            "/attendance/class/" + str(httpx.QueryParams({"date": "2026-01-01"})),
            "/fees/pay"
        ]

        for ep in endpoints:
            await check_unauthorized(client, ep)

if __name__ == "__main__":
    asyncio.run(run_security_check())

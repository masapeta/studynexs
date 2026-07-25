"""Tests — Health & Readiness probes."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "StudyNexs" in data["service"]


@pytest.mark.asyncio
async def test_ready(client: AsyncClient):
    resp = await client.get("/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("ready", "degraded")


@pytest.mark.asyncio
async def test_metrics_returns_prometheus_text(client: AsyncClient):
    """Regression: /metrics must serve Prometheus text, not demand a `request` query param.

    A stringized `Request` annotation with the import hidden inside the function made FastAPI
    treat `request` as a required query parameter, so the scrape endpoint 422'd (and crashed
    when a value was supplied). It must respond with text/plain and no required params.
    """
    resp = await client.get("/metrics")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/plain")
    assert "studynexs_platform_uptime_seconds" in resp.text
    assert "studynexs_http_requests_total" in resp.text
    assert "studynexs_ai_llm_requests_total" in resp.text

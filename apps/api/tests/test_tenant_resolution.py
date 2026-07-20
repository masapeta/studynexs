"""Unit tests for tenant slug extraction — shared API host (P0-01)."""

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.core.config import Environment
from app.core.tenant import extract_tenant_slug, subdomain_slug_from_host


def _request(host: str, *, tenant_header: str = "") -> Request:
    headers: list[tuple[bytes, bytes]] = [(b"host", host.encode())]
    if tenant_header:
        headers.append((b"x-tenant-slug", tenant_header.encode()))
    scope = {"type": "http", "headers": headers, "method": "GET", "path": "/api/v1/users"}
    return Request(scope)


def _prod_settings_mock() -> MagicMock:
    mock = MagicMock()
    mock.TENANT_BASE_DOMAIN = "studynexs.com"
    mock.TENANT_RESERVED_SUBDOMAINS = [
        "api",
        "app",
        "demo",
        "dev",
        "test",
        "admin",
        "www",
    ]
    mock.is_development = False
    mock.ENVIRONMENT = Environment.PRODUCTION
    mock.DEFAULT_TENANT_SLUG = "dev"
    return mock


def test_subdomain_slug_from_host_school_tenant():
    assert subdomain_slug_from_host("dps.studynexs.com", "studynexs.com") == "dps"


def test_subdomain_slug_from_host_reserved_api():
    assert subdomain_slug_from_host("api.studynexs.com", "studynexs.com") is None


def test_subdomain_slug_from_host_reserved_www():
    assert subdomain_slug_from_host("www.studynexs.com", "studynexs.com") is None


def test_extract_tenant_slug_api_host_uses_header(monkeypatch):
    monkeypatch.setattr("app.core.tenant.get_settings", _prod_settings_mock)
    req = _request("api.studynexs.com", tenant_header="dps")
    assert extract_tenant_slug(req) == "dps"


def test_extract_tenant_slug_api_host_without_header_raises_in_production(monkeypatch):
    monkeypatch.setattr("app.core.tenant.get_settings", _prod_settings_mock)
    req = _request("api.studynexs.com")
    with pytest.raises(HTTPException) as exc:
        extract_tenant_slug(req)
    assert exc.value.status_code == 400


def test_extract_tenant_slug_school_subdomain_ignores_header(monkeypatch):
    monkeypatch.setattr("app.core.tenant.get_settings", _prod_settings_mock)
    req = _request("dps.studynexs.com", tenant_header="other")
    assert extract_tenant_slug(req) == "dps"

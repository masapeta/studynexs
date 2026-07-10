"""Commit-before-response guarantee (CommitOnSuccessRoute + get_db).

On this FastAPI version, generator-dependency teardown runs AFTER the response is sent, so
committing in get_db's teardown would turn a commit-time failure into a silent 2xx with lost
data. CommitOnSuccessRoute commits before the response is sent instead. These tests guard the
mechanism (real route class + real get_db, with a fake session factory) and its coverage.
"""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.routing import APIRoute
from starlette.testclient import TestClient

import app.core.database as database
from app.core.api_route import CommitOnSuccessRoute
from app.core.database import get_db
from app.main import app as real_app


def _all_api_routes():
    """Yield every APIRoute in the real app, descending into included routers."""
    for r in real_app.routes:
        if type(r).__name__ == "_IncludedRouter":
            for sub in getattr(getattr(r, "original_router", None), "routes", []):
                if isinstance(sub, APIRoute):
                    yield sub
        elif isinstance(r, APIRoute):
            yield r


def test_all_domain_routes_commit_before_response():
    """Every /api/v1 route must use CommitOnSuccessRoute so writes commit in-request.

    Only the parameterless system probes (/health, /ready, /metrics) — which never touch the
    DB — may skip it. Fails if a new router forgets route_class=CommitOnSuccessRoute.
    """
    exempt = {"/health", "/ready", "/metrics"}
    offenders = [
        r.path
        for r in _all_api_routes()
        if r.path not in exempt and not isinstance(r, CommitOnSuccessRoute)
    ]
    assert not offenders, f"routes not committing before response: {offenders}"


class _FakeSession:
    def __init__(self, fail_commit: bool = False):
        self.fail_commit = fail_commit
        self.committed = False
        self.rolled_back = False

    async def commit(self):
        if self.fail_commit:
            raise RuntimeError("simulated commit failure")
        self.committed = True

    async def rollback(self):
        self.rolled_back = True


def _mini_app(session: _FakeSession) -> FastAPI:
    """A throwaway app that uses the REAL CommitOnSuccessRoute and REAL get_db, with the
    session factory swapped for a fake — so we test the actual mechanism without a database."""

    @asynccontextmanager
    async def fake_factory():
        yield session

    # get_db does `async with async_session_factory() as session: request.state.db_session = ...`
    database.async_session_factory = fake_factory  # type: ignore[assignment]

    from fastapi import APIRouter

    mini = FastAPI()
    router = APIRouter(route_class=CommitOnSuccessRoute)

    @router.get("/ok")
    async def ok(db=Depends(get_db)):
        return {"ok": True}

    @router.get("/boom")
    async def boom(db=Depends(get_db)):
        raise ValueError("endpoint error")

    mini.include_router(router)
    return mini


def test_commit_happens_on_success():
    original = database.async_session_factory
    session = _FakeSession()
    try:
        mini = _mini_app(session)
        client = TestClient(mini, raise_server_exceptions=False)
        resp = client.get("/ok")
        assert resp.status_code == 200
        assert session.committed is True  # committed before the response
    finally:
        database.async_session_factory = original


def test_commit_failure_surfaces_as_5xx():
    original = database.async_session_factory
    session = _FakeSession(fail_commit=True)
    try:
        mini = _mini_app(session)
        client = TestClient(mini, raise_server_exceptions=False)
        resp = client.get("/ok")
        assert resp.status_code >= 500  # a commit-time failure must NOT be a false 2xx
        assert session.committed is False
    finally:
        database.async_session_factory = original


def test_endpoint_error_rolls_back_and_does_not_commit():
    original = database.async_session_factory
    session = _FakeSession()
    try:
        mini = _mini_app(session)
        client = TestClient(mini, raise_server_exceptions=False)
        resp = client.get("/boom")
        assert resp.status_code >= 500
        assert session.committed is False
        assert session.rolled_back is True  # get_db rolls back on error
    finally:
        database.async_session_factory = original

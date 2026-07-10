"""Route class that commits the request's DB session BEFORE the response is sent.

Background: FastAPI (>=0.106) runs generator-dependency teardown AFTER the response has been
sent to the client. `get_db` therefore cannot safely commit in its teardown — a failure at
COMMIT time (connection drop, serialization failure, deferred-constraint violation) would land
after the client already received a 2xx, silently losing the write.

This route class closes that gap: after the endpoint has produced its (already-serialized)
response but before Starlette sends it, it commits the session stashed on `request.state` by
`get_db`. If the commit fails, the exception propagates and FastAPI returns a 5xx — the client
never sees a false success. `get_db` no longer commits; it only rolls back on error and closes.

Every module's APIRouter is constructed with `route_class=CommitOnSuccessRoute` (see
tests/test_commit_route.py, which asserts full coverage so a new router can't silently opt out).
Endpoints that don't use `get_db` (health/ready/metrics) simply have no session to commit.
"""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import Request, Response
from fastapi.routing import APIRoute


class CommitOnSuccessRoute(APIRoute):
    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        original = super().get_route_handler()

        async def commit_on_success(request: Request) -> Response:
            response = await original(request)
            session = getattr(request.state, "db_session", None)
            # Only commit a successful response. Error responses (>=400) and raised exceptions
            # leave the transaction to be rolled back by get_db's teardown.
            if session is not None and response.status_code < 400:
                await session.commit()
            return response

        return commit_on_success

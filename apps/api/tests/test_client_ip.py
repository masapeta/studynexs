"""H2 — auth rate-limit client IP must not be spoofable. Trust X-Real-IP (from our proxy)
and the socket peer; never the client-supplied left-most X-Forwarded-For.
"""
from starlette.requests import Request

from app.modules.auth.endpoints.auth import _get_client_ip

PEER = "203.0.113.9"


def _request(headers: dict, client=(PEER, 4444)) -> Request:
    return Request({
        "type": "http",
        "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
        "client": client,
    })


def test_trusts_x_real_ip():
    req = _request({"X-Real-IP": "10.0.0.5", "X-Forwarded-For": "1.2.3.4"})
    assert _get_client_ip(req) == "10.0.0.5"


def test_ignores_spoofable_forwarded_for():
    # No X-Real-IP → the client-supplied XFF must be ignored; use the real socket peer.
    req = _request({"X-Forwarded-For": "1.2.3.4, 9.9.9.9"})
    assert _get_client_ip(req) == PEER


def test_falls_back_to_socket_peer():
    assert _get_client_ip(_request({})) == PEER

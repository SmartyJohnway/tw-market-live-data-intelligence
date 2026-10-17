from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient
from starlette.responses import JSONResponse

from server.local_network_boundary import ERROR_CODE, LocalNetworkBoundaryMiddleware, is_loopback_network_scope
from server.main import app


def _client(*, client=("127.0.0.1", 50123), server=("127.0.0.1", 8000)):
    return TestClient(app, client=client, base_url=f"http://{server[0]}/")


def test_ipv4_and_ipv6_loopback_socket_addresses_are_accepted():
    assert is_loopback_network_scope({"client": ("127.0.0.1", 1234), "server": ("127.0.0.1", 8000)})
    assert is_loopback_network_scope({"client": ("::1", 1234), "server": ("::1", 8000)})
    assert _client().get("/api/health").status_code == 200

    sent = []
    async def downstream(scope, receive, send):
        await JSONResponse({"ok": True})(scope, receive, send)
    async def invoke_ipv6_scope():
        middleware = LocalNetworkBoundaryMiddleware(downstream)
        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}
        async def send(message):
            sent.append(message)
        await middleware({"type": "http", "method": "GET", "path": "/api/health", "headers": [], "client": ("::1", 50123), "server": ("::1", 8000)}, receive, send)
    asyncio.run(invoke_ipv6_scope())
    assert sent[0]["status"] == 200


def test_non_loopback_client_or_server_is_rejected():
    assert not is_loopback_network_scope({"client": ("192.168.20.3", 1234), "server": ("127.0.0.1", 8000)})
    assert not is_loopback_network_scope({"client": ("127.0.0.1", 1234), "server": ("192.0.2.20", 8000)})
    assert not is_loopback_network_scope({"client": ("2001:db8::12", 1234), "server": ("::1", 8000)})
    assert not is_loopback_network_scope({"client": ("2001:db8::12", 1234), "server": ("198.51.100.9", 8000)})


def test_synthetic_non_ip_scope_is_an_in_process_asgi_transport():
    assert is_loopback_network_scope({"client": ("in-process-peer", 1234), "server": ("asgi-server", 8000)})
    assert _client().get("/api/health").status_code == 200


def test_known_remote_scope_rejected_despite_spoofed_forwarding_headers():
    response = _client(client=("192.0.2.44", 50123)).get(
        "/api/health",
        headers={"X-Forwarded-For": "127.0.0.1", "X-Real-IP": "127.0.0.1", "Forwarded": "for=127.0.0.1", "Host": "localhost", "Origin": "http://localhost"},
    )
    assert response.status_code == 403
    assert response.json() == {"error": ERROR_CODE}
    assert response.headers["cache-control"] == "no-store"


def test_entire_fastapi_request_surface_rejects_remote_client():
    paths = (
        "/api/health",                 # health/status
        "/api/unified/capabilities",   # Unified API
        "/api/governance",             # retained non-Unified API
        "/workbench/",                 # workbench/static surface
        "/openapi.json",               # OpenAPI
        "/docs",                       # interactive API docs
    )
    with _client(client=("198.51.100.7", 9000)) as client:
        for path in paths:
            response = client.get(path)
            assert response.status_code == 403, path
            assert response.json() == {"error": ERROR_CODE}, path


def test_remote_server_scope_is_rejected_even_with_loopback_client():
    response = _client(server=("198.51.100.8", 8000)).get("/api/health")
    assert response.status_code == 403
    assert response.json() == {"error": ERROR_CODE}


def test_rejection_body_is_stable_and_bounded():
    response = _client(client=("203.0.113.8", 10)).get("/api/health")
    assert response.status_code == 403
    assert response.json() == {"error": "local_service_loopback_required"}
    assert len(response.content) < 100
    assert "traceback" not in response.text.lower()
    assert "C:\\" not in response.text


def test_cors_is_browser_policy_not_network_access_control():
    remote = _client(client=("192.0.2.8", 9000)).get(
        "/api/health", headers={"Origin": "http://localhost:3000"}
    )
    assert remote.status_code == 403

    local = _client().get("/api/health", headers={"Origin": "https://untrusted.example"})
    assert local.status_code == 200
    assert "access-control-allow-origin" not in local.headers

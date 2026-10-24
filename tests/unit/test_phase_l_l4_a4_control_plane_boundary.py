from __future__ import annotations

import asyncio

import httpx
from fastapi.testclient import TestClient

from server.local_control_plane_boundary import (
    CONTROL_PLANE_ERROR,
    CONTENT_TYPE_ERROR,
    LEGACY_DISABLED,
    LOCAL_STATE_MUTATION,
    NETWORK_EXECUTION,
    POST_ROUTE_CLASSIFICATIONS,
    READ_OR_OFFLINE_PROJECTION,
    classify_post_path,
)
from server.main import app
from tests.post_route_surface import schema_post_paths_with_visibility_guard


PRIVILEGED_PATH = "/api/unified/authorizations"


async def _post(*, url="http://127.0.0.1:8000", origin=None, fetch_site=None,
                content_type="application/json", client_addr=("127.0.0.1", 54000),
                path=PRIVILEGED_PATH, headers=None):
    sent_headers = {"Content-Type": content_type}
    if origin is not None:
        sent_headers["Origin"] = origin
    if fetch_site is not None:
        sent_headers["Sec-Fetch-Site"] = fetch_site
    sent_headers.update(headers or {})
    transport = httpx.ASGITransport(app=app, client=client_addr)
    async with httpx.AsyncClient(transport=transport, base_url=url) as client:
        return await client.post(path, json={}, headers=sent_headers)


def test_every_fastapi_post_route_has_exactly_one_explicit_classification():
    actual = schema_post_paths_with_visibility_guard(app)
    assert actual == set(POST_ROUTE_CLASSIFICATIONS)
    assert {classify_post_path(path) for path in actual} == {
        READ_OR_OFFLINE_PROJECTION,
        LOCAL_STATE_MUTATION,
        NETWORK_EXECUTION,
        LEGACY_DISABLED,
    }


def test_route_classes_keep_read_mutation_execution_and_disabled_distinct():
    assert classify_post_path("/api/unified/validate-request") == READ_OR_OFFLINE_PROJECTION
    assert classify_post_path("/api/unified/preview-request") == READ_OR_OFFLINE_PROJECTION
    assert classify_post_path("/api/watchlists/wl-123/evidence-request-preview") == READ_OR_OFFLINE_PROJECTION
    assert classify_post_path("/api/unified/authorizations") == LOCAL_STATE_MUTATION
    assert classify_post_path("/api/unified/result-package") == LOCAL_STATE_MUTATION
    assert classify_post_path("/api/watchlist-mutations/preview") == LOCAL_STATE_MUTATION
    assert classify_post_path("/api/unified/executions") == NETWORK_EXECUTION
    assert classify_post_path("/api/unified/fetch-evidence") == NETWORK_EXECUTION
    assert classify_post_path("/api/m5k/live-observation/execute") == LEGACY_DISABLED
    assert classify_post_path("/api/m7g/controlled-refresh/execute") == LEGACY_DISABLED
    assert classify_post_path("/api/unified/not-a-route") is None


def test_cross_site_privileged_post_is_rejected_before_semantic_route():
    response = asyncio.run(_post(origin="https://attacker.example"))
    assert response.status_code == 403
    assert response.json() == {"error": CONTROL_PLANE_ERROR}
    assert response.headers["cache-control"] == "no-store"


def test_same_site_but_different_origin_is_rejected():
    response = asyncio.run(_post(origin="http://localhost:8000"))
    assert response.status_code == 403
    assert response.json() == {"error": CONTROL_PLANE_ERROR}


def test_different_port_or_scheme_is_not_same_origin():
    for origin in ("http://127.0.0.1:8001", "https://127.0.0.1:8000"):
        response = asyncio.run(_post(origin=origin))
        assert response.status_code == 403
        assert response.json() == {"error": CONTROL_PLANE_ERROR}


def test_origin_null_is_rejected():
    response = asyncio.run(_post(origin="null"))
    assert response.status_code == 403
    assert response.json() == {"error": CONTROL_PLANE_ERROR}


def test_cross_site_fetch_metadata_is_rejected():
    response = asyncio.run(_post(origin="http://127.0.0.1:8000", fetch_site="cross-site"))
    assert response.status_code == 403
    assert response.json() == {"error": CONTROL_PLANE_ERROR}


def test_same_site_fetch_metadata_is_rejected():
    response = asyncio.run(_post(origin="http://127.0.0.1:8000", fetch_site="same-site"))
    assert response.status_code == 403
    assert response.json() == {"error": CONTROL_PLANE_ERROR}


def test_same_origin_loopback_post_reaches_normal_route_validation():
    response = asyncio.run(_post(origin="http://127.0.0.1:8000", fetch_site="same-origin"))
    assert response.status_code == 422
    assert response.json() != {"error": CONTROL_PLANE_ERROR}


def test_same_origin_localhost_alias_is_supported():
    response = asyncio.run(_post(
        url="http://localhost:8000", origin="http://localhost:8000", fetch_site="same-origin"
    ))
    assert response.status_code == 422
    assert response.json() != {"error": CONTROL_PLANE_ERROR}


def test_native_local_caller_without_browser_headers_remains_supported():
    response = asyncio.run(_post())
    assert response.status_code == 422
    assert response.json() != {"error": CONTROL_PLANE_ERROR}


def test_privileged_post_requires_json_content_type():
    response = asyncio.run(_post(origin="http://127.0.0.1:8000", content_type="text/plain"))
    assert response.status_code == 415
    assert response.json() == {"error": CONTENT_TYPE_ERROR}
    response_with_charset = asyncio.run(_post(
        origin="http://127.0.0.1:8000", content_type="application/json; charset=utf-8"
    ))
    assert response_with_charset.status_code == 422


def test_forwarded_headers_cannot_make_remote_scope_local():
    response = asyncio.run(_post(
        origin="http://127.0.0.1:8000",
        client_addr=("192.0.2.44", 54000),
        headers={"X-Forwarded-For": "127.0.0.1", "X-Real-IP": "127.0.0.1"},
    ))
    assert response.status_code == 403
    assert response.json() == {"error": "local_service_loopback_required"}


def test_network_boundary_remains_outermost_for_remote_socket_evidence():
    response = asyncio.run(_post(
        origin="http://127.0.0.1:8000", client_addr=("198.51.100.24", 54000)
    ))
    assert response.status_code == 403
    assert response.json() == {"error": "local_service_loopback_required"}


def test_legacy_network_execution_routes_are_unconditionally_disabled(monkeypatch):
    from server import main

    calls = []
    monkeypatch.setattr(main, "_m5k_execute_live_observation", lambda *a, **k: calls.append("m5k"), raising=False)
    monkeypatch.setattr(main, "_m7g09_execute_controlled_refresh", lambda *a, **k: calls.append("m7g"), raising=False)
    client = TestClient(app)
    m5k = client.post("/api/m5k/live-observation/execute", json={"confirm_live_observation": True})
    m7g = client.post("/api/m7g/controlled-refresh/execute", json={"request_package": {}})
    assert m5k.status_code == 410
    assert m5k.json()["detail"]["error"] == "legacy_live_observation_execution_disabled"
    assert m7g.status_code == 410
    assert m7g.json()["detail"]["error"] == "legacy_controlled_refresh_execution_disabled"
    assert calls == []
    import inspect
    source = inspect.getsource(main)
    assert "execute_live_observation as _m5k_execute_live_observation" not in source
    assert "execute_m7g_controlled_manual_refresh as _m7g09_execute_controlled_refresh" not in source


def test_probe_endpoints_remain_disabled_and_unified_api_remains_fixed():
    client = TestClient(app)
    for name in ("twse", "tpex", "yahoo", "twse_mis", "finmind", "feasibility"):
        assert client.get(f"/api/probe/{name}").status_code == 410
    assert client.post("/api/unified/executions", json={}).status_code == 422


def test_cors_is_not_an_access_control_decision_for_read_routes():
    response = TestClient(app).get("/api/health", headers={"Origin": "https://attacker.example"})
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers

from __future__ import annotations

import asyncio
import json

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from server.unified_bounded_io import bounded_json_response, read_bounded_request_body
from server.unified_payload_bounds import MAX_UNIFIED_REQUEST_BYTES, MAX_UNIFIED_RESPONSE_BYTES
from server.unified_workbench_router import router


def _request(chunks: list[bytes], headers: list[tuple[bytes, bytes]] | None = None):
    messages = [{"type": "http.request", "body": chunk, "more_body": True} for chunk in chunks]
    messages.append({"type": "http.request", "body": b"", "more_body": False})
    calls = {"count": 0}

    async def receive():
        calls["count"] += 1
        return messages.pop(0)

    scope = {"type": "http", "method": "POST", "path": "/", "headers": headers or []}
    return Request(scope, receive), calls


@pytest.mark.parametrize("size", [7, 8])
def test_bounded_http_body_accepts_limit_minus_one_and_limit(size):
    request, _ = _request([b"x" * size])
    assert asyncio.run(read_bounded_request_body(request, 8)) == b"x" * size


def test_bounded_http_body_rejects_chunked_overflow_without_reading_later_chunks():
    request, calls = _request([b"x" * 5, b"y" * 4, b"must-not-be-read"])
    with pytest.raises(HTTPException) as caught:
        asyncio.run(read_bounded_request_body(request, 8))
    assert caught.value.status_code == 413
    assert caught.value.detail == "request_too_large"
    assert calls["count"] == 2


def test_bounded_http_body_rejects_trustworthy_oversized_content_length_before_read():
    request, calls = _request([], [(b"content-length", b"9")])
    with pytest.raises(HTTPException) as caught:
        asyncio.run(read_bounded_request_body(request, 8))
    assert caught.value.status_code == 413
    assert calls["count"] == 0


def test_all_unified_post_routes_use_common_bounded_body_reader():
    post_paths = {route.path for route in router.routes if "POST" in getattr(route, "methods", set())}
    assert post_paths == {
        "/api/unified/validate-request", "/api/unified/preview-request",
        "/api/unified/authorizations", "/api/unified/executions",
        "/api/unified/fetch-evidence", "/api/unified/result-package",
    }
    import inspect
    for route in router.routes:
        if "POST" in getattr(route, "methods", set()):
            assert "read_bounded_request_body" in inspect.getsource(route.endpoint)
            assert "request.body(" not in inspect.getsource(route.endpoint)


def test_unified_transport_authorities_remain_existing_values():
    from server.unified_mcp import local_service_client
    assert MAX_UNIFIED_REQUEST_BYTES == 1 * 1024 * 1024
    assert MAX_UNIFIED_RESPONSE_BYTES == 8 * 1024 * 1024
    assert local_service_client.MAX_REQUEST_BYTES == MAX_UNIFIED_REQUEST_BYTES
    assert local_service_client.MAX_RESPONSE_BYTES == MAX_UNIFIED_RESPONSE_BYTES


@pytest.mark.parametrize("size,accepted", [(63, True), (64, True), (65, False)])
def test_bounded_json_response_has_exact_limit_behavior(size, accepted):
    response = bounded_json_response({"x": "a" * (size - len('{"x":""}'))}, max_bytes=64)
    if accepted:
        assert response.status_code == 200
        assert len(response.body) <= 64
    else:
        assert response.status_code == 500
        assert json.loads(response.body) == {"error": "response_too_large"}


def test_catalog_and_execution_schema_bounds_remain_authoritative():
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    catalog = json.loads((root / "docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json").read_text(encoding="utf-8"))
    assert catalog["bounds"]["default_target_limit"] == 10
    assert catalog["bounds"]["hard_target_limit"] == 50
    assert catalog["bounds"]["hard_operation_limit"] == 100
    schemas = [root / f"schemas/unified_market_evidence_execution_request.{version}.schema.json" for version in ("v1", "v2", "v3")]
    for path in schemas:
        schema = json.loads(path.read_text(encoding="utf-8"))
        assert schema["properties"]["maximum_records"]["maximum"] == 500
        assert schema["properties"]["timeout_seconds"]["minimum"] == 1
        assert schema["properties"]["timeout_seconds"]["maximum"] == 60

    request_schema = json.loads((root / "schemas/unified_market_evidence_request.v3.schema.json").read_text(encoding="utf-8"))
    recent_performance = next(
        item for item in request_schema["properties"]["data_needs"]["items"]["allOf"]
        if item.get("if", {}).get("properties", {}).get("type", {}).get("const") == "recent_performance"
    )
    lookback = recent_performance["then"]["properties"]["parameters"]["properties"]["lookback_trading_days"]
    assert (lookback["minimum"], lookback["maximum"]) == (1, 20)

    disclosure_schema = json.loads((root / "schemas/material_disclosure_evidence.v1.schema.json").read_text(encoding="utf-8"))
    assert disclosure_schema["properties"]["items"]["maxItems"] == 50


def test_unsupported_generic_pagination_parameters_remain_rejected_by_closed_schema():
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    schema = json.loads((root / "schemas/unified_market_evidence_request.v3.schema.json").read_text(encoding="utf-8"))
    assert schema["additionalProperties"] is False


def test_mcp_markdown_plus_structured_content_amplification_is_rejected(monkeypatch):
    from server.unified_mcp import server as mcp_server
    monkeypatch.setattr(mcp_server, "MAX_UNIFIED_RESPONSE_BYTES", 120)
    result = mcp_server._success("market_export_ai_handoff", {"ai_ready_markdown": "m" * 80})
    assert result.isError is True
    assert result.structuredContent == {"error": "mcp_result_too_large"}
    assert result.content[0].text == '{"error":"mcp_result_too_large"}'

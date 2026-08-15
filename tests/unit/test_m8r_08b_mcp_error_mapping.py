import asyncio
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from server.unified_mcp.error_mapping import map_internal_error, map_local_service_error
from server.unified_mcp.local_service_client import ACTION_TIMEOUT_SECONDS, DEFAULT_SERVICE_URL, TIMEOUT_SECONDS, LocalServiceClientError, UnifiedLocalServiceClient, validate_loopback_service_url
import server.unified_mcp.local_service_client as local_service_client


def test_loopback_url_validation_rejects_every_non_local_shape():
    assert validate_loopback_service_url(DEFAULT_SERVICE_URL) == DEFAULT_SERVICE_URL
    assert validate_loopback_service_url("http://localhost:8123") == "http://127.0.0.1:8123"
    assert validate_loopback_service_url("http://[::1]:8123") == "http://[::1]:8123"
    rejected = (
        "http://0.0.0.0:8000", "http://192.168.1.5:8000", "https://127.0.0.1:8000",
        "http://example.test:8000", "http://user:pass@127.0.0.1:8000",
        "http://127.0.0.1:8000/api", "http://127.0.0.1:8000?x=1",
        "http://127.0.0.1:8000#x", "http://127.0.0.1",
    )
    for value in rejected:
        try:
            UnifiedLocalServiceClient(value)
        except LocalServiceClientError as exc:
            assert exc.code == "local_service_url_invalid"
        else:
            raise AssertionError(value)


def test_bounded_upstream_error_preserves_only_governed_fields():
    result = map_local_service_error(LocalServiceClientError(
        "local_service_http_error", status_code=409,
        payload={"error": "mode_c_execution_not_finalized", "trace_id": "trace", "secret": "do-not-leak", "path": "C:/secret"},
    ))
    assert result.isError is True
    assert result.structuredContent == {"http_status": 409, "error": "mode_c_execution_not_finalized", "trace_id": "trace"}
    assert "secret" not in result.content[0].text
    assert "C:/" not in result.content[0].text


def test_adapter_errors_are_opaque_and_do_not_echo_exception_text():
    result = map_local_service_error(LocalServiceClientError("local_service_timeout"))
    assert result.isError is True
    assert result.structuredContent["error"] == "local_service_timeout"
    internal = map_internal_error()
    assert internal.structuredContent["error"] == "mcp_adapter_internal_error"
    assert "trace_id" in internal.structuredContent


class _ServiceHandler(BaseHTTPRequestHandler):
    calls: list[tuple[str, str, object]] = []
    mode = "normal"

    def log_message(self, *_args):
        return

    def _send(self, status: int, body: bytes, content_type: str = "application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        type(self).calls.append(("GET", self.path, None))
        if type(self).mode == "redirect":
            self.send_response(302)
            self.send_header("Location", "http://example.test/")
            self.end_headers()
        elif type(self).mode == "incompatible":
            self._send(200, json.dumps({"service_contract_version": "other.v1"}).encode())
        elif type(self).mode == "non_json":
            self._send(200, b"not-json", "text/plain")
        elif type(self).mode == "large":
            self._send(200, b"{" + b'"x":"' + (b"x" * 128) + b'"}')
        else:
            self._send(200, json.dumps({"service_contract_version": "unified_market_evidence_local_service.v1"}).encode())

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length))
        type(self).calls.append(("POST", self.path, payload))
        if type(self).mode == "action_over_legacy_timeout" and self.path == "/api/unified/fetch-evidence":
            time.sleep(16)
        self._send(200, b"{}")


class _LoopbackService:
    def __enter__(self):
        _ServiceHandler.calls = []
        _ServiceHandler.mode = "normal"
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), _ServiceHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return f"http://127.0.0.1:{self.server.server_port}"

    def __exit__(self, *_args):
        self.server.shutdown()
        self.thread.join(timeout=5)
        self.server.server_close()


def test_client_uses_only_fixed_exact_routes_and_envelopes():
    with _LoopbackService() as url:
        async def run():
            client = UnifiedLocalServiceClient(url)
            await client.describe_capabilities()
            envelope = {"request": {"request_id": "unchanged"}}
            await client.validate_request(envelope)
            await client.preview_request(envelope)
            await client.fetch_evidence(envelope)
            identifier = "umea-v1-0123456789abcdef0123"
            await client.read_result(identifier)
            await client.export_ai_handoff(identifier)
        asyncio.run(run())
    assert _ServiceHandler.calls == [
        ("GET", "/api/unified/capabilities", None),
        ("POST", "/api/unified/validate-request", {"request": {"request_id": "unchanged"}}),
        ("POST", "/api/unified/preview-request", {"request": {"request_id": "unchanged"}}),
        ("POST", "/api/unified/fetch-evidence", {"request": {"request_id": "unchanged"}}),
        ("POST", "/api/unified/result-package", {"control_package_id": "umea-v1-0123456789abcdef0123"}),
        ("GET", "/api/unified/result-package/umea-v1-0123456789abcdef0123/handoff", None),
    ]


@pytest.mark.parametrize(
    ("mode", "code"),
    (("redirect", "local_service_protocol_invalid"), ("non_json", "local_service_protocol_invalid"), ("large", "local_service_response_too_large")),
)
def test_client_fails_closed_for_redirect_non_json_and_oversize(mode, code):
    with _LoopbackService() as url:
        _ServiceHandler.mode = mode
        client = UnifiedLocalServiceClient(url, max_response_bytes=64)
        with pytest.raises(LocalServiceClientError, match=code):
            asyncio.run(client.describe_capabilities())


def test_service_version_mismatch_fails_closed_and_invalid_id_never_connects():
    with _LoopbackService() as url:
        async def run():
            client = UnifiedLocalServiceClient(url)
            with pytest.raises(LocalServiceClientError, match="control_package_id_invalid"):
                await client.export_ai_handoff("../bad")
            _ServiceHandler.mode = "incompatible"
            with pytest.raises(LocalServiceClientError, match="local_service_contract_incompatible"):
                await client.verify_service_contract()
        asyncio.run(run())
    assert _ServiceHandler.calls == [("GET", "/api/unified/capabilities", None)]


def test_action_over_legacy_timeout_uses_separate_finite_bound():
    assert TIMEOUT_SECONDS == 15.0
    assert ACTION_TIMEOUT_SECONDS == 85.0
    with _LoopbackService() as url:
        _ServiceHandler.mode = "action_over_legacy_timeout"
        started = time.monotonic()
        result = asyncio.run(UnifiedLocalServiceClient(url).fetch_evidence({"request": {"request_id": "slow"}}))
        assert result == {}
        assert time.monotonic() - started > TIMEOUT_SECONDS
    assert _ServiceHandler.calls == [("POST", "/api/unified/fetch-evidence", {"request": {"request_id": "slow"}})]


def test_action_timeout_is_bounded_and_has_no_retry(monkeypatch):
    attempts = []

    class TimeoutClient:
        def __init__(self, **kwargs):
            attempts.append(kwargs["timeout"].read)
        async def __aenter__(self):
            raise local_service_client.httpx.TimeoutException("synthetic")
        async def __aexit__(self, *_args):
            return False

    monkeypatch.setattr(local_service_client.httpx, "AsyncClient", TimeoutClient)
    with pytest.raises(LocalServiceClientError, match="local_service_action_timeout"):
        asyncio.run(UnifiedLocalServiceClient("http://127.0.0.1:8000").fetch_evidence({"request": {}}))
    assert attempts == [ACTION_TIMEOUT_SECONDS]

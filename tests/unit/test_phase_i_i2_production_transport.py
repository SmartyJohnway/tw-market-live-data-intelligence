"""Offline conformance to immutable A3 transport; external sockets denied."""
import json
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from server.services import phase_i_i2_live_acceptance_candidate as a3
from server.services import phase_i_i2_production_transport as production


@pytest.fixture(autouse=True)
def deny_network(monkeypatch):
    def deny(*args, **kwargs):
        raise AssertionError("external sockets forbidden")
    monkeypatch.setattr("socket.socket.connect", deny)
    monkeypatch.setattr("socket.create_connection", deny)


def outcome(module, status, mime, body, exception=False):
    calls = []
    def delegate(url, timeout):
        calls.append((url, timeout))
        assert url == module.SOURCE_ENDPOINT and timeout == 30
        if exception:
            raise OSError("synthetic transport failure")
        return status, {"Content-Type": mime}, body
    try:
        acquired = module.acquire_taifex_once(
            transport=delegate, clock=lambda: datetime(2026, 10, 1, tzinfo=timezone.utc))
        result = ("available", acquired.http_status, acquired.content_type,
                  acquired.response_byte_count, acquired.response_sha256, acquired.retry_count)
    except RuntimeError as error:
        result = (error.code, error.status, error.content_type,
                  error.byte_count, error.response_sha256, 0)
    assert len(calls) == 1
    return result


@pytest.mark.parametrize("status,mime,body,exception", [
    (200, "application/octet-stream", b"[]", False),
    (200, "application/json", b"[]", False),
    (200, "Application/JSON; charset=utf-8", b"[]", False),
    (302, "application/json", b"[]", False),
    (500, "application/json", b"[]", False),
    (200, "text/html", b"[]", False),
    (200, "application/json", b"\xff", False),
    (200, "application/json", b"{", False),
    (200, "application/json", b"{}", False),
    (200, "application/json", b"x" * 2097153, False),
    (200, "application/json", json.dumps([{}] * 5001).encode(), False),
    (200, "application/json", b"[]", True),
], ids=["octet", "json", "parameters", "redirect", "http", "mime",
        "utf8", "json-invalid", "root", "bytes", "rows", "exception"])
def test_transport_conformance(status, mime, body, exception):
    assert outcome(production, status, mime, body, exception) == outcome(a3, status, mime, body, exception)


def test_production_imports_do_not_depend_on_acceptance_modules():
    import ast
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    for name in ("phase_i_i2_production_candidate.py", "phase_i_i2_production_transport.py"):
        tree = ast.parse((root / "server/services" / name).read_text(encoding="utf-8"))
        assert not any(isinstance(node, ast.ImportFrom) and "acceptance" in (node.module or "")
                       for node in ast.walk(tree))


def test_real_transport_read_bound_and_redirect_handler():
    class Response:
        status = 200
        headers = {"Content-Type": "application/json"}
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self, size):
            assert size == 2097153
            return b"[]"
    class Opener:
        def open(self, request, timeout):
            assert request.full_url == production.SOURCE_ENDPOINT
            assert request.get_method() == "GET" and timeout == 30
            return Response()
    with patch.object(production.urllib.request, "build_opener", return_value=Opener()) as build:
        production._read_once(production.SOURCE_ENDPOINT, 30)
        assert isinstance(build.call_args.args[0], production._RejectRedirects)
        assert build.call_args.args[0].redirect_request(None, None, 302, "", {}, "other") is None


@pytest.mark.parametrize("url,timeout", [("https://invalid.example", 30), (production.SOURCE_ENDPOINT, 15)])
def test_fixed_transport_scope_rejected_before_io(url, timeout):
    with patch.object(production.urllib.request, "build_opener") as build:
        with pytest.raises(production.ProductionTransportError, match="transport_scope"):
            production._read_once(url, timeout)
        build.assert_not_called()

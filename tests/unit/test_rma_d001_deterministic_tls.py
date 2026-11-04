from __future__ import annotations

import json
import ssl
from types import SimpleNamespace

import certifi

from scripts import ssl_policy
from scripts import m8a_twse_official_eod_adapter as twse_eod
from scripts import m8a_tpex_official_eod_adapter as tpex_eod
from scripts import m8r_06_03_production_adapter as production_adapter
from server.services import phase_i_i1_production_candidate as i1
from server.services import phase_i_i2_production_transport as i2
from server.services import phase_i_i3_production_transport as i3


def _assert_verified_certifi_context(context: ssl.SSLContext, *, compatibility: bool) -> None:
    assert isinstance(context, ssl.SSLContext)
    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.check_hostname is True
    expected = ssl.create_default_context(cafile=certifi.where())
    assert context.cert_store_stats() == expected.cert_store_stats()
    if hasattr(ssl, "VERIFY_X509_STRICT"):
        if compatibility:
            assert context.verify_flags & ssl.VERIFY_X509_STRICT == 0
        else:
            assert context.verify_flags & ssl.VERIFY_X509_STRICT == expected.verify_flags & ssl.VERIFY_X509_STRICT

def test_strict_and_compatibility_use_deterministic_certifi_trust() -> None:
    _assert_verified_certifi_context(ssl_policy.build_ssl_context("strict"), compatibility=False)
    _assert_verified_certifi_context(ssl_policy.build_ssl_context("compatibility"), compatibility=True)


def _fake_response(body: bytes = b"[]"):
    class Response:
        status = 200
        headers = {"Content-Type": "application/json"}
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            return False
        def read(self, *_args):
            return body
    return Response()


def test_eod_and_research_transports_receive_strict_context(monkeypatch) -> None:
    seen: list[ssl.SSLContext | None] = []
    def fake_urlopen(_request, *, timeout, context=None):
        assert timeout > 0
        seen.append(context)
        return _fake_response()
    monkeypatch.setattr(twse_eod.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(tpex_eod.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(production_adapter, "urlopen", fake_urlopen)
    twse_eod.fetch_twse_official_eod_json()
    tpex_eod.fetch_tpex_official_eod_json()
    production_adapter._fetch_official_payload("https://example.test/data", timeout=1)
    assert len(seen) == 3
    for context in seen:
        _assert_verified_certifi_context(context, compatibility=False)

def _captured_https_context(handlers) -> ssl.SSLContext:
    for handler in handlers:
        context = getattr(handler, "_context", None)
        if isinstance(context, ssl.SSLContext):
            return context
    raise AssertionError("verified HTTPS context was not wired into opener")


def test_i1_and_i2_strict_openers_use_deterministic_context(monkeypatch) -> None:
    i1_handlers = []
    monkeypatch.setattr(i1.urllib.request, "build_opener", lambda *handlers: i1_handlers.extend(handlers) or object())
    i1._no_redirect_opener()
    _assert_verified_certifi_context(_captured_https_context(i1_handlers), compatibility=False)

    i2_handlers = []
    class StopBeforeOpen:
        def open(self, *_args, **_kwargs):
            raise RuntimeError("stop-before-network")
    monkeypatch.setattr(i2.urllib.request, "build_opener", lambda *handlers: i2_handlers.extend(handlers) or StopBeforeOpen())
    try:
        i2._read_once(i2.SOURCE_ENDPOINT, i2.TIMEOUT_SECONDS)
    except RuntimeError as exc:
        assert str(exc) == "stop-before-network"
    _assert_verified_certifi_context(_captured_https_context(i2_handlers), compatibility=False)


def test_i3_strict_opener_uses_deterministic_context(monkeypatch) -> None:
    handlers = []
    monkeypatch.setattr(i3, "build_opener", lambda *items: handlers.extend(items) or object())
    i3._opener("strict")
    _assert_verified_certifi_context(_captured_https_context(handlers), compatibility=False)

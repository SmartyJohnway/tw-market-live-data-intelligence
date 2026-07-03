import json
import ssl
import urllib.request

import pytest

from scripts import ssl_policy as sp
from scripts.m5k_common import execute_live_observation
from scripts.run_m6b_source_contract_preflight import build_report


def test_ssl_policy_default_env_and_cli_precedence(monkeypatch):
    monkeypatch.delenv(sp.SSL_POLICY_ENV_VAR, raising=False)
    assert sp.resolve_ssl_policy(None) == "strict"
    monkeypatch.setenv(sp.SSL_POLICY_ENV_VAR, "compatibility")
    assert sp.resolve_ssl_policy(None) == "compatibility"
    assert sp.resolve_ssl_policy("strict") == "strict"


def test_invalid_ssl_policy_fails_closed():
    with pytest.raises(ValueError):
        sp.resolve_ssl_policy("bad")


def test_strict_does_not_create_unverified_context(monkeypatch):
    called = False
    def fake_unverified():
        nonlocal called
        called = True
    monkeypatch.setattr(ssl, "_create_unverified_context", fake_unverified)
    assert sp.build_ssl_context("strict") is None
    assert called is False


def test_compatibility_is_explicit_and_reported():
    ctx = sp.build_ssl_context("compatibility")
    diag = sp.ssl_policy_diagnostics("compatibility", network_calls_may_have_occurred=True)
    assert isinstance(ctx, ssl.SSLContext)
    assert diag["compatibility_mode_used"] is True
    assert diag["tls_verification_mode"] == "verified_tls_compatibility_context"
    assert diag["silent_tls_fallback"] is False


def test_unsafe_explicit_reported(monkeypatch):
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    monkeypatch.setattr(ssl, "_create_unverified_context", lambda: ctx)
    assert sp.build_ssl_context("unsafe-explicit") is ctx
    diag = sp.ssl_policy_diagnostics("unsafe-explicit")
    assert diag["unsafe_mode_used"] is True
    assert "certificate verification is disabled" in diag["warning"]


def test_m5k_live_output_includes_ssl_diagnostics_without_network_on_invalid_watchlist():
    result = execute_live_observation({"schema_version": "m5k_watchlist.v1", "categories": []}, write_latest=False, ssl_policy="compatibility")
    diag = result["diagnostics"]["ssl_policy"]
    assert result["status"] == "failed_closed_invalid_watchlist"
    assert diag["ssl_policy"] == "compatibility"
    assert diag["network_calls_may_have_occurred"] is False


def test_m6b_preflight_output_includes_selected_ssl_policy(monkeypatch):
    monkeypatch.delenv(sp.SSL_POLICY_ENV_VAR, raising=False)
    report = build_report(mode="check_only", ssl_policy="unsafe-explicit")
    assert report["ssl_policy"]["selected"] == "unsafe-explicit"
    assert report["ssl_policy"]["unsafe_mode_used"] is True
    assert report["network_calls_may_have_occurred"] is False


def test_network_request_helper_receives_selected_ssl_context(monkeypatch):
    calls = []
    class Resp:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self): return json.dumps({"msgArray": []}).encode()
    def fake_urlopen(req, timeout, context=None):
        calls.append(context)
        return Resp()
    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    watchlist = {"schema_version":"m5n_watchlist.v1","watchlist_id":"t","items":[{"id":"twse:2330","symbol":"2330","display_name":"2330","market":"twse","instrument_type":"listed_stock","adapter":"twse_mis_equity_etf_quote","preferred_sources":["TWSE_MIS"],"category":"c","enabled":True,"display_order":1,"tags":[],"notes":"descriptive"}]}
    result = execute_live_observation(watchlist, write_latest=False, ssl_policy="compatibility")
    assert calls and isinstance(calls[0], ssl.SSLContext)
    assert result["diagnostics"]["ssl_policy"]["compatibility_mode_used"] is True

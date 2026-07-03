import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scripts.m5k_common import validate_watchlist
from scripts.observation_contract import normalize_failure, normalize_taifex_row, normalize_twse_mis_row
from scripts.run_m6b_source_contract_preflight import build_report
from server.main import app

FORBIDDEN = ["raw_payload", "response_sample", "raw_fields_sample", "target_price", "ranking", "broker order"]


@pytest.mark.unit
def test_twse_dirty_rows_fail_closed_without_trading_fields():
    instrument = {"symbol": "2330", "market": "twse", "instrument_type": "listed_stock"}
    cases = [
        {"z": "-", "y": "0", "d": "", "t": None},
        {"z": "bad", "y": "-", "tlong": "bad"},
        {},
    ]
    for row in cases:
        obs = normalize_twse_mis_row(row, instrument, "2026-07-03T00:00:00Z")
        assert obs["status"] in {"reference_value_only", "value_unavailable"}
        assert obs["price_like_value"] in {0.0, None}
        assert obs["data_quality_flags"]
        assert obs["reference_only"] is (obs["status"] == "reference_value_only")
        assert not {"buy", "sell", "hold", "target_price", "ranking", "recommendation"} & set(obs)


@pytest.mark.unit
def test_taifex_dirty_rows_report_degraded_closed_session():
    instrument = {"symbol": "TX", "market": "taifex", "instrument_type": "futures"}
    obs = normalize_taifex_row({"CLastPrice": "bad", "CDate": "", "CTime": None, "Status": "closed"}, instrument, "2026-07-03T00:00:00Z")
    assert obs["status"] == "missing_value"
    assert obs["price_like_value"] is None
    assert "invalid_numeric_field" in obs["data_quality_flags"]
    assert obs["freshness_assessment"] == "stale_or_closed_session"
    assert obs["reference_only"] is False


@pytest.mark.unit
def test_normalize_failure_no_raw_payload_or_trading_fields():
    failure = normalize_failure(symbol="0050", source="TWSE_MIS", adapter_id="twse_mis_equity_etf_quote", reason="unexpected_non_json_response")
    text = json.dumps(failure).lower()
    for forbidden in FORBIDDEN:
        assert forbidden not in text


@pytest.mark.unit
def test_watchlist_rejects_forbidden_semantics_nested_values():
    base = {
        "schema_version": "m5n_watchlist.v1",
        "items": [{"id": "twse:2330", "symbol": "2330", "display_name": "2330", "market": "twse", "instrument_type": "listed_stock", "adapter": "TWSE_MIS", "preferred_sources": ["TWSE_MIS"], "category": "default", "enabled": True, "display_order": 1, "tags": ["entry"], "notes": "target price idea", "metadata": {"custom": "stop loss"}}],
    }
    result = validate_watchlist(base)
    assert result["valid"] is False
    assert any("forbidden_semantics" in e for e in result["errors"])


@pytest.mark.unit
def test_watchlist_allows_normal_chinese_stock_name():
    watchlist = {"schema_version": "m5n_watchlist.v1", "items": [{"id": "twse:2330", "symbol": "2330", "display_name": "台積電", "market": "twse", "instrument_type": "listed_stock", "adapter": "TWSE_MIS", "preferred_sources": ["TWSE_MIS"], "category": "台灣股票", "enabled": True, "display_order": 1, "tags": ["半導體"], "notes": "描述性觀察"}]}
    assert validate_watchlist(watchlist)["valid"] is True


@pytest.mark.mock
def test_m6b_check_only_no_network_report_contract():
    report = build_report(mode="check_only")
    assert report["network_calls_may_have_occurred"] is False
    assert report["raw_payload_included"] is False
    assert report["targets"] == ["2330", "0050", "TX"]
    assert report["ssl_policy"]["selected"] == "strict"
    assert all(c["tls_status"] == "not_executed" for c in report["checks"])


@pytest.mark.unit
def test_ai_and_api_surfaces_do_not_leak_raw_payload_terms():
    client = TestClient(app)
    endpoints = ["/api/conversation/context", "/api/source-health/latest", "/api/source-health/history", "/api/m5k/live-observation/history"]
    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == 200
        data = response.json()
        def walk(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    assert key not in {"raw_payload", "response_sample", "raw_fields_sample"}
                    if key in {"recommendation", "target_price", "ranking"}:
                        assert child is False
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)
        walk(data)
        assert "broker order" not in response.text.lower()

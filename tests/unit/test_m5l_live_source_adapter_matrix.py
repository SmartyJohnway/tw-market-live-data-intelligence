from fastapi.testclient import TestClient

from scripts.m5k_common import (
    execute_live_observation,
    load_json,
    load_source_adapter_matrix,
    plan_live_observation,
    source_capabilities,
    validate_source_adapter_matrix,
)
from server.main import app


def _watchlist(symbol, market, instrument_type):
    return {"schema_version":"m5k_watchlist.v1","watchlist_id":"unit","categories":[{"category_id":"x","label":"x","instruments":[{"symbol":symbol,"market":market,"instrument_type":instrument_type,"preferred_sources":["TWSE_MIS"],"enabled":True}]}]}


def test_adapter_matrix_schema_loads_and_has_status_groups():
    matrix = load_source_adapter_matrix()
    result = validate_source_adapter_matrix(matrix)
    assert result["valid"] is True
    statuses = {a["verification_status"] for a in matrix["adapters"]}
    assert "accepted_with_caveats" in statuses
    assert "rejected_for_live_observation" in statuses
    assert "future_candidate" in statuses


def test_source_routes_are_adapter_driven():
    assert plan_live_observation(_watchlist("2330", "twse", "listed_equity"))["planned_routes"][0]["adapter_id"] == "twse_mis_equity_etf_quote"
    assert plan_live_observation(_watchlist("0050", "twse", "listed_etf"))["planned_routes"][0]["adapter_id"] == "twse_mis_equity_etf_quote"
    assert plan_live_observation(_watchlist("3483", "tpex", "listed_or_otc_equity"))["planned_routes"][0]["ex_ch"] == "otc_3483.tw"
    assert plan_live_observation(_watchlist("TAIEX", "twse", "index"))["planned_routes"][0]["adapter_id"] == "twse_mis_taiex_index_quote"
    assert plan_live_observation(_watchlist("TX", "taifex", "futures"))["planned_routes"][0]["adapter_id"] == "taifex_mis_tx_futures_quote"


def test_observation_and_failure_envelope_consistency(monkeypatch):
    def fake_taifex(instrument, retrieved_at, timeout=12):
        return ({"symbol":"TX","display_symbol":"TX","instrument_type":"futures","market":"taifex","source":"TAIFEX_MIS","adapter_id":"taifex_mis_tx_futures_quote","status":"ok","price_like_value":1.0,"source_timestamp":"2026-06-30T01:00:00+08:00","retrieved_at_utc":retrieved_at,"freshness_assessment":"fresh","delay_status":"measured","delay_seconds":1,"caveats":[],"contract":"TXF-F","contract_month":"202607","contract_selector":"front_month"}, {"status":"accepted_for_bounded_observation"})
    monkeypatch.setattr("scripts.m5k_common.fetch_taifex_tx_observation", fake_taifex)
    payload = execute_live_observation(_watchlist("TX", "taifex", "futures"), write_latest=False)
    obs = payload["observations"][0]
    for key in ["symbol","display_symbol","instrument_type","market","source","adapter_id","status","price_like_value","source_timestamp","retrieved_at_utc","freshness_assessment","delay_status","delay_seconds","caveats"]:
        assert key in obs
    payload = execute_live_observation(_watchlist("BAD", "unknown", "listed_equity"), write_latest=False)
    assert payload["status"] == "failed_closed_invalid_watchlist"


def test_fastapi_m5l_capability_endpoints_and_no_raw_payload_leakage():
    client = TestClient(app)
    matrix = client.get("/api/m5l/source-adapter-matrix")
    assert matrix.status_code == 200
    caps = client.get("/api/m5l/source-capabilities")
    assert caps.status_code == 200
    text = matrix.text + caps.text
    assert '"raw_payload":' not in text
    assert '"response_sample":' not in text


def test_source_capabilities_summary():
    caps = source_capabilities()
    assert caps["schema_version"] == "m5l_source_capabilities.v1"
    assert any(c["adapter_id"] == "taifex_mis_tx_futures_quote" for c in caps["capabilities"])


def test_mcp_m5l_capability_tools_exposed_without_network():
    from server.mcp_server import get_m5l_source_adapter_matrix_tool, get_m5l_source_capabilities_tool
    matrix = get_m5l_source_adapter_matrix_tool()
    caps = get_m5l_source_capabilities_tool()
    assert matrix["tool"] == "get_m5l_source_adapter_matrix"
    assert caps["tool"] == "get_m5l_source_capabilities"
    assert matrix["validation"]["valid"] is True
    assert caps["content"]["governance"]["network_free_startup"] is True


def test_twse_mis_price_falls_back_to_y_as_reference_only_when_z_missing_dash():
    from scripts.m5k_common import _parse_mis_item
    obs = _parse_mis_item({"z":"-", "y":"2370.0000", "d":"20260630", "t":"09:31:15"}, {"symbol":"2330", "market":"twse", "instrument_type":"listed_equity"}, "2026-06-30T01:31:16Z")
    assert obs["price_like_value"] == 2370.0
    assert obs["price_source_field"] == "y"
    assert obs["price_semantics"] == "previous_close_or_reference_fallback_not_current_trade"
    assert obs["status"] == "reference_value_only"
    assert "current_z_unavailable_used_y_reference" in obs["data_quality_flags"]
    assert "current_z_unavailable_y_reference_fallback_not_current_trade" in obs["caveats"]


def test_twse_mis_price_unavailable_when_z_and_y_missing_dash():
    from scripts.m5k_common import _parse_mis_item
    obs = _parse_mis_item({"z":"-", "y":"-", "d":"20260630", "t":"09:31:15"}, {"symbol":"0050", "market":"twse", "instrument_type":"listed_etf"}, "2026-06-30T01:31:16Z")
    assert obs["price_like_value"] is None
    assert obs["price_source_field"] is None
    assert obs["status"] == "value_unavailable"


def test_twse_mis_price_prefers_numeric_z_over_y():
    from scripts.m5k_common import _parse_mis_item
    obs = _parse_mis_item({"z":"2460.0000", "y":"2370.0000", "d":"20260630", "t":"09:31:15"}, {"symbol":"2330", "market":"twse", "instrument_type":"listed_equity"}, "2026-06-30T01:31:16Z")
    assert obs["price_like_value"] == 2460.0
    assert obs["price_source_field"] == "z"
    assert obs["price_semantics"] == "last_or_current_quote_as_reported_by_source"
    assert obs["status"] == "ok"


def test_twse_mis_source_timestamp_prefers_tlong():
    from scripts.m5k_common import _parse_mis_item
    obs = _parse_mis_item({"z":"2460.0000", "y":"2370.0000", "d":"19990101", "t":"00:00:00", "tlong":"1718951400000"}, {"symbol":"2330", "market":"twse", "instrument_type":"listed_equity"}, "2024-06-21T06:30:05Z")
    assert obs["source_timestamp"] == "2024-06-21T06:30:00Z"
    assert obs["delay_seconds"] == 5
    assert obs["staleness_seconds"] == 5

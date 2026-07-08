import copy
import json

from scripts.observation_contract import build_bounded_watchlist_cross_context

FORBIDDEN_KEYS = ["twse_mis_rich_facts", "bid_prices", "ask_prices", "bid_quantities_raw", "ask_quantities_raw", "raw_unknown_facts", "raw_twse_mis_payload", "raw_full_ladder_arrays"]
FORBIDDEN_PHRASES = ["buy opportunity", "sell pressure", "support level", "resistance level", "target price estimate", "main force accumulation", "liquidity signal", "confirmed trend", "market breadth improved", "sector rotation confirmed", "capital inflow confirmed", "market-wide trend confirmed", "futures lead signal"]


def fixture_watchlist():
    return {"schema_version": "m5n_watchlist.v1", "items": [
        {"id":"index:taiex", "symbol":"TAIEX", "display_name":"TAIEX", "market":"twse", "instrument_type":"index", "category":"index", "enabled":True},
        {"id":"taifex:TX", "symbol":"TX", "display_name":"TX", "market":"taifex", "instrument_type":"futures", "category":"futures", "enabled":True},
        {"id":"twse:2330", "symbol":"2330", "display_name":"TSMC", "market":"twse", "instrument_type":"listed_stock", "category":"equity", "enabled":True},
        {"id":"twse:0050", "symbol":"0050", "display_name":"TW50 ETF", "market":"twse", "instrument_type":"etf", "category":"etf", "enabled":True},
        {"id":"twse:9999", "symbol":"9999", "display_name":"Missing", "market":"twse", "instrument_type":"listed_stock", "category":"equity", "enabled":True},
        {"id":"twse:1111", "symbol":"1111", "display_name":"Failed", "market":"twse", "instrument_type":"listed_stock", "category":"equity", "enabled":True},
        {"id":"twse:2222", "symbol":"2222", "display_name":"Reference", "market":"twse", "instrument_type":"listed_stock", "category":"equity", "enabled":True},
        {"id":"twse:3333", "symbol":"3333", "display_name":"Projection only", "market":"twse", "instrument_type":"listed_stock", "category":"equity", "enabled":True},
        {"id":"twse:4444", "symbol":"4444", "display_name":"Metrics only", "market":"twse", "instrument_type":"listed_stock", "category":"equity", "enabled":True},
    ]}


def fixture_latest():
    def obs(symbol, status="ok", reference_only=False, freshness="fresh", source="TWSE_MIS"):
        return {"symbol": symbol, "display_symbol": symbol, "market": "taifex" if symbol == "TX" else "twse", "instrument_type": "futures" if symbol == "TX" else "listed_stock", "status": status, "source": source, "adapter_id": f"adapter_{symbol}", "retrieved_at_utc": "2026-07-07T04:00:00Z", "reference_only": reference_only, "freshness_assessment": freshness}
    return {"status":"ok", "observations":[obs("TAIEX"), obs("TX"), obs("2330"), obs("0050"), obs("2222", "degraded", True, "stale"), obs("3333"), obs("4444")], "failures":[{"symbol":"1111", "source":"TWSE_MIS", "adapter_id":"adapter_1111", "status":"failed", "reason":"fixture failure", "retrieved_at_utc":"2026-07-07T04:00:00Z"}]}


def metric(symbol, change_percent, change=1.0):
    return {"symbol": symbol, "safe_for_ai_context": True, "price_change_metrics": {"change_percent": {"status":"computed", "value": change_percent}, "change": {"status":"computed", "value": change}}}


def projection(symbol):
    return {"symbol": symbol, "safe_for_ai_context": True}


def build_fixture_context():
    return build_bounded_watchlist_cross_context(
        fixture_watchlist(), fixture_latest(),
        {"schema_version":"m7b_ai_safe_market_context_collection.v1", "projections":[projection(s) for s in ["TAIEX", "TX", "2330", "0050", "2222", "3333"]]},
        {"schema_version":"m7c_deterministic_metrics_collection.v1", "contexts":[metric("TAIEX", 0.5), metric("TX", -0.1), metric("2330", 2.1), metric("0050", 0.0), metric("2222", -1.0), metric("4444", 1.1)]},
    )


def test_valid_bounded_context_and_counts_without_mutation():
    w, l = fixture_watchlist(), fixture_latest()
    w0, l0 = copy.deepcopy(w), copy.deepcopy(l)
    ctx = build_bounded_watchlist_cross_context(w, l, {"projections":[projection("2330")]}, {"contexts":[metric("2330", 2.0)]})
    assert w == w0 and l == l0
    assert ctx["context_status"] == "runtime_computed_candidate"
    assert ctx["runtime_populated"] is True
    assert ctx["safe_for_ai_context"] is False
    assert ctx["bounded_watchlist_only"] is True
    assert ctx["not_full_market_breadth"] is True
    assert ctx["not_trading_signal"] is True
    assert ctx["not_recommendation"] is True


def test_coverage_breadth_relative_and_context_groups():
    ctx = build_fixture_context()
    cov = ctx["watchlist_observation_coverage"]
    assert cov["watchlist_item_count"] == 9
    assert cov["observed_item_count"] == 6
    assert cov["missing_observation_count"] == 1
    assert cov["failed_observation_count"] == 1
    assert cov["reference_only_count"] == 1
    assert cov["has_m7b_projection_count"] == 6
    assert cov["has_m7c_metrics_count"] == 6
    breadth = ctx["bounded_breadth_summary"]
    assert breadth["bounded_positive_change_count"] == 3
    assert breadth["bounded_negative_change_count"] == 2
    assert breadth["bounded_flat_change_count"] == 1
    assert breadth["bounded_unavailable_change_count"] == 3
    assert breadth["not_full_market_breadth"] is True
    rel = ctx["bounded_relative_change_summary"]
    assert [x["change_percent"] for x in rel["top_positive_change_percent_items"]] == [2.1, 1.1, 0.5]
    assert [x["change_percent"] for x in rel["top_negative_change_percent_items"]] == [-1.0, -0.1]
    assert rel["not_recommendation"] is True
    assert ctx["index_relative_context"]["index_comparison_pairs"][0]["not_market_prediction"] is True
    assert ctx["futures_relative_context"]["futures_comparison_pairs"][0]["not_futures_lead_signal"] is True
    assert ctx["etf_group_context"]["etf_like_items"][0]["symbol"] == "0050"
    assert ctx["etf_group_context"]["not_sector_rotation"] is True
    assert ctx["etf_group_context"]["not_capital_flow"] is True


def test_freshness_missing_degraded_provenance_and_safety_serialization():
    ctx = build_fixture_context()
    assert ctx["source_freshness_summary"]["failed_source_count"] == 1
    assert ctx["missing_context_summary"]["missing_required_observation_items"][0]["symbol"] == "9999"
    assert {x["symbol"] for x in ctx["degraded_context_summary"]["reference_only_items"]} == {"2222"}
    assert ctx["provenance_summary"]["provenance_available"] is True
    rendered = json.dumps(ctx, ensure_ascii=False).lower()
    for key in FORBIDDEN_KEYS:
        assert key not in rendered
    for phrase in FORBIDDEN_PHRASES:
        assert phrase not in rendered


def test_unsupported_missing_inputs_block_without_raise():
    assert build_bounded_watchlist_cross_context({}, fixture_latest())["context_status"] == "blocked_missing_watchlist"
    assert build_bounded_watchlist_cross_context(fixture_watchlist(), None)["context_status"] == "blocked_missing_latest_observation"

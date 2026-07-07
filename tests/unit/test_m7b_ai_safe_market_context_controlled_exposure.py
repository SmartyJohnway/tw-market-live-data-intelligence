import copy
import json

from scripts.m5k_common import (
    build_ai_safe_market_context_projections_for_latest_observations,
    build_conversation_context,
    build_watchlist_rows,
)
from scripts.m5q_source_health import build_report
from scripts.observation_contract import (
    build_ai_safe_market_context_projection_from_observation,
    normalize_failure,
    normalize_observation,
    normalize_taifex_row,
    normalize_twse_mis_row,
    promote_ai_safe_market_context_projection_for_controlled_context,
)

RETRIEVED_AT = "2026-07-07T04:00:00Z"
FORBIDDEN_KEYS = ["twse_mis_rich_facts", "bid_prices", "ask_prices", "bid_quantities_raw", "ask_quantities_raw", "raw_unknown_facts"]
FORBIDDEN_PHRASES = [
    "buy opportunity",
    "sell pressure",
    "support level",
    "resistance level",
    "target price estimate",
    "main force accumulation",
    "liquidity signal",
    "confirmed trend",
    "realtime feed",
    "official api definition validated",
    "verified quantity unit available",
]


def _watchlist():
    return {
        "schema_version": "m5n_watchlist.v1",
        "watchlist_id": "m7b_controlled",
        "name": "M7B controlled exposure",
        "items": [
            {"id": "twse:2330", "symbol": "2330", "display_name": "TSMC", "market": "twse", "instrument_type": "listed_stock", "adapter": "twse_mis_equity_etf_quote", "category": "equity", "enabled": True, "display_order": 1, "tags": [], "notes": ""},
            {"id": "taifex:TX", "symbol": "TX", "display_name": "TX", "market": "taifex", "instrument_type": "futures", "adapter": "taifex_mis_tx_futures_quote", "category": "futures", "enabled": True, "display_order": 2, "tags": [], "notes": ""},
        ],
    }


def _twse_obs(**overrides):
    row = {
        "c": "2330", "ch": "2330.tw", "ex": "tse", "n": "台積電", "z": "1000", "y": "990", "o": "995", "h": "1005", "l": "980",
        "v": "1234", "tv": "5678", "b": "999_998_997", "g": "10_20_30", "a": "1000_1001_1002", "f": "11_21_31",
        "u": "1089", "w": "891", "d": "20260707", "t": "13:20:00", "tlong": "1793952000000", "ts": "0", "pz": "-", "ps": "-",
    }
    row.update(overrides)
    return normalize_twse_mis_row(row, {"symbol": "2330", "display_symbol": "2330", "market": "twse", "instrument_type": "listed_stock", "adapter_id": "twse_mis_equity_etf_quote"}, RETRIEVED_AT)


def _taifex_obs():
    return normalize_taifex_row({"CLastPrice": "100", "CDate": "20260707", "CTime": "120000", "Status": "open", "SymbolID": "TXF202607"}, {"symbol": "TX", "instrument_type": "futures", "contract_selector": "front_month"}, RETRIEVED_AT)


def test_promotion_helper_is_pure_and_promotes_only_valid_candidate():
    candidate = build_ai_safe_market_context_projection_from_observation(_twse_obs())
    original = copy.deepcopy(candidate)
    promoted = promote_ai_safe_market_context_projection_for_controlled_context(candidate)
    assert candidate == original
    assert promoted is not candidate
    assert promoted["safe_for_ai_context"] is True
    assert promoted["exposure_status"] == "ai_safe_context_enabled"
    assert promoted["controlled_exposure_policy"] == "m7b_controlled_context_projection_v1"
    assert promoted["exposure_scope"] == "conversation_context_only"
    assert promoted["raw_rich_facts_exposed"] is False
    assert promoted["full_ladder_exposed"] is False


def test_invalid_projection_is_not_promoted():
    invalid = {"schema_version": "m7a_twse_mis_rich_facts.v1", "projection_status": "runtime_projected_candidate", "exposure_status": "ai_safe_projection_candidate"}
    promoted = promote_ai_safe_market_context_projection_for_controlled_context(invalid)
    assert promoted["safe_for_ai_context"] is False
    assert promoted["exposure_status"] == "blocked"
    assert promoted["blocked_reason"] == "not_valid_m7b_projection_candidate"
    assert promoted["raw_rich_facts_exposed"] is False
    assert promoted["full_ladder_exposed"] is False


def test_conversation_context_includes_controlled_projection_without_raw_rich_facts():
    latest = {"status": "ok", "observations": [_twse_obs()], "failures": []}
    context = build_conversation_context(_watchlist(), latest)
    collection = context["ai_safe_market_context_projection"]
    assert collection["schema_version"] == "m7b_ai_safe_market_context_collection.v1"
    assert collection["enabled"] is True
    assert collection["safe_for_ai_context"] is True
    assert collection["projection_count"] == 1
    projection = collection["projections"][0]
    assert projection["safe_for_ai_context"] is True
    assert projection["exposure_status"] == "ai_safe_context_enabled"
    rendered = json.dumps(context, ensure_ascii=False).lower()
    for key in FORBIDDEN_KEYS:
        assert key not in rendered
    for phrase in FORBIDDEN_PHRASES:
        assert phrase not in rendered
    assert context["governance"]["recommendation"] is False
    assert context["governance"]["buy_sell_hold"] is False
    assert context["ai_guidance_summary"]["trading_recommendation"] is False


def test_non_twse_and_failure_observations_do_not_produce_controlled_projection():
    generic = normalize_observation(symbol="X", source="OTHER", adapter_id="other", status="ok", retrieved_at_utc=RETRIEVED_AT, price_like_value=1.0)
    failure = normalize_failure(symbol="2330", source="TWSE_MIS", adapter_id="twse_mis_equity_etf_quote", reason="missing")
    latest = {"status": "ok", "observations": [_taifex_obs(), generic], "failures": [failure]}
    assert build_ai_safe_market_context_projections_for_latest_observations(latest) == []
    context = build_conversation_context(_watchlist(), latest)
    assert context["ai_safe_market_context_projection"]["projection_count"] == 0


def test_fastapi_mcp_latest_watchlist_and_source_health_boundaries(monkeypatch):
    latest = {"status": "ok", "observations": [_twse_obs()], "failures": []}
    import server.main as fastapi_main
    import server.mcp_server as mcp_server

    monkeypatch.setattr(fastapi_main, "_m5k_read_latest_observation", lambda: latest)
    monkeypatch.setattr(mcp_server, "_m5k_read_latest_observation", lambda: latest)
    monkeypatch.setattr(fastapi_main, "_m5k_load_json", lambda path: _watchlist())
    monkeypatch.setattr(mcp_server, "_m5k_load_json", lambda path: _watchlist())

    api_context = fastapi_main.get_conversation_context()["content"]
    mcp_context = mcp_server.get_conversation_context_tool()["content"]
    assert api_context["ai_safe_market_context_projection"]["projection_count"] == 1
    assert mcp_context["ai_safe_market_context_projection"]["projection_count"] == 1
    assert "twse_mis_rich_facts" not in json.dumps(api_context, ensure_ascii=False)
    assert "twse_mis_rich_facts" not in json.dumps(mcp_context, ensure_ascii=False)

    api_latest = fastapi_main.get_m5k_latest_live_observation()
    assert "ai_safe_market_context_projection" not in json.dumps(api_latest, ensure_ascii=False)
    assert api_latest["observations"][0]["twse_mis_rich_facts"]["ai_exposure_policy"]["safe_for_ai_context"] is False

    watchlist = fastapi_main.get_watchlist()
    rows_text = json.dumps(watchlist["rows"], ensure_ascii=False)
    assert "ai_safe_market_context_projection" not in rows_text
    assert "twse_mis_rich_facts" not in rows_text
    assert build_watchlist_rows(_watchlist(), latest)[0]["last_observation"] == 1000.0

    health = build_report(execution_mode="check_only", live_result=latest)
    health_text = json.dumps(health, ensure_ascii=False)
    assert "ai_safe_market_context_projection" not in health_text
    assert "twse_mis_rich_facts" not in health_text

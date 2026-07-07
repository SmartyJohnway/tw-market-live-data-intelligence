import copy
import json
from pathlib import Path

from scripts.m5k_common import (
    build_conversation_context,
    build_deterministic_metrics_context_collection,
    build_deterministic_metrics_contexts_for_latest_observations,
    build_watchlist_rows,
)
from scripts.m5q_source_health import build_report
from scripts.observation_contract import (
    build_deterministic_metrics_context_from_observation,
    normalize_failure,
    normalize_observation,
    normalize_taifex_row,
    normalize_twse_mis_row,
    promote_deterministic_metrics_context_for_controlled_context,
)

RETRIEVED_AT = "2026-07-07T04:00:00Z"
FORBIDDEN_KEYS = ["twse_mis_rich_facts", "bid_prices", "ask_prices", "bid_quantities_raw", "ask_quantities_raw", "raw_unknown_facts"]
FORBIDDEN_PHRASES = [
    "buy opportunity", "sell pressure", "support level", "resistance level", "target price estimate",
    "main force accumulation", "liquidity signal", "confirmed trend", "realtime feed",
    "official api definition validated", "verified quantity unit available",
]


def _watchlist():
    return {"schema_version": "m5n_watchlist.v1", "watchlist_id": "m7c_controlled", "name": "M7C controlled exposure", "items": [
        {"id": "twse:2330", "symbol": "2330", "display_name": "TSMC", "market": "twse", "instrument_type": "listed_stock", "adapter": "twse_mis_equity_etf_quote", "category": "equity", "enabled": True, "display_order": 1, "tags": [], "notes": ""},
        {"id": "taifex:TX", "symbol": "TX", "display_name": "TX", "market": "taifex", "instrument_type": "futures", "adapter": "taifex_mis_tx_futures_quote", "category": "futures", "enabled": True, "display_order": 2, "tags": [], "notes": ""},
    ]}


def _twse_obs(**overrides):
    row = {
        "c": "2330", "ch": "2330.tw", "ex": "tse", "n": "台積電", "z": "1000", "y": "990", "o": "995", "h": "1005", "l": "980",
        "v": "1234", "tv": "5678", "b": "999_998_997_996_995", "g": "10_20_30_40_50", "a": "1000_1001_1002_1003_1004", "f": "11_21_31_41_51",
        "u": "1089", "w": "891", "d": "20260707", "t": "13:20:00", "tlong": "1793952000000", "ts": "0", "pz": "-", "ps": "-",
    }
    row.update(overrides)
    return normalize_twse_mis_row(row, {"symbol": "2330", "display_symbol": "2330", "market": "twse", "instrument_type": "listed_stock", "adapter_id": "twse_mis_equity_etf_quote"}, RETRIEVED_AT)


def _taifex_obs():
    return normalize_taifex_row({"CLastPrice": "100", "CDate": "20260707", "CTime": "120000", "Status": "open", "SymbolID": "TXF202607"}, {"symbol": "TX", "instrument_type": "futures", "contract_selector": "front_month"}, RETRIEVED_AT)


def test_promotion_helper_promotes_valid_candidate_without_mutation_and_blocks_invalid():
    candidate = build_deterministic_metrics_context_from_observation(_twse_obs())
    original = copy.deepcopy(candidate)
    promoted = promote_deterministic_metrics_context_for_controlled_context(candidate)
    assert candidate == original
    assert promoted is not candidate
    assert promoted["safe_for_ai_context"] is True
    assert promoted["exposure_status"] == "ai_safe_context_enabled"
    assert promoted["controlled_exposure_policy"] == "m7c_controlled_deterministic_metrics_context_v1"
    assert promoted["exposure_scope"] == "conversation_context_only"
    assert promoted["raw_rich_facts_exposed"] is False
    assert promoted["raw_full_ladder_exposed"] is False
    assert promoted["metrics_are_signals"] is False
    assert promoted["not_trading_signal"] is True
    assert promoted["not_recommendation"] is True
    assert "future_builder_requirements" not in promoted

    blocked = promote_deterministic_metrics_context_for_controlled_context({"schema_version": "bad"})
    assert blocked["safe_for_ai_context"] is False
    assert blocked["exposure_status"] == "blocked"
    assert blocked["blocked_reason"] == "not_valid_m7c_deterministic_metrics_candidate"
    assert blocked["raw_rich_facts_exposed"] is False
    assert blocked["raw_full_ladder_exposed"] is False
    assert blocked["metrics_are_signals"] is False


def test_collection_helper_builds_promoted_metrics_and_skips_invalid_inputs():
    latest = {"status": "ok", "observations": [_twse_obs()], "failures": []}
    original = copy.deepcopy(latest)
    collection = build_deterministic_metrics_context_collection(latest)
    assert latest == original
    assert collection["schema_version"] == "m7c_deterministic_metrics_collection.v1"
    assert collection["enabled"] is True
    assert collection["safe_for_ai_context"] is True
    assert collection["metrics_context_count"] == 1
    assert len(collection["contexts"]) == 1
    ctx = collection["contexts"][0]
    assert ctx["price_change_metrics"]["change"]["value"] == 10
    assert ctx["displayed_quote_spread_metrics"]["displayed_spread"]["value"] == 1
    assert collection["raw_rich_facts_exposed"] is False
    assert collection["raw_full_ladder_exposed"] is False
    assert collection["metrics_are_signals"] is False
    assert collection["not_trading_signal"] is True
    assert collection["not_recommendation"] is True

    generic = normalize_observation(symbol="X", source="OTHER", adapter_id="other", status="ok", retrieved_at_utc=RETRIEVED_AT, price_like_value=1.0)
    failure = normalize_failure(symbol="2330", source="TWSE_MIS", adapter_id="twse_mis_equity_etf_quote", reason="missing")
    empty = {"status": "ok", "observations": [_taifex_obs(), generic], "failures": [failure]}
    assert build_deterministic_metrics_contexts_for_latest_observations(empty) == []
    assert build_deterministic_metrics_context_collection(empty)["contexts"] == []


def test_conversation_context_includes_controlled_metrics_without_raw_rich_facts_or_ladders():
    context = build_conversation_context(_watchlist(), {"status": "ok", "observations": [_twse_obs()], "failures": []})
    collection = context["deterministic_metrics_context"]
    assert collection["safe_for_ai_context"] is True
    assert collection["metrics_context_count"] == 1
    assert collection["contexts"][0]["open_high_low_position_metrics"]["distance_from_high_percent"]["status"] == "computed"
    rendered = json.dumps(collection, ensure_ascii=False).lower()
    for key in FORBIDDEN_KEYS:
        assert key not in rendered
    for phrase in FORBIDDEN_PHRASES:
        assert phrase not in rendered


def test_fastapi_mcp_latest_watchlist_source_health_boundaries(monkeypatch):
    latest = {"status": "ok", "observations": [_twse_obs()], "failures": []}
    import server.main as fastapi_main
    import server.mcp_server as mcp_server

    monkeypatch.setattr(fastapi_main, "_m5k_read_latest_observation", lambda: latest)
    monkeypatch.setattr(mcp_server, "_m5k_read_latest_observation", lambda: latest)
    monkeypatch.setattr(fastapi_main, "_m5k_load_json", lambda path: _watchlist())
    monkeypatch.setattr(mcp_server, "_m5k_load_json", lambda path: _watchlist())

    api_context = fastapi_main.get_conversation_context()["content"]
    mcp_context = mcp_server.get_conversation_context_tool()["content"]
    assert api_context["deterministic_metrics_context"]["metrics_context_count"] == 1
    assert mcp_context["deterministic_metrics_context"]["metrics_context_count"] == 1

    api_latest = fastapi_main.get_m5k_latest_live_observation()
    assert "deterministic_metrics_context" not in json.dumps(api_latest, ensure_ascii=False)
    assert api_latest["observations"][0]["twse_mis_rich_facts"]["ai_exposure_policy"]["safe_for_ai_context"] is False

    rows = fastapi_main.get_watchlist()["rows"]
    rows_text = json.dumps(rows, ensure_ascii=False)
    assert "deterministic_metrics_context" not in rows_text
    assert "twse_mis_rich_facts" not in rows_text
    assert build_watchlist_rows(_watchlist(), latest)[0]["last_observation"] == 1000.0

    health_text = json.dumps(build_report(execution_mode="check_only", live_result=latest), ensure_ascii=False)
    assert "deterministic_metrics_context" not in health_text
    assert "twse_mis_rich_facts" not in health_text


def test_runtime_references_remain_controlled_to_shared_conversation_context():
    root = Path(__file__).resolve().parents[2]
    allowed = {
        "scripts/observation_contract.py", "scripts/m5k_common.py",
        "tests/unit/test_m7c_deterministic_metrics_builder.py", "tests/unit/test_m7c_deterministic_metrics_schema.py",
        "tests/unit/test_m7c_deterministic_metrics_controlled_exposure.py", "tests/unit/test_m7c_deterministic_metrics_final_acceptance.py",
        "tests/unit/test_twse_mis_rich_field_inventory.py",
    }
    names = ["build_deterministic_metrics_context_from_observation", "promote_deterministic_metrics_context_for_controlled_context", "build_deterministic_metrics_context_collection"]
    for base in ["server", "frontend", "scripts", "tests/unit"]:
        for path in (root / base).rglob("*.py"):
            rel = path.relative_to(root).as_posix()
            text = path.read_text(encoding="utf-8")
            if any(name in text for name in names):
                assert rel in allowed

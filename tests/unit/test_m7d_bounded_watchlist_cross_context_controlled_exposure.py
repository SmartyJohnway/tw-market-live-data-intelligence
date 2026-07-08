import copy
import json
from pathlib import Path

from scripts.m5k_common import build_bounded_watchlist_cross_context_collection, build_conversation_context, build_watchlist_rows
from scripts.observation_contract import normalize_twse_mis_row, promote_bounded_watchlist_cross_context_for_controlled_context
from scripts.m5q_source_health import build_report
from tests.unit.test_m7d_bounded_watchlist_cross_context_builder import build_fixture_context, fixture_latest, fixture_watchlist

FORBIDDEN_KEYS = ["twse_mis_rich_facts", "bid_prices", "ask_prices", "bid_quantities_raw", "ask_quantities_raw", "raw_unknown_facts", "raw_twse_mis_payload", "raw_full_ladder_arrays"]
FORBIDDEN_PHRASES = ["buy opportunity", "sell pressure", "support level", "resistance level", "target price estimate", "main force accumulation", "liquidity signal", "confirmed trend", "market breadth improved", "sector rotation confirmed", "capital inflow confirmed", "market-wide trend confirmed", "futures lead signal"]


def test_valid_and_invalid_promotion_without_mutation():
    candidate = build_fixture_context()
    original = copy.deepcopy(candidate)
    promoted = promote_bounded_watchlist_cross_context_for_controlled_context(candidate)
    assert candidate == original
    assert promoted is not candidate
    assert promoted["safe_for_ai_context"] is True
    assert promoted["exposure_status"] == "ai_safe_context_enabled"
    assert promoted["controlled_exposure_policy"] == "m7d_controlled_bounded_watchlist_cross_context_v1"
    assert promoted["exposure_scope"] == "conversation_context_only"
    assert promoted["bounded_watchlist_only"] is True
    assert promoted["not_full_market_breadth"] is True
    assert promoted["cross_context_is_signal"] is False
    assert promoted["raw_rich_facts_exposed"] is False
    assert promoted["raw_full_ladder_exposed"] is False
    assert "future_builder_requirements" not in promoted
    blocked = promote_bounded_watchlist_cross_context_for_controlled_context({"schema_version":"bad"})
    assert blocked["safe_for_ai_context"] is False
    assert blocked["exposure_status"] == "blocked"
    assert blocked["blocked_reason"] == "not_valid_m7d_bounded_watchlist_cross_context_candidate"


def test_collection_helper_builds_one_context_from_shared_m7b_m7c_helpers_without_mutation():
    watchlist = {"schema_version": "m5n_watchlist.v1", "items": [
        {"id":"twse:2330", "symbol":"2330", "display_name":"TSMC", "market":"twse", "instrument_type":"listed_stock", "category":"equity", "enabled":True, "display_order":1, "adapter":"twse_mis_equity_etf_quote", "tags":[], "notes":""},
    ]}
    row = {"c":"2330", "ch":"2330.tw", "ex":"tse", "n":"台積電", "z":"1000", "y":"990", "o":"995", "h":"1005", "l":"980", "v":"1", "tv":"2", "b":"999_998_997_996_995", "g":"10_20_30_40_50", "a":"1000_1001_1002_1003_1004", "f":"11_21_31_41_51", "d":"20260707", "t":"13:20:00", "tlong":"1793952000000"}
    obs = normalize_twse_mis_row(row, {"symbol":"2330", "display_symbol":"2330", "market":"twse", "instrument_type":"listed_stock", "adapter_id":"twse_mis_equity_etf_quote"}, "2026-07-07T04:00:00Z")
    latest = {"status":"ok", "observations":[obs], "failures":[]}
    w0, l0 = copy.deepcopy(watchlist), copy.deepcopy(latest)
    collection = build_bounded_watchlist_cross_context_collection(watchlist, latest)
    assert watchlist == w0 and latest == l0
    assert collection["schema_version"] == "m7d_bounded_watchlist_cross_context_collection.v1"
    assert collection["enabled"] is True
    assert collection["safe_for_ai_context"] is True
    assert collection["context_count"] == 1
    assert len(collection["contexts"]) == 1
    assert collection["bounded_watchlist_only"] is True
    assert collection["not_full_market_breadth"] is True
    assert collection["cross_context_is_signal"] is False


def test_conversation_context_includes_bounded_context_without_raw_fields(monkeypatch):
    from scripts import m5k_common
    monkeypatch.setattr(m5k_common, "build_bounded_watchlist_cross_context_collection", lambda w, l: {"schema_version":"m7d_bounded_watchlist_cross_context_collection.v1", "enabled": True, "safe_for_ai_context": True, "context_count": 1, "contexts": [promote_bounded_watchlist_cross_context_for_controlled_context(build_fixture_context())], "bounded_watchlist_only": True, "not_full_market_breadth": True, "cross_context_is_signal": False, "not_trading_signal": True, "not_recommendation": True, "raw_rich_facts_exposed": False, "raw_full_ladder_exposed": False})
    context = build_conversation_context(fixture_watchlist(), fixture_latest())
    collection = context["bounded_watchlist_cross_context"]
    assert collection["safe_for_ai_context"] is True
    assert collection["context_count"] == 1
    assert collection["contexts"][0]["bounded_breadth_summary"]["status"] == "computed"
    rendered = json.dumps(collection, ensure_ascii=False).lower()
    for key in FORBIDDEN_KEYS:
        assert key not in rendered
    for phrase in FORBIDDEN_PHRASES:
        assert phrase not in rendered


def test_fastapi_mcp_latest_watchlist_source_health_boundaries(monkeypatch):
    latest = fixture_latest()
    import server.main as fastapi_main
    import server.mcp_server as mcp_server
    from scripts import m5k_common
    fake_collection = {"schema_version":"m7d_bounded_watchlist_cross_context_collection.v1", "enabled": True, "safe_for_ai_context": True, "context_count": 1, "contexts": [promote_bounded_watchlist_cross_context_for_controlled_context(build_fixture_context())], "bounded_watchlist_only": True, "not_full_market_breadth": True, "cross_context_is_signal": False, "not_trading_signal": True, "not_recommendation": True, "raw_rich_facts_exposed": False, "raw_full_ladder_exposed": False}
    monkeypatch.setattr(m5k_common, "build_bounded_watchlist_cross_context_collection", lambda w, l: fake_collection)
    monkeypatch.setattr(fastapi_main, "_m5k_read_latest_observation", lambda: latest)
    monkeypatch.setattr(mcp_server, "_m5k_read_latest_observation", lambda: latest)
    monkeypatch.setattr(fastapi_main, "_m5k_load_json", lambda path: fixture_watchlist())
    monkeypatch.setattr(mcp_server, "_m5k_load_json", lambda path: fixture_watchlist())
    assert fastapi_main.get_conversation_context()["content"]["bounded_watchlist_cross_context"]["context_count"] == 1
    assert mcp_server.get_conversation_context_tool()["content"]["bounded_watchlist_cross_context"]["context_count"] == 1
    assert "bounded_watchlist_cross_context" not in json.dumps(fastapi_main.get_m5k_latest_live_observation(), ensure_ascii=False)
    assert "bounded_watchlist_cross_context" not in json.dumps(fastapi_main.get_watchlist()["rows"], ensure_ascii=False)
    assert "bounded_watchlist_cross_context" not in json.dumps(build_watchlist_rows(fixture_watchlist(), latest), ensure_ascii=False)
    assert "bounded_watchlist_cross_context" not in json.dumps(build_report(execution_mode="check_only", live_result=latest), ensure_ascii=False)


def test_runtime_references_remain_controlled_to_shared_conversation_context():
    root = Path(__file__).resolve().parents[2]
    allowed = {
        "scripts/observation_contract.py", "scripts/m5k_common.py",
        "tests/unit/test_m7d_bounded_watchlist_cross_context_schema.py",
        "tests/unit/test_m7d_bounded_watchlist_cross_context_builder.py",
        "tests/unit/test_m7d_bounded_watchlist_cross_context_controlled_exposure.py",
        "tests/unit/test_m7d_bounded_watchlist_cross_context_final_acceptance.py",
        "tests/unit/test_twse_mis_rich_field_inventory.py",
    }
    names = ["build_bounded_watchlist_cross_context", "promote_bounded_watchlist_cross_context_for_controlled_context", "build_bounded_watchlist_cross_context_collection"]
    for base in ["server", "frontend", "scripts", "tests/unit"]:
        for path in (root / base).rglob("*.py"):
            rel = path.relative_to(root).as_posix()
            text = path.read_text(encoding="utf-8")
            if any(name in text for name in names):
                assert rel in allowed

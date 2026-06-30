import asyncio
import json

from fastapi.testclient import TestClient

from server.main import app
from server import mcp_server
from scripts.m5k_common import DEFAULT_WATCHLIST_PATH, build_conversation_context, load_json, validate_watchlist, watchlist_schema, watchlist_summary


def test_m5n_watchlist_schema_and_default_symbols():
    watchlist = load_json(DEFAULT_WATCHLIST_PATH)
    validation = validate_watchlist(watchlist)
    assert validation["valid"] is True
    assert "watchlist_summary" not in watchlist
    assert "items" not in watchlist
    assert watchlist_schema()["required_item_fields"] == ["id", "symbol", "display_name", "market", "instrument_type", "adapter", "category", "enabled", "display_order", "tags", "notes"]
    assert watchlist_summary(watchlist)["symbols"] == ["0050", "00878", "00919", "00929", "00934", "00939", "00940", "00981A", "1569", "2317", "2324", "2330", "2603", "2609", "3293", "3483", "3543", "TAIEX", "TX"]


def test_conversation_context_omits_raw_payloads():
    context = build_conversation_context(load_json(DEFAULT_WATCHLIST_PATH), {"observations": [], "failures": []})
    assert context["schema_version"] == "m5n_conversation_context.v1"
    assert context["governance"]["raw_endpoint_payload_included"] is False
    assert "raw_payload" not in json.dumps(context)


def test_fastapi_watchlist_endpoints():
    client = TestClient(app)
    for path in ["/api/watchlist", "/api/watchlist/summary", "/api/watchlist/schema", "/api/conversation/context"]:
        response = client.get(path)
        assert response.status_code == 200
        assert response.json()["governance"]["network_calls"] is False


def test_mcp_watchlist_tools_readonly():
    async def run():
        tools = await mcp_server.list_tools()
        names = {tool.name for tool in tools}
        assert {"get_watchlist", "get_watchlist_summary", "validate_watchlist", "get_conversation_context"}.issubset(names)
        for name in ["get_watchlist", "get_watchlist_summary", "validate_watchlist", "get_conversation_context"]:
            payload = json.loads((await mcp_server.call_tool(name, {}))[0].text)
            assert payload["status"] == "ok"
            assert payload["governance"]["network_calls"] is False
    asyncio.run(run())


def test_frontend_watchlist_workspace_static_contract():
    html = (DEFAULT_WATCHLIST_PATH.parents[1] / "frontend/readonly-preview/watchlist-workspace.html").read_text(encoding="utf-8")
    assert "/api/watchlist" in html
    assert "Last observation" in html
    assert "Export JSON" in html


def test_watchlist_governance_safety_recommendation_assertion_allowed():
    watchlist = load_json(DEFAULT_WATCHLIST_PATH)
    watchlist["governance"]["recommendation"] = False
    assert validate_watchlist(watchlist)["valid"] is True


def test_repaired_conversation_context_surfaces_all_governed_products():
    wl = load_json(DEFAULT_WATCHLIST_PATH)
    latest = {
        "schema_version": "m5k_live_observation.v1",
        "status": "ok",
        "generated_at_utc": "2026-06-30T00:00:00Z",
        "watchlist_id": "test",
        "observations": [
            {"symbol": "00878", "status": "ok", "source": "TWSE_MIS", "adapter_id": "twse_mis_equity_etf_quote", "price_like_value": 100.0, "price_semantics": "last_trade", "source_timestamp": "2026-06-30T00:00:00Z", "retrieved_at_utc": "2026-06-30T00:00:01Z", "freshness_assessment": "candidate", "delay_status": "not_realtime_guaranteed", "caveats": ["not_realtime_guaranteed"]},
            {"symbol": "2330", "status": "ok", "observation_status": "reference_value_only", "reference_only": True, "source": "TWSE_MIS", "adapter_id": "twse_mis_equity_etf_quote", "price_like_value": 900.0, "price_semantics": "previous_close_reference_not_current_trade", "failure_reason": "reference_value_only", "recommended_next_step": "Do not infer current trade."},
        ],
        "failures": [{"symbol": "TAIEX", "status": "failed", "source": "TWSE_MIS", "reason": "test_failure", "recommended_next_step": "Inspect source availability."}],
    }
    context = build_conversation_context(wl, latest)
    watchlist_symbols = watchlist_summary(wl)["symbols"]
    rows = context["per_symbol_observations"]
    assert [r["symbol"] for r in rows] == watchlist_symbols
    assert set(context["observation_summary"]) == {"healthy", "degraded", "failed", "unsupported", "reference_only"}
    assert context["observation_summary"]["healthy"] >= 1
    assert context["observation_summary"]["degraded"] >= 1
    assert context["observation_summary"]["failed"] >= 1
    assert context["observation_summary"]["reference_only"] >= 1
    assert any(r["status"] in {"unavailable", "failed", "unsupported"} for r in rows)
    assert all("symbol" in r and "recommended_next_step" in r and "display_caveats" in r for r in rows)
    assert context["canonical_summary"]["canonical_source"]
    assert context["canonical_summary"]["canonical_symbols"]
    assert context["source_health_summary"]["source_health_status"] in {"available", "not_available"}
    assert context["ai_guidance_summary"]["descriptive_only"] is True


def test_repaired_conversation_context_governance_no_leakage_or_trading_fields():
    context = build_conversation_context(load_json(DEFAULT_WATCHLIST_PATH))
    serialized = json.dumps(context, ensure_ascii=False).lower()
    assert "raw_payload" not in serialized
    assert "response_sample" not in serialized
    assert "raw_fields_sample" not in serialized
    assert context["governance"]["recommendation"] is False
    assert context["governance"]["target_price"] is False
    assert context["governance"]["ranking"] is False
    assert context["governance"]["buy_sell_hold"] is False
    for forbidden in ['"target_price": true', 'buy/sell/hold', 'target price']:
        assert forbidden not in serialized


def test_repaired_conversation_markdown_sections():
    context = build_conversation_context(load_json(DEFAULT_WATCHLIST_PATH))
    md = __import__("scripts.m5k_common", fromlist=["conversation_context_markdown"]).conversation_context_markdown(context)
    for section in ["Executive Summary", "Watchlist Summary", "Canonical Summary", "Latest Observation Summary", "Healthy Observations", "Degraded Observations", "Reference-only Observations", "Failed Observations", "Source Health", "Current Caveats", "Suggested Questions For AI"]:
        assert section in md
    assert "Canonical Summary is Level 1" in md


def test_stale_or_closed_session_ok_row_is_degraded_not_healthy():
    wl = load_json(DEFAULT_WATCHLIST_PATH)
    latest = {
        "schema_version": "m5k_live_observation.v1",
        "status": "ok",
        "generated_at_utc": "2026-06-30T00:00:00Z",
        "watchlist_id": "test",
        "observations": [
            {"symbol": "TX", "status": "ok", "source": "TAIFEX", "adapter_id": "taifex_mis_tx_futures_quote", "price_like_value": 45550.0, "price_semantics": "last_trade_price_or_settlement_fallback_as_reported_by_taifex_mis", "freshness_assessment": "stale_or_closed_session", "delay_status": "delay_seconds_measured_from_source_timestamp_not_exchange_realtime_sla", "caveats": ["not_realtime_guaranteed"]},
        ],
        "failures": [],
    }
    context = build_conversation_context(wl, latest)
    row = next(r for r in context["per_symbol_observations"] if r["symbol"] == "TX")
    assert row["status"] == "ok"
    assert row["freshness"] == "stale_or_closed_session"
    assert "TX" not in context["ai_guidance_summary"]["current_observations_available"]
    assert "TX" in context["ai_guidance_summary"]["degraded_observations"]
    assert "TX" in context["ai_guidance_summary"]["stale_or_closed_session_observations"]
    assert context["observation_summary"]["degraded"] >= 1
    assert context["observation_summary"]["healthy"] == 0
    md = __import__("scripts.m5k_common", fromlist=["conversation_context_markdown"]).conversation_context_markdown(context)
    assert "## Degraded Observations" in md
    degraded = md.split("## Degraded Observations", 1)[1].split("## Reference-only Observations", 1)[0]
    healthy = md.split("## Healthy Observations", 1)[1].split("## Degraded Observations", 1)[0]
    assert "TX TX futures" in degraded
    assert "TX TX futures" not in healthy

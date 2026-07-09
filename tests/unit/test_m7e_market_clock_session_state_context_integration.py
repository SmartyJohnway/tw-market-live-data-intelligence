from datetime import datetime, timezone

from scripts.m5k_common import build_conversation_context

FORBIDDEN = {"raw_payload", "twse_mis_rich_facts", "raw_rich_facts", "raw_unknown_facts", "full_ladder", "bid_prices", "ask_prices", "source_investigation_notes", "response_sample"}


def _watchlist():
    return {"schema_version": "m5n_watchlist.v1", "watchlist_id": "t", "name": "T", "items": [{"id": "2330", "symbol": "2330", "display_name": "TSMC", "market": "twse", "instrument_type": "equity", "adapter": "twse_mis_equity_etf_quote", "category": "core", "enabled": True, "display_order": 1, "tags": [], "notes": ""}]}


def _keys(value):
    if isinstance(value, dict):
        out = set(value)
        for child in value.values(): out |= _keys(child)
        return out
    if isinstance(value, list):
        out = set()
        for child in value: out |= _keys(child)
        return out
    return set()


def test_shared_context_integration_preserves_existing_keys_and_strips_raw():
    latest = {"schema_version": "latest.v1", "status": "ok", "generated_at_utc": "2026-01-05T01:09:00+00:00", "observations": [{"symbol": "2330", "source": "TWSE_MIS", "status": "ok", "retrieved_at_utc": "2026-01-05T01:09:00+00:00", "price_like_value": 100, "twse_mis_rich_facts": {"raw_payload": 1}, "full_ladder": [1], "bid_prices": [1], "ask_prices": [2], "response_sample": {"x": 1}}]}
    context = build_conversation_context(_watchlist(), latest, now_utc="2026-01-05T01:10:00+00:00")
    for key in ["ai_safe_market_context_projection", "deterministic_metrics_context", "bounded_watchlist_cross_context", "watchlist_summary", "per_symbol_observations", "latest_observation_summary", "ai_guidance_summary"]:
        assert key in context
    assert context["market_clock_session_state"]["safe_for_ai_context"] is True
    assert context["market_clock_session_state"]["builder_output_safe_for_ai_context"] is False
    assert context["market_clock_session_state"]["currentness_label"] == "live_candidate"
    assert context["ai_guidance_summary"]["market_clock_session_state"]
    assert not (FORBIDDEN & _keys(context["market_clock_session_state"]))


def test_currentness_caveats_for_weekend_and_heuristic():
    context = build_conversation_context(_watchlist(), {"generated_at_utc": "2026-01-03T01:09:00+00:00", "observations": []}, now_utc="2026-01-03T01:10:00+00:00")
    limitations = context["ai_guidance_summary"]["current_limitations"]
    assert any("must not be described as current intraday movement" in item for item in limitations)
    assert any("weekday heuristic only" in item for item in limitations)

from datetime import datetime, timedelta, timezone

from scripts.market_clock_session_state import (
    build_market_clock_session_state,
    promote_market_clock_session_state_for_controlled_context,
)

FORBIDDEN = {
    "raw_payload",
    "twse_mis_rich_facts",
    "raw_rich_facts",
    "raw_unknown_facts",
    "full_ladder",
    "bid_prices",
    "ask_prices",
    "source_investigation_notes",
    "response_sample",
}


def _iso(y, m, d, hh, mm):
    return datetime(y, m, d, hh, mm, tzinfo=timezone.utc).isoformat()


def _keys(value):
    if isinstance(value, dict):
        out = set(value)
        for child in value.values():
            out |= _keys(child)
        return out
    if isinstance(value, list):
        out = set()
        for child in value:
            out |= _keys(child)
        return out
    return set()


def test_controlled_promotion_success_live_candidate():
    now = _iso(2026, 1, 5, 1, 10)
    candidate = build_market_clock_session_state(
        now_utc=now,
        latest_observation={"retrieved_at_utc": (datetime.fromisoformat(now) - timedelta(seconds=60)).isoformat()},
    )
    promoted = promote_market_clock_session_state_for_controlled_context(candidate)
    assert candidate["safe_for_ai_context"] is False
    assert promoted["safe_for_ai_context"] is True
    assert promoted["builder_output_safe_for_ai_context"] is False
    assert promoted["exposure_status"] == "ai_safe_context_enabled"
    assert promoted["session_state"] == "regular_open"
    assert promoted["currentness_label"] == "live_candidate"
    assert promoted["raw_payload_exposed"] is False
    assert promoted["raw_rich_facts_exposed"] is False
    assert promoted["raw_full_ladder_exposed"] is False
    assert promoted["not_trading_signal"] is True
    assert promoted["not_recommendation"] is True


def test_controlled_promotion_fail_closed_for_malformed_candidate():
    promoted = promote_market_clock_session_state_for_controlled_context({"schema_version": "wrong"})
    assert promoted["safe_for_ai_context"] is False
    assert promoted["exposure_status"] == "ai_safe_context_disabled"
    assert promoted["context_status"] == "controlled_context_rejected"
    assert promoted["failure_reason"]
    assert promoted["raw_payload_exposed"] is False
    assert promoted["raw_rich_facts_exposed"] is False
    assert promoted["raw_full_ladder_exposed"] is False


def test_controlled_promotion_strips_raw_payload_keys():
    now = _iso(2026, 1, 5, 1, 10)
    candidate = build_market_clock_session_state(now_utc=now, latest_observation={"retrieved_at_utc": now, **{k: {"x": 1} for k in FORBIDDEN}})
    promoted = promote_market_clock_session_state_for_controlled_context(candidate | {"response_sample": {"bad": True}})
    assert not (FORBIDDEN & _keys(promoted))

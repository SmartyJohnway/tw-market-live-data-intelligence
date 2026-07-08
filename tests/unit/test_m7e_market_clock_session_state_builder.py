from datetime import datetime, timedelta, timezone

from scripts.market_clock_session_state import build_market_clock_session_state
from tests.unit.test_m7e_twse_holiday_schedule_classifier import FIXTURE


def iso(y, m, d, hh, mm):
    # UTC helper for Asia/Taipei local fixtures: local - 8h.
    return datetime(y, m, d, hh, mm, tzinfo=timezone.utc).isoformat()


def obs_at(now, seconds_old=60):
    return {"retrieved_at_utc": (datetime.fromisoformat(now) - timedelta(seconds=seconds_old)).isoformat(), "raw_payload": {"must": "not leak"}}


def test_weekday_session_states_with_weekday_heuristic_only():
    cases = [
        (iso(2026, 1, 5, 1, 10), "regular_open", "weekday_heuristic_only"),
        (iso(2026, 1, 5, 0, 30), "preopen", "weekday_heuristic_only"),
        (iso(2026, 1, 5, 5, 45), "postclose", "weekday_heuristic_only"),
        (iso(2026, 1, 5, 10, 0), "closed", "weekday_heuristic_only"),
    ]
    for now, state, confidence in cases:
        got = build_market_clock_session_state(now_utc=now)
        assert got["session_state"] == state
        assert got["calendar_confidence"] == confidence
        assert got["holiday_status"] == "records_missing"


def test_weekend_holiday_and_explicit_endpoint_trading_label():
    saturday = build_market_clock_session_state(now_utc=iso(2026, 1, 3, 1, 10), holiday_schedule_records=FIXTURE, latest_observation={"retrieved_at_utc": iso(2026, 1, 3, 1, 9)})
    assert saturday["session_state"] == "weekend_closed"
    assert saturday["holiday_status"] == "weekend"
    assert saturday["currentness_label"] == "not_current"

    holiday = build_market_clock_session_state(now_utc=iso(2026, 1, 1, 1, 10), holiday_schedule_records=FIXTURE)
    assert holiday["session_state"] == "holiday_closed"
    assert holiday["holiday_status"] == "endpoint_non_trading_date"

    trading_label = build_market_clock_session_state(now_utc=iso(2026, 1, 2, 1, 10), holiday_schedule_records=FIXTURE, latest_observation={"retrieved_at_utc": iso(2026, 1, 2, 1, 9)})
    assert trading_label["holiday_status"] == "explicit_endpoint_trading_label"
    assert trading_label["session_state"] == "regular_open"


def test_freshness_and_currentness_classification():
    now = iso(2026, 1, 5, 1, 10)
    assert build_market_clock_session_state(now_utc=now, latest_observation=obs_at(now, 60))["currentness_label"] == "live_candidate"
    stale = build_market_clock_session_state(now_utc=now, latest_observation=obs_at(now, 1000))
    assert stale["freshness_state"] == "stale"
    assert stale["currentness_label"] == "reference_only"

    postclose_now = iso(2026, 1, 5, 5, 45)
    assert build_market_clock_session_state(now_utc=postclose_now, latest_observation=obs_at(postclose_now, 60))["currentness_label"] == "reference_only"

    weekend_now = iso(2026, 1, 3, 1, 10)
    assert build_market_clock_session_state(now_utc=weekend_now, latest_observation=obs_at(weekend_now, 60))["currentness_label"] == "not_current"

    missing = build_market_clock_session_state(now_utc=now, latest_observation={"symbol": "2330"})
    assert missing["freshness_state"] == "no_observation"
    assert missing["currentness_label"] == "degraded_unknown"

    future = build_market_clock_session_state(now_utc=now, latest_observation={"retrieved_at_utc": (datetime.fromisoformat(now) + timedelta(seconds=120)).isoformat()})
    assert future["freshness_state"] == "future_timestamp"
    assert future["currentness_label"] == "degraded_unknown"


def test_builder_does_not_expose_raw_payload_or_positive_signal_claims():
    got = build_market_clock_session_state(now_utc=iso(2026, 1, 5, 1, 10), latest_observation={"retrieved_at_utc": iso(2026, 1, 5, 1, 9), "raw_rich_facts": {"x": 1}, "full_ladder": [1]})
    text = str(got)
    assert "raw_rich_facts': {'x'" not in text
    assert "full_ladder': [1]" not in text
    assert got["safe_for_ai_context"] is False
    assert got["builder_output_safe_for_ai_context"] is False
    assert got["quality_gates"]["raw_payload_exposed"] is False
    for phrase in ["buy signal", "sell signal", "recommendation", "support", "resistance", "capital flow"]:
        assert phrase in got["blocked_language"]
        assert phrase not in got["allowed_language"]

import json

import pytest

from scripts.twse_trading_calendar import build_twse_trading_calendar_from_holiday_schedule, load_twse_trading_calendar_artifact
from scripts.market_clock_session_state import build_market_clock_session_state

RECORDS = [
    {"Name": "中華民國開國紀念日", "Date": "1150101", "Weekday": "四", "Description": "依規定放假1日。"},
    {"Name": "國曆新年開始交易日", "Date": "1150102", "Weekday": "五", "Description": "國曆新年開始交易。"},
    {"Name": "市場無交易，僅辦理結算交割作業", "Date": "1150212", "Weekday": "四", "Description": ""},
    {"Name": "bad", "Date": "bad", "Weekday": "?", "Description": "invalid"},
]

def test_calendar_artifact_shape_and_invalid_records():
    cal = build_twse_trading_calendar_from_holiday_schedule(year=2026, holiday_schedule_records=RECORDS, generated_at_utc="2026-01-01T00:00:00Z")
    assert cal["schema_version"] == "twse_trading_calendar.v1"
    assert cal["market"] == "TWSE"
    assert cal["year"] == 2026
    assert cal["date_count"] == 365
    assert cal["trading_day_count"] + cal["non_trading_day_count"] == 365
    assert cal["source"]["runtime_fetch"] is False
    assert cal["not_full_exchange_calendar_engine"] is True
    assert cal["no_realtime_sla"] is True
    assert cal["not_trading_advice"] is True
    assert cal["invalid_records"] and cal["invalid_records"][0]["Date"] == "bad"
    assert "Description" not in cal["dates"][0].get("source_evidence", [{}])[0]

def test_load_artifact_validates_schema_and_does_not_mutate(tmp_path):
    cal = build_twse_trading_calendar_from_holiday_schedule(year=2026, holiday_schedule_records=RECORDS, generated_at_utc="2026-01-01T00:00:00Z")
    p = tmp_path / "cal.json"
    p.write_text(json.dumps(cal), encoding="utf-8")
    loaded = load_twse_trading_calendar_artifact(p)
    loaded["dates"] = []
    assert len(load_twse_trading_calendar_artifact(p)["dates"]) == 365
    bad = tmp_path / "bad.json"
    bad.write_text('{"schema_version":"wrong"}', encoding="utf-8")
    with pytest.raises(ValueError):
        load_twse_trading_calendar_artifact(bad)

def test_market_clock_builder_uses_calendar_artifact_without_missing_records_caveat():
    cal = build_twse_trading_calendar_from_holiday_schedule(year=2026, holiday_schedule_records=RECORDS, generated_at_utc="2026-01-01T00:00:00Z")
    state = build_market_clock_session_state(now_utc="2026-02-12T02:00:00Z", trading_calendar_artifact=cal)
    assert state["calendar_confidence"] == "controlled_twse_holiday_schedule_artifact"
    assert state["holiday_status"] == "endpoint_non_trading_date"
    assert state["is_trading_day_candidate"] is False
    assert not any("Holiday records missing" in c for c in state["semantic_caveats"])


def test_market_clock_builder_fails_closed_when_calendar_artifact_missing_date():
    cal = build_twse_trading_calendar_from_holiday_schedule(year=2026, holiday_schedule_records=RECORDS, generated_at_utc="2026-01-01T00:00:00Z")
    cal["dates"] = [d for d in cal["dates"] if d["date"] != "2026-01-05"]

    state = build_market_clock_session_state(
        now_utc="2026-01-05T01:10:00+00:00",
        latest_observation={"retrieved_at_utc": "2026-01-05T01:09:00+00:00"},
        trading_calendar_artifact=cal,
    )

    assert state["calendar_confidence"] == "artifact_missing_date"
    assert state["is_trading_day_candidate"] is False
    assert state["currentness_label"] == "degraded_unknown"
    assert state["holiday_status"] == "date_not_found_in_artifact"
    assert "Date not found in supplied TWSE trading calendar artifact." in state["semantic_caveats"]

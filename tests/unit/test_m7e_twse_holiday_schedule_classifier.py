from datetime import date
import pytest

from scripts.market_clock_session_state import classify_twse_holiday_schedule_records, parse_twse_roc_date

FIXTURE = [
    {"Name": "中華民國開國紀念日", "Date": "1150101", "Weekday": "四", "Description": "依規定放假1日。"},
    {"Name": "國曆新年開始交易日", "Date": "1150102", "Weekday": "五", "Description": "國曆新年開始交易。"},
    {"Name": "農曆春節前最後交易日", "Date": "1150211", "Weekday": "三", "Description": "農曆春節前最後交易。"},
    {"Name": "市場無交易，僅辦理結算交割作業", "Date": "1150212", "Weekday": "四", "Description": ""},
    {"Name": "市場無交易，僅辦理結算交割作業", "Date": "1150213", "Weekday": "五", "Description": ""},
    {"Name": "農曆春節後開始交易日", "Date": "1150223", "Weekday": "一", "Description": "農曆春節後開始交易。"},
]


def test_parse_twse_roc_date():
    assert parse_twse_roc_date("1150101") == date(2026, 1, 1)
    assert parse_twse_roc_date("1141231") == date(2025, 12, 31)
    for bad in ["", "115010", "11501010", "abc0101", "0000101", "1150230"]:
        with pytest.raises(ValueError):
            parse_twse_roc_date(bad)


def test_holiday_schedule_trading_day_trap_and_non_trading_dates():
    got = classify_twse_holiday_schedule_records(FIXTURE + [{"Name": "壞資料", "Date": "bad", "Weekday": "?"}])
    non = {r["gregorian_date"]: r for r in got["endpoint_non_trading_dates"]}
    explicit = {r["gregorian_date"]: r for r in got["explicit_endpoint_trading_dates"]}
    assert "2026-01-01" in non
    assert "2026-02-12" in non
    assert "2026-02-13" in non
    assert "2026-01-02" in explicit
    assert "2026-02-11" in explicit
    assert "2026-02-23" in explicit
    assert "2026-01-02" not in non
    assert got["invalid_records"]
    assert got["schema_version"] == "m7e_twse_holiday_schedule_classification.v1"

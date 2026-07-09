from scripts.twse_trading_calendar import build_twse_trading_calendar_from_holiday_schedule, resolve_twse_trading_day, is_twse_trading_day, parse_twse_roc_date

RECORDS = [
    {"Name": "中華民國開國紀念日", "Date": "1150101", "Weekday": "四", "Description": "依規定放假1日。"},
    {"Name": "國曆新年開始交易日", "Date": "1150102", "Weekday": "五", "Description": "國曆新年開始交易。"},
    {"Name": "農曆春節前最後交易日", "Date": "1150211", "Weekday": "三", "Description": "農曆春節前最後交易。<br>"},
    {"Name": "市場無交易，僅辦理結算交割作業", "Date": "1150212", "Weekday": "四", "Description": ""},
    {"Name": "市場無交易，僅辦理結算交割作業", "Date": "1150213", "Weekday": "五", "Description": ""},
    {"Name": "農曆春節後開始交易日", "Date": "1150223", "Weekday": "一", "Description": "農曆春節後開始交易。"},
]

def artifact():
    return build_twse_trading_calendar_from_holiday_schedule(year=2026, holiday_schedule_records=RECORDS, generated_at_utc="2026-01-01T00:00:00Z")

def by_date(cal, d):
    return next(x for x in cal["dates"] if x["date"] == d)

def test_roc_date_and_trading_day_trap():
    assert parse_twse_roc_date("1150101").isoformat() == "2026-01-01"
    cal = artifact()
    expected = {
        "2026-01-01": (False, "endpoint_non_trading_date"),
        "2026-01-02": (True, "explicit_endpoint_trading_label"),
        "2026-02-11": (True, "explicit_endpoint_trading_label"),
        "2026-02-12": (False, "endpoint_non_trading_date"),
        "2026-02-13": (False, "endpoint_non_trading_date"),
        "2026-02-23": (True, "explicit_endpoint_trading_label"),
    }
    for d, (is_trading, reason) in expected.items():
        row = by_date(cal, d)
        assert row["is_trading_day"] is is_trading
        assert row["reason"] == reason

def test_weekend_rule():
    cal = artifact()
    assert by_date(cal, "2026-01-03")["reason"] == "weekend_non_trading"
    assert by_date(cal, "2026-01-03")["is_trading_day"] is False
    assert by_date(cal, "2026-01-04")["reason"] == "weekend_non_trading"
    assert by_date(cal, "2026-01-04")["is_trading_day"] is False

def test_resolver_and_boolean_wrapper():
    cal = artifact()
    r = resolve_twse_trading_day(target_date="2026-01-02", calendar_artifact=cal)
    assert r["trading_day_status"] == "trading_day"
    assert r["calendar_confidence"] == "controlled_twse_holiday_schedule_artifact"
    r = resolve_twse_trading_day(target_date="2026-02-12", calendar_artifact=cal)
    assert r["trading_day_status"] == "non_trading_day"
    assert r["calendar_confidence"] == "controlled_twse_holiday_schedule_artifact"
    assert is_twse_trading_day("2026-01-02", cal) is True
    assert is_twse_trading_day("2026-02-12", cal) is False

def test_resolver_without_artifact_and_missing_date():
    r = resolve_twse_trading_day(target_date="2026-01-02")
    assert r["calendar_confidence"] == "weekday_heuristic_only"
    assert r["source"] == "weekday_heuristic"
    assert "artifact not supplied" in r["caveats"][0]
    cal = artifact()
    cal["dates"] = [d for d in cal["dates"] if d["date"] != "2026-01-02"]
    missing = resolve_twse_trading_day(target_date="2026-01-02", calendar_artifact=cal)
    assert missing["calendar_confidence"] == "artifact_missing_date"
    assert missing["trading_day_status"] == "unknown"
    assert missing["is_trading_day"] is None
    assert is_twse_trading_day("2026-01-02", cal) is None

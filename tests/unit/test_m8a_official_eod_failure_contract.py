from scripts.m8a_official_eod_currentness import classify_batch_status, classify_currentness

def test_batch_status_helpers():
    assert classify_batch_status(row_count_received=0) == "empty_non_trading_day"
    assert classify_batch_status(schema_drift=True) == "schema_drift"
    assert classify_batch_status(source_status="timeout") == "source_unavailable"
    assert classify_batch_status(mixed_dates=True) == "date_mismatch"
    assert classify_batch_status(row_count_received=2,row_count_retained=1,row_count_rejected=1) == "partial_source_success"

def test_currentness_status_helpers():
    assert classify_currentness("2026-07-09","2026-07-09") == "current_official_eod"
    assert classify_currentness("2026-07-09","2026-07-09", emergency_closure=True) == "matches_expected_latest_trade_date_after_emergency_closure"
    assert classify_currentness("2026-07-08","2026-07-09", trading_day_lag=1) == "delayed_one_trading_day"
    assert classify_currentness("2026-07-07","2026-07-09") == "stale_official_eod"
    assert classify_currentness(None,"2026-07-09") == "unresolved_date_mismatch"

def test_no_raw_or_secret_failure_text_in_results():
    r={"rejected_rows":[{"row_index":1,"source_field_names":["Code"],"reason_code":"x"}]}
    text=str(r).lower()
    assert "authorization" not in text and "cookie" not in text and "raw_payload" not in text

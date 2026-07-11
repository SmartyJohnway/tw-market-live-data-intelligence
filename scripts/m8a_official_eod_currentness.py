"""Pure M8A currentness and failure status helpers."""
BATCH_STATUSES={"successful_eod_batch","empty_non_trading_day","source_unavailable","source_error","schema_drift","date_mismatch","valid_zero_trade_row","partial_source_success"}
CURRENTNESS_STATUSES={"current_official_eod","matches_expected_latest_trade_date_after_emergency_closure","delayed_one_trading_day","stale_official_eod","unresolved_date_mismatch"}
def classify_batch_status(*, source_status="success", row_count_received=0, row_count_retained=0, row_count_rejected=0, mixed_dates=False, schema_drift=False):
    if schema_drift: return "schema_drift"
    if source_status in {"timeout","unavailable"}: return "source_unavailable"
    if source_status not in {"success","ok"}: return "source_error"
    if mixed_dates: return "date_mismatch"
    if row_count_received == 0: return "empty_non_trading_day"
    if row_count_retained and row_count_rejected: return "partial_source_success"
    return "successful_eod_batch"
def classify_currentness(reported_trade_date, expected_latest_trade_date, *, emergency_closure=False, trading_day_lag=0, unresolved=False):
    if unresolved or not reported_trade_date or not expected_latest_trade_date: return "unresolved_date_mismatch"
    if reported_trade_date == expected_latest_trade_date: return "matches_expected_latest_trade_date_after_emergency_closure" if emergency_closure else "current_official_eod"
    if trading_day_lag == 1: return "delayed_one_trading_day"
    return "stale_official_eod"

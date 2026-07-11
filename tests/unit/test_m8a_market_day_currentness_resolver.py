from scripts.m8a_market_day_currentness_resolver import resolve_market_day_currentness
EV={"source_id":"NCDR_DGPA_CLOSURE_CAP","entry_id":"e","area_name":"臺北市","area_level":"municipality","target_date":"2026-07-10","work_status":"closed","decision_status":"closure_confirmed","closure_scope":"full_day"}
def test_normal_weekend_and_taipei_closure():
    assert resolve_market_day_currentness(evaluation_time_asia_taipei='2026-07-09T16:00:00+08:00',reported_trade_date='2026-07-09')['currentness_status']=='current_official_eod'
    assert resolve_market_day_currentness(evaluation_time_asia_taipei='2026-07-11T16:00:00+08:00',reported_trade_date='2026-07-10')['actual_market_day_status']=='scheduled_closed'
    r=resolve_market_day_currentness(evaluation_time_asia_taipei='2026-07-10T16:00:00+08:00',reported_trade_date='2026-07-09',closure_events=[EV])
    assert r['exchange_market_status']=='closed_by_taipei_work_suspension_rule'
    assert r['currentness_status']=='matches_expected_latest_trade_date_after_emergency_closure'
def test_delayed_stale_unresolved_special():
    assert resolve_market_day_currentness(evaluation_time_asia_taipei='2026-07-10T16:00:00+08:00',reported_trade_date='2026-07-09')['currentness_status']=='delayed_one_trading_day'
    assert resolve_market_day_currentness(evaluation_time_asia_taipei='2026-07-10T16:00:00+08:00',reported_trade_date='2026-07-08')['currentness_status']=='stale_official_eod'
    assert resolve_market_day_currentness(evaluation_time_asia_taipei='2026-07-10T16:00:00+08:00',reported_trade_date=None)['currentness_status']=='unresolved_date_mismatch'
    assert resolve_market_day_currentness(evaluation_time_asia_taipei='2026-07-10T16:00:00+08:00',reported_trade_date='2026-07-09',exchange_special_status='closed_by_exchange_special_announcement')['actual_market_day_status']=='emergency_closed'

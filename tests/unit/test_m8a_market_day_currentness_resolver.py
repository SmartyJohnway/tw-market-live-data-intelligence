from scripts.m8a_market_day_currentness_resolver import resolve_market_day_currentness, previous_actual_trading_day
EV={"source_id":"NCDR_DGPA_CLOSURE_CAP","entry_id":"e","area_name":"臺北市","area_level":"municipality","target_date":"2026-07-10","work_status":"closed","decision_status":"closure_confirmed","closure_scope":"full_day"}
def cal(closed):
    return {"dates":[{"date":d,"is_trading_day":False} for d in closed]}
def test_unknown_empty_and_taipei_closure_states():
    assert resolve_market_day_currentness(evaluation_time_asia_taipei='2026-07-09T16:00:00+08:00',reported_trade_date='2026-07-09',closure_events=None)['emergency_closure_status']=='emergency_closure_unknown'
    assert resolve_market_day_currentness(evaluation_time_asia_taipei='2026-07-09T16:00:00+08:00',reported_trade_date='2026-07-09',closure_events=[],closure_query_succeeded=True)['emergency_closure_status']=='no_emergency_closure_found'
    r=resolve_market_day_currentness(evaluation_time_asia_taipei='2026-07-10T16:00:00+08:00',reported_trade_date='2026-07-09',closure_events=[EV])
    assert r['exchange_market_status']=='closed_by_taipei_work_suspension_rule'
    assert r['currentness_status']=='matches_expected_latest_trade_date_after_emergency_closure'
def test_pre_and_post_eod_session_logic():
    assert resolve_market_day_currentness(evaluation_time_asia_taipei='2026-07-10T10:00:00+08:00',reported_trade_date='2026-07-09',closure_events=[],closure_query_succeeded=True)['expected_latest_completed_trade_date']=='2026-07-09'
    assert resolve_market_day_currentness(evaluation_time_asia_taipei='2026-07-10T16:00:00+08:00',reported_trade_date='2026-07-10',closure_events=[],closure_query_succeeded=True)['expected_latest_completed_trade_date']=='2026-07-10'
def test_consecutive_scheduled_holidays_and_emergency_previous_search():
    c=cal(['2026-07-08','2026-07-09'])
    assert previous_actual_trading_day(__import__('datetime').date.fromisoformat('2026-07-10'), c).isoformat()=='2026-07-07'
    ev=dict(EV, target_date='2026-07-09')
    assert previous_actual_trading_day(__import__('datetime').date.fromisoformat('2026-07-10'), None, [ev]).isoformat()=='2026-07-08'
def test_delayed_stale_unresolved_special():
    assert resolve_market_day_currentness(evaluation_time_asia_taipei='2026-07-10T16:00:00+08:00',reported_trade_date='2026-07-09',closure_events=[],closure_query_succeeded=True)['currentness_status']=='delayed_one_trading_day'
    assert resolve_market_day_currentness(evaluation_time_asia_taipei='2026-07-10T16:00:00+08:00',reported_trade_date='2026-07-08',closure_events=[],closure_query_succeeded=True)['currentness_status']=='stale_official_eod'
    assert resolve_market_day_currentness(evaluation_time_asia_taipei='2026-07-10T16:00:00+08:00',reported_trade_date=None)['currentness_status']=='unresolved_date_mismatch'
    assert resolve_market_day_currentness(evaluation_time_asia_taipei='2026-07-10T16:00:00+08:00',reported_trade_date='2026-07-09',exchange_special_status='closed_by_exchange_special_announcement')['actual_market_day_status']=='emergency_closed'

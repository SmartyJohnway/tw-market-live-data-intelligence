from datetime import date
from scripts.m8a_market_day_currentness_resolver import resolve_market_day_currentness, previous_actual_trading_day, previous_actual_trading_day_resolution
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
    assert previous_actual_trading_day(date.fromisoformat('2026-07-10'), c).isoformat()=='2026-07-07'
    ev=dict(EV, target_date='2026-07-09')
    assert previous_actual_trading_day(date.fromisoformat('2026-07-10'), None, [ev]).isoformat()=='2026-07-08'
def test_saturday_and_sunday_preserve_friday_emergency_causality():
    sat=resolve_market_day_currentness(evaluation_time_asia_taipei='2026-07-11T16:00:00+08:00',reported_trade_date='2026-07-09',closure_events=[EV],closure_query_succeeded=True)
    sun=resolve_market_day_currentness(evaluation_time_asia_taipei='2026-07-12T16:00:00+08:00',reported_trade_date='2026-07-09',closure_events=[EV],closure_query_succeeded=True)
    assert sat['currentness_status']=='matches_expected_latest_trade_date_after_emergency_closure'
    assert sun['currentness_status']=='matches_expected_latest_trade_date_after_emergency_closure'
    assert {'date':'2026-07-10','reason':'emergency_closed'} in sat['expected_latest_completed_trade_date_resolution_trace']
    assert {'date':'2026-07-10','reason':'emergency_closed'} in sun['expected_latest_completed_trade_date_resolution_trace']
def test_normal_weekend_without_emergency_stays_current_official_eod():
    r=resolve_market_day_currentness(evaluation_time_asia_taipei='2026-07-11T16:00:00+08:00',reported_trade_date='2026-07-10',closure_events=[],closure_query_succeeded=True)
    assert r['currentness_status']=='current_official_eod'
    assert r['expected_latest_completed_trade_date_resolution_trace'][0]['reason']=='weekend'
def test_before_next_actual_trading_session_preserves_emergency_causality():
    r=resolve_market_day_currentness(evaluation_time_asia_taipei='2026-07-13T10:00:00+08:00',reported_trade_date='2026-07-09',closure_events=[EV],closure_query_succeeded=True)
    assert r['expected_latest_completed_trade_date']=='2026-07-09'
    assert r['currentness_status']=='matches_expected_latest_trade_date_after_emergency_closure'
def test_delayed_stale_unresolved_special_and_trace():
    assert resolve_market_day_currentness(evaluation_time_asia_taipei='2026-07-10T16:00:00+08:00',reported_trade_date='2026-07-09',closure_events=[],closure_query_succeeded=True)['currentness_status']=='delayed_one_trading_day'
    assert resolve_market_day_currentness(evaluation_time_asia_taipei='2026-07-10T16:00:00+08:00',reported_trade_date='2026-07-08',closure_events=[],closure_query_succeeded=True)['currentness_status']=='stale_official_eod'
    assert resolve_market_day_currentness(evaluation_time_asia_taipei='2026-07-10T16:00:00+08:00',reported_trade_date=None)['currentness_status']=='unresolved_date_mismatch'
    trace=previous_actual_trading_day_resolution(date.fromisoformat('2026-07-13'), exchange_special_closures=['2026-07-10'])
    assert {'date':'2026-07-10','reason':'exchange_special_closed'} in trace['skipped_dates']

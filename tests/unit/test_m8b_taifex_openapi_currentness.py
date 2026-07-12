from scripts.m8b_taifex_currentness import evaluate_taifex_derivatives_currentness, final_settlement_currentness

def test_currentness_uses_evaluation_time_current_after_close():
 r=evaluate_taifex_derivatives_currentness(reported_trade_date='2026-07-10',evaluation_time_asia_taipei='2026-07-10T16:00:00+08:00',closure_query_succeeded=True)
 assert r['status']=='current_official_derivatives_eod'
 assert r['expected_latest_completed_trade_date']=='2026-07-10'

def test_currentness_weekend_prior_trading_date():
 r=evaluate_taifex_derivatives_currentness(reported_trade_date='2026-07-10',evaluation_time_asia_taipei='2026-07-12T12:00:00+08:00',closure_query_succeeded=True)
 assert r['status']=='current_official_derivatives_eod'
 assert r['expected_latest_completed_trade_date']=='2026-07-10'

def test_currentness_emergency_closure_explanation():
 closure=[{'source_id':'NCDR_DGPA_CLOSURE_CAP','area_name':'臺北市','target_date':'2026-07-13','status':'Actual','area_level':'municipality','work_status':'closed','decision_status':'closure_confirmed','closure_scope':'full_day','entry_id':'x'}]
 r=evaluate_taifex_derivatives_currentness(reported_trade_date='2026-07-10',evaluation_time_asia_taipei='2026-07-13T16:00:00+08:00',closure_events=closure,closure_query_succeeded=True)
 assert r['status']=='unresolved_date_mismatch'
 assert 'taifex_specific_closure_evidence_missing' in r['caveats']
 assert r['expected_latest_completed_trade_date']=='2026-07-10'

def test_currentness_missing_evaluation_time_unresolved_and_delayed():
 assert evaluate_taifex_derivatives_currentness(reported_trade_date='2026-07-10',evaluation_time_asia_taipei=None)['status']=='unresolved_date_mismatch'
 r=evaluate_taifex_derivatives_currentness(reported_trade_date='2026-07-09',evaluation_time_asia_taipei='2026-07-10T16:00:00+08:00',closure_query_succeeded=True)
 assert r['status']=='delayed_one_trading_day'

def test_currentness_does_not_force_twse_tpex_equality_and_session_unresolved():
 r=evaluate_taifex_derivatives_currentness(reported_trade_date='2026-07-10',evaluation_time_asia_taipei='2026-07-10T16:00:00+08:00',session='unknown',closure_query_succeeded=True)
 assert r['status']=='session_semantics_unresolved'
 assert r['source_specific'] is True

def test_final_settlement_not_daily_stale():
 assert final_settlement_currentness('2025-01-01')['status']=='official_final_settlement_reference'
 assert final_settlement_currentness('2025-01-01',latest_reference_date='2026-01-01')['status']=='historical_final_settlement_reference'


def test_taifex_special_closure_can_confirm_and_calendar_incomplete_is_provisional():
 r=evaluate_taifex_derivatives_currentness(reported_trade_date='2026-07-10',evaluation_time_asia_taipei='2026-07-13T16:00:00+08:00',closure_query_succeeded=True,exchange_special_closures=['2026-07-13'])
 assert r['status']=='matches_expected_latest_trade_date_after_emergency_closure'
 assert r['calendar_evidence']=='incomplete' and r['currentness_confidence']=='provisional'

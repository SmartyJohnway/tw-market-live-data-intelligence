from scripts.m8c_taifex_mis_probe_common import classify_currentness

def test_recent_retrieval_old_closed_not_fresh():
    c=classify_currentness(retrieved_recent=True,source_timestamp_state='resolved',session_alignment='closed_session_aligned',market_phase='closed',quote_age_state='not_applicable_closed_session',calendar_evidence='provided')
    assert c['overall_ai_currentness']=='closed_session_latest_completed'
    assert c['overall_ai_currentness']!='active_session_fresh_liveish'

def test_special_closure_and_unresolved():
    assert classify_currentness(retrieved_recent=True,source_timestamp_state='resolved',session_alignment='special_closure_aligned',market_phase='closed',quote_age_state='not_applicable_closed_session',calendar_evidence='official')['overall_ai_currentness']=='special_closure_latest_completed'
    assert classify_currentness(retrieved_recent=True,source_timestamp_state='missing',session_alignment='aligned',market_phase='trading',quote_age_state='fresh',calendar_evidence='missing')['overall_ai_currentness']=='source_timestamp_unresolved'
    assert classify_currentness(retrieved_recent=True,source_timestamp_state='resolved',session_alignment='unresolved',market_phase='trading',quote_age_state='fresh',calendar_evidence='missing')['overall_ai_currentness']=='session_alignment_unresolved'

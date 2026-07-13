from __future__ import annotations
from datetime import datetime
from zoneinfo import ZoneInfo
FRESH_SECONDS=90; AGING_SECONDS=300

def evaluate_taifex_mis_currentness(*, accepted_mode_1:bool, source_timestamp_asia_taipei:str|None, evaluation_time_asia_taipei:str|None, session:str, market_phase:str|None, calendar_context:dict|None=None, transport_state:str='completed'):
    if not accepted_mode_1:
        overall='transport_completed_without_valid_snapshot'; age_state='unavailable'; ts_state='unresolved'
    elif session!='regular':
        overall='session_alignment_unresolved'; age_state='unresolved'; ts_state='ambiguous_after_hours'
    else:
        try:
            src=datetime.fromisoformat(source_timestamp_asia_taipei) if source_timestamp_asia_taipei else None
            ev=datetime.fromisoformat(evaluation_time_asia_taipei) if evaluation_time_asia_taipei else datetime.now(ZoneInfo('Asia/Taipei'))
            if src and src.tzinfo is None: src=src.replace(tzinfo=ZoneInfo('Asia/Taipei'))
            if ev.tzinfo is None: ev=ev.replace(tzinfo=ZoneInfo('Asia/Taipei'))
            age=(ev-src).total_seconds() if src else None
            ts_state='resolved' if src else 'unresolved'
        except Exception:
            age=None; ts_state='unresolved'
        if ts_state!='resolved': overall='source_timestamp_unresolved'; age_state='unresolved'
        elif not market_phase or market_phase=='unresolved': overall='market_phase_unresolved'; age_state='fresh' if age is not None and age<=FRESH_SECONDS else 'aging_or_stale'
        elif market_phase in ('closed','postclose'): overall='closed_session_latest_completed'; age_state='closed'
        elif market_phase in ('preopen','indicative'): overall='preopen_indicative_snapshot'; age_state='preopen'
        elif age is not None and age<=FRESH_SECONDS and market_phase in ('trading','active'): overall='active_session_fresh_liveish'; age_state='fresh'
        elif age is not None and age<=AGING_SECONDS and market_phase in ('trading','active'): overall='active_session_aging_liveish'; age_state='aging'
        else: overall='active_session_stale_liveish'; age_state='stale'
    return {'transport_state':transport_state,'session_alignment':'aligned' if session=='regular' else 'unresolved','market_phase':market_phase or 'unresolved','source_timestamp_state':ts_state,'quote_age_state':age_state,'calendar_evidence':(calendar_context or {}).get('authority','not_provided'),'currentness_confidence':'bounded_policy_not_exchange_sla','retrieved_at_freshness_ignored_for_upgrade':True,'overall_ai_currentness':overall}

from __future__ import annotations
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo
FRESH_SECONDS=90; AGING_SECONDS=300
VERIFIED_ACTIVE_MARKET_PHASES={'active_regular_trading'}

def _parse_dt(v):
    if not v: return None
    dt=datetime.fromisoformat(v)
    return dt.replace(tzinfo=ZoneInfo('Asia/Taipei')) if dt.tzinfo is None else dt

def _regular_window(ev):
    t=ev.astimezone(ZoneInfo('Asia/Taipei')).time()
    return dtime(8,45) <= t <= dtime(13,45)

def evaluate_taifex_mis_currentness(*, accepted_mode_1:bool, source_timestamp_asia_taipei:str|None, evaluation_time_asia_taipei:str|None, session:str, market_phase:str|None, calendar_context:dict|None=None, transport_state:str='completed', session_suffix_aligned:bool=True):
    phase=market_phase or 'market_phase_unresolved'
    if not accepted_mode_1:
        overall='transport_completed_without_valid_snapshot'; age_state='unavailable'; ts_state='unresolved'; aligned='aligned' if session=='regular' else 'unresolved'
    elif session!='regular' or not session_suffix_aligned:
        overall='session_alignment_unresolved'; age_state='unresolved'; ts_state='ambiguous_after_hours' if session!='regular' else 'resolved'; aligned='unresolved'
    else:
        try:
            src=_parse_dt(source_timestamp_asia_taipei); ev=_parse_dt(evaluation_time_asia_taipei) or datetime.now(ZoneInfo('Asia/Taipei'))
            age=(ev-src).total_seconds() if src else None
            ts_state='resolved' if src else 'unresolved'
        except Exception:
            src=None; ev=datetime.now(ZoneInfo('Asia/Taipei')); age=None; ts_state='unresolved'
        aligned='aligned'
        if ts_state!='resolved': overall='source_timestamp_unresolved'; age_state='unresolved'
        elif age is not None and age < 0: overall='source_timestamp_unresolved'; age_state='future_source_timestamp'
        elif not _regular_window(ev): overall='session_alignment_unresolved'; age_state='outside_regular_session_window'
        elif phase not in VERIFIED_ACTIVE_MARKET_PHASES:
            overall='market_phase_unresolved' if phase=='market_phase_unresolved' else 'closed_session_latest_completed'; age_state='phase_not_active'
        elif age is not None and age<=FRESH_SECONDS: overall='active_session_fresh_liveish'; age_state='fresh'
        elif age is not None and age<=AGING_SECONDS: overall='active_session_aging_liveish'; age_state='aging'
        else: overall='active_session_stale_liveish'; age_state='stale'
    return {'transport_state':transport_state,'session_alignment':aligned,'market_phase':phase,'source_timestamp_state':ts_state,'quote_age_state':age_state,'calendar_evidence':(calendar_context or {}).get('authority','not_provided'),'currentness_confidence':'bounded_policy_not_exchange_sla','retrieved_at_freshness_ignored_for_upgrade':True,'overall_ai_currentness':overall}

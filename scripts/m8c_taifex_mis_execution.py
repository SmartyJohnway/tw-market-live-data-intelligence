from __future__ import annotations
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
from .m8c_taifex_mis_limits import RuntimeBudget, LimitError
from .m8c_taifex_mis_contracts import validate_selectors, SelectorError
from .m8c_taifex_mis_rest_client import TaifexMisRestClient
from .m8c_taifex_mis_identity_resolver import resolve_identity_results
from .m8c_taifex_mis_sockjs_xhr_client import collect_initial_states
from .m8c_taifex_mis_observation import build_observation

def execute_taifex_mis_snapshot(*, operator_confirmed:bool, requested_contracts:list[dict], evaluation_time_asia_taipei:str|None=None, calendar_context:dict|None=None, max_total_execution_seconds:int=20, max_accounted_payload_bytes:int=2_000_000, max_bootstrap_rows:int=2_000, max_option_chain_rows:int=2_000, max_frames:int=100, max_decoded_messages:int=500, max_retained_observations:int=100, session_factory=None, monotonic_clock=None, wall_clock=None)->dict:
    if not operator_confirmed:
        return {'status':'operator_confirmation_required','network_performed':False,'observations':[],'caveats':['explicit_operator_confirmation_required']}
    try:
        budget=RuntimeBudget(max_total_execution_seconds=max_total_execution_seconds,max_accounted_payload_bytes=max_accounted_payload_bytes,max_bootstrap_rows=max_bootstrap_rows,max_option_chain_rows=max_option_chain_rows,max_frames=max_frames,max_decoded_messages=max_decoded_messages,max_retained_observations=max_retained_observations,monotonic_clock=monotonic_clock)
        selectors=validate_selectors(requested_contracts,budget)
    except (SelectorError,LimitError) as e:
        return {'status':'rejected_invalid_scope','network_performed':False,'observations':[],'caveats':[str(e)]}
    session=(session_factory or requests.Session)(); selector_results=[]; observations=[]; caveats=[]; transport={}
    try:
        successes, failures=resolve_identity_results(selectors, TaifexMisRestClient(session,budget)); selector_results.extend(failures)
        symbols=[v['runtime_symbol_id'] for v in successes]; budget.set_selector_counts(budget.selectors,budget.products,budget.months,budget.strikes,len(symbols))
        if symbols:
            transport=collect_initial_states(session,symbols,budget)
            for r in successes:
                sel=r['selector']; mode1=transport['accepted_initial_states'].get(r['runtime_symbol_id']); obs=build_observation(sel,r,mode1_quote=mode1,detail_row=r.get('detail_row'),list_row=r.get('list_row'),evaluation_time_asia_taipei=evaluation_time_asia_taipei,calendar_context=calendar_context); budget.retain_observation(); observations.append(obs); selector_results.append({'selector':sel.key,'status':'ok' if mode1 else 'snapshot_incomplete','runtime_symbol_id':r['runtime_symbol_id']})
            caveats.extend(transport.get('caveats',[]))
        if failures and observations: status='partial_source_success'
        elif failures and not observations: status='source_error'
        elif observations and len(observations)==len(symbols): status='successful_liveish_snapshot'
        else: status='snapshot_incomplete'
    except Exception as e:
        status='partial_source_success' if observations else ('transport_connection_failure' if 'sockjs' in str(type(e)).lower() else 'source_error')
        caveats.append(str(e))
    finally:
        close=getattr(session,'close',None)
        if close: close()
    return {'status':status,'network_performed':True,'timing':{'evaluation_time_asia_taipei':evaluation_time_asia_taipei or datetime.now(ZoneInfo('Asia/Taipei')).isoformat()},'accounting':{k:getattr(budget,k) for k in ('rest_request_payload_bytes','sockjs_send_payload_bytes','response_payload_bytes','total_accounted_payload_bytes','rest_rows','frames','decoded_messages','selectors','products','months','strikes','symbols','retained_observations')},'transport_summary':{'reconnect_attempts':0,'unsubscribe_sent':False,'unsupported_mode_count':transport.get('unsupported_mode_count',0),'accepted_initial_state_count':len(transport.get('accepted_initial_states',{}))},'selector_results':selector_results,'observations':observations,'caveats':caveats,'raw_payload_retained':False,'ai_context_allowed':False}

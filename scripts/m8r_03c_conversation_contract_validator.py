from __future__ import annotations
from copy import deepcopy
from datetime import date
from typing import Any
from scripts.m8r_03c_contracts import compile_contract_metadata

FORBIDDEN_KEYS={"raw_payload","raw_rest_records","full_option_chain","option_chain","sockjs_frames","cookies","cookie","session_id","session_ids","authorization","access_token","refresh_token"}
SOURCE_FAMILIES={"TWSE_MIS","TAIFEX_MIS","TWSE_OPENAPI","TPEX_OPENAPI","TAIFEX_OPENAPI","BENCHMARK_FIXTURE"}
CURRENT_SOURCES={"TWSE_MIS","TAIFEX_MIS"}; EOD_SOURCES={"TWSE_OPENAPI","TPEX_OPENAPI","TAIFEX_OPENAPI","BENCHMARK_FIXTURE"}
META=compile_contract_metadata(); SCOPE=set(META['scope_modes']); TIME=set(META['time_modes']); DEPTH=set(META['evidence_depth_modes']); CALC=set(META['calculation_statuses']); COVER=set(META['coverage_states'])

class M8R03CValidationError(ValueError):
    def __init__(self, code: str, path: str, detail: str):
        self.code=code; self.path=path; self.detail=detail
        super().__init__(f'{code}:{path}:{detail}')

def _err(c,p,d): raise M8R03CValidationError(c,p,d)
def assert_no_forbidden_keys(v: Any, path='$'):
    if isinstance(v, dict):
        for k,x in v.items():
            if str(k).lower() in FORBIDDEN_KEYS: _err('source_fact_boundary_invalid', f'{path}.{k}', 'forbidden raw/secret key')
            assert_no_forbidden_keys(x, f'{path}.{k}')
    elif isinstance(v, list):
        for i,x in enumerate(v): assert_no_forbidden_keys(x, f'{path}[{i}]')
def _obj(v,p):
    if not isinstance(v, dict): _err('field_type_invalid',p,'expected object')
    return v
def _strict(o,p,allowed):
    extra=set(o)-set(allowed)
    if extra: _err('unknown_field_rejected',p+'.'+sorted(extra)[0],'unknown field')
def _str(v,p,nullable=False):
    if v is None and nullable: return
    if not isinstance(v,str) or not v.strip(): _err('field_type_invalid',p,'expected non-empty string')
def _bool(v,p):
    if not isinstance(v,bool): _err('field_type_invalid',p,'expected boolean')
def _list(v,p):
    if not isinstance(v,list): _err('field_type_invalid',p,'expected list')
    return v
def _time(v,p):
    o=_obj(v,p); _strict(o,p,{'mode','lookback_trading_days','explicit_range'})
    if o.get('mode') not in TIME: _err('enum_value_invalid',p+'.mode','invalid time mode')
    if 'lookback_trading_days' in o and o.get('lookback_trading_days') is not None and (not isinstance(o.get('lookback_trading_days'),int) or o['lookback_trading_days']<=0): _err('explicit_range_invalid',p+'.lookback_trading_days','must be positive')
    ex=o.get('explicit_range')
    if o['mode']=='explicit_range':
        r=_obj(ex,p+'.explicit_range'); _strict(r,p+'.explicit_range',{'range_type','start_date','end_date','trading_days','named_period','user_text'})
        if r.get('range_type') not in {'trading_days','calendar_dates','year_to_date','named_period'}: _err('enum_value_invalid',p+'.explicit_range.range_type','invalid')
        _str(r.get('user_text'),p+'.explicit_range.user_text')
        if r['range_type']=='trading_days' and (not isinstance(r.get('trading_days'),int) or r['trading_days']<=0): _err('explicit_range_invalid',p+'.explicit_range.trading_days','positive required')
        if r['range_type']=='named_period': _str(r.get('named_period'),p+'.explicit_range.named_period')
        if r['range_type']=='calendar_dates':
            try:
                s=date.fromisoformat(r.get('start_date')); e=date.fromisoformat(r.get('end_date')) if r.get('end_date') else s
            except Exception: _err('explicit_range_invalid',p+'.explicit_range','invalid ISO date')
            if s>e: _err('explicit_range_invalid',p+'.explicit_range','start after end')
    elif ex is not None: _err('explicit_range_invalid',p+'.explicit_range','must be null unless explicit_range mode')
    return deepcopy(o)

def validate_conversation_intent(value: dict) -> dict:
    assert_no_forbidden_keys(value); o=deepcopy(_obj(value,'$'))
    allowed={'schema_version','original_user_text','scope_modes','time_scope','evidence_depth','explicit_user_constraints','inferred_defaults','clarification_required','clarification_reason'}
    _strict(o,'$',allowed)
    if o.get('schema_version')!='m8r_ai_market_conversation_intent.v1': _err('schema_version_invalid','$.schema_version','invalid')
    _str(o.get('original_user_text'),'$.original_user_text')
    scopes=_list(o.get('scope_modes'),'$.scope_modes')
    if not scopes: _err('required_field_missing','$.scope_modes','non-empty required')
    if len(set(scopes))!=len(scopes): _err('enum_value_invalid','$.scope_modes','duplicate scope')
    bad=[s for s in scopes if s not in SCOPE]
    if bad: _err('enum_value_invalid','$.scope_modes','unknown scope')
    if 'watchlist_subset' in scopes and not (o.get('inferred_defaults',{}).get('persistent_watchlist_reference') or o.get('inferred_defaults',{}).get('parent_evidence_request_id')): _err('watchlist_reference_required','$.scope_modes','watchlist_subset requires context')
    o['time_scope']=_time(o.get('time_scope'),'$.time_scope')
    if o.get('evidence_depth') not in DEPTH: _err('enum_value_invalid','$.evidence_depth','invalid')
    for f in ('explicit_user_constraints','inferred_defaults'):
        if not isinstance(o.get(f),dict): _err('field_type_invalid','$.'+f,'expected object')
    _bool(o.get('clarification_required'),'$.clarification_required')
    if o['clarification_required']: _str(o.get('clarification_reason'),'$.clarification_reason')
    elif o.get('clarification_reason') is not None: _err('clarification_invariant_failed','$.clarification_reason','must be null')
    return o

def _watchlist_ref(v,p,required=False):
    if v is None:
        if required: _err('watchlist_reference_required',p,'required')
        return None
    o=deepcopy(_obj(v,p)); _strict(o,p,{'watchlist_id','source','enabled_target_ids'})
    _str(o.get('watchlist_id'),p+'.watchlist_id')
    if o.get('source') not in {'operator_supplied','local_fixture','persistent_user_watchlist','follow_up_context'}: _err('enum_value_invalid',p+'.source','invalid')
    ids=_list(o.get('enabled_target_ids'),p+'.enabled_target_ids')
    if not ids: _err('watchlist_reference_required',p+'.enabled_target_ids','non-empty')
    if len(ids)!=len(set(ids)): _err('coverage_target_duplicate',p+'.enabled_target_ids','duplicate')
    for x in ids: _str(x,p+'.enabled_target_ids[]')
    return o

def _evidence_item(v,p,priority,seen):
    o=deepcopy(_obj(v,p)); _strict(o,p,{'capability_id','priority','time_scope','preferred_timing_class','source_family_preference','fallback_behavior','required_for_answer'})
    _str(o.get('capability_id'),p+'.capability_id')
    if o.get('priority')!=priority: _err('evidence_priority_mismatch',p+'.priority','wrong priority')
    if o['capability_id'] in seen and seen[o['capability_id']]!=priority: _err('evidence_priority_mismatch',p+'.capability_id','conflicting priority')
    if o['capability_id'] in seen: _err('evidence_priority_mismatch',p+'.capability_id','duplicate capability')
    seen[o['capability_id']]=priority
    o['time_scope']=_time(o.get('time_scope'),p+'.time_scope'); _str(o.get('preferred_timing_class'),p+'.preferred_timing_class'); _list(o.get('source_family_preference'),p+'.source_family_preference'); _str(o.get('fallback_behavior'),p+'.fallback_behavior'); _bool(o.get('required_for_answer'),p+'.required_for_answer')
    return o

def validate_evidence_request(value: dict) -> dict:
    assert_no_forbidden_keys(value); o=deepcopy(_obj(value,'$'))
    allowed={'schema_version','request_id','original_user_text','conversation_intent','explicit_user_constraints','inferred_defaults','persistent_watchlist_reference','dynamic_entity_requests','market_context_requests','required_evidence','useful_evidence','optional_evidence','execution_policy','clarification_required','clarification_reason','identity_resolver_output','follow_up_context'}
    _strict(o,'$',allowed)
    if o.get('schema_version')!='m8r_ai_evidence_request.v1': _err('schema_version_invalid','$.schema_version','invalid')
    _str(o.get('request_id'),'$.request_id'); _str(o.get('original_user_text'),'$.original_user_text')
    o['conversation_intent']=validate_conversation_intent(o.get('conversation_intent'))
    if o['original_user_text'] != o['conversation_intent']['original_user_text']: _err('bundle_request_mismatch','$.original_user_text','intent mismatch')
    if o.get('clarification_required') != o['conversation_intent']['clarification_required'] or o.get('clarification_reason') != o['conversation_intent']['clarification_reason']: _err('clarification_invariant_failed','$.clarification_required','intent mismatch')
    for f in ('explicit_user_constraints','inferred_defaults','identity_resolver_output'):
        if not isinstance(o.get(f),dict): _err('field_type_invalid','$.'+f,'expected object')
    scopes=set(o['conversation_intent']['scope_modes']); o['persistent_watchlist_reference']=_watchlist_ref(o.get('persistent_watchlist_reference'),'$.persistent_watchlist_reference',bool(scopes & {'watchlist','watchlist_subset'}))
    dyn=[]
    for i,e in enumerate(_list(o.get('dynamic_entity_requests'),'$.dynamic_entity_requests')):
        d=deepcopy(_obj(e,f'$.dynamic_entity_requests[{i}]')); _strict(d,f'$.dynamic_entity_requests[{i}]',{'input_reference','entity_role','selection_reason','priority','requested_time_range','requested_source_timing_class','fallback_behavior','persistent_watchlist_mutation'})
        if d.get('persistent_watchlist_mutation') is not False: _err('dynamic_watchlist_mutation_forbidden',f'$.dynamic_entity_requests[{i}].persistent_watchlist_mutation','must be false')
        d['requested_time_range']=_time(d.get('requested_time_range'),f'$.dynamic_entity_requests[{i}].requested_time_range'); dyn.append(d)
    o['dynamic_entity_requests']=dyn; _list(o.get('market_context_requests'),'$.market_context_requests')
    seen={}
    for field,prio in [('required_evidence','required'),('useful_evidence','useful'),('optional_evidence','optional')]:
        o[field]=[_evidence_item(x,f'$.{field}[{i}]',prio,seen) for i,x in enumerate(_list(o.get(field),f'$.{field}'))]
    pol=deepcopy(_obj(o.get('execution_policy'),'$.execution_policy')); _strict(pol,'$.execution_policy',{'operator_confirmation_required','network_allowed','polling','scheduler'})
    for flag in pol: _bool(pol[flag],'$.execution_policy.'+flag)
    if pol.get('network_allowed') or pol.get('polling') or pol.get('scheduler'): _err('execution_policy_invalid','$.execution_policy','network/polling/scheduler disabled')
    o['execution_policy']=pol
    if o.get('follow_up_context') is not None:
        _strict(_obj(o['follow_up_context'],'$.follow_up_context'),'$.follow_up_context',{'conversation_context_id','parent_evidence_request_id','reusable_resolutions','freshness_recheck_required'})
    return o

def validate_watchlist_snapshot_request(value: dict) -> dict:
    o=validate_evidence_request(value); scopes=set(o['conversation_intent']['scope_modes'])
    if not (scopes & {'watchlist','watchlist_subset'}): _err('watchlist_reference_required','$.conversation_intent.scope_modes','watchlist scope required')
    return o

def validate_watchlist_performance_request(value: dict) -> dict:
    o=validate_watchlist_snapshot_request(value); mode=o['conversation_intent']['time_scope']['mode']
    if mode not in {'recent','historical','explicit_range','current_plus_recent'}: _err('explicit_range_invalid','$.conversation_intent.time_scope.mode','performance needs recent/historical range')
    return o

def _coverage(c,p):
    c=_obj(c,p); _strict(c,p,{'target_id','coverage_state','present_field_groups','missing_field_groups','reason_code'})
    _str(c.get('target_id'),p+'.target_id')
    if c.get('coverage_state') not in COVER: _err('enum_value_invalid',p+'.coverage_state','invalid')
    _list(c.get('present_field_groups'),p+'.present_field_groups'); _list(c.get('missing_field_groups'),p+'.missing_field_groups')
    if c['coverage_state']=='unavailable' and not c.get('reason_code'): _err('coverage_reason_required',p+'.reason_code','required')
    if c['coverage_state']=='partial' and not c.get('missing_field_groups'): _err('coverage_missing_fields_required',p+'.missing_field_groups','required')
    if c['coverage_state']=='usable' and not c.get('present_field_groups'): _err('coverage_minimum_fields_missing',p+'.present_field_groups','required')

def _metric(m,p):
    m=_obj(m,p); _strict(m,p,{'metric_id','value','unit','formula_id','input_period','source_dependencies','calculation_status','as_of'})
    for f in ('metric_id','unit','formula_id','as_of'): _str(m.get(f),p+'.'+f)
    _time(m.get('input_period'),p+'.input_period'); _list(m.get('source_dependencies'),p+'.source_dependencies')
    if m.get('calculation_status') not in CALC: _err('enum_value_invalid',p+'.calculation_status','invalid')

def _validate_bundle(value, schema):
    assert_no_forbidden_keys(value); o=deepcopy(_obj(value,'$'))
    allowed={'schema_version','bundle_id','request_id','generated_at_utc','conversation_context','targets','facts','derived_metrics','resolution_assumptions','missing_evidence','coverage','source_summary','issues'}
    _strict(o,'$',allowed)
    if o.get('schema_version')!=schema: _err('schema_version_invalid','$.schema_version','invalid')
    for f in ('bundle_id','request_id','generated_at_utc'): _str(o.get(f),'$.'+f)
    if not isinstance(o.get('conversation_context'),dict): _err('field_type_invalid','$.conversation_context','object')
    _list(o.get('targets'),'$.targets'); _list(o.get('facts'),'$.facts'); _list(o.get('derived_metrics'),'$.derived_metrics'); _list(o.get('missing_evidence'),'$.missing_evidence'); _list(o.get('resolution_assumptions'),'$.resolution_assumptions'); _list(o.get('issues'),'$.issues')
    ids=[]
    cov=_obj(o.get('coverage'),'$.coverage'); _strict(cov,'$.coverage',{'requested_target_ids','targets'})
    requested=_list(cov.get('requested_target_ids'),'$.coverage.requested_target_ids')
    for i,c in enumerate(_list(cov.get('targets'),'$.coverage.targets')): _coverage(c,f'$.coverage.targets[{i}]'); ids.append(c['target_id'])
    if ids != requested or len(ids)!=len(set(ids)): _err('coverage_target_missing','$.coverage.targets','must exactly match requested order')
    for i,m in enumerate(o['derived_metrics']): _metric(m,f'$.derived_metrics[{i}]')
    for i,miss in enumerate(o['missing_evidence']):
        mo=_obj(miss,f'$.missing_evidence[{i}]'); _strict(mo,f'$.missing_evidence[{i}]',{'target_id','capability_id','reason_code','required_for_answer','impact','fallback_used','recommended_follow_up'}); _str(mo.get('capability_id'),f'$.missing_evidence[{i}].capability_id'); _str(mo.get('reason_code'),f'$.missing_evidence[{i}].reason_code'); _bool(mo.get('required_for_answer'),f'$.missing_evidence[{i}].required_for_answer')
    if not isinstance(o.get('source_summary'),dict): _err('field_type_invalid','$.source_summary','object')
    return o

def validate_watchlist_snapshot_bundle(value: dict) -> dict: return _validate_bundle(value,'m8r_watchlist_snapshot_bundle.v1')
def validate_watchlist_performance_bundle(value: dict) -> dict: return _validate_bundle(value,'m8r_watchlist_performance_bundle.v1')

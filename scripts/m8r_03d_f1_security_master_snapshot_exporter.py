from __future__ import annotations
import copy, hashlib, json
from datetime import datetime, timezone, date
from pathlib import Path
from typing import Any

SNAPSHOT_SCHEMA_VERSION='tw_verified_security_master_snapshot.v1'
MANIFEST_SCHEMA_VERSION='tw_verified_security_master_snapshot_manifest.v1'
PRODUCER_VERSION='m8r_03d_f1_snapshot_exporter.v1'
SKILL_PATH='skills/tw-security-master-classifier'
FORBIDDEN_RAW_FIELDS={'raw_html','raw_payload','raw_cells','html','cookies','session_id','access_token','refresh_token'}
MARKET_MAP={'twse':'TWSE','tpex':'TPEX','listed':'TWSE','tpex_otc':'TPEX'}
CONFIRMED={'confirmed_dual_lane','confirmed_official_single_lane'}
QUARANTINE={'quarantine_conflict','quarantine_unknown'}
EXEC_TYPES={'common_share','etf'}
CURRENT_OBS={'observed_in_latest_verified_snapshot'}
CAPTURE_OBS={'observed_in_capture'}
HIST_OBS={'historical_capture'}
FIXTURE_OBS={'fixture_observation_only'}

def canonical_json(v:Any)->str:
    return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def sha256_json(v:Any)->str: return hashlib.sha256(canonical_json(v).encode()).hexdigest()
def _parse_dt(s:str):
    return datetime.fromisoformat(s.replace('Z','+00:00'))
def _valid_date(s):
    if s in (None,'unknown','not_applicable'): return True
    try: date.fromisoformat(s); return True
    except Exception: return False

def compute_skill_contract_hash(skill_root: str|Path=SKILL_PATH)->str:
    root=Path(skill_root); files=[root/'SKILL.md',*(root/'references').glob('*.md'),root/'references/source-manifest.json']
    h=hashlib.sha256()
    for p in sorted(files, key=lambda x: str(x)):
        h.update(str(p.relative_to(root)).encode()); h.update(b'\0'); h.update(p.read_bytes()); h.update(b'\0')
    return h.hexdigest()

def _market(m): return MARKET_MAP.get((m or '').lower(), m.upper() if isinstance(m,str) and m.isupper() else m)
def _target_id(rec):
    ident=rec.get('identity') or {}; cls=rec.get('classification') or {}
    return rec.get('canonical_target_id') or f"{_market(cls.get('market'))}:{ident.get('security_code')}"
def _event_id(ev): return ev.get('event_id') or ev.get('event_key') or sha256_json({k:v for k,v in ev.items() if k!='record_hash'})[:16]
def _events_for(code, events): return [copy.deepcopy(e)|{'event_id':_event_id(e)} for e in events if str(e.get('security_code') or '')==str(code or '')]

def derive_lifecycle_view(record:dict, events:list[dict], *, as_of:str)->dict:
    obs=(record.get('observation') or {}).get('status'); basis=[]; state='unknown'; status='unavailable'; caveat=[]
    dated=[]
    for e in events:
        eff=e.get('termination_effective_date') or e.get('effective_date') or e.get('maturity_date')
        if isinstance(eff,str) and _valid_date(eff) and eff not in {'unknown','not_applicable'} and eff<=as_of: dated.append(e)
    types=[e.get('event_type') for e in dated]
    if any(t in {'twse_delisted','tpex_delisted','emerging_terminated','gisa_terminated','early_terminated'} for t in types): state='terminated'; status='resolved'
    elif 'matured' in types or any(e.get('maturity_date') not in (None,'unknown','not_applicable') and e.get('maturity_date')<=as_of for e in dated): state='matured'; status='resolved'
    elif any(t in {'twse_suspended','tpex_suspended','emerging_suspended'} for t in types): state='suspended'; status='partial'
    elif obs=='observed_in_latest_verified_snapshot': state='active_with_current_observation_basis'; status='partial'; caveat.append('active_state_based_on_current_verified_observation_not_lifecycle_event')
    elif obs=='observed_in_capture': state='unknown'; status='partial'; caveat.append('capture_observation_freshness_not_independently_established')
    elif obs=='fixture_observation_only': state='unknown'; status='unavailable'; caveat.append('fixture_observation_only_not_runtime_truth')
    elif obs=='historical_capture': state='unknown'; status='unavailable'; caveat.append('historical_capture_not_current')
    basis=[_event_id(e) for e in dated]
    return {'state':state,'resolution_status':status,'as_of':as_of,'basis_event_ids':basis,'events':events,'caveats':caveat}

def _eligibility(record, lifecycle):
    cls=record.get('classification') or {}; obs=record.get('observation') or {}; reasons=[]
    st=cls.get('classification_status'); typ=cls.get('instrument_type')
    status='allowed'
    if st in QUARANTINE or cls.get('conflicts') or record.get('conflicts'): status='blocked'; reasons.append('classification_quarantine_or_conflict')
    elif st=='provisional_single_lane': status='allowed_with_caveat'; reasons.append('provisional_single_lane')
    elif st not in CONFIRMED: status='blocked'; reasons.append('classification_not_confirmed')
    if typ not in EXEC_TYPES: status='blocked'; reasons.append('unsupported_instrument_type')
    if obs.get('status') in FIXTURE_OBS: status='blocked'; reasons.append('fixture_observation_only')
    if obs.get('status') in CAPTURE_OBS and status=='allowed': status='allowed_with_caveat'; reasons.append('capture_observation_freshness_caveat')
    if obs.get('status') in HIST_OBS: status='blocked'; reasons.append('historical_capture_not_current')
    if lifecycle['state'] in {'terminated','matured','suspended','conflicted','inactive'}: status='blocked'; reasons.append('lifecycle_blocks_current_execution')
    elif lifecycle['state']=='unknown' and status=='allowed': status='allowed_with_caveat'; reasons.append('lifecycle_unknown')
    return {'status':status,'reason_codes':sorted(set(reasons))}

def _bounded_record(rec, lifecycle_events, as_of):
    ident=copy.deepcopy(rec.get('identity') or {}); cls=copy.deepcopy(rec.get('classification') or {}); obs=copy.deepcopy(rec.get('observation') or {})
    cls['market']=_market(cls.get('market')); code=ident.get('security_code'); events=_events_for(code,lifecycle_events)+(copy.deepcopy(rec.get('lifecycle_events') or []))
    lifecycle=derive_lifecycle_view({'observation':obs},events,as_of=as_of)
    caveats=list(rec.get('caveats') or [])+lifecycle.pop('caveats',[])
    out={'record_id':rec.get('record_id') or 'security-'+sha256_json({'id':ident,'cls':cls})[:16],'canonical_target_id':_target_id({'identity':ident,'classification':cls}),
         'identity':{k:ident.get(k) for k in ['security_code','security_name_zh','security_name_en','isin','cfi']},
         'classification':{k:cls.get(k) for k in ['asset_class','instrument_family','instrument_type','equity_subtype','market','board','listed_common_stock_core_flag','classification_status','reason_codes','conflicts']},
         'observation':{k:obs.get(k) for k in ['status','observed_at','source_updated_date']},'lifecycle':lifecycle,'execution_eligibility':{},
         'evidence_summary':{'evidence_count':len(rec.get('evidence') or []),'official_source_families':sorted({e.get('source_family') for e in rec.get('evidence',[]) if isinstance(e,dict) and e.get('source_family')}),'source_lanes':sorted({e.get('source_lane') for e in rec.get('evidence',[]) if isinstance(e,dict) and e.get('source_lane')}),'evidence_status':'bounded_summary_only'},
         'conflicts':copy.deepcopy(rec.get('conflicts') or []),'caveats':caveats}
    out['execution_eligibility']=_eligibility(out,out['lifecycle'])
    out['record_hash']=sha256_json({k:v for k,v in out.items() if k!='record_hash'})
    return out

def export_verified_security_master_snapshot(*, classification_records:list[dict], lifecycle_events:list[dict], source_context:dict, generated_at_utc:str, effective_observation_date:str|None=None)->tuple[dict,dict]:
    _parse_dt(generated_at_utc); as_of=effective_observation_date or generated_at_utc[:10]
    if not _valid_date(as_of) or as_of in {'unknown','not_applicable'}: raise ValueError('invalid_effective_observation_date')
    skill_hash=source_context.get('skill_contract_hash') or compute_skill_contract_hash()
    records=[_bounded_record(r,lifecycle_events,as_of) for r in classification_records]
    coverage={'markets':sorted({r['classification'].get('market') for r in records if r['classification'].get('market')}),'instrument_types':sorted({r['classification'].get('instrument_type') for r in records if r['classification'].get('instrument_type')}),'record_count':len(records),'lifecycle_event_count':len(lifecycle_events),'coverage_status':source_context.get('coverage_status','partial_manual_snapshot')}
    snapshot={'schema_version':SNAPSHOT_SCHEMA_VERSION,'snapshot_id':source_context.get('snapshot_id') or 'tw-vsm-'+sha256_json({'generated_at_utc':generated_at_utc,'records':records,'events':lifecycle_events})[:16],'generated_at_utc':generated_at_utc,'effective_observation_date':as_of,'source_skill':{'name':'tw-security-master-classifier','skill_version':source_context.get('skill_version') or 'source-manifest-1.1.0','skill_path':SKILL_PATH,'skill_contract_hash':skill_hash},'coverage':coverage,'records':records}
    manifest={'schema_version':MANIFEST_SCHEMA_VERSION,'snapshot_id':snapshot['snapshot_id'],'snapshot_path':source_context.get('snapshot_path','tw_verified_security_master_snapshot.json'),'generated_at_utc':generated_at_utc,'effective_observation_date':as_of,'record_count':len(records),'lifecycle_event_count':len(lifecycle_events),'snapshot_sha256':sha256_json(snapshot),'schema_sha256':hashlib.sha256((SNAPSHOT_SCHEMA_VERSION+'|'+MANIFEST_SCHEMA_VERSION).encode()).hexdigest(),'skill_contract_hash':skill_hash,'producer_version':PRODUCER_VERSION,'validation_status':'passed','validation_issues':[],'coverage':coverage}
    return snapshot, manifest

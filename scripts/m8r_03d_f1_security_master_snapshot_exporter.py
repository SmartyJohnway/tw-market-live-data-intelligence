from __future__ import annotations
import copy, hashlib, json
from datetime import datetime, timezone, date
from pathlib import Path
from typing import Any
import jsonschema

SNAPSHOT_SCHEMA_VERSION='tw_verified_security_master_snapshot.v1'
MANIFEST_SCHEMA_VERSION='tw_verified_security_master_snapshot_manifest.v1'
PRODUCER_VERSION='m8r_03d_f1_snapshot_exporter.v1'
SUPPORTED_PRODUCER_VERSIONS={PRODUCER_VERSION}
SKILL_PATH='skills/tw-security-master-classifier'
SKILL_SCHEMA_DIR=Path(SKILL_PATH)/'references'/'schemas'
F1_SCHEMA_DIR=Path('docs/contracts/schemas')
SNAPSHOT_SCHEMA_PATH=F1_SCHEMA_DIR/'tw_verified_security_master_snapshot.v1.schema.json'
MANIFEST_SCHEMA_PATH=F1_SCHEMA_DIR/'tw_verified_security_master_snapshot_manifest.v1.schema.json'
FORBIDDEN_RAW_FIELDS={'raw_html','raw_payload','raw_cells','html','cookies','session_id','access_token','refresh_token'}
MARKET_MAP={'twse':'TWSE','tpex':'TPEX','listed':'TWSE','tpex_otc':'TPEX'}
CONFIRMED={'confirmed_dual_lane','confirmed_official_single_lane'}
QUARANTINE={'quarantine_conflict','quarantine_unknown'}
EXEC_TYPES={'common_share','etf'}
OBS_STATUSES={'observed_in_capture','observed_in_latest_verified_snapshot','fixture_observation_only','historical_capture'}
DATE_FIELDS={'effective_date','announcement_date','issue_date','listing_date','registration_date','last_trading_date','maturity_date','termination_effective_date','contract_termination_date','source_updated_date'}

def canonical_json(v:Any)->str:
    return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def sha256_json(v:Any)->str: return hashlib.sha256(canonical_json(v).encode()).hexdigest()
def _load_json(path:Path)->dict: return json.loads(path.read_text(encoding='utf-8'))
def compute_schema_hash()->str: return sha256_json({'snapshot_schema':_load_json(SNAPSHOT_SCHEMA_PATH),'manifest_schema':_load_json(MANIFEST_SCHEMA_PATH)})
def parse_utc_timestamp(s:str)->datetime:
    if not isinstance(s,str): raise ValueError('invalid_utc_timestamp')
    d=datetime.fromisoformat(s[:-1]+'+00:00' if s.endswith('Z') else s)
    if d.tzinfo is None or d.utcoffset()!=timezone.utc.utcoffset(d): raise ValueError('invalid_utc_timestamp')
    return d.astimezone(timezone.utc)
def validate_iso_date(s, *, allow_unknown=False):
    if allow_unknown and s in ('unknown','not_applicable',None): return True
    if s is None: return True
    date.fromisoformat(s); return True

def compute_skill_contract_hash(skill_root: str|Path=SKILL_PATH)->str:
    root=Path(skill_root)
    files=[root/'SKILL.md',*(root/'references').glob('*.md'),root/'references/source-manifest.json',*(root/'references'/'schemas').glob('*.json')]
    h=hashlib.sha256()
    for p in sorted(files, key=lambda x: str(x)):
        h.update(str(p.relative_to(root)).encode()); h.update(b'\0'); h.update(p.read_bytes()); h.update(b'\0')
    return h.hexdigest()

def _load_skill_schema(name:str)->dict:
    return json.loads((SKILL_SCHEMA_DIR/name).read_text(encoding='utf-8'))

def validate_skill_classification_record(record:dict)->None:
    jsonschema.Draft202012Validator(_load_skill_schema('classification-result.schema.json')).validate(record)
    ident=record.get('identity') or {}; cls=record.get('classification') or {}; obs=record.get('observation') or {}
    if not ident.get('security_code') and not ident.get('isin'): raise ValueError('missing_identity')
    if cls.get('classification_status') not in QUARANTINE and (not ident.get('security_code') or _market(cls.get('market')) not in {'TWSE','TPEX'}): raise ValueError('missing_runtime_identity')
    if cls.get('market') not in {'twse','tpex','emerging','gisa','public_unlisted','derivatives','fund_registry','gold_spot','index_registry','sto_registry','listed','tpex_otc'}: raise ValueError('invalid_market')
    if obs.get('status') not in OBS_STATUSES: raise ValueError('invalid_observation_status')
    parse_utc_timestamp(obs['observed_at']) if obs.get('observed_at') else None
    validate_iso_date(obs.get('source_updated_date'))

def validate_skill_lifecycle_event(event:dict)->None:
    jsonschema.Draft202012Validator(_load_skill_schema('lifecycle-event.schema.json')).validate(event)
    for k,v in event.items():
        if k in DATE_FIELDS: validate_iso_date(v, allow_unknown=True)
    if not (event.get('isin') or event.get('canonical_target_id') or (event.get('market') and event.get('security_code')) or event.get('security_code')):
        raise ValueError('invalid_lifecycle_identity')

def _market(m): return MARKET_MAP.get((m or '').lower(), m.upper() if isinstance(m,str) and m.isupper() else m)
def _target_id(rec):
    ident=rec.get('identity') or {}; cls=rec.get('classification') or {}; market=_market(cls.get('market')); code=ident.get('security_code')
    if rec.get('canonical_target_id'): return rec.get('canonical_target_id')
    if market not in {'TWSE','TPEX'} or not code: raise ValueError('invalid_canonical_target_identity')
    return f"{market}:{code}"
def _event_id(ev): return ev.get('event_id') or ev.get('event_key') or sha256_json({k:v for k,v in ev.items() if k!='record_hash'})[:16]

def _assign_lifecycle_events(records:list[dict], events:list[dict])->tuple[dict[str,list[dict]],list[dict]]:
    by_isin={}; by_cid={}; by_market_code={}; by_code={}
    for r in records:
        ident=r.get('identity') or {}; cls=r.get('classification') or {}; cid=_target_id(r)
        rr={'cid':cid,'record':r}; by_cid[cid]=rr
        if ident.get('isin'): by_isin.setdefault(ident['isin'],[]).append(rr)
        if ident.get('security_code'):
            by_code.setdefault(ident['security_code'],[]).append(rr); by_market_code.setdefault((_market(cls.get('market')),ident['security_code']),[]).append(rr)
    assigned={_target_id(r):[] for r in records}; quarantine=[]
    def ids_for(e):
        key_matches=[]
        if e.get('isin'): key_matches.append(('isin', by_isin.get(e['isin'],[])))
        if e.get('canonical_target_id'): key_matches.append(('canonical_target_id', [by_cid[e['canonical_target_id']]] if e.get('canonical_target_id') in by_cid else []))
        if e.get('market') and e.get('security_code'): key_matches.append(('market_security_code', by_market_code.get((_market(e.get('market')),str(e.get('security_code'))),[])))
        elif e.get('security_code'):
            all_matches=by_code.get(str(e.get('security_code')),[])
            key_matches.append(('security_code', all_matches if len(all_matches)==1 else []))
            if len(all_matches)>1: return [], 'lifecycle_identity_ambiguous'
        if not key_matches: return [], 'lifecycle_identity_unresolved'
        cid_sets=[{m['cid'] for m in matches} for _k,matches in key_matches]
        if any(not x for x in cid_sets): return [], 'lifecycle_identity_unresolved'
        first=cid_sets[0]
        if any(x!=first for x in cid_sets[1:]): return [], 'lifecycle_identity_conflict'
        if len(first)!=1: return [], 'lifecycle_identity_ambiguous'
        return [by_cid[next(iter(first))]], None
    for ev in events:
        e=copy.deepcopy(ev)|{'event_id':_event_id(ev)}; matches, problem=ids_for(e)
        if problem:
            e['quarantine_reason']=problem; quarantine.append(e); continue
        assigned[matches[0]['cid']].append(e)
    return assigned, quarantine

def derive_lifecycle_view(record:dict, events:list[dict], *, as_of:str)->dict:
    obs=(record.get('observation') or {}).get('status'); state='unknown'; status='unavailable'; caveat=[]; dated=[]
    for e in events:
        eff=e.get('termination_effective_date') or e.get('effective_date') or e.get('maturity_date')
        if isinstance(eff,str) and eff not in {'unknown','not_applicable'} and validate_iso_date(eff) and eff<=as_of: dated.append(e)
    types=[e.get('event_type') for e in dated]
    if any(t in {'twse_delisted','tpex_delisted','emerging_terminated','gisa_terminated','early_terminated'} for t in types): state='terminated'; status='resolved'
    elif 'matured' in types or any(e.get('maturity_date') not in (None,'unknown','not_applicable') and e.get('maturity_date')<=as_of for e in dated): state='matured'; status='resolved'
    elif any(t in {'twse_suspended','tpex_suspended','emerging_suspended'} for t in types): state='suspended'; status='partial'
    elif obs=='observed_in_latest_verified_snapshot': state='active_with_current_observation_basis'; status='partial'; caveat.append('active_state_based_on_current_verified_observation_not_lifecycle_event')
    elif obs=='observed_in_capture': state='unknown'; status='partial'; caveat.append('capture_observation_freshness_not_independently_established')
    elif obs=='fixture_observation_only': caveat.append('fixture_observation_only_not_runtime_truth')
    elif obs=='historical_capture': caveat.append('historical_capture_not_current')
    return {'state':state,'resolution_status':status,'as_of':as_of,'basis_event_ids':[_event_id(e) for e in dated],'events':events,'caveats':caveat}

def _eligibility(record, lifecycle):
    cls=record.get('classification') or {}; obs=record.get('observation') or {}; reasons=[]; st=cls.get('classification_status'); typ=cls.get('instrument_type'); status='allowed'
    if st in QUARANTINE or cls.get('conflicts') or record.get('conflicts'): status='blocked'; reasons.append('classification_quarantine_or_conflict')
    elif st=='provisional_single_lane': status='allowed_with_caveat'; reasons.append('provisional_single_lane')
    elif st not in CONFIRMED: status='blocked'; reasons.append('classification_not_confirmed')
    if typ not in EXEC_TYPES: status='blocked'; reasons.append('unsupported_instrument_type')
    if obs.get('status')=='fixture_observation_only': status='blocked'; reasons.append('fixture_observation_only')
    if obs.get('status')=='observed_in_capture' and status=='allowed': status='allowed_with_caveat'; reasons.append('capture_observation_freshness_caveat')
    if obs.get('status')=='historical_capture': status='blocked'; reasons.append('historical_capture_not_current')
    if lifecycle['state'] in {'terminated','matured','suspended','conflicted','inactive'}: status='blocked'; reasons.append('lifecycle_blocks_current_execution')
    elif lifecycle['state']=='unknown' and status=='allowed': status='allowed_with_caveat'; reasons.append('lifecycle_unknown')
    return {'status':status,'reason_codes':sorted(set(reasons))}

def _bounded_record(rec, assigned_events, as_of):
    ident=copy.deepcopy(rec.get('identity') or {}); cls=copy.deepcopy(rec.get('classification') or {}); obs=copy.deepcopy(rec.get('observation') or {})
    cls['market']=_market(cls.get('market')); cid=_target_id({'identity':ident,'classification':cls}); events=assigned_events.get(cid,[])+copy.deepcopy(rec.get('lifecycle_events') or [])
    lifecycle=derive_lifecycle_view({'observation':obs},events,as_of=as_of); caveats=list(rec.get('caveats') or [])+lifecycle.pop('caveats',[])
    out={'record_id':rec.get('record_id') or 'security-'+sha256_json({'id':ident,'cls':cls})[:16],'canonical_target_id':cid,
         'identity':{k:ident.get(k) for k in ['security_code','security_name_zh','security_name_en','isin','cfi']},
         'classification':{k:cls.get(k) for k in ['asset_class','instrument_family','instrument_type','equity_subtype','market','board','listed_common_stock_core_flag','classification_status','reason_codes','conflicts']},
         'observation':{k:obs.get(k) for k in ['status','observed_at','source_updated_date']},'lifecycle':lifecycle,'execution_eligibility':{},
         'evidence_summary':{'evidence_count':len(rec.get('evidence') or []),'official_source_families':sorted({e.get('source_family') for e in rec.get('evidence',[]) if isinstance(e,dict) and e.get('source_family')}),'source_lanes':sorted({e.get('source_lane') for e in rec.get('evidence',[]) if isinstance(e,dict) and e.get('source_lane')}),'evidence_status':'bounded_summary_only'},
         'conflicts':copy.deepcopy(rec.get('conflicts') or []),'caveats':caveats}
    out['execution_eligibility']=_eligibility(out,out['lifecycle']); out['record_hash']=sha256_json({k:v for k,v in out.items() if k!='record_hash'}); return out

def export_verified_security_master_snapshot(*, classification_records:list[dict], lifecycle_events:list[dict], source_context:dict, generated_at_utc:str, effective_observation_date:str|None=None)->tuple[dict,dict]:
    parse_utc_timestamp(generated_at_utc); as_of=effective_observation_date or generated_at_utc[:10]; validate_iso_date(as_of)
    for r in classification_records: validate_skill_classification_record(r)
    for e in lifecycle_events: validate_skill_lifecycle_event(e)
    skill_hash=source_context.get('skill_contract_hash') or compute_skill_contract_hash(); assigned, quarantined=_assign_lifecycle_events(classification_records,lifecycle_events)
    records=[_bounded_record(r,assigned,as_of) for r in classification_records]
    retained_event_count=sum(len(r['lifecycle']['events']) for r in records)
    coverage={'markets':sorted({r['classification'].get('market') for r in records if r['classification'].get('market')}),'instrument_types':sorted({r['classification'].get('instrument_type') for r in records if r['classification'].get('instrument_type')}),'record_count':len(records),'lifecycle_event_count':retained_event_count,'coverage_status':source_context.get('coverage_status','partial_manual_snapshot'),'quarantined_lifecycle_event_count':len(quarantined)}
    snapshot={'schema_version':SNAPSHOT_SCHEMA_VERSION,'snapshot_id':source_context.get('snapshot_id') or 'tw-vsm-'+sha256_json({'generated_at_utc':generated_at_utc,'records':records,'events':lifecycle_events})[:16],'generated_at_utc':generated_at_utc,'effective_observation_date':as_of,'source_skill':{'name':'tw-security-master-classifier','skill_version':source_context.get('skill_version') or 'source-manifest-1.1.0','skill_path':SKILL_PATH,'skill_contract_hash':skill_hash},'coverage':coverage,'quarantined_lifecycle_events':quarantined,'records':records}
    manifest={'schema_version':MANIFEST_SCHEMA_VERSION,'snapshot_id':snapshot['snapshot_id'],'snapshot_path':source_context.get('snapshot_path','tw_verified_security_master_snapshot.json'),'generated_at_utc':generated_at_utc,'effective_observation_date':as_of,'record_count':len(records),'lifecycle_event_count':retained_event_count,'snapshot_sha256':sha256_json(snapshot),'schema_sha256':compute_schema_hash(),'skill_contract_hash':skill_hash,'producer_version':PRODUCER_VERSION,'validation_status':'passed','validation_issues':[],'coverage':coverage}
    return snapshot, manifest

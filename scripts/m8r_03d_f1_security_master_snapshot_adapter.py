from __future__ import annotations
from dataclasses import dataclass
import json, re
import jsonschema
from datetime import datetime, timezone, date
from pathlib import Path
from scripts.m8r_03d_f1_security_master_snapshot_exporter import SNAPSHOT_SCHEMA_VERSION, MANIFEST_SCHEMA_VERSION, SUPPORTED_PRODUCER_VERSIONS, sha256_json, FORBIDDEN_RAW_FIELDS, CONFIRMED, QUARANTINE, compute_schema_hash, compute_skill_contract_hash, parse_utc_timestamp, validate_iso_date, SNAPSHOT_SCHEMA_PATH, MANIFEST_SCHEMA_PATH

RESOLUTION_SCHEMA_VERSION='m8r_03d_f1_security_identity_resolution.v1'
class VerifiedSecurityMasterSnapshotError(ValueError): pass

@dataclass(frozen=True)
class ValidatedVerifiedSecurityMasterSnapshot:
    snapshot: dict
    manifest: dict
    lookup: dict
    validation: dict

def _walk_forbidden(v,path=''):
    if isinstance(v,dict):
        for k,x in v.items():
            if k in FORBIDDEN_RAW_FIELDS or k.lower() in FORBIDDEN_RAW_FIELDS: raise VerifiedSecurityMasterSnapshotError(f'forbidden_raw_field:{path}/{k}')
            _walk_forbidden(x,f'{path}/{k}')
    elif isinstance(v,list):
        for i,x in enumerate(v): _walk_forbidden(x,f'{path}/{i}')

def _lifecycle_event_count(snapshot): return sum(len((r.get('lifecycle') or {}).get('events') or []) for r in snapshot.get('records') or [])
def _timestamps_valid(snapshot):
    parse_utc_timestamp(snapshot.get('generated_at_utc')); validate_iso_date(snapshot.get('effective_observation_date'))
    for r in snapshot.get('records') or []:
        obs=r.get('observation') or {}; parse_utc_timestamp(obs['observed_at']) if obs.get('observed_at') else None; validate_iso_date(obs.get('source_updated_date'))
        life=r.get('lifecycle') or {}; validate_iso_date(life.get('as_of'))
        for e in life.get('events') or []:
            for k in ('effective_date','announcement_date','maturity_date','last_trading_date','termination_effective_date','contract_termination_date'):
                if k in e: validate_iso_date(e.get(k), allow_unknown=True)

def _load_schema(path): return json.loads(Path(path).read_text(encoding='utf-8'))

def _conflict_categories(record):
    cats=set()
    for c in (record.get('conflicts') or []) + ((record.get('classification') or {}).get('conflicts') or []):
        if isinstance(c,str): cats.add(c)
        elif isinstance(c,dict):
            for key in ('category','reason_code','code','severity','field'):
                if c.get(key): cats.add(str(c.get(key)))
    return cats

def _validate_canonical_identity(record):
    cid=record.get('canonical_target_id') or ''
    if ':' not in cid: raise ValueError('canonical_identity_mismatch')
    market, code=cid.split(':',1)
    cls_market=(record.get('classification') or {}).get('market')
    ident_code=(record.get('identity') or {}).get('security_code')
    if market not in {'TWSE','TPEX'} or cls_market not in {'TWSE','TPEX'} or not ident_code or market!=cls_market or code!=ident_code:
        raise ValueError('canonical_identity_mismatch')

def validate_verified_security_master_snapshot(snapshot:dict, manifest:dict, *, allow_fixture_snapshot:bool=False, require_current_skill_contract:bool=True)->dict:
    issues=[]
    def issue(c): issues.append({'code':c})
    try: jsonschema.Draft202012Validator(_load_schema(SNAPSHOT_SCHEMA_PATH)).validate(snapshot)
    except Exception as e: issue('snapshot_schema_invalid')
    try: jsonschema.Draft202012Validator(_load_schema(MANIFEST_SCHEMA_PATH)).validate(manifest)
    except Exception as e: issue('manifest_schema_invalid')
    if manifest.get('schema_version')!=MANIFEST_SCHEMA_VERSION: issue('unsupported_manifest_schema')
    if snapshot.get('schema_version')!=SNAPSHOT_SCHEMA_VERSION: issue('unsupported_snapshot_schema')
    if manifest.get('validation_status')!='passed': issue('manifest_validation_not_passed')
    if manifest.get('producer_version') not in SUPPORTED_PRODUCER_VERSIONS: issue('unsupported_producer_version')
    if manifest.get('schema_sha256')!=compute_schema_hash(): issue('schema_hash_mismatch')
    if manifest.get('snapshot_id')!=snapshot.get('snapshot_id'): issue('snapshot_id_mismatch')
    if manifest.get('generated_at_utc')!=snapshot.get('generated_at_utc'): issue('generated_at_mismatch')
    if manifest.get('effective_observation_date')!=snapshot.get('effective_observation_date'): issue('effective_observation_date_mismatch')
    if manifest.get('record_count')!=len(snapshot.get('records') or []): issue('record_count_mismatch')
    attached_count=_lifecycle_event_count(snapshot)
    quarantined_events=snapshot.get('quarantined_lifecycle_events') or []
    quarantined_count=len(quarantined_events)
    coverage=snapshot.get('coverage') or {}
    if manifest.get('lifecycle_event_count')!=attached_count: issue('lifecycle_event_count_mismatch')
    if coverage.get('lifecycle_event_count')!=attached_count: issue('lifecycle_event_count_mismatch')
    if coverage.get('quarantined_lifecycle_event_count')!=quarantined_count: issue('quarantined_lifecycle_event_count_mismatch')
    if coverage.get('total_lifecycle_event_count') is not None and coverage.get('total_lifecycle_event_count')!=attached_count+quarantined_count: issue('total_lifecycle_event_count_mismatch')
    attached_ids={e.get('event_id') or e.get('event_key') for r in snapshot.get('records') or [] for e in ((r.get('lifecycle') or {}).get('events') or [])}
    quarantined_ids={e.get('event_id') or e.get('event_key') for e in quarantined_events}
    if None in attached_ids: attached_ids.remove(None)
    if None in quarantined_ids: quarantined_ids.remove(None)
    if attached_ids.intersection(quarantined_ids): issue('duplicate_lifecycle_event_disposition')
    if manifest.get('coverage')!=snapshot.get('coverage'): issue('coverage_mismatch')
    skill_hash=(snapshot.get('source_skill') or {}).get('skill_contract_hash')
    if manifest.get('skill_contract_hash')!=skill_hash: issue('skill_contract_hash_mismatch')
    if require_current_skill_contract and skill_hash!=compute_skill_contract_hash(): issue('current_skill_contract_hash_mismatch')
    if manifest.get('snapshot_sha256')!=sha256_json(snapshot): issue('snapshot_hash_mismatch')
    try: _walk_forbidden(snapshot); _timestamps_valid(snapshot)
    except Exception as e: issue(str(e).split(':')[0])
    ids=set(); isin_groups={}
    for r in snapshot.get('records') or []:
        cid=r.get('canonical_target_id')
        if cid in ids: issue('duplicate_canonical_target_id')
        ids.add(cid)

        try: _validate_canonical_identity(r)
        except Exception as e: issue(str(e))
        if r.get('record_hash')!=sha256_json({k:v for k,v in r.items() if k!='record_hash'}): issue('record_hash_mismatch')
        isin=(r.get('identity') or {}).get('isin')
        if isin: isin_groups.setdefault(isin,[]).append(r)
    for isin, group in isin_groups.items():
        identities={r.get('canonical_target_id') for r in group}; quarantined=all(((r.get('classification') or {}).get('classification_status') in QUARANTINE or bool(_conflict_categories(r).intersection({'identity_conflict','classification_conflict'}))) for r in group)
        if len(identities)>1 and not quarantined: issue('duplicate_unresolved_isin_identity')
    if issues: raise VerifiedSecurityMasterSnapshotError(json.dumps(issues,ensure_ascii=False,sort_keys=True))
    return {'valid':True,'issue_count':0,'require_current_skill_contract':require_current_skill_contract}

def build_verified_security_master_lookup(snapshot:dict)->dict:
    lookup={'snapshot':snapshot,'by_canonical':{},'by_isin':{},'by_code':{},'by_name':{}}
    for r in snapshot.get('records') or []:
        cid=r['canonical_target_id']; lookup['by_canonical'][cid]=r
        ident=r.get('identity') or {}; market=(r.get('classification') or {}).get('market')
        if ident.get('isin'): lookup['by_isin'].setdefault(ident['isin'].upper(),[]).append(r)
        if ident.get('security_code'):
            lookup['by_code'].setdefault((market,ident['security_code']),[]).append(r); lookup['by_code'].setdefault((None,ident['security_code']),[]).append(r)
        for k in ('security_name_zh','security_name_en'):
            n=_norm_name(ident.get(k))
            if n: lookup['by_name'].setdefault(n,[]).append(r)
    return lookup

def load_verified_security_master_snapshot(snapshot_path:str|Path, manifest_path:str|Path, *, allow_fixture_snapshot:bool=False, require_current_skill_contract:bool=True)->ValidatedVerifiedSecurityMasterSnapshot:
    snap=json.loads(Path(snapshot_path).read_text(encoding='utf-8')); man=json.loads(Path(manifest_path).read_text(encoding='utf-8'))
    validation=validate_verified_security_master_snapshot(snap,man,allow_fixture_snapshot=allow_fixture_snapshot,require_current_skill_contract=require_current_skill_contract)
    return ValidatedVerifiedSecurityMasterSnapshot(snapshot=snap, manifest=man, lookup=build_verified_security_master_lookup(snap), validation=validation)

def _norm_name(s): return re.sub(r'\s+','',(s or '')).casefold()
def _selected(r,snapshot,reason,caveats=None):
    cls=r.get('classification') or {}; pol='potentially_eligible' if cls.get('classification_status') in CONFIRMED else 'blocked' if cls.get('classification_status') in QUARANTINE else 'caveated'
    return {'snapshot_id':snapshot.get('snapshot_id'),'record_id':r.get('record_id'),'record_hash':r.get('record_hash'),'canonical_target_id':r.get('canonical_target_id'),'identity':r.get('identity'),'classification':r.get('classification'),'lifecycle':r.get('lifecycle'),'execution_eligibility':r.get('execution_eligibility'),'classification_resolution_status':cls.get('classification_status'),'classification_execution_policy':pol,'resolution_reason':reason,'caveats':caveats or r.get('caveats') or []}

def resolve_verified_security_identity(query:str, snapshot_lookup:dict, *, market_context:str|None=None, allow_fixture_snapshot:bool=False, execute_mode:bool=True, as_of_date:str|None=None)->dict:
    q=(query or '').strip(); snap=snapshot_lookup['snapshot']; cands=[]; reason=[]
    if q in snapshot_lookup['by_canonical']: cands=[snapshot_lookup['by_canonical'][q]]; reason.append('exact_canonical_target_id')
    elif re.fullmatch(r'[A-Z]{2}[A-Z0-9]{10}',q.upper()): cands=snapshot_lookup['by_isin'].get(q.upper(),[]); reason.append('exact_isin')
    elif re.fullmatch(r'(TWSE|TPEX):[A-Z0-9._-]{1,20}',q): cands=[snapshot_lookup['by_canonical'].get(q)] if snapshot_lookup['by_canonical'].get(q) else []; reason.append('exact_canonical_target_id')
    elif re.fullmatch(r'[A-Z0-9._-]{1,20}',q):
        cands=snapshot_lookup['by_code'].get((market_context,q),[]) if market_context else snapshot_lookup['by_code'].get((None,q),[]); reason.append('exact_code')
        if not cands: cands=snapshot_lookup['by_name'].get(_norm_name(q),[]); reason.append('exact_normalized_name')
    else: cands=snapshot_lookup['by_name'].get(_norm_name(q),[]); reason.append('exact_normalized_name')
    cands=[c for c in cands if c]
    out={'schema_version':RESOLUTION_SCHEMA_VERSION,'query':query,'resolution_status':'not_found','candidate_count':len(cands),'selected':{},'candidates':[_selected(c,snap,reason[0]) for c in cands],'reason_codes':reason,'caveats':[]}
    if not cands: return out
    blocked=[c for c in cands if (c.get('classification') or {}).get('classification_status') in QUARANTINE]
    if blocked and len(cands)==1: out['resolution_status']='quarantined'; out['selected']=_selected(blocked[0],snap,reason[0]); out['reason_codes'].append('classification_quarantine'); return out
    if len(cands)>1: out['resolution_status']='ambiguous'; out['reason_codes'].append('multiple_candidates'); return out
    r=cands[0]
    if market_context and (r.get('classification') or {}).get('market')!=market_context: out['resolution_status']='not_found'; out['reason_codes'].append('market_mismatch'); return out
    if execute_mode and (r.get('observation') or {}).get('status')=='fixture_observation_only' and not allow_fixture_snapshot:
        out['resolution_status']='quarantined'; out['selected']=_selected(r,snap,reason[0],['fixture_observation_only_rejected_in_production']); out['reason_codes'].append('fixture_observation_only_rejected'); return out
    out['resolution_status']='resolved'; out['selected']=_selected(r,snap,reason[0]); return out

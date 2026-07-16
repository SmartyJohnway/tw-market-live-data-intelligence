from __future__ import annotations
import json, re
from pathlib import Path
from typing import Any
from scripts.m8r_03d_f1_security_master_snapshot_exporter import SNAPSHOT_SCHEMA_VERSION, MANIFEST_SCHEMA_VERSION, sha256_json, FORBIDDEN_RAW_FIELDS, CONFIRMED, QUARANTINE

RESOLUTION_SCHEMA_VERSION='m8r_03d_f1_security_identity_resolution.v1'
class VerifiedSecurityMasterSnapshotError(ValueError): pass

def _walk_forbidden(v,path=''):
    if isinstance(v,dict):
        for k,x in v.items():
            if k in FORBIDDEN_RAW_FIELDS or k.lower() in FORBIDDEN_RAW_FIELDS: raise VerifiedSecurityMasterSnapshotError(f'forbidden_raw_field:{path}/{k}')
            _walk_forbidden(x,f'{path}/{k}')
    elif isinstance(v,list):
        for i,x in enumerate(v): _walk_forbidden(x,f'{path}/{i}')

def validate_verified_security_master_snapshot(snapshot:dict, manifest:dict, *, allow_fixture_snapshot:bool=False)->dict:
    issues=[]
    def issue(c): issues.append({'code':c})
    if manifest.get('schema_version')!=MANIFEST_SCHEMA_VERSION: issue('unsupported_manifest_schema')
    if snapshot.get('schema_version')!=SNAPSHOT_SCHEMA_VERSION: issue('unsupported_snapshot_schema')
    if manifest.get('validation_status')!='passed': issue('manifest_validation_not_passed')
    if manifest.get('snapshot_id')!=snapshot.get('snapshot_id'): issue('snapshot_id_mismatch')
    if manifest.get('record_count')!=len(snapshot.get('records') or []): issue('record_count_mismatch')
    if manifest.get('snapshot_sha256')!=sha256_json(snapshot): issue('snapshot_hash_mismatch')
    try: _walk_forbidden(snapshot)
    except VerifiedSecurityMasterSnapshotError as e: issue(str(e))
    ids=set(); isins={}
    for r in snapshot.get('records') or []:
        cid=r.get('canonical_target_id')
        if cid in ids: issue('duplicate_canonical_target_id')
        ids.add(cid)
        rh=r.get('record_hash'); calc=sha256_json({k:v for k,v in r.items() if k!='record_hash'})
        if rh!=calc: issue('record_hash_mismatch')
        isin=(r.get('identity') or {}).get('isin')
        if isin and isin in isins and r.get('execution_eligibility',{}).get('status')!='blocked': issue('duplicate_unresolved_isin_identity')
        isins[isin]=cid
        if not allow_fixture_snapshot and (r.get('observation') or {}).get('status')=='fixture_observation_only':
            # valid as file but not accepted for production lookup selected records
            pass
    if issues: raise VerifiedSecurityMasterSnapshotError(json.dumps(issues,ensure_ascii=False))
    return {'valid':True,'issue_count':0}

def load_verified_security_master_snapshot(snapshot_path:str|Path, manifest_path:str|Path, *, allow_fixture_snapshot:bool=False)->tuple[dict,dict]:
    snap=json.loads(Path(snapshot_path).read_text(encoding='utf-8')); man=json.loads(Path(manifest_path).read_text(encoding='utf-8'))
    validate_verified_security_master_snapshot(snap,man,allow_fixture_snapshot=allow_fixture_snapshot); return snap,man

def _norm_name(s): return re.sub(r'\s+','',(s or '')).casefold()
def build_verified_security_master_lookup(snapshot:dict)->dict:
    lookup={'snapshot':snapshot,'by_canonical':{},'by_isin':{},'by_code':{},'by_name':{}}
    for r in snapshot.get('records') or []:
        cid=r['canonical_target_id']; lookup['by_canonical'][cid]=r
        ident=r.get('identity') or {}; market=(r.get('classification') or {}).get('market')
        if ident.get('isin'): lookup['by_isin'].setdefault(ident['isin'].upper(),[]).append(r)
        if ident.get('security_code'): lookup['by_code'].setdefault((market,ident['security_code']),[]).append(r); lookup['by_code'].setdefault((None,ident['security_code']),[]).append(r)
        for k in ('security_name_zh','security_name_en'):
            n=_norm_name(ident.get(k));
            if n: lookup['by_name'].setdefault(n,[]).append(r)
    return lookup

def _selected(r,snapshot,reason,caveats=None):
    cls=r.get('classification') or {}; pol='potentially_eligible' if cls.get('classification_status') in CONFIRMED else 'blocked' if cls.get('classification_status') in QUARANTINE else 'caveated'
    return {'snapshot_id':snapshot.get('snapshot_id'),'record_id':r.get('record_id'),'record_hash':r.get('record_hash'),'canonical_target_id':r.get('canonical_target_id'),'identity':r.get('identity'),'classification':r.get('classification'),'lifecycle':r.get('lifecycle'),'execution_eligibility':r.get('execution_eligibility'),'classification_resolution_status':cls.get('classification_status'),'classification_execution_policy':pol,'resolution_reason':reason,'caveats':caveats or r.get('caveats') or []}

def resolve_verified_security_identity(query:str, snapshot_lookup:dict, *, market_context:str|None=None, allow_fixture_snapshot:bool=False, execute_mode:bool=True, as_of_date:str|None=None)->dict:
    q=(query or '').strip(); snap=snapshot_lookup['snapshot']; cands=[]; reason=[]
    if q in snapshot_lookup['by_canonical']: cands=[snapshot_lookup['by_canonical'][q]]; reason.append('exact_canonical_target_id')
    elif re.fullmatch(r'[A-Z]{2}[A-Z0-9]{10}',q.upper()): cands=snapshot_lookup['by_isin'].get(q.upper(),[]); reason.append('exact_isin')
    elif re.fullmatch(r'(TWSE|TPEX):[A-Z0-9._-]{1,20}',q): cands=[snapshot_lookup['by_canonical'].get(q)] if snapshot_lookup['by_canonical'].get(q) else []; reason.append('exact_canonical_target_id')
    elif re.fullmatch(r'[A-Z0-9._-]{1,20}',q):
        cands=snapshot_lookup['by_code'].get((market_context,q),[]) if market_context else snapshot_lookup['by_code'].get((None,q),[])
        reason.append('exact_code')
        if not cands:
            cands=snapshot_lookup['by_name'].get(_norm_name(q),[])
            reason.append('exact_normalized_name')
    else: cands=snapshot_lookup['by_name'].get(_norm_name(q),[]); reason.append('exact_normalized_name')
    cands=[c for c in cands if c]
    out={'schema_version':RESOLUTION_SCHEMA_VERSION,'query':query,'resolution_status':'not_found','candidate_count':len(cands),'selected':{},'candidates':[_selected(c,snap,reason[0]) for c in cands],'reason_codes':reason,'caveats':[]}
    if not cands: return out
    blocked=[c for c in cands if (c.get('classification') or {}).get('classification_status') in QUARANTINE]
    if blocked and len(cands)==1: out['resolution_status']='quarantined'; out['selected']=_selected(blocked[0],snap,reason[0]); out['reason_codes'].append('classification_quarantine'); return out
    if len(cands)>1: out['resolution_status']='ambiguous'; out['reason_codes'].append('multiple_candidates'); return out
    r=cands[0]
    if market_context and (r.get('classification') or {}).get('market')!=market_context: out['resolution_status']='not_found'; out['reason_codes'].append('market_mismatch'); return out
    obs=(r.get('observation') or {}).get('status')
    if execute_mode and obs=='fixture_observation_only' and not allow_fixture_snapshot: out['resolution_status']='quarantined'; out['selected']=_selected(r,snap,reason[0],['fixture_observation_only_rejected_in_production']); out['reason_codes'].append('fixture_observation_only_rejected'); return out
    out['resolution_status']='resolved'; out['selected']=_selected(r,snap,reason[0]); return out

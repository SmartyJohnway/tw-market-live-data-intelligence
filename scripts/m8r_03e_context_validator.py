from __future__ import annotations
import hashlib,json,re
from pathlib import Path
from typing import Any
import jsonschema

PACKAGE_SCHEMA_VERSION='m8r_watchlist_ai_context_package.v1'
HANDOFF_SCHEMA_VERSION='m8r_watchlist_conversation_handoff.v1'
MANIFEST_SCHEMA_VERSION='m8r_watchlist_ai_context_manifest.v1'
CITATION_SCHEMA_VERSION='m8r_watchlist_ai_fact_citation.v1'
MISSING_SCHEMA_VERSION='m8r_watchlist_missing_evidence.v1'
BUILDER_VERSION='m8r_03e_context_builder.v1'
SCHEMA_DIR=Path('docs/contracts/schemas')
SCHEMA_FILES=[
 'm8r_watchlist_ai_context_package.v1.schema.json',
 'm8r_watchlist_conversation_handoff.v1.schema.json',
 'm8r_watchlist_ai_context_manifest.v1.schema.json',
 'm8r_watchlist_ai_fact_citation.v1.schema.json',
 'm8r_watchlist_missing_evidence.v1.schema.json']
FORBIDDEN_FIELDS={x.lower() for x in ['raw_payload','raw_html','raw_cells','cookies','headers','authorization','authorization_header','access_token','refresh_token','session_id','msgArray','browser_frame','complete_endpoint_dump','operator_secrets','one_shot_nonce']}
EVIDENCE_STATUSES={'supported','supported_with_caveat','partial','unavailable','conflicted','stale','not_applicable'}
COVERAGE_STATUSES={'complete','partial','failed','blocked'}

def canonical_json(v:Any)->str: return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def sha256_json(v:Any)->str: return hashlib.sha256(canonical_json(v).encode()).hexdigest()
def artifact_hash_without(v:dict, field:str)->str:
    c=json.loads(json.dumps(v)); c[field]=None; return sha256_json(c)
def schema_bundle_sha256()->str:
    return sha256_json({p:json.loads((SCHEMA_DIR/p).read_text(encoding='utf-8')) for p in SCHEMA_FILES})
def _schema(name): return json.loads((SCHEMA_DIR/name).read_text(encoding='utf-8'))
def validate_schema(obj,name): jsonschema.Draft202012Validator(_schema(name)).validate(obj)

def walk_forbidden(v,path='$',issues=None):
    issues=[] if issues is None else issues
    if isinstance(v,dict):
        for k,x in v.items():
            if k.lower() in FORBIDDEN_FIELDS: issues.append({'code':'forbidden_field','path':f'{path}.{k}'})
            walk_forbidden(x,f'{path}.{k}',issues)
    elif isinstance(v,list):
        for i,x in enumerate(v): walk_forbidden(x,f'{path}[{i}]',issues)
    return issues

def ptr_get(obj:Any, ptr:str):
    if not ptr.startswith('/'): raise KeyError(ptr)
    cur=obj
    for raw in ptr.strip('/').split('/') if ptr!='/' else []:
        tok=raw.replace('~1','/').replace('~0','~')
        cur=cur[int(tok)] if isinstance(cur,list) else cur[tok]
    return cur

def _collect_target_cites(package):
    ids=[]
    for t in package.get('targets',[]): ids.extend(t.get('citations',[]))
    return set(ids)

def validate_watchlist_ai_context_package(package:dict, *, upstream_artifacts:dict|None=None)->dict:
    issues=[]
    try: validate_schema(package,'m8r_watchlist_ai_context_package.v1.schema.json')
    except Exception as e: issues.append({'code':'schema_validation_failed','detail':str(e)[:160]})
    issues+=walk_forbidden(package)
    if package.get('package_hash')!=artifact_hash_without(package,'package_hash'): issues.append({'code':'package_hash_mismatch'})
    cids=set(); cited=_collect_target_cites(package)
    for c in package.get('citation_index',[]):
        cid=c.get('citation_id')
        if cid in cids: issues.append({'code':'duplicate_citation_id','citation_id':cid})
        cids.add(cid)
        try:
            val=ptr_get(package,c.get('fact_path',''))
            if c.get('value_hash')!=sha256_json(val): issues.append({'code':'citation_value_hash_mismatch','citation_id':cid})
        except Exception: issues.append({'code':'citation_fact_path_mismatch','citation_id':cid})
        if c.get('source_path') and upstream_artifacts:
            art=upstream_artifacts.get(c.get('source_artifact_type')) or upstream_artifacts.get(c.get('source_artifact_id'))
            if art is not None:
                try: ptr_get(art,c['source_path'])
                except Exception: issues.append({'code':'citation_source_path_mismatch','citation_id':cid})
    if not cited.issubset(cids): issues.append({'code':'target_orphan_citation'})
    for cid in cids:
        if cid not in cited and any(c.get('target_id') for c in package.get('citation_index',[]) if c.get('citation_id')==cid):
            issues.append({'code':'orphan_citation','citation_id':cid})
    if [t.get('target_id') for t in package.get('targets',[])] != package.get('request',{}).get('enabled_target_order',[]): issues.append({'code':'target_order_mismatch'})
    return {'valid':not issues,'issues':issues}

def validate_watchlist_conversation_handoff(handoff:dict, *, context_package:dict)->dict:
    issues=[]
    try: validate_schema(handoff,'m8r_watchlist_conversation_handoff.v1.schema.json')
    except Exception as e: issues.append({'code':'schema_validation_failed','detail':str(e)[:160]})
    issues+=walk_forbidden(handoff)
    if handoff.get('handoff_hash')!=artifact_hash_without(handoff,'handoff_hash'): issues.append({'code':'handoff_hash_mismatch'})
    if handoff.get('context_package_id')!=context_package.get('context_package_id'): issues.append({'code':'context_package_id_mismatch'})
    if handoff.get('target_order')!=context_package.get('request',{}).get('enabled_target_order',[]): issues.append({'code':'target_order_mismatch'})
    if context_package.get('coverage_summary',{}).get('coverage_status')!='complete' and not handoff.get('required_disclosures'): issues.append({'code':'missing_required_disclosure'})
    return {'valid':not issues,'issues':issues}

def validate_watchlist_ai_context_manifest(manifest:dict, *, context_package:dict, handoff:dict, upstream_artifacts:dict|None=None)->dict:
    issues=[]
    try: validate_schema(manifest,'m8r_watchlist_ai_context_manifest.v1.schema.json')
    except Exception as e: issues.append({'code':'schema_validation_failed','detail':str(e)[:160]})
    if manifest.get('context_package_sha256')!=sha256_json(context_package): issues.append({'code':'package_hash_mismatch'})
    if manifest.get('conversation_handoff_sha256')!=sha256_json(handoff): issues.append({'code':'handoff_hash_mismatch'})
    if manifest.get('schema_bundle_sha256')!=schema_bundle_sha256(): issues.append({'code':'schema_hash_mismatch'})
    up=manifest.get('upstream',{})
    if up.get('request_id')!=context_package.get('request',{}).get('request_id'): issues.append({'code':'upstream_id_mismatch'})
    if manifest.get('validation_status')=='passed' and manifest.get('validation_issues'): issues.append({'code':'validation_status_mismatch'})
    return {'valid':not issues,'issues':issues}

from __future__ import annotations
import hashlib,json
from functools import lru_cache
from pathlib import Path
from typing import Any
import jsonschema
from scripts.m8r_03c_conversation_contract_validator import validate_watchlist_snapshot_request, validate_watchlist_performance_request
from scripts.m8r_03c_watchlist_bundle_builder import validate_watchlist_snapshot_bundle, validate_watchlist_performance_bundle
from scripts.m8r_03d_watchlist_execution_plan import canonical_request_hash

PACKAGE_SCHEMA_VERSION='m8r_watchlist_ai_context_package.v2'
HANDOFF_SCHEMA_VERSION='m8r_watchlist_conversation_handoff.v1'
MANIFEST_SCHEMA_VERSION='m8r_watchlist_ai_context_manifest.v1'
CITATION_SCHEMA_VERSION='m8r_watchlist_ai_fact_citation.v1'
MISSING_SCHEMA_VERSION='m8r_watchlist_missing_evidence.v1'
BUILDER_VERSION='m8r_03e_context_builder.v1'
SCHEMA_DIR=Path('docs/contracts/schemas')
SCHEMA_FILES=['m8r_watchlist_ai_context_package.v2.schema.json','m8r_watchlist_conversation_handoff.v1.schema.json','m8r_watchlist_ai_context_manifest.v1.schema.json','m8r_watchlist_ai_fact_citation.v1.schema.json','m8r_watchlist_missing_evidence.v1.schema.json']
FORBIDDEN_FIELDS={x.lower() for x in ['raw_payload','raw_html','raw_cells','cookies','headers','authorization','authorization_header','access_token','refresh_token','session_id','msgArray','browser_frame','complete_endpoint_dump','operator_secrets','one_shot_nonce']}
CITATION_REQUIRES_SOURCE={'supported','supported_with_caveat','partial','stale'}
BUNDLE_SCHEMA_BY_TYPE={'snapshot':'m8r_watchlist_snapshot_bundle.v1','performance':'m8r_watchlist_performance_bundle.v1'}

def canonical_json(v:Any)->str: return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def sha256_json(v:Any)->str: return hashlib.sha256(canonical_json(v).encode()).hexdigest()
def artifact_hash_without(v:dict, field:str)->str:
    c=json.loads(json.dumps(v)); c[field]=None; return sha256_json(c)
def schema_bundle_sha256()->str:
    return sha256_json({p:json.loads((SCHEMA_DIR/p).read_text(encoding='utf-8')) for p in SCHEMA_FILES})
@lru_cache(maxsize=len(SCHEMA_FILES))
def _validator(name: str):
    # Schemas are repository-shipped immutable inputs for a process; caching avoids
    # reparsing/compiling the same contract during one bounded pipeline.
    schema = json.loads((SCHEMA_DIR / name).read_text(encoding='utf-8'))
    return jsonschema.Draft202012Validator(schema)
def _schema(name): return _validator(name).schema
def validate_schema(obj,name): _validator(name).validate(obj)

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

def _bundle_type_from_bundle(bundle:dict)->str:
    sv=bundle.get('schema_version','')
    return 'performance' if 'performance' in sv else 'snapshot'

def _request_target_order(req:dict)->list[str]: return list((req.get('persistent_watchlist_reference') or {}).get('enabled_target_ids') or [])
def _bundle_target_order(bundle:dict)->list[str]: return list((bundle.get('coverage') or {}).get('requested_target_ids') or [t.get('target_id') for t in bundle.get('targets',[])])
def _planned_group_keys(plan:dict)->set[tuple[str,tuple[str,...]]]: return {(g.get('source_family'),tuple(g.get('target_ids') or [])) for g in plan.get('source_call_groups',[])}
def _executed_group_keys(result:dict)->set[tuple[str,tuple[str,...]]]: return {(g.get('source_family'),tuple(g.get('target_ids') or [])) for g in (result.get('source_execution_summary') or {}).get('group_results',[]) if g.get('source_family') and g.get('target_ids')}

def validate_m8r_03e_upstream_artifacts(*, validated_request:dict, execution_plan:dict, execution_result:dict, watchlist_bundle:dict)->dict:
    issues=[]; bundle_type=execution_plan.get('bundle_type') or _bundle_type_from_bundle(watchlist_bundle)
    try:
        req=validate_watchlist_performance_request(validated_request) if bundle_type=='performance' else validate_watchlist_snapshot_request(validated_request)
    except Exception as e: issues.append({'code':'validated_request_invalid','detail':str(e)[:160]}); req=validated_request
    try:
        validate_watchlist_performance_bundle(watchlist_bundle) if bundle_type=='performance' else validate_watchlist_snapshot_bundle(watchlist_bundle)
    except Exception as e: issues.append({'code':'watchlist_bundle_invalid','detail':str(e)[:160]})
    if execution_plan.get('schema_version')!='m8r_03d_watchlist_execution_plan.v1': issues.append({'code':'execution_plan_invalid'})
    if execution_result.get('schema_version')!='m8r_03d_watchlist_execution_result.v1': issues.append({'code':'execution_result_invalid'})
    rid=req.get('request_id')
    if execution_plan.get('request_id')!=rid or execution_result.get('request_id')!=rid or watchlist_bundle.get('request_id')!=rid: issues.append({'code':'request_id_mismatch'})
    rh=canonical_request_hash(req)
    if execution_plan.get('request_hash')!=rh or execution_result.get('request_hash')!=rh: issues.append({'code':'request_hash_mismatch'})
    if execution_result.get('plan_id')!=execution_plan.get('plan_id'): issues.append({'code':'plan_id_mismatch'})
    if execution_plan.get('bundle_type')!=bundle_type or watchlist_bundle.get('schema_version')!=BUNDLE_SCHEMA_BY_TYPE.get(bundle_type): issues.append({'code':'bundle_type_mismatch'})
    order=_request_target_order(req)
    if execution_plan.get('target_order')!=order or _bundle_target_order(watchlist_bundle)!=order: issues.append({'code':'target_order_mismatch'})
    if [t.get('target_id') for t in execution_plan.get('targets',[])]!=order: issues.append({'code':'plan_target_ids_mismatch'})
    if [t.get('target_id') for t in watchlist_bundle.get('targets',[])]!=order: issues.append({'code':'bundle_target_ids_mismatch'})
    planned=_planned_group_keys(execution_plan); executed=_executed_group_keys(execution_result)
    if executed and not executed.issubset(planned): issues.append({'code':'planned_vs_executed_source_groups_mismatch'})
    return {'valid':not issues,'issues':issues,'bundle_type':bundle_type,'request_hash':rh,'target_order':order}

def _artifact_id(artifact_type:str, art:dict)->str|None:
    return {'watchlist_bundle':art.get('bundle_id'),'execution_plan':art.get('plan_id'),'execution_result':art.get('run_id'),'validated_request':art.get('request_id'),'verified_security_master_snapshot':art.get('snapshot_id')}.get(artifact_type)

def _artifact_for(c:dict, upstream_artifacts:dict|None):
    if not upstream_artifacts: return None
    typ=c.get('source_artifact_type'); sid=c.get('source_artifact_id')
    art=upstream_artifacts.get(typ) or upstream_artifacts.get(sid)
    return art

def material_fact_paths(package:dict)->set[str]:
    paths=set()
    for i,t in enumerate(package.get('targets',[])):
        for sec in ('identity','classification','lifecycle','execution_eligibility','current_observation','eod_reference','performance'):
            for k,v in (t.get(sec) or {}).items():
                if v is not None and v != {} and v != []: paths.add(f'/targets/{i}/{sec}/{k}')
    return paths

def _collect_target_cites(package):
    ids=[]
    for t in package.get('targets',[]): ids.extend(t.get('citations',[]))
    return set(ids)

def _source_value_for(c:dict, source_artifact:dict):
    return ptr_get(source_artifact,c.get('source_path',''))

def validate_watchlist_ai_context_package(package:dict, *, upstream_artifacts:dict|None=None)->dict:
    issues=[]
    try: validate_schema(package,'m8r_watchlist_ai_context_package.v2.schema.json')
    except Exception as e: issues.append({'code':'schema_validation_failed','detail':str(e)[:160]})
    issues+=walk_forbidden(package)
    if package.get('package_hash')!=artifact_hash_without(package,'package_hash'): issues.append({'code':'package_hash_mismatch'})
    cb=package.get('context_budget') or {}
    if cb.get('serialized_size_basis')=='canonical_json_utf8_final_package_including_package_hash':
        if cb.get('final_serialized_bytes')!=len(canonical_json(package).encode()): issues.append({'code':'serialized_byte_count_mismatch'})
    cids=set(); cited=_collect_target_cites(package); fact_to_cites={}
    for c in package.get('citation_index',[]):
        cid=c.get('citation_id'); fact_path=c.get('fact_path','')
        if cid in cids: issues.append({'code':'duplicate_citation_id','citation_id':cid})
        cids.add(cid); fact_to_cites.setdefault(fact_path,[]).append(c)
        try:
            val=ptr_get(package,fact_path)
            if c.get('value_hash')!=sha256_json(val): issues.append({'code':'citation_value_hash_mismatch','citation_id':cid})
        except Exception: issues.append({'code':'citation_fact_path_mismatch','citation_id':cid}); val=None
        if fact_path not in material_fact_paths(package): issues.append({'code':'citation_non_material_or_absent_fact','citation_id':cid})
        if c.get('evidence_status') in CITATION_REQUIRES_SOURCE:
            art=_artifact_for(c,upstream_artifacts)
            if art is None: issues.append({'code':'citation_source_artifact_missing','citation_id':cid}); continue
            if _artifact_id(c.get('source_artifact_type'),art)!=c.get('source_artifact_id'): issues.append({'code':'citation_source_artifact_id_mismatch','citation_id':cid})
            try:
                source_val=_source_value_for(c,art)
                if val is not None and sha256_json(source_val)!=c.get('value_hash'): issues.append({'code':'citation_source_value_hash_mismatch','citation_id':cid})
            except Exception: issues.append({'code':'citation_source_path_mismatch','citation_id':cid})
    if not cited.issubset(cids): issues.append({'code':'target_orphan_citation'})
    for cid in cids:
        if cid not in cited and any(c.get('target_id') for c in package.get('citation_index',[]) if c.get('citation_id')==cid): issues.append({'code':'orphan_citation','citation_id':cid})
    for path in material_fact_paths(package):
        if path not in fact_to_cites:
            code='missing_identity_citation' if '/identity/' in path else 'uncited_material_fact'
            issues.append({'code':code,'fact_path':path})
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
    expected_counts={'target_count':len(context_package.get('targets',[])),'fact_count':len(material_fact_paths(context_package)),'citation_count':len(context_package.get('citation_index',[])),'missing_evidence_count':len(context_package.get('missing_evidence',[])),'caveat_count':len(context_package.get('caveats',[])),'evidence_limitation_count':len(context_package.get('evidence_limitations',[]))}
    for k,v in expected_counts.items():
        if (manifest.get('counts') or {}).get(k)!=v: issues.append({'code':'manifest_count_mismatch','field':k})
    if upstream_artifacts:
        req=upstream_artifacts.get('validated_request') or {}; plan=upstream_artifacts.get('execution_plan') or {}; result=upstream_artifacts.get('execution_result') or {}; bundle=upstream_artifacts.get('watchlist_bundle') or {}
        expected={'request_hash':sha256_json(req),'execution_plan_id':plan.get('plan_id'),'execution_plan_hash':sha256_json(plan),'execution_result_id':result.get('run_id'),'execution_result_hash':sha256_json(result),'bundle_id':bundle.get('bundle_id'),'bundle_hash':sha256_json(bundle),'security_master_snapshot_ids':sorted({t.get('identity',{}).get('snapshot_id') for t in context_package.get('targets',[]) if t.get('identity',{}).get('snapshot_id')})}
        for k,v in expected.items():
            if up.get(k)!=v: issues.append({'code':'upstream_hash_or_id_mismatch','field':k})
    if manifest.get('validation_status')=='passed' and manifest.get('validation_issues'): issues.append({'code':'validation_status_mismatch'})
    return {'valid':not issues,'issues':issues}

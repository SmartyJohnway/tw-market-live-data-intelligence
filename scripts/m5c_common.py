from __future__ import annotations
import hashlib,json,shutil
from pathlib import Path
from jsonschema import Draft202012Validator
try:
    from verify_m5b_manifest import verify as verify_m5b_manifest
    from validate_m5b_execution_authorization import validate_authorization as validate_m5b_authorization
except ModuleNotFoundError:
    from scripts.verify_m5b_manifest import verify as verify_m5b_manifest
    from scripts.validate_m5b_execution_authorization import validate_authorization as validate_m5b_authorization
RUN_ID='m5b_twse_openapi_20260627T015136Z'
RUN_DIR=Path('research/live_probe_runs/m5b')/RUN_ID
AUTH='docs/authorization/decisions/M5B_TWSE_OPENAPI_2330_0050_00929_AUTHORIZATION.json'
AUTH_REQ='tests/fixtures/authorization/valid_m5a_live_probe_request.json'
TARGETS=['2330','0050','00929']
SOURCE='TWSE_OpenAPI'
MERGE_COMMIT='3b4f616f9d87856b61a16b52e5f84009b7f5fb92'
CANONICAL_RUN_DIR=str(RUN_DIR)
REQ_ART=['authorization_snapshot.json','request_snapshot.json','execution_receipt.json','bounded_probe_result.json','bounded_normalized_rows.json','source_contract_assessment.json','freshness_delay_assessment.json','run_summary.json','staging_candidate.json','evidence_ledger.json','sha256_manifest.json']
FORBID_PREFIX=('research/generated/','frontend/public/','production/','prod/')
SUCCESS_CONTRACT_STATUSES={'normalized_pass','partial_pass'}
FORBID_FLAGS=['production_current_state','realtime_guaranteed','trading_signal','generated_artifact_promoted','frontend_published','production_ready','promotion_authorized','frontend_publication_authorized','generated_artifact_write']
def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def safe_load(p):
    try:
        return load(p), None
    except Exception as exc:
        return None, {'code':'json_read_failed','path':str(p),'detail':str(exc)}
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def candidate_hash(run_dir=RUN_DIR): return sha(Path(run_dir)/'staging_candidate.json')
def manifest_hash(run_dir=RUN_DIR): return sha(Path(run_dir)/'sha256_manifest.json')
def _contract_errors(rd:Path):
    errs=[]; missing=[a for a in REQ_ART if not (rd/a).exists()]
    if missing: errs.append({'code':'missing_required_artifact','items':missing})
    if missing: return errs
    docs={}
    for name in ['sha256_manifest.json','staging_candidate.json','run_summary.json','execution_receipt.json']:
        doc, err = safe_load(rd/name)
        if err: errs.append(err)
        else: docs[name]=doc
    if errs: return errs
    man=docs['sha256_manifest.json']; cand=docs['staging_candidate.json']; summ=docs['run_summary.json']; rec=docs['execution_receipt.json']
    if set(man.get('manifest',{})) != {a for a in REQ_ART if a!='sha256_manifest.json'}:
        errs.append({'code':'manifest_contract_mismatch','expected':sorted(a for a in REQ_ART if a!='sha256_manifest.json'),'actual':sorted(man.get('manifest',{}))})
    statuses={'candidate':cand.get('contract_status'),'summary':summ.get('contract_status'),'receipt':rec.get('contract_status'),'manifest':man.get('contract_status')}
    if len(set(statuses.values())) != 1 or next(iter(statuses.values())) not in SUCCESS_CONTRACT_STATUSES:
        errs.append({'code':'contract_status_blocked','statuses':statuses,'allowed':sorted(SUCCESS_CONTRACT_STATUSES)})
    for objname,obj in [('candidate',cand),('summary',summ),('receipt',rec),('manifest',man)]:
        if obj.get('source_id')!=SOURCE: errs.append({'code':'source_mismatch','object':objname})
        if set(map(str,obj.get('requested_targets',[])))!=set(TARGETS): errs.append({'code':'target_drift','object':objname})
        for f in FORBID_FLAGS:
            if obj.get(f) is True: errs.append({'code':'forbidden_flag','object':objname,'flag':f})
    rows=cand.get('rows',[]); row_targets=[str(r.get('symbol')) for r in rows if isinstance(r,dict)]
    if len(row_targets)!=len(set(row_targets)) or set(row_targets)!=set(TARGETS): errs.append({'code':'target_drift','object':'candidate.rows'})
    if cand.get('source_id')!=SOURCE or not all(isinstance(r,dict) and r.get('source')==SOURCE for r in rows): errs.append({'code':'source_mismatch','object':'candidate.rows'})
    return errs
def verify_evidence(run_dir=RUN_DIR, authorization=AUTH, request=AUTH_REQ):
    rd=Path(run_dir); errs=[]
    errs += verify_m5b_manifest(rd)
    errs += _contract_errors(rd)
    receipt=rd/'execution_receipt.json'
    errs += validate_m5b_authorization(authorization, request, receipt, mode='receipt_audit') if receipt.exists() else [{'code':'receipt_missing','path':str(receipt)}]
    ok=not errs
    return {'status':'pass' if ok else 'blocked','errors':errs,'run_id':RUN_ID,'source_id':SOURCE,'targets':TARGETS,'manifest_sha256':manifest_hash(rd) if (rd/'sha256_manifest.json').exists() else None,'staging_candidate_sha256':candidate_hash(rd) if (rd/'staging_candidate.json').exists() else None,'classification':'historical_evidence_snapshot','freshness':'eod_batch_not_current_realtime','receipt_audit': not validate_m5b_authorization(authorization, request, receipt, mode='receipt_audit') if receipt.exists() else False}
def forbid_path(path):
    s=str(path).replace('\\','/')
    parts=[]
    for part in s.split('/'):
        if part in ('','.'): continue
        if part=='..':
            if parts: parts.pop()
            continue
        parts.append(part)
    norm='/'.join(parts)
    return any(norm.startswith(p.rstrip('/')) or ('/'+p) in ('/'+norm+'/') for p in FORBID_PREFIX)
def readonly_payload_from_candidate(c):
    return {'schema_version':'controlled_refresh_staging_payload.v1','generated_at_utc':c['retrieved_at_utc'],'staging_only': True,'operator_confirmations': {'confirm_fixture_backed': True, 'confirm_no_live_probe': True},'target_universe': {'mode':'bounded','scope':'watchlist','symbols': TARGETS, 'full_market_scan': False},'validation': {'frontend_write': False, 'full_market_scan': False, 'generated_artifact_write': False, 'network_authorized': False, 'production_write': False, 'trading_signal': False},'source_runs':[{'source_id':c['source_id'],'authority_level':'official','source_type':'official_openapi','request_method':'LOCAL_HISTORICAL_EVIDENCE','url_or_fixture':str(RUN_DIR/'staging_candidate.json'),'http_status':c.get('http_status'), 'contract_status':c.get('contract_status'), 'raw_evidence_ref':str(RUN_DIR/'staging_candidate.json'),'errors':[], 'source_risk_flags':['official_eod_reference_source','not_intraday_live_feed','not_realtime_guaranteed'],'retrieved_at_utc':r['retrieved_at_utc'],'source_timestamp':c['source_timestamp'],'freshness_status':'stale','delay_status':'stale','staleness_seconds':86400,'normalization_status':c['normalization_status'],'data_quality_flags':['historical_evidence_snapshot','not_current_realtime'],'normalized_sample_preview':r} for r in c['rows']]}
def validate_schema(path,schema_path='docs/authorization/m5c_staging_promotion_request_schema.json'):
    data=load(path); schema=load(schema_path)
    return [{'code':'schema_error','path':'$' + ''.join(f'/{x}' for x in e.path),'detail':e.message} for e in Draft202012Validator(schema).iter_errors(data)]
def copy_run(src, dst): shutil.copytree(src, dst); return Path(dst)

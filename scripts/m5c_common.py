from __future__ import annotations
import hashlib,json
from pathlib import Path
RUN_ID='m5b_twse_openapi_20260627T015136Z'
RUN_DIR=Path('research/live_probe_runs/m5b')/RUN_ID
TARGETS=['2330','0050','00929']
SOURCE='TWSE_OpenAPI'
MERGE_COMMIT='3b4f616f9d87856b61a16b52e5f84009b7f5fb92'
REQ_ART=['authorization_snapshot.json','request_snapshot.json','execution_receipt.json','bounded_probe_result.json','bounded_normalized_rows.json','source_contract_assessment.json','freshness_delay_assessment.json','run_summary.json','staging_candidate.json','sha256_manifest.json']
FORBID_PREFIX=('research/generated/','frontend/public/','production/prod/')
FORBID_FLAGS=['production_current_state','realtime_guaranteed','trading_signal','generated_artifact_promoted','frontend_published','production_ready','promotion_authorized','frontend_publication_authorized','generated_artifact_write']
def load(p): return json.loads(Path(p).read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def candidate_hash(run_dir=RUN_DIR): return sha(Path(run_dir)/'staging_candidate.json')
def manifest_hash(run_dir=RUN_DIR): return sha(Path(run_dir)/'sha256_manifest.json')
def verify_evidence(run_dir=RUN_DIR):
    rd=Path(run_dir); errs=[]
    missing=[a for a in REQ_ART if not (rd/a).exists()]
    if missing: errs.append({'code':'missing_artifact','items':missing})
    if missing or not (rd/'sha256_manifest.json').exists(): return {'status':'blocked','errors':errs}
    man=load(rd/'sha256_manifest.json')
    for name,dig in man.get('manifest',{}).items():
        if (rd/name).exists() and sha(rd/name)!=dig: errs.append({'code':'manifest_mismatch','artifact':name})
    cand=load(rd/'staging_candidate.json'); summ=load(rd/'run_summary.json'); rec=load(rd/'execution_receipt.json')
    for objname,obj in [('candidate',cand),('summary',summ),('receipt',rec),('manifest',man)]:
        if obj.get('source_id')!=SOURCE: errs.append({'code':'source_mismatch','object':objname})
        if set(map(str,obj.get('requested_targets',[])))!=set(TARGETS): errs.append({'code':'target_drift','object':objname})
        for f in FORBID_FLAGS:
            if obj.get(f) is True: errs.append({'code':'forbidden_flag','object':objname,'flag':f})
    rows=cand.get('rows',[]); row_targets=[str(r.get('symbol')) for r in rows]
    if set(row_targets)!=set(TARGETS): errs.append({'code':'target_drift','object':'candidate.rows'})
    if cand.get('source_id')==SOURCE and all(r.get('source')==SOURCE for r in rows): pass
    else: errs.append({'code':'source_mismatch','object':'candidate.rows'})
    return {'status':'pass' if not errs else 'blocked','errors':errs,'run_id':RUN_ID,'source_id':SOURCE,'targets':TARGETS,'manifest_sha256':manifest_hash(rd),'staging_candidate_sha256':candidate_hash(rd),'classification':'historical_evidence_snapshot','freshness':'eod_batch_not_current_realtime','receipt_audit': rec.get('authorization_consumed') is True}
def forbid_path(path):
    s=str(path).replace('\\','/')
    return any(s.startswith(p) or ('/'+p) in s for p in FORBID_PREFIX)
def readonly_payload_from_candidate(c):
    return {
        'schema_version':'controlled_refresh_staging_payload.v1',
        'generated_at_utc':c['retrieved_at_utc'],
        'staging_only': True,
        'operator_confirmations': {'confirm_fixture_backed': True, 'confirm_no_live_probe': True},
        'target_universe': {'mode':'bounded','scope':'watchlist','symbols': TARGETS, 'full_market_scan': False},
        'validation': {'frontend_write': False, 'full_market_scan': False, 'generated_artifact_write': False, 'network_authorized': False, 'production_write': False, 'trading_signal': False},
        'source_runs':[{'source_id':c['source_id'],'authority_level':'official','source_type':'official_openapi','request_method':'LOCAL_HISTORICAL_EVIDENCE','url_or_fixture':str(RUN_DIR/'staging_candidate.json'),'http_status':c.get('http_status'), 'contract_status':c.get('contract_status'), 'raw_evidence_ref':str(RUN_DIR/'staging_candidate.json'),'errors':[], 'source_risk_flags':['official_eod_reference_source','not_intraday_live_feed','not_realtime_guaranteed'],'retrieved_at_utc':r['retrieved_at_utc'],'source_timestamp':c['source_timestamp'],'freshness_status':'stale','delay_status':'stale','staleness_seconds':86400,'normalization_status':c['normalization_status'],'data_quality_flags':['historical_evidence_snapshot','not_current_realtime'],'normalized_sample_preview':r} for r in c['rows']]
    }

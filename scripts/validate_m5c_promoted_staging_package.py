from __future__ import annotations
import argparse,json,hashlib
from pathlib import Path
try:
    from verify_m5c_staging_manifest import verify as verify_manifest
    from validate_m5c_supplemental_audit import validate as validate_audit, AUDIT as AUDIT_PATH
    from validate_m5c_run_summary_destination_correction import validate as validate_destination_correction, CORRECTION as CORRECTION_PATH
except ModuleNotFoundError:
    from scripts.verify_m5c_staging_manifest import verify as verify_manifest
    from scripts.validate_m5c_supplemental_audit import validate as validate_audit, AUDIT as AUDIT_PATH
    from scripts.validate_m5c_run_summary_destination_correction import validate as validate_destination_correction, CORRECTION as CORRECTION_PATH
REQ=['authorization_snapshot.json','request_snapshot.json','source_binding.json','staging_payload.json','promotion_receipt.json','validation_report.json','lineage.json','evidence_ledger.json','rollback_plan.json','frontend_readonly_context_package.json','run_summary.json','sha256_manifest.json']
TARGETS=['2330','0050','00929']; TARGET_SET=set(TARGETS)
RUN='research/live_probe_runs/m5b/m5b_twse_openapi_20260627T015136Z'; DEST='research/staging/m5c/m5c_twse_openapi_20260627_authorized_01'; AUTH_ID='M5C_TWSE_OPENAPI_STAGING_PROMOTION_AUTHORIZATION_20260627_AUTHORIZED_01'
AUTH_PATH=Path('docs/authorization/decisions/M5C_TWSE_OPENAPI_STAGING_PROMOTION_AUTHORIZATION.json'); REQ_PATH=Path('docs/authorization/requests/M5C_TWSE_OPENAPI_STAGING_PROMOTION_REQUEST.json')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p): return json.loads(Path(p).read_text())
def _flag_errors(name,obj):
    errs=[]
    for k,v in {'historical_evidence_snapshot':True,'current_realtime':False,'realtime_guaranteed':False,'staging_only':True,'production_ready':False,'frontend_publication_authorized':False,'generated_artifact_write':False,'trading_signal':False}.items():
        if obj.get(k)!=v: errs.append({'code':'flag_mismatch','path':name,'field':k,'expected':v,'actual':obj.get(k)})
    return errs
def _require(obj,name,field,expected,errs):
    if field not in obj: errs.append({'code':'required_binding_missing','object':name,'field':field})
    elif obj.get(field)!=expected: errs.append({'code':'binding_value_mismatch','object':name,'field':field,'expected':expected,'actual':obj.get(field)})
def validate_core_package(d, allowed_consumption_statuses=None):
    d=Path(d); errs=[]
    for n in REQ:
        if not (d/n).exists(): errs.append({'code':'missing_artifact','path':n})
    if errs: return errs
    errs += verify_manifest(d)
    docs={n:load(d/n) for n in REQ}
    for n,o in docs.items(): errs += _flag_errors(n,o)
    auth_snap=docs['authorization_snapshot.json']; req_snap=docs['request_snapshot.json']; auth=auth_snap.get('authorization',{}); req=req_snap.get('request',{})
    bind=docs['source_binding.json']; line=docs['lineage.json']; rec=docs['promotion_receipt.json']
    canonical_auth=load(AUTH_PATH); canonical_req=load(REQ_PATH)
    if auth != canonical_auth: errs.append({'code':'authorization_snapshot_drift'})
    if req != canonical_req: errs.append({'code':'request_snapshot_drift'})
    expected_manifest=sha(Path(RUN)/'sha256_manifest.json'); expected_candidate=sha(Path(RUN)/'staging_candidate.json'); expected_auth_sha=sha(AUTH_PATH); expected_req_sha=sha(REQ_PATH)
    for n,o in docs.items():
        if n == 'frontend_readonly_context_package.json':
            continue
        _require(o,n,'authorization_id',AUTH_ID,errs); _require(o,n,'source_run_dir',RUN,errs)
        if o.get('targets') != TARGETS: errs.append({'code':'artifact_targets_mismatch','path':n,'actual':o.get('targets')})
    _require(auth,'authorization','authorization_id',AUTH_ID,errs); _require(auth,'authorization','destination',DEST,errs); _require(auth,'authorization','source_id','TWSE_OpenAPI',errs)
    if auth.get('targets')!=TARGETS: errs.append({'code':'authorization_targets_mismatch'})
    _require(req,'request','source_run_dir',RUN,errs); _require(req,'request','source_id','TWSE_OpenAPI',errs)
    if req.get('targets')!=TARGETS: errs.append({'code':'request_targets_mismatch','actual':req.get('targets')})
    _require(bind,'source_binding','source_run_dir',RUN,errs); _require(bind,'source_binding','source_run_id','m5b_twse_openapi_20260627T015136Z',errs)
    if bind.get('source_id','TWSE_OpenAPI')!='TWSE_OpenAPI': errs.append({'code':'source_binding_source_id_mismatch'})
    _require(auth,'authorization','source_manifest_sha256',expected_manifest,errs); _require(auth,'authorization','staging_candidate_sha256',expected_candidate,errs)
    _require(bind,'source_binding','source_manifest_sha256',expected_manifest,errs); _require(bind,'source_binding','staging_candidate_sha256',expected_candidate,errs)
    _require(line,'lineage','m5b_manifest_sha256',expected_manifest,errs); _require(line,'lineage','m5b_candidate_sha256',expected_candidate,errs)
    _require(line,'lineage','m5c_authorization_sha256',expected_auth_sha,errs); _require(line,'lineage','m5c_request_sha256',expected_req_sha,errs)
    if rec.get('actual_staging_promotion_performed') is not True: errs.append({'code':'promotion_not_performed'})
    _require(rec,'promotion_receipt','destination',DEST,errs)
    run_destination=docs['run_summary.json'].get('destination')
    if run_destination != DEST: errs.append({'code':'run_summary_destination_requires_review_correction','actual':run_destination})
    cp=Path(rec.get('consumption_record',''))
    if not cp.exists(): errs.append({'code':'consumption_record_missing','path':str(cp)})
    else:
        c=load(cp)
        if c.get('authorization_id')!=AUTH_ID or c.get('destination')!=DEST: errs.append({'code':'consumption_record_mismatch'})
        status=c.get('status')
        if status is None: pass
        elif status not in (allowed_consumption_statuses or {'succeeded'}): errs.append({'code':'consumption_status_not_succeeded','actual':status})
    payload=docs['staging_payload.json']; rows=payload.get('rows',[]); syms=[str(r.get('symbol')) for r in rows]
    if set(syms)!=TARGET_SET or len(syms)!=len(set(syms)): errs.append({'code':'target_uniqueness_failed'})
    if any(r.get('source')!='TWSE_OpenAPI' for r in rows): errs.append({'code':'source_mismatch'})
    if payload.get('full_market_payload_retained') is not False: errs.append({'code':'raw_full_market_payload_forbidden'})
    forbidden={'buy','sell','hold','ranking','target_price','recommendation','current_market_state'}
    def walk(x):
        if isinstance(x,dict):
            for k,v in x.items():
                if str(k).lower() in forbidden: return True
                if walk(v): return True
        elif isinstance(x,list): return any(walk(i) for i in x)
        return False
    if any(walk(docs[n]) for n in REQ): errs.append({'code':'forbidden_field_present'})
    return errs
def validate_reviewed_canonical_package(d, allowed_consumption_statuses=None):
    d=Path(d); errs=validate_core_package(d, allowed_consumption_statuses)
    errs += validate_audit(AUDIT_PATH, d)
    docs={}
    if all((d/n).exists() for n in REQ): docs={n:load(d/n) for n in REQ}
    if docs and docs['run_summary.json'].get('destination') != DEST:
        correction_errors=validate_destination_correction(CORRECTION_PATH, d)
        if correction_errors:
            errs.append({'code':'run_summary_destination_mismatch_without_valid_correction','actual':docs['run_summary.json'].get('destination'),'errors':correction_errors})
        else:
            errs=[e for e in errs if e.get('code')!='run_summary_destination_requires_review_correction']
    if docs:
        cp=Path(docs['promotion_receipt.json'].get('consumption_record',''))
        if cp.exists():
            c=load(cp)
            if c.get('status') is None:
                audit=load(AUDIT_PATH)
                if audit.get('promotion_status')!='already_performed_once_not_refinalized': errs.append({'code':'legacy_consumption_status_missing_without_audit_exemption'})
    return errs
validate=validate_reviewed_canonical_package
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--package-dir',required=True); ns=ap.parse_args(argv)
    errs=validate_reviewed_canonical_package(ns.package_dir); print(json.dumps({'status':'pass' if not errs else 'blocked','errors':errs},indent=2,sort_keys=True)); return 0 if not errs else 1
if __name__=='__main__': raise SystemExit(main())

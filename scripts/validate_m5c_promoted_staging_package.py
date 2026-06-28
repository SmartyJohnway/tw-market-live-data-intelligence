from __future__ import annotations
import argparse,json,hashlib
from pathlib import Path
try:
    from verify_m5c_staging_manifest import verify as verify_manifest
except ModuleNotFoundError:
    from scripts.verify_m5c_staging_manifest import verify as verify_manifest
REQ=['authorization_snapshot.json','request_snapshot.json','source_binding.json','staging_payload.json','promotion_receipt.json','validation_report.json','lineage.json','evidence_ledger.json','rollback_plan.json','frontend_readonly_context_package.json','run_summary.json','sha256_manifest.json']
TARGETS={'2330','0050','00929'}
RUN='research/live_probe_runs/m5b/m5b_twse_openapi_20260627T015136Z'
DEST='research/staging/m5c/m5c_twse_openapi_20260627_authorized_01'
AUTH_ID='M5C_TWSE_OPENAPI_STAGING_PROMOTION_AUTHORIZATION_20260627_AUTHORIZED_01'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p): return json.loads(Path(p).read_text())
def _flag_errors(name,obj):
    errs=[]
    for k,v in {'historical_evidence_snapshot':True,'current_realtime':False,'realtime_guaranteed':False,'staging_only':True,'production_ready':False,'frontend_publication_authorized':False,'generated_artifact_write':False,'trading_signal':False}.items():
        if obj.get(k)!=v: errs.append({'code':'flag_mismatch','path':name,'field':k,'expected':v,'actual':obj.get(k)})
    return errs
def validate(d):
    d=Path(d); errs=[]
    for n in REQ:
        if not (d/n).exists(): errs.append({'code':'missing_artifact','path':n})
    if errs: return errs
    errs += verify_manifest(d)
    docs={n:load(d/n) for n in REQ}
    for n,o in docs.items(): errs += _flag_errors(n,o)
    auth=docs['authorization_snapshot.json'].get('authorization',{})
    req=docs['request_snapshot.json'].get('request',{})
    bind=docs['source_binding.json']; line=docs['lineage.json']; rec=docs['promotion_receipt.json']
    if auth.get('authorization_id')!=AUTH_ID: errs.append({'code':'authorization_id_mismatch'})
    if auth.get('destination')!=DEST or str(d)!=DEST: errs.append({'code':'destination_mismatch','authorization':auth.get('destination'),'package_dir':str(d)})
    if auth.get('targets')!=['2330','0050','00929']: errs.append({'code':'authorization_targets_mismatch'})
    if req.get('source_run_dir')!=RUN or req.get('source_id')!='TWSE_OpenAPI': errs.append({'code':'request_source_binding_mismatch'})
    if bind.get('source_run_dir')!=RUN or bind.get('source_run_id')!='m5b_twse_openapi_20260627T015136Z': errs.append({'code':'source_binding_run_mismatch'})
    expected_manifest=sha(Path(RUN)/'sha256_manifest.json'); expected_candidate=sha(Path(RUN)/'staging_candidate.json')
    for obj,name in [(auth,'authorization'),(bind,'source_binding'),(line,'lineage')]:
        if obj.get('source_manifest_sha256') and obj.get('source_manifest_sha256')!=expected_manifest: errs.append({'code':'source_manifest_hash_mismatch','object':name})
        if obj.get('staging_candidate_sha256') and obj.get('staging_candidate_sha256')!=expected_candidate: errs.append({'code':'candidate_hash_mismatch','object':name})
    if line.get('m5b_manifest_sha256')!=expected_manifest or line.get('m5b_candidate_sha256')!=expected_candidate: errs.append({'code':'lineage_hash_mismatch'})
    if rec.get('actual_staging_promotion_performed') is not True: errs.append({'code':'promotion_not_performed'})
    cp=Path(rec.get('consumption_record',''))
    if not cp.exists(): errs.append({'code':'consumption_record_missing','path':str(cp)})
    else:
        c=load(cp)
        if c.get('authorization_id')!=AUTH_ID or c.get('destination')!=DEST: errs.append({'code':'consumption_record_mismatch'})
    payload=docs['staging_payload.json']; rows=payload.get('rows',[]); syms=[str(r.get('symbol')) for r in rows]
    if set(syms)!=TARGETS or len(syms)!=len(set(syms)): errs.append({'code':'target_uniqueness_failed'})
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
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--package-dir',required=True); ns=ap.parse_args(argv)
    errs=validate(ns.package_dir); print(json.dumps({'status':'pass' if not errs else 'blocked','errors':errs},indent=2,sort_keys=True)); return 0 if not errs else 1
if __name__=='__main__': raise SystemExit(main())

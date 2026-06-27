from __future__ import annotations
import argparse, json, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path
import requests
try:
    from scripts.validate_m5b_execution_authorization import validate_authorization, sha256_file
except ModuleNotFoundError:
    from validate_m5b_execution_authorization import validate_authorization, sha256_file
try:
    from scripts.probe_twse_openapi import normalize_twse_openapi_row
except ModuleNotFoundError:
    from probe_twse_openapi import normalize_twse_openapi_row
ALLOWED_TARGETS=['2330','0050','00929']; ROOT=Path('research/live_probe_runs/m5b'); URL='https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL'

def classify_retryable_failure(status=None, exc=None): return bool(exc) or status==429 or (status is not None and 500<=status<=599)
def validate_execution_scope(source, targets, output_dir):
    errors=[]; p=Path(output_dir)
    if source!='TWSE_OpenAPI': errors.append({'code':'source_mismatch','path':'$.source'})
    if not targets: errors.append({'code':'targets_empty','path':'$.targets'})
    if any(t in ('*','ALL','all') for t in targets): errors.append({'code':'wildcard_target','path':'$.targets'})
    if len(targets)!=len(set(targets)): errors.append({'code':'duplicate_targets','path':'$.targets'})
    if sorted(targets)!=sorted(ALLOWED_TARGETS): errors.append({'code':'target_set_mismatch','path':'$.targets'})
    if p.is_absolute() or '..' in p.parts: errors.append({'code':'output_path_unsafe','path':'$.output_dir'})
    try: p.relative_to(ROOT)
    except Exception: errors.append({'code':'output_outside_m5b','path':'$.output_dir'})
    return errors
def bind_request_and_authorization(auth, request): return {'request_sha256':sha256_file(request),'authorization_sha256':sha256_file(auth)}
def map_authorized_targets(targets): return {t:t for t in targets}
def redact_and_bound_response(data, targets): return [r for r in data if str(r.get('Code','')).strip() in targets]
def status_for(rows, failed, http):
    if http != 200: return 'http_failed'
    if not rows: return 'source_empty'
    return 'normalized_pass' if not failed and len(rows)==3 else 'partial_pass'
def build_execution_receipt(run_id, auth, attempts, retry_reason, http_status, success):
    a=json.loads(Path(auth).read_text())
    return {'run_id':run_id,'authorization_id':a['authorization_id'],'authorization_consumed':True,'source_id':'TWSE_OpenAPI','requested_targets':ALLOWED_TARGETS,'retained_targets':[],'retrieved_at_utc':datetime.now(timezone.utc).isoformat(),'http_status':http_status,'attempt_count':attempts,'retry_reason':retry_reason,'success':success,'production_current_state':False,'realtime_guaranteed':False,'trading_signal':False,'generated_artifact_promoted':False,'frontend_published':False}
def common_art(run_id, targets, retained, http, contract, errors):
    return {'run_id':run_id,'source_id':'TWSE_OpenAPI','requested_targets':targets,'retained_targets':retained,'retrieved_at_utc':datetime.now(timezone.utc).isoformat(),'source_timestamp':None,'http_status':http,'contract_status':contract,'parse_status':'parsed' if http==200 else 'not_parsed','normalization_status':'normalized' if retained else 'empty','failed_targets':[t for t in targets if t not in retained],'errors':errors,'caveats':['official_eod_reference_source','not_realtime_guaranteed','not_production_current_state','no_full_raw_payload_retained'],'production_current_state':False,'realtime_guaranteed':False,'trading_signal':False,'generated_artifact_promoted':False,'frontend_published':False}
def write_json(p,o): p.write_text(json.dumps(o,indent=2,ensure_ascii=False,sort_keys=True)+"\n")
def write_artifacts(out, auth, req, attempts, retry_reason, http_status, rows, errors):
    out.mkdir(parents=True,exist_ok=False); run_id=out.name; retained=[r['symbol'] for r in rows]; contract=status_for(rows,[t for t in ALLOWED_TARGETS if t not in retained],http_status)
    shutil.copyfile(auth,out/'authorization_snapshot.json'); shutil.copyfile(req,out/'request_snapshot.json')
    receipt=build_execution_receipt(run_id,auth,attempts,retry_reason,http_status,contract in ('normalized_pass','partial_pass')); receipt.update({'retained_targets':retained,'contract_status':contract})
    write_json(out/'execution_receipt.json',receipt)
    base=common_art(run_id,ALLOWED_TARGETS,retained,http_status,contract,errors)
    result={**base,'rows':rows}; write_json(out/'bounded_probe_result.json',result); write_json(out/'bounded_normalized_rows.json',{**base,'rows':rows})
    write_json(out/'source_contract_assessment.json',{**base,'endpoint':URL,'request_method':'GET','required_headers':{'Accept':'application/json'},'required_cookies_or_session':False,'raw_full_response_retention':False,'legal_maintenance_risk':'official public OpenAPI; schema drift/rate limits possible','ai_integration_suitability':'bounded EOD/reference integration only'})
    write_json(out/'freshness_delay_assessment.json',{**base,'freshness_status':'eod_reference','delay_status':'not_realtime_guaranteed','official_realtime_claim':False})
    ledger={**base,'artifacts':[]}; write_json(out/'evidence_ledger.json',ledger)
    summary={**base,'live_probe_executed':True,'live_probe_succeeded':contract in ('normalized_pass','partial_pass'),'staging_candidate_created':False,'production_promotion_performed':False,'generated_artifacts_refreshed':False,'frontend_published':False,'trading_output_produced':False,'authorization_consumed':True,'retry_count':attempts-1,'endpoint':URL}
    write_json(out/'run_summary.json',summary)
    manifest={}
    for f in sorted(out.glob('*.json')):
        if f.name!='sha256_manifest.json': manifest[f.name]=hashlib.sha256(f.read_bytes()).hexdigest()
    write_json(out/'sha256_manifest.json',{**base,'manifest':manifest,'manifest_status':'pass'})

def execute(args):
    attempts=0; retry_reason=None; last_status=None; last_exc=None; data=None
    while attempts < 2:
        attempts += 1
        try:
            resp=requests.get(URL,headers={'Accept':'application/json'},timeout=10); last_status=resp.status_code
            if resp.status_code==200: data=resp.json(); break
            if not classify_retryable_failure(resp.status_code): break
            retry_reason=f'HTTP {resp.status_code}'
        except (requests.Timeout, requests.ConnectionError) as e:
            last_exc=e; retry_reason=type(e).__name__
        if attempts>=2: break
    errors=[] if data is not None else [{'code':'network_or_http_failed','detail':str(last_exc) if last_exc else f'HTTP {last_status}'}]
    bounded=redact_and_bound_response(data if isinstance(data,list) else [], ALLOWED_TARGETS)
    now=datetime.now(timezone.utc); rows=[]
    for raw in bounded:
        n=normalize_twse_openapi_row(raw,now); n.pop('raw_row',None); n.pop('unmapped_raw_fields',None); rows.append(n)
    if any(r['symbol'] not in ALLOWED_TARGETS for r in rows): errors.append({'code':'unauthorized_symbol_in_result'}) ; rows=[r for r in rows if r['symbol'] in ALLOWED_TARGETS]
    write_artifacts(Path(args.output_dir), args.authorization, args.request, attempts, retry_reason, last_status, rows, errors)
    print(json.dumps({'ok':True,'run_id':Path(args.output_dir).name,'attempt_count':attempts,'retry_reason':retry_reason,'http_status':last_status,'retained_targets':[r['symbol'] for r in rows],'network_used':True},indent=2,sort_keys=True)); return 0

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument('--check-only',action='store_true'); p.add_argument('--execute-live',action='store_true'); p.add_argument('--acknowledge-bounded-live-probe',action='store_true'); p.add_argument('--authorization'); p.add_argument('--request'); p.add_argument('--source',required=True); p.add_argument('--targets',nargs='+',required=True); p.add_argument('--output-dir',required=True); p.add_argument('--attempt-count',type=int,default=2)
    a=p.parse_args(argv); errors=validate_execution_scope(a.source,a.targets,a.output_dir)
    if a.attempt_count>2: errors.append({'code':'attempt_count_too_high','path':'$.attempt_count'})
    if not a.authorization: errors.append({'code':'missing_authorization','path':'$.authorization'})
    if not a.request: errors.append({'code':'missing_request','path':'$.request'})
    if a.authorization and a.request: errors += validate_authorization(a.authorization,a.request)
    if a.execute_live and not a.acknowledge_bounded_live_probe: errors.append({'code':'missing_acknowledgement','path':'$.acknowledgement'})
    if Path(a.output_dir,'execution_receipt.json').exists(): errors.append({'code':'reused_authorization_receipt','path':'$.output_dir'})
    if a.check_only or not a.execute_live or errors:
        print(json.dumps({'ok':not errors,'errors':errors,'network_used':False,'writes':False,'execution_performed':False},indent=2,sort_keys=True)); return 0 if not errors else 1
    return execute(a)
if __name__=='__main__': raise SystemExit(main())

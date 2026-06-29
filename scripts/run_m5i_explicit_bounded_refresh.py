#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys, urllib.request
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.m5i_common import *
from scripts.validate_m5i_refresh_candidate import validate_candidate

URL='https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL'

def parse_twse_rows(data, targets, retrieved_at):
    by={str(r.get('Code') or r.get('code') or r.get('證券代號') or '').strip():r for r in data if isinstance(r,dict)}
    rows=[]; failures=[]
    for t in targets:
        r=by.get(t)
        if not r:
            failures.append({'symbol':t,'status':'missing_from_source'}); continue
        price_raw=r.get('ClosingPrice') or r.get('收盤價') or r.get('close')
        if price_raw is None or str(price_raw).strip() == '':
            failures.append({'symbol':t,'status':'missing_close_price'}); continue
        try:
            price=float(str(price_raw).replace(',',''))
        except Exception:
            failures.append({'symbol':t,'status':'unparsable_close_price'}); continue

        date=str(r.get('Date') or r.get('date') or retrieved_at[:10])
        rows.append({'symbol':t,'price_like_value':price,'source_id':SOURCE,'source_authority':'official','source_timestamp':date,'retrieved_at':retrieved_at,'freshness_status':'stale','delay_status':'eod_batch','display_caveats':['official_eod_reference_source','not_realtime_guaranteed','freshness_must_be_displayed'],'source_risk_flags':['official_eod_reference_source','not_intraday_live_feed','not_realtime_guaranteed'],'data_quality_flags':['reviewed_refresh_snapshot','not_current_realtime'],'normalization_status':'ok','price_semantics':'official_eod_close','staleness_seconds':0})
    return rows, failures

def write_candidate(out, targets, rows, failures, auth, retrieved_at):
    out.mkdir(parents=True,exist_ok=False)
    c={'schema_version':'m5i_refresh_candidate.v1','generated_at_utc':retrieved_at,'source':SOURCE,'source_date':rows[0]['source_timestamp'] if rows else retrieved_at[:10],'symbols':rows,'failed_targets':failures,'global_caveats':REQ_CAVEATS,'reviewed_refresh_snapshot':True,'current_realtime':False,'production_current_state':False,'production_ready':False,'realtime_guaranteed':False,'trading_signal':False,'readonly_only':True,'freshness_status':'stale','stale_status':'stale','badge':'historical/stale'}
    b={'schema_version':'m5i_source_binding.v1','source':SOURCE,'targets':targets,'authorization_id':auth['authorization_id'],'single_use_id':auth['single_use_id'],'retrieved_at_utc':retrieved_at,'request_method':'GET','url':URL,'bounded_refresh':True,'full_market_scan':False}
    s={'schema_version':'m5i_refresh_summary.v1','status':'candidate_created','runner_started':True,'network_calls_may_have_occurred':True,'targets':targets,'failed_targets':failures,'no_frontend_publication':True,'no_generated_refresh':True,'no_production_refresh':True,'no_trading_output':True}
    v={'schema_version':'m5i_validation_report.v1','status':'pending'}
    for name,obj in {'market-context.json':c,'source_binding.json':b,'refresh_summary.json':s,'validation_report.json':v}.items(): write_lf(out/name,dump(obj))
    man={'schema_version':'m5i_sha256_manifest.v1','files':{n:sha(out/n) for n in ['market-context.json','source_binding.json','refresh_summary.json','validation_report.json']},'manifest_final':True}
    write_lf(out/'sha256_manifest.json',dump(man))
    result=validate_candidate(out)
    v['status']='passed'; v['manifest_sha256']=result['manifest_sha256']; write_lf(out/'validation_report.json',dump(v))
    man['files']['validation_report.json']=sha(out/'validation_report.json'); write_lf(out/'sha256_manifest.json',dump(man))
    return validate_candidate(out)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--execute-refresh',action='store_true'); ap.add_argument('--authorization-token'); ap.add_argument('--source',default=SOURCE); ap.add_argument('--targets',nargs='+',default=[]); ap.add_argument('--check-only',action='store_true'); ap.add_argument('--output-dir');
    for f in ['no-frontend-publication','no-production-refresh','no-generated-refresh','no-trading-output']: ap.add_argument('--'+f,action='store_true')
    a=ap.parse_args()
    if not a.execute_refresh:
        print(dump({'status':'check_only','network_calls':False,'artifact_writes':False,'execute_mode_available':True})); return 0
    if not a.authorization_token: print('authorization required',file=sys.stderr); return 2
    auth=load(a.authorization_token); errs=validate_authorization(auth,a.targets,a.source)
    for flag in ['no_frontend_publication','no_production_refresh','no_generated_refresh','no_trading_output']:
        if getattr(a,flag) is not True: errs.append(f'cli_{flag}_required')
    if errs: print(dump({'status':'failed_closed','errors':errs,'runner_started':False,'network_calls_may_have_occurred':False}),file=sys.stderr); return 2
    claim=claim_authorization(auth)
    retrieved=now(); evidence=REPO/'research/live_probe_runs/m5i'/retrieved.replace(':','').replace('-','')
    evidence.mkdir(parents=True,exist_ok=False)
    req=urllib.request.Request(URL,headers={'User-Agent':'tw-market-m5i-explicit-bounded-refresh/1.0'})
    with urllib.request.urlopen(req,timeout=20) as resp:
        raw=resp.read(); status=resp.status
    write_lf(evidence/'raw_twse_openapi_response.json',raw.decode('utf-8','replace'))
    data=json.loads(raw.decode('utf-8'))
    rows,fail=parse_twse_rows(data,a.targets,retrieved)
    out=Path(a.output_dir) if a.output_dir else REPO/'research/staging/m5i'/('m5i_refresh_candidate_'+retrieved.replace(':','').replace('-',''))
    val=write_candidate(out,a.targets,rows,fail,auth,retrieved)
    promoted = promote_m5i_candidate_to_m5f(out)
    final_status = 'refresh_executed_and_promoted' if promoted.get('status') == 'promoted' else 'refresh_executed_but_promotion_failed'
    print(dump({'status':final_status,'candidate_dir':str(out),'evidence_dir':str(evidence),'claim_file':str(claim),'http_status':status,**val,'network_calls_may_have_occurred':True, 'promotion': promoted})); return 0
if __name__=='__main__': raise SystemExit(main())

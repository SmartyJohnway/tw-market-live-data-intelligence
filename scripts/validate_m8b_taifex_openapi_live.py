from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.m8b_taifex_openapi_execution import execute_taifex_openapi_refresh

def main():
    p=argparse.ArgumentParser(); p.add_argument('--contexts',required=True); p.add_argument('--products',default=''); p.add_argument('--contracts',default=''); p.add_argument('--session',action='append',dest='sessions'); p.add_argument('--confirm',action='store_true')
    a=p.parse_args()
    contracts=[]
    for item in filter(None,a.contracts.split(',')):
        parts=item.split(':'); d={}
        if len(parts)>0: d['contract_month']=parts[0]
        if len(parts)>1: d['strike_price']=parts[1]
        if len(parts)>2: d['option_type']=parts[2]
        contracts.append(d)
    res=execute_taifex_openapi_refresh(operator_confirmed=a.confirm, requested_contexts=[x for x in a.contexts.split(',') if x], requested_products=[x for x in a.products.split(',') if x], requested_contracts=contracts, requested_sessions=a.sessions)
    head=subprocess.run(['git','rev-parse','HEAD'],capture_output=True,text=True).stdout.strip()
    summary={"evaluation_timestamp":res.get('started_at_utc'),"head":head,"requested_contexts":res.get('requested_contexts'),"requested_products":res.get('requested_products'),"overall_status":res.get('overall_status'),"raw_payload_retained":False,"endpoints":{}}
    for k,v in res.get('endpoint_results',{}).items():
        obs=v.get('observations',[])
        summary['endpoints'][k]={"endpoint_fetch_status":v.get('batch_status'),"endpoint_row_count":v.get('row_count_received'),"retained_row_count":v.get('row_count_retained'),"reported_trade_dates":v.get('reported_trade_dates'),"currentness_statuses":sorted({(o.get('currentness') or {}).get('status') for o in obs}),"session_labels_observed":sorted({o.get('source_session_label') for o in obs if o.get('source_session_label')}),"quotation_unit_caveats":sorted({c for o in obs for c in o.get('caveats',[]) if 'quotation' in c}),"sample_retained_observation":obs[0] if obs else None}
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__': main()

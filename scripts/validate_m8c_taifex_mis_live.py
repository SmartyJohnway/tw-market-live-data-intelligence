#!/usr/bin/env python
from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.m8c_taifex_mis_execution import execute_taifex_mis_snapshot

def compact_validation_summary(res):
    compact=json.loads(json.dumps(res, default=str))
    for obs in compact.get('observations',[]):
        obs.pop('normalized_field_candidates', None)
        obs.pop('field_provenance', None)
        obs['quote_values_retained']=False
    return compact

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument('--contracts-json'); p.add_argument('--auto-smoke',action='store_true'); p.add_argument('--confirm',action='store_true'); p.add_argument('--pretty',action='store_true'); a=p.parse_args(argv)
    if a.contracts_json: contracts=json.loads(a.contracts_json)
    elif a.auto_smoke: contracts=[{'instrument_type':'future','requested_product_id':'TX','contract_month_or_week':'202607','session':'regular'}]
    else: contracts=[]
    res=execute_taifex_mis_snapshot(operator_confirmed=a.confirm, requested_contracts=contracts, calendar_context={'authority':'operator_validator'})
    res['tested_head_sha']=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    res['raw_payload_retained']=False; res['cookies_retained']=False; res['sockjs_session_ids_retained']=False
    summary=compact_validation_summary(res)
    if a.confirm:
        out=Path('research/probe_runs/m8c_01_taifex_mis_runtime/m8c_01_bounded_live_validation_summary.json'); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(summary,indent=2,default=str),encoding='utf-8')
    print(json.dumps(summary,indent=2 if a.pretty else None,default=str)); return 0
if __name__=='__main__': raise SystemExit(main())

#!/usr/bin/env python
from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import requests
from scripts.m8c_taifex_mis_execution import execute_taifex_mis_snapshot
from scripts.m8c_taifex_mis_limits import RuntimeBudget
from scripts.m8c_taifex_mis_rest_client import TaifexMisRestClient

def compact_validation_summary(res):
    compact=json.loads(json.dumps(res, default=str))
    for obs in compact.get('observations',[]):
        obs.pop('normalized_field_candidates', None); obs.pop('field_provenance', None); obs['quote_values_retained']=False
    return compact

def _first_month(rest, cid, symtype):
    rows=rest.months(cid,'0',symtype)
    for r in rows:
        m=str(r.get('item') or '')
        if len(m)==6 and m.isdigit(): return m
    raise RuntimeError(f'no_month_for_{cid}')

ACCOUNTING_KEYS=('rest_request_payload_bytes','sockjs_send_payload_bytes','response_payload_bytes','total_accounted_payload_bytes','rest_rows','frames','decoded_messages','selectors','products','months','strikes','symbols','retained_observations')

def _budget_accounting(budget):
    return {k:getattr(budget,k) for k in ACCOUNTING_KEYS}

def _combine_accounting(a,b):
    return {k:(a or {}).get(k,0)+(b or {}).get(k,0) for k in ACCOUNTING_KEYS}

def build_auto_smoke_contracts():
    session=requests.Session()
    discovery_budget=RuntimeBudget(max_total_execution_seconds=10, max_accounted_payload_bytes=1_000_000)
    try:
        rest=TaifexMisRestClient(session, discovery_budget)
        txm=_first_month(rest,'TXF','F'); mtxm=_first_month(rest,'MXF','F'); txom=_first_month(rest,'TXO','O')
        chain=rest.option_chain('TXO', txom)
        opt=next((r for r in chain if str(r.get('SymbolID','')).endswith('-O') and r.get('StrikePrice') not in (None,'') and str(r.get('CP','')).upper().startswith(('C','P'))), None)
        if not opt: raise RuntimeError('no_bounded_txo_option_row')
        contracts=[
            {'instrument_type':'future','requested_product_id':'TX','contract_month_or_week':txm,'session':'regular'},
            {'instrument_type':'future','requested_product_id':'MTX','contract_month_or_week':mtxm,'session':'regular'},
            {'instrument_type':'option','requested_product_id':'TXO','contract_month_or_week':txom,'strike_price':str(opt['StrikePrice']),'option_type':'call' if str(opt['CP']).upper().startswith('C') else 'put','session':'regular'},
        ]
        return contracts, _budget_accounting(discovery_budget)
    finally:
        session.close()

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument('--contracts-json'); p.add_argument('--auto-smoke',action='store_true'); p.add_argument('--confirm',action='store_true'); p.add_argument('--pretty',action='store_true'); a=p.parse_args(argv)
    discovery_accounting={}
    if a.contracts_json: contracts=json.loads(a.contracts_json)
    elif a.auto_smoke and a.confirm: contracts, discovery_accounting=build_auto_smoke_contracts()
    elif a.auto_smoke: contracts=[]
    else: contracts=[]
    runtime_payload_limit=1_000_000 if discovery_accounting else 2_000_000
    res=execute_taifex_mis_snapshot(operator_confirmed=a.confirm, requested_contracts=contracts, calendar_context={'authority':'operator_validator'}, max_accounted_payload_bytes=runtime_payload_limit)
    res['tested_head_sha']=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(); res['auto_smoke_contracts']=contracts
    res['selector_discovery_accounting']=discovery_accounting
    res['runtime_execution_accounting']=res.get('accounting',{})
    res['combined_validator_accounting']=_combine_accounting(discovery_accounting, res.get('accounting',{}))
    res['combined_validator_hard_bounds']={'max_accounted_payload_bytes':2_000_000,'discovery_payload_cap':1_000_000 if discovery_accounting else 0,'runtime_payload_cap':runtime_payload_limit}
    res['raw_payload_retained']=False; res['cookies_retained']=False; res['sockjs_session_ids_retained']=False
    summary=compact_validation_summary(res)
    if a.confirm:
        out=Path('research/probe_runs/m8c_01_taifex_mis_runtime/m8c_01_bounded_live_validation_summary.json'); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(summary,indent=2,default=str),encoding='utf-8')
    print(json.dumps(summary,indent=2 if a.pretty else None,default=str)); return 0
if __name__=='__main__': raise SystemExit(main())

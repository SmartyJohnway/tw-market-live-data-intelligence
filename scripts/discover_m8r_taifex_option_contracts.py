#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, re, sys
import requests
from datetime import datetime, timezone
from pathlib import Path
from decimal import Decimal, InvalidOperation
from typing import Any
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.m8c_taifex_mis_contracts import validate_selectors
from scripts.m8c_taifex_mis_limits import RuntimeBudget
from scripts.m8c_taifex_mis_rest_client import TaifexMisRestClient
from scripts.m8c_taifex_mis_identity_resolver import resolve_identity_results, _cp_enum, _dec
from scripts.m8b_taifex_openapi_execution import execute_taifex_openapi_refresh

SCHEMA_VERSION="m8r_taifex_option_contract_discovery.v1"
RUN_ID_RE=re.compile(r"^[A-Za-z0-9_.=-]+$")

def now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def safe_root(root:str)->Path:
    p=Path(root)
    if not root or p.is_absolute() or '..' in p.parts: raise SystemExit('bounded artifact root must be relative and normalized')
    if str(p).startswith(('frontend/public','research/generated')): raise SystemExit('forbidden artifact root')
    return p

def norm_strike(v:Any)->str|None:
    try: return format(Decimal(str(v).replace(',','')).normalize(),'f')
    except (InvalidOperation, ValueError, AttributeError): return None

def cp(v:Any)->str|None:
    t=str(v or '').strip().lower()
    if t in {'c','call','買權'}: return 'C'
    if t in {'p','put','賣權'}: return 'P'
    return None

def identity(strike, call_put, product, underlying, expiry, session, source):
    return {'strike':str(strike),'call_put':call_put,'product':product,'underlying':underlying,'expiry':expiry,'session':session,'source_evidence':[source]}

def discover_mis(product:str, underlying:str, expiry:str, session:str)->dict[str,Any]:
    # Bounded by one explicitly requested product/month/session option chain. No raw rows retained.
    budget=RuntimeBudget()
    rest=TaifexMisRestClient(requests.Session(), budget=budget)
    sel={'instrument_type':'option','requested_product_id':product,'contract_month_or_week':expiry,'session':session,'strike_price':'1','option_type':'call'}
    validated=validate_selectors([sel], budget=budget)[0]
    cid='TXO' if product=='TXO' else product
    rows=rest.option_chain(cid, expiry)
    ids=[]
    for row in rows:
        if not str(row.get('SymbolID','')).endswith('-O'): continue
        s=norm_strike(row.get('StrikePrice'))
        c=_cp_enum(row.get('CP')) or cp(row.get('CP'))
        if s and c: ids.append(identity(s,c,product,underlying,expiry,session,'TAIFEX_MIS'))
    return {'status':'succeeded','contract_count':len(ids),'exact_contract_identities':ids,'network_request_count':1}

def discover_openapi(product:str, underlying:str, expiry:str, session:str)->dict[str,Any]:
    selector={'instrument_type':'option','requested_product_id':product,'contract_month_or_week':expiry,'session':session}
    result=execute_taifex_openapi_refresh(operator_confirmed=True, requested_contexts=['options_eod'], requested_products=[product], requested_contracts=[selector], requested_sessions=[session])
    ids=[]
    for obs in result.get('observations') or []:
        ci=obs.get('contract_identity') or (obs.get('safe_fields') or {}).get('contract_identity') or {}
        prod=ci.get('product_id') or obs.get('product_id') or obs.get('symbol')
        exp=ci.get('contract_month_or_week') or ci.get('contract_month')
        if prod!=product or str(exp)!=expiry: continue
        s=norm_strike(ci.get('strike_price'))
        c=cp(ci.get('option_type'))
        sess=ci.get('session') or session
        if s and c and sess==session: ids.append(identity(s,c,product,underlying,expiry,session,'TAIFEX_OPENAPI'))
    return {'status':'succeeded' if result.get('status')!='blocked' else 'blocked','contract_count':len(ids),'exact_contract_identities':ids,'network_request_count':result.get('network_request_count')}

def merge_identities(results):
    merged={}
    for source,res in results.items():
        for item in res.get('exact_contract_identities') or []:
            key=(item['strike'],item['call_put'],item['product'],item['underlying'],item['expiry'],item['session'])
            base=merged.setdefault(key,{k:item[k] for k in ['strike','call_put','product','underlying','expiry','session']}|{'source_evidence':[]})
            for ev in item.get('source_evidence',[]):
                if ev not in base['source_evidence']: base['source_evidence'].append(ev)
    return sorted(merged.values(), key=lambda x:(Decimal(x['strike']), x['call_put']))

def build_discovery(*, discovery_id, product, underlying, expiry, session, source_families):
    results={}; attempted=[]
    if 'TAIFEX_MIS' in source_families:
        attempted.append('TAIFEX_MIS')
        try: results['TAIFEX_MIS']=discover_mis(product,underlying,expiry,session)
        except Exception as exc: results['TAIFEX_MIS']={'status':'failed','failure_reason':type(exc).__name__,'contract_count':0,'exact_contract_identities':[]}
    if 'TAIFEX_OPENAPI' in source_families:
        attempted.append('TAIFEX_OPENAPI')
        try: results['TAIFEX_OPENAPI']=discover_openapi(product,underlying,expiry,session)
        except Exception as exc: results['TAIFEX_OPENAPI']={'status':'failed','failure_reason':type(exc).__name__,'contract_count':0,'exact_contract_identities':[]}
    exact=merge_identities(results)
    strikes=[Decimal(x['strike']) for x in exact]
    return {'schema_version':SCHEMA_VERSION,'discovery_id':discovery_id,'created_at_utc':now(),'product':product,'underlying':underlying,'expiry':expiry,'session':session,'sources_attempted':attempted,'source_results':{k:{kk:vv for kk,vv in v.items() if kk!='exact_contract_identities'} for k,v in results.items()},'exact_contract_identities':exact,'contract_count':len(exact),'strike_min':format(min(strikes),'f') if strikes else None,'strike_max':format(max(strikes),'f') if strikes else None,'raw_payload_retained':False,'operator_selection_required':True}

def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument('--product', required=True); ap.add_argument('--underlying', required=True); ap.add_argument('--expiry', required=True); ap.add_argument('--session', required=True, choices=['regular'])
    ap.add_argument('--source-family', action='append', choices=['TAIFEX_MIS','TAIFEX_OPENAPI'], required=True)
    ap.add_argument('--operator-confirmed', action='store_true'); ap.add_argument('--allow-network', action='store_true')
    ap.add_argument('--artifact-root', required=True); ap.add_argument('--discovery-id')
    args=ap.parse_args(argv)
    if not args.operator_confirmed or not args.allow_network: raise SystemExit('requires --operator-confirmed and --allow-network')
    if not re.fullmatch(r'\d{6}', args.expiry): raise SystemExit('explicit YYYYMM expiry required')
    did=args.discovery_id or 'm8r02b-f1-discovery-'+now().replace(':','').replace('-','')
    if not RUN_ID_RE.fullmatch(did): raise SystemExit('invalid discovery id')
    artifact=build_discovery(discovery_id=did, product=args.product.upper(), underlying=args.underlying.upper(), expiry=args.expiry, session=args.session, source_families=args.source_family)
    root=safe_root(args.artifact_root); root.mkdir(parents=True, exist_ok=True)
    path=root/'taifex_option_contract_discovery.json'
    path.write_text(json.dumps(artifact,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'written','path':str(path),'contract_count':artifact['contract_count'],'operator_selection_required':True},ensure_ascii=False))
if __name__=='__main__': main()

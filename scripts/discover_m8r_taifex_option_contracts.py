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
from scripts.m8b_taifex_openapi_client import fetch_endpoint, TaifexOpenApiError
from scripts.m8b_taifex_derivatives_observation import validate_required_fields, validate_contract_month, map_call_put, map_session

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
    status='succeeded' if ids else 'no_matching_scope'
    return _source_result(status, contract_count=len(ids), reason_code=None if ids else 'no_matching_contract_identity') | {'exact_contract_identities':ids}

def _source_result(status: str, *, network_request_count: int = 1, contract_count: int = 0, reason_code: str | None = None, **extra) -> dict[str, Any]:
    return {"status": status, "network_request_count": network_request_count, "contract_count": contract_count, "reason_code": reason_code, **extra}


def discover_openapi(product:str, underlying:str, expiry:str, session:str, *, fetcher=None)->dict[str,Any]:
    # Direct bounded identity discovery over one official options EOD endpoint call.
    # Retains only normalized contract identities and aggregate counts; no prices, volume, OI, bid/ask, headers, cookies, tokens, or raw rows.
    try:
        data=(fetcher or fetch_endpoint)("DailyMarketReportOpt")
    except TaifexOpenApiError as exc:
        status = "source_unavailable" if exc.status in {"source_unavailable", "source_error"} else "failed"
        return _source_result(status, reason_code=exc.status) | {"exact_contract_identities": []}
    except Exception as exc:
        return _source_result("source_unavailable", reason_code=type(exc).__name__) | {"exact_contract_identities": []}
    rows=data if isinstance(data,list) else data.get("rows",[]) if isinstance(data,dict) else []
    if not isinstance(rows, list):
        return _source_result("failed", reason_code="schema_drift", row_count_received=0, schema_valid_row_count=0, matching_product_month_row_count=0, matching_exact_identity_row_count=0) | {"exact_contract_identities": []}
    row_count_received=len(rows); schema_valid=0; matching_product_month=0; ids=[]; seen=set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        ok, _missing = validate_required_fields(row, ["Contract", "ContractMonth(Week)", "StrikePrice", "CallPut", "TradingSession"])
        if not ok:
            continue
        schema_valid += 1
        if str(row.get("Contract") or "").strip().upper() != product:
            continue
        cm, _cmv = validate_contract_month(row.get("ContractMonth(Week)"))
        sess, _sv, _sc = map_session(row.get("TradingSession"))
        if cm != expiry or sess != session:
            continue
        matching_product_month += 1
        strike, _stv = norm_strike(row.get("StrikePrice")), None
        opt, _opv = map_call_put(row.get("CallPut"))
        call_put = cp(opt)
        if not strike or call_put not in {"C", "P"}:
            continue
        key=(product, underlying, expiry, strike, call_put, session)
        if key in seen:
            continue
        seen.add(key)
        ids.append(identity(strike,call_put,product,underlying,expiry,session,'TAIFEX_OPENAPI'))
    status = "succeeded" if ids else "no_matching_scope"
    reason = None if ids else "no_matching_contract_identity"
    return _source_result(status, contract_count=len(ids), reason_code=reason, row_count_received=row_count_received, schema_valid_row_count=schema_valid, matching_product_month_row_count=matching_product_month, matching_exact_identity_row_count=len(ids)) | {"exact_contract_identities": ids}

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
        except Exception as exc: results['TAIFEX_MIS']=_source_result('failed', contract_count=0, reason_code=type(exc).__name__) | {'exact_contract_identities':[]}
    if 'TAIFEX_OPENAPI' in source_families:
        attempted.append('TAIFEX_OPENAPI')
        try: results['TAIFEX_OPENAPI']=discover_openapi(product,underlying,expiry,session)
        except Exception as exc: results['TAIFEX_OPENAPI']=_source_result('failed', contract_count=0, reason_code=type(exc).__name__) | {'exact_contract_identities':[]}
    exact=merge_identities(results)
    strikes=[Decimal(x['strike']) for x in exact]
    created=now()
    completed=created
    return {'schema_version':SCHEMA_VERSION,'discovery_id':discovery_id,'created_at_utc':created,'completed_at_utc':completed,'product':product,'underlying':underlying,'expiry':expiry,'session':session,'sources_attempted':attempted,'source_results':{k:{kk:vv for kk,vv in v.items() if kk!='exact_contract_identities'} for k,v in results.items()},'exact_contract_identities':exact,'contract_count':len(exact),'strike_min':format(min(strikes),'f') if strikes else None,'strike_max':format(max(strikes),'f') if strikes else None,'raw_payload_retained':False,'operator_selection_required':True}

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

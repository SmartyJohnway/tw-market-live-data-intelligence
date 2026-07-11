"""TPEx official latest EOD adapter for M8A."""
from __future__ import annotations
import json, urllib.request
from typing import Any
from scripts.m8a_official_eod_observation import create_observation, empty_adapter_result, parse_decimal_text, parse_int_text, parse_roc_yyyymmdd, utc_now
SOURCE_ID="TPEX_OPENAPI"; ENDPOINT_CONTRACT_ID="tpex_openapi_mainboard_daily_close_quotes_v1"; URL="https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes"
REQUIRED=["Date","SecuritiesCompanyCode","CompanyName","Close","Change","Open","High","Low","Average","TradingShares","TransactionAmount","TransactionNumber","LatestBidPrice","LatesAskPrice","Capitals","NextReferencePrice","NextLimitUp","NextLimitDown"]
OMITTED=["Average","LatestBidPrice","LatesAskPrice","Capitals","NextReferencePrice","NextLimitUp","NextLimitDown"]
SECURITY_MASTER={("tpex_otc","8069"):"equity",("tpex_otc","006201"):"etf",("tpex_otc","00687C"):"etn"}
def classify_instrument(market:str,symbol:str,security_master:dict|None=None)->dict:
    sm=security_master or SECURITY_MASTER; t=sm.get((market,symbol)) or sm.get(symbol) if isinstance(sm,dict) else None
    if t: return {"instrument_type":t,"classification_status":"classified","source":"security_master"}
    return {"instrument_type":"unknown","classification_status":"unclassified","source":"security_master_miss","caveat":"unclassified rows are excluded from deterministic metrics and AI context by default"}
def fetch_tpex_official_eod_json(*,timeout:int=20,url:str=URL)->tuple[list[dict],int,str]:
    req=urllib.request.Request(url,method="GET",headers={"Accept":"application/json","User-Agent":"tw-market-m8a-official-eod/1.0"})
    with urllib.request.urlopen(req,timeout=timeout) as resp: status=resp.status; ctype=resp.headers.get("Content-Type",""); body=resp.read()
    if status<200 or status>=300: raise RuntimeError(f"http_status_{status}")
    if "json" not in ctype.lower(): raise RuntimeError("wrong_content_type")
    data=json.loads(body.decode("utf-8-sig"));
    if not isinstance(data,list): raise RuntimeError("top_level_not_array")
    return data,status,ctype
def _reject(i,row,reason,fv=None): return {"row_index":i,"symbol":row.get("SecuritiesCompanyCode") if isinstance(row,dict) else None,"source_field_names":sorted(row.keys()) if isinstance(row,dict) else [],"reason_code":reason,"field_validation":fv or {}}
def parse_tpex_official_eod_rows(rows:Any,*,requested_symbols:list[str],retrieved_at_utc:str|None=None,http_status:int|None=None,security_master:dict|None=None)->dict:
    result=empty_adapter_result(SOURCE_ID,ENDPOINT_CONTRACT_ID,requested_symbols,retrieved_at_utc); result.update(http_status=http_status,source_status="success",batch_status="successful_eod_batch")
    if not isinstance(rows,list): result.update(source_status="error",batch_status="schema_drift"); return result
    req=set(map(str,requested_symbols)); seen=set(); dates=set(); result["row_count_received"]=len(rows)
    if not rows: result.update(batch_status="empty_non_trading_day"); return result
    for i,row in enumerate(rows):
        if not isinstance(row,dict): result["rejected_rows"].append(_reject(i,{},"row_not_object")); continue
        missing=[f for f in REQUIRED if f not in row]
        if missing: result["rejected_rows"].append(_reject(i,row,"missing_required_fields",{"missing":missing})); continue
        sym=str(row.get("SecuritiesCompanyCode") or "").strip();
        if sym not in req: continue
        result["row_count_examined"]+=1; trade_date,dv=parse_roc_yyyymmdd(row.get("Date")); fv={"Date":dv}; price={}; activity={}
        for src,dst in [("Open","open"),("High","high"),("Low","low"),("Close","close")]: price[dst],fv[src]=parse_decimal_text(row.get(src))
        price["change"],fv["Change"]=parse_decimal_text(row.get("Change"),allow_negative=True)
        for src,dst in [("TradingShares","trade_volume"),("TransactionAmount","trade_value"),("TransactionNumber","transaction_count")]: activity[dst],fv[src]=parse_int_text(row.get(src))
        cls=classify_instrument("tpex_otc",sym,security_master); caveats=[]
        if cls["classification_status"]=="unclassified": caveats.append(cls["caveat"])
        obs=create_observation(source_id=SOURCE_ID,endpoint_contract_id=ENDPOINT_CONTRACT_ID,market="tpex_otc",symbol=sym,name=row.get("CompanyName"),instrument_type=cls["instrument_type"],trade_date=trade_date,retrieved_at_utc=retrieved_at_utc,price=price,activity=activity,field_validation={**fv,"instrument_classification":cls},source_fields_present=[k for k in REQUIRED if k in row],omitted_source_fields=OMITTED,caveats=caveats,provenance={"source_url":URL,"request_method":"GET"})
        key=(obs["market"],obs["symbol"],obs["trade_date"])
        if key in seen: result["rejected_rows"].append(_reject(i,row,"duplicate_identity",fv)); continue
        seen.add(key); dates.add(trade_date); result["observations"].append(obs)
    result["reported_trade_dates"]=sorted(d for d in dates if d); result["row_count_retained"]=len(result["observations"]); result["row_count_rejected"]=len(result["rejected_rows"])
    if len(result["reported_trade_dates"])>1: result["batch_status"]="date_mismatch"
    elif result["row_count_rejected"] and result["observations"]: result["batch_status"]="partial_source_success"
    result["completed_at_utc"]=utc_now(); return result
def execute_tpex_official_eod_adapter(requested_symbols:list[str],*,timeout:int=20,security_master:dict|None=None)->dict:
    ts=utc_now()
    try: rows,status,ctype=fetch_tpex_official_eod_json(timeout=timeout)
    except Exception as exc:
        r=empty_adapter_result(SOURCE_ID,ENDPOINT_CONTRACT_ID,requested_symbols,ts); r.update(source_status="error",batch_status="source_error",completed_at_utc=utc_now()); r["caveats"].append(str(exc).splitlines()[0][:80]); return r
    r=parse_tpex_official_eod_rows(rows,requested_symbols=requested_symbols,retrieved_at_utc=ts,http_status=status,security_master=security_master); r["provenance"]={"source_url":URL,"content_type":ctype,"request_method":"GET"}; return r

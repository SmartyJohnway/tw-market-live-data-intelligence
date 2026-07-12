from __future__ import annotations
from scripts.m8b_taifex_derivatives_observation import *
from scripts.m8b_taifex_openapi_client import fetch_endpoint, TaifexOpenApiError
ENDPOINT="DailyMarketReportOpt"
FIELDS=["Date","Contract","ContractMonth(Week)","StrikePrice","CallPut","Open","High","Low","Close","Volume","SettlementPrice","OpenInterest","BestBid","BestAsk","TradingSession","TradingHalt"]
def normalize_taifex_options_eod(*, requested_products, requested_contract_months=None, requested_strikes=None, requested_option_types=None, requested_sessions=None, retrieved_at=None, fetcher=None):
    res=empty_adapter_result(ENDPOINT, requested_products); res["batch_status"]="not_started"; products=set(requested_products or []); months=set(requested_contract_months or []); strikes={str(x) for x in (requested_strikes or [])}; types=set(requested_option_types or []); sessions=set(requested_sessions or [])
    if not products or not (months and strikes and types): res.update(batch_status="rejected_invalid_scope", caveats=["bounded option contract_month, strike, and option_type required"]); return res
    try: data=(fetcher or fetch_endpoint)(ENDPOINT)
    except TaifexOpenApiError as e: res.update(batch_status=e.status, source_status=e.status, provenance=e.metadata); return res
    rows=data if isinstance(data,list) else data.get("rows",[]); res["http_status"]=(data.get("http_status") if isinstance(data,dict) else 200); res["row_count_received"]=len(rows); seen=set(); dates=set()
    for i,row in enumerate(rows):
        res["row_count_examined"]+=1
        if not isinstance(row,dict) or row.get("Contract") not in products: continue
        cm,cmv=validate_contract_month(row.get("ContractMonth(Week)")); strike,stv=parse_decimal_text(row.get("StrikePrice"),allow_missing=False); opt,opv=map_call_put(row.get("CallPut")); session,sv,sc=map_session(row.get("TradingSession")); td,dv=parse_yyyymmdd(row.get("Date")); dates.add(td) if td else None
        if cm not in months or strike not in strikes or opt not in types or (sessions and session not in sessions): continue
        present,omitted=source_field_presence(row,FIELDS); fv={"Date":dv,"ContractMonth(Week)":cmv,"StrikePrice":stv,"CallPut":opv,"TradingSession":sv}; caveats=sc[:]
        if not (td and cm and strike and opt): res["row_count_rejected"]+=1; res["rejected_rows"].append({"index":i,"reason":"identity_parse_failure"}); continue
        ident=(td,row.get("Contract"),cm,strike,opt,session)
        if ident in seen: res.update(batch_status="identity_parse_failure"); res["rejected_rows"].append({"index":i,"reason":"duplicate_identity"}); return res
        seen.add(ident); price={}; activity={}; oi={}
        for src,dst in [("Open","open"),("High","high"),("Low","low"),("Close","close"),("SettlementPrice","settlement"),("BestBid","best_bid"),("BestAsk","best_ask")]: price[dst],fv[src]=parse_decimal_text(row.get(src))
        activity["volume"],fv["Volume"]=parse_non_negative_int(row.get("Volume")); oi["open_interest"],fv["OpenInterest"]=parse_non_negative_int(row.get("OpenInterest"))
        obs=create_observation(endpoint_contract_id=ENDPOINT, context_type=CONTEXT_TYPES["options"], instrument_type="options", product_id=row.get("Contract"), contract_identity={"trade_date":td,"product_id":row.get("Contract"),"contract_month_or_week":cm,"strike_price":strike,"option_type":opt,"session":session}, trade_date=td, retrieved_at_utc=retrieved_at, session=session, source_session_label=row.get("TradingSession"), field_validation=fv, source_fields_present=present, omitted_source_fields=omitted, caveats=caveats, provenance={"endpoint":ENDPOINT,"raw_payload_retained":False}, payload={"price":price,"activity":activity,"open_interest":oi,"trading_halt":row.get("TradingHalt")})
        res["observations"].append(obs)
    res["batch_status"]="date_mismatch" if len(dates)>1 else ("successful_derivatives_eod_batch" if res["observations"] else "empty_non_trading_day")
    res["row_count_retained"]=len(res["observations"]); res["reported_trade_dates"]=sorted(d for d in dates if d); res["source_status"]="ok" if res["observations"] else res["batch_status"]; return res

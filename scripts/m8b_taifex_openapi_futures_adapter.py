from __future__ import annotations
from scripts.m8b_taifex_derivatives_observation import *
from scripts.m8b_taifex_openapi_client import fetch_endpoint, TaifexOpenApiError
ENDPOINT="DailyMarketReportFut"
FIELDS=["Date","Contract","ContractMonth(Week)","Open","High","Low","Last","Change","%","Volume","SettlementPrice","OpenInterest","BestBid","BestAsk","TradingSession","TradingHalt"]
def normalize_taifex_futures_eod(*, requested_products, requested_contract_months=None, requested_sessions=None, retrieved_at=None, fetcher=None):
    res=empty_adapter_result(ENDPOINT, requested_products); res["batch_status"]="not_started"; products=set(requested_products or []); months=set(requested_contract_months or []); sessions=set(requested_sessions or [])
    if not products: res.update(batch_status="rejected_invalid_scope", caveats=["requested_products required"]); return res
    try: data=(fetcher or fetch_endpoint)(ENDPOINT)
    except TaifexOpenApiError as e: res.update(batch_status=e.status, source_status=e.status, provenance=e.metadata); return res
    rows=data if isinstance(data,list) else data.get("rows",[]); res["http_status"]=(data.get("http_status") if isinstance(data,dict) else 200); res["row_count_received"]=len(rows); seen=set(); dates=set()
    for i,row in enumerate(rows):
        res["row_count_examined"]+=1
        if not isinstance(row,dict): res["row_count_rejected"]+=1; continue
        if row.get("Contract") not in products: continue
        cm,cmv=validate_contract_month(row.get("ContractMonth(Week)")); session,sv,sc=map_session(row.get("TradingSession")); td,dv=parse_yyyymmdd(row.get("Date")); dates.add(td) if td else None
        if months and cm not in months: continue
        if sessions and session not in sessions: continue
        present,omitted=source_field_presence(row,FIELDS); fv={"Date":dv,"ContractMonth(Week)":cmv,"TradingSession":sv}; caveats=sc[:]
        if not (td and cm and row.get("Contract")): res["row_count_rejected"]+=1; res["rejected_rows"].append({"index":i,"reason":"identity_parse_failure"}); continue
        ident=(td,row.get("Contract"),cm,session)
        if ident in seen: res.update(batch_status="identity_parse_failure"); res["rejected_rows"].append({"index":i,"reason":"duplicate_identity"}); return res
        seen.add(ident)
        price={}; activity={}; oi={}
        for src,dst,neg in [("Open","open",False),("High","high",False),("Low","low",False),("Last","last",False),("Change","change",True),("%","change_percent",True),("SettlementPrice","settlement",False),("BestBid","best_bid",False),("BestAsk","best_ask",False)]: price[dst],fv[src]=parse_decimal_text(row.get(src),allow_negative=neg)
        activity["volume"],fv["Volume"]=parse_non_negative_int(row.get("Volume")); oi["open_interest"],fv["OpenInterest"]=parse_non_negative_int(row.get("OpenInterest"))
        status="complete" if all([price.get("settlement") is not None, activity.get("volume") is not None, oi.get("open_interest") is not None]) else "partial"
        obs=create_observation(endpoint_contract_id=ENDPOINT, context_type=CONTEXT_TYPES["futures"], instrument_type="futures", product_id=row.get("Contract"), contract_identity={"trade_date":td,"product_id":row.get("Contract"),"contract_month_or_week":cm,"session":session}, trade_date=td, retrieved_at_utc=retrieved_at, session=session, source_session_label=row.get("TradingSession"), observation_status=status, field_validation=fv, source_fields_present=present, omitted_source_fields=omitted, caveats=caveats, provenance={"endpoint":ENDPOINT,"raw_payload_retained":False}, payload={"price":price,"activity":activity,"open_interest":oi,"trading_halt":row.get("TradingHalt")})
        res["observations"].append(obs)
    if len(dates)>1: res["batch_status"]="date_mismatch"; res["caveats"].append("mixed source dates observed")
    else: res["batch_status"]="successful_derivatives_eod_batch" if res["observations"] else "empty_non_trading_day"
    res["row_count_retained"]=len(res["observations"]); res["reported_trade_dates"]=sorted(d for d in dates if d); res["source_status"]="ok" if res["observations"] else res["batch_status"]; return res

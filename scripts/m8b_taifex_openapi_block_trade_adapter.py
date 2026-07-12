from __future__ import annotations
from scripts.m8b_taifex_derivatives_observation import *
from scripts.m8b_taifex_openapi_client import fetch_endpoint, TaifexOpenApiError
ENDPOINT="BlockTrade"; FIELDS=["Date","Contract","ContractMonth(Week)","StrikePrice","CallPut","Volume","HighestPrice","LowestPrice","TradingSession"]
def normalize_taifex_block_trade(*, requested_products, requested_contract_months=None, requested_strikes=None, requested_option_types=None, requested_sessions=None, retrieved_at=None, fetcher=None):
    res=empty_adapter_result(ENDPOINT, requested_products); products=set(requested_products or []); months=set(requested_contract_months or []); strikes={str(x) for x in (requested_strikes or [])}; types=set(requested_option_types or []); sessions=set(requested_sessions or [])
    if not products: res.update(batch_status="rejected_invalid_scope", caveats=["requested_products required"]); return res
    try: data=(fetcher or fetch_endpoint)(ENDPOINT)
    except TaifexOpenApiError as e: res.update(batch_status=e.status, source_status=e.status, provenance=e.metadata); return res
    rows=data if isinstance(data,list) else data.get("rows",[]); res["row_count_received"]=len(rows); seen=set(); dates=set(); schema_valid_rows=0; matching_scope_rows=0; invalid_matching_rows=0
    for i,row in enumerate(rows):
        res["row_count_examined"]+=1
        if not isinstance(row,dict): res["row_count_rejected"]+=1; continue
        ok_schema, missing_schema = validate_required_fields(row, FIELDS)
        if ok_schema: schema_valid_rows += 1
        else:
            res["row_count_rejected"]+=1; res["rejected_rows"].append({"index":i,"reason":"schema_drift","missing_fields":missing_schema}); continue
        if row.get("Contract") not in products: continue
        td,dv=parse_yyyymmdd(row.get("Date")); cm,cmv=validate_contract_month(row.get("ContractMonth(Week)")); session,sv,sc=map_session(row.get("TradingSession")); strike_raw=row.get("StrikePrice"); cp_raw=row.get("CallPut"); is_future=str(strike_raw).strip()=="-" and str(cp_raw).strip()=="-"
        strike,stv=("not_applicable",{"valid":True}) if is_future else parse_decimal_text(strike_raw,allow_missing=False); opt,opv=map_call_put(cp_raw, allow_not_applicable=is_future)
        if months and cm not in months: continue
        if strikes and strike not in strikes: continue
        if types and opt not in types: continue
        if sessions and session not in sessions: continue
        matching_scope_rows += 1
        vol,vv=parse_non_negative_int(row.get("Volume"),allow_missing=False); high,hv=parse_decimal_text(row.get("HighestPrice"),allow_missing=False); low,lv=parse_decimal_text(row.get("LowestPrice"),allow_missing=False)
        if not(td and cm and row.get("Contract") and vol is not None and high and low and (is_future or (strike and opt))): invalid_matching_rows += 1; res["row_count_rejected"]+=1; res["rejected_rows"].append({"index":i,"reason":"identity_parse_failure"}); continue
        ident={"trade_date":td,"product_id":row.get("Contract"),"contract_month_or_week":cm,"session":session,"highest_price":high,"lowest_price":low}
        if not is_future: ident.update(strike_price=strike, option_type=opt)
        key=tuple(sorted(ident.items()))
        if key in seen: res.update(batch_status="identity_parse_failure"); res["rejected_rows"].append({"index":i,"reason":"duplicate_aggregate_identity"}); return res
        seen.add(key); dates.add(td); present,omitted=source_field_presence(row,FIELDS)
        res["observations"].append(create_observation(endpoint_contract_id=ENDPOINT, context_type=CONTEXT_TYPES["block_trade"], instrument_type="block_trade", product_id=row.get("Contract"), contract_identity=ident, trade_date=td, retrieved_at_utc=retrieved_at, session=session, source_session_label=row.get("TradingSession"), field_validation={"Date":dv,"ContractMonth(Week)":cmv,"StrikePrice":stv,"CallPut":opv,"Volume":vv,"HighestPrice":hv,"LowestPrice":lv,"TradingSession":sv}, source_fields_present=present, omitted_source_fields=omitted, caveats=sc+["aggregate row identity, not transaction id","block trade activity has no directional inference"], provenance={"endpoint":ENDPOINT,"raw_payload_retained":False}, payload={"block_trade":{"volume":vol,"highest_price":high,"lowest_price":low,"strike_price":strike,"option_type":opt}}))
    finalize_adapter_result(res, rows, schema_valid_rows=schema_valid_rows, matching_scope_rows=matching_scope_rows, invalid_matching_rows=invalid_matching_rows, dates=dates); return res

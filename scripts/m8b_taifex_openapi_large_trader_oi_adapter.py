from __future__ import annotations
from scripts.m8b_taifex_derivatives_observation import *
from scripts.m8b_taifex_openapi_client import fetch_endpoint, TaifexOpenApiError
FIELDS_F=["Date","Contract","ContractName","SettlementMonth","TypeOfTraders","Top5Buy","Top5Sell","Top10Buy","Top10Sell","OIOfMarket"]
FIELDS_O=FIELDS_F[:3]+["CallPut"]+FIELDS_F[3:]
def normalize_taifex_large_trader_oi(*, endpoint, requested_products, requested_settlement_months=None, requested_option_types=None, requested_trader_types=None, retrieved_at=None, fetcher=None):
    if endpoint not in {"OpenInterestOfLargeTradersFutures","OpenInterestOfLargeTradersOptions"}: return dict(empty_adapter_result(endpoint, requested_products), batch_status="rejected_invalid_scope")
    res=empty_adapter_result(endpoint, requested_products); products=set(requested_products or []); months=set(requested_settlement_months or []); types=set(requested_option_types or []); traders=set(requested_trader_types or [])
    if not products: res.update(batch_status="rejected_invalid_scope", caveats=["requested_products required"]); return res
    try: data=(fetcher or fetch_endpoint)(endpoint)
    except TaifexOpenApiError as e: res.update(batch_status=e.status, source_status=e.status, provenance=e.metadata); return res
    rows=data if isinstance(data,list) else data.get("rows",[]); res["row_count_received"]=len(rows); dates=set(); isopt=endpoint.endswith("Options"); schema_valid_rows=0
    for i,row in enumerate(rows):
        res["row_count_examined"]+=1
        if not isinstance(row,dict): res["row_count_rejected"]+=1; continue
        required = FIELDS_O if isopt else FIELDS_F
        ok_schema, missing_schema = validate_required_fields(row, required)
        if ok_schema: schema_valid_rows += 1
        else:
            res["row_count_rejected"]+=1; res["rejected_rows"].append({"index":i,"reason":"schema_drift","missing_fields":missing_schema}); continue
        if row.get("Contract") not in products: continue
        td,dv=parse_yyyymmdd(row.get("Date")); sm,smv=validate_contract_month(row.get("SettlementMonth")); trader=str(row.get("TypeOfTraders","")).strip(); opt=None; opv={"valid":True}
        if isopt: opt,opv=map_call_put(row.get("CallPut"));
        if months and sm not in months: continue
        if types and opt not in types: continue
        if traders and trader not in traders: continue
        if not(td and sm and trader and (not isopt or opt)): res["row_count_rejected"]+=1; res["rejected_rows"].append({"index":i,"reason":"identity_parse_failure"}); continue
        vals={}; fv={"Date":dv,"SettlementMonth":smv,"CallPut":opv}
        for f,k in [("Top5Buy","top5_buy"),("Top5Sell","top5_sell"),("Top10Buy","top10_buy"),("Top10Sell","top10_sell"),("OIOfMarket","market_open_interest")]: vals[k],fv[f]=parse_non_negative_int(row.get(f),allow_missing=False)
        core_fields=["Top5Buy","Top5Sell","Top10Buy","Top10Sell","OIOfMarket"]
        bad_fields=[k for k in core_fields if (fv.get(k) or {}).get("valid") is False]
        dates.add(td); present,omitted=source_field_presence(row,FIELDS_O if isopt else FIELDS_F); caveats=["large trader open-interest concentration; not investor-category positioning"]
        if bad_fields: caveats.append("malformed_or_missing_core_oi_fields:"+",".join(bad_fields))
        ident={"trade_date":td,"product_id":row.get("Contract"),"settlement_month":sm,"type_of_traders":trader};
        if isopt: ident["option_type"]=opt
        res["observations"].append(create_observation(endpoint_contract_id=endpoint, context_type=CONTEXT_TYPES["large_trader_oi"], instrument_type="options" if isopt else "futures", product_id=row.get("Contract"), product_name=row.get("ContractName"), contract_identity=ident, trade_date=td, retrieved_at_utc=retrieved_at, session="not_applicable", observation_status=("partial" if bad_fields else "complete"), field_validation=fv, source_fields_present=present, omitted_source_fields=omitted, caveats=caveats, provenance={"endpoint":endpoint,"raw_payload_retained":False}, payload={"large_trader_open_interest":dict(vals, type_of_traders=trader, option_type=opt)}))
    res["batch_status"]="schema_drift" if rows and schema_valid_rows == 0 else ("successful_derivatives_eod_batch" if res["observations"] else ("no_matching_bounded_scope" if rows else "empty_non_trading_day")); res["row_count_retained"]=len(res["observations"]); res["reported_trade_dates"]=sorted(dates); res["source_status"]="ok" if res["observations"] else res["batch_status"]; return res

from __future__ import annotations
from scripts.m8b_taifex_derivatives_observation import *
from scripts.m8b_taifex_openapi_client import fetch_endpoint, TaifexOpenApiError
ENDPOINT="FinalSettlementPrice"; FIELDS=["TheFinalSettlementDay","DeliveryMonth","Contract","ContractName","TheFinalSettlementPrice"]
def normalize_taifex_final_settlement(*, requested_products, requested_delivery_months=None, retrieved_at=None, fetcher=None):
    res=empty_adapter_result(ENDPOINT, requested_products); products=set(requested_products or []); months=set(requested_delivery_months or [])
    if not products: res.update(batch_status="rejected_invalid_scope", caveats=["requested_products required"]); return res
    try: data=(fetcher or fetch_endpoint)(ENDPOINT)
    except TaifexOpenApiError as e: res.update(batch_status=e.status, source_status=e.status, provenance=e.metadata); return res
    rows=data if isinstance(data,list) else data.get("rows",[]); res["row_count_received"]=len(rows); dates=set()
    for i,row in enumerate(rows):
        res["row_count_examined"]+=1
        if not isinstance(row,dict) or row.get("Contract") not in products: continue
        dm=str(row.get("DeliveryMonth","")).strip();
        if months and dm not in months: continue
        td,dv=parse_yyyymmdd(row.get("TheFinalSettlementDay")); price,pv=parse_decimal_text(row.get("TheFinalSettlementPrice"),allow_missing=False); present,omitted=source_field_presence(row,FIELDS)
        if not(td and dm and price): res["row_count_rejected"]+=1; continue
        dates.add(td); cur=currentness("official_final_settlement_reference", trade_date=td, caveats=["not latest daily market state"])
        res["observations"].append(create_observation(endpoint_contract_id=ENDPOINT, context_type=CONTEXT_TYPES["final_settlement"], instrument_type="final_settlement", product_id=row.get("Contract"), product_name=row.get("ContractName"), contract_identity={"final_settlement_day":td,"delivery_month":dm,"product_id":row.get("Contract")}, trade_date=td, retrieved_at_utc=retrieved_at, session="not_applicable", currentness_value=cur, field_validation={"TheFinalSettlementDay":dv,"TheFinalSettlementPrice":pv}, source_fields_present=present, omitted_source_fields=omitted, caveats=["official final settlement reference; not latest daily market state"], provenance={"endpoint":ENDPOINT,"raw_payload_retained":False}, payload={"final_settlement":{"delivery_month":dm,"final_settlement_price":price}}))
    res["batch_status"]="successful_derivatives_eod_batch" if res["observations"] else "empty_non_trading_day"; res["row_count_retained"]=len(res["observations"]); res["reported_trade_dates"]=sorted(dates); res["source_status"]="ok" if res["observations"] else res["batch_status"]; return res

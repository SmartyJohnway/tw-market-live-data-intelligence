from __future__ import annotations
from scripts.m8b_taifex_derivatives_observation import *
from scripts.m8b_taifex_openapi_client import fetch_endpoint, TaifexOpenApiError
from scripts.m8b_taifex_currentness import final_settlement_currentness
ENDPOINT="FinalSettlementPrice"; FIELDS=["TheFinalSettlementDay","DeliveryMonth","Contract","ContractName","TheFinalSettlementPrice"]
def normalize_taifex_final_settlement(*, requested_products, requested_delivery_months=None, retrieved_at=None, fetcher=None):
    res=empty_adapter_result(ENDPOINT, requested_products); products=set(requested_products or []); months=set(requested_delivery_months or [])
    if not products: res.update(batch_status="rejected_invalid_scope", caveats=["requested_products required"]); return res
    try: data=(fetcher or fetch_endpoint)(ENDPOINT)
    except TaifexOpenApiError as e: res.update(batch_status=e.status, source_status=e.status, provenance=e.metadata); return res
    rows=data if isinstance(data,list) else data.get("rows",[]); res["row_count_received"]=len(rows); dates=set(); schema_valid_rows=0; matching_scope_rows=0; invalid_matching_rows=0
    source_latest_by_product = {}
    endpoint_latest = None
    for source_row in rows:
        if not isinstance(source_row, dict):
            continue
        ok_schema, _ = validate_required_fields(source_row, FIELDS)
        if not ok_schema:
            continue
        source_day, _ = parse_yyyymmdd(source_row.get("TheFinalSettlementDay"))
        if not source_day:
            continue
        product = source_row.get("Contract")
        if product and (source_latest_by_product.get(product) is None or source_day > source_latest_by_product[product]):
            source_latest_by_product[product] = source_day
        if endpoint_latest is None or source_day > endpoint_latest:
            endpoint_latest = source_day
    res["source_latest_reference"] = {"basis": "product_specific_contract", "latest_by_product": dict(source_latest_by_product), "endpoint_wide_latest_final_settlement_day": endpoint_latest, "raw_payload_retained": False}
    for i,row in enumerate(rows):
        res["row_count_examined"]+=1
        if not isinstance(row,dict): res["row_count_rejected"]+=1; continue
        ok_schema, missing_schema = validate_required_fields(row, FIELDS)
        if ok_schema: schema_valid_rows += 1
        else:
            res["row_count_rejected"]+=1; res["rejected_rows"].append({"index":i,"reason":"schema_drift","missing_fields":missing_schema}); continue
        if row.get("Contract") not in products: continue
        dm=str(row.get("DeliveryMonth","")).strip();
        if months and dm not in months: continue
        matching_scope_rows += 1
        td,dv=parse_yyyymmdd(row.get("TheFinalSettlementDay")); price,pv=parse_decimal_text(row.get("TheFinalSettlementPrice"),allow_missing=False); present,omitted=source_field_presence(row,FIELDS)
        if not(td and dm and price): invalid_matching_rows += 1; res["row_count_rejected"]+=1; res["rejected_rows"].append({"index":i,"reason":"invalid_required_fields" if td and dm else "identity_parse_failure"}); continue
        dates.add(td); source_latest_reference_date=source_latest_by_product.get(row.get("Contract")) or endpoint_latest; cur=final_settlement_currentness(td, latest_reference_date=source_latest_reference_date)
        res["observations"].append(create_observation(endpoint_contract_id=ENDPOINT, context_type=CONTEXT_TYPES["final_settlement"], instrument_type="final_settlement", product_id=row.get("Contract"), product_name=row.get("ContractName"), contract_identity={"final_settlement_day":td,"delivery_month":dm,"product_id":row.get("Contract")}, trade_date=td, retrieved_at_utc=retrieved_at, session="not_applicable", currentness_value=cur, field_validation={"TheFinalSettlementDay":dv,"TheFinalSettlementPrice":pv}, source_fields_present=present, omitted_source_fields=omitted, caveats=["official final settlement reference; not latest daily market state"], provenance={"endpoint":ENDPOINT,"raw_payload_retained":False}, payload={"final_settlement":{"delivery_month":dm,"final_settlement_price":price,"source_latest_reference_date":source_latest_reference_date}}))
    finalize_adapter_result(res, rows, schema_valid_rows=schema_valid_rows, matching_scope_rows=matching_scope_rows, invalid_matching_rows=invalid_matching_rows, dates=dates); return res

from __future__ import annotations
from decimal import Decimal, InvalidOperation
from scripts.m8b_taifex_derivatives_observation import *
from scripts.m8b_taifex_openapi_client import fetch_endpoint, TaifexOpenApiError
ENDPOINT="PutCallRatio"; FIELDS=["Date","PutVolume","CallVolume","PutCallVolumeRatio%","PutOI","CallOI","PutCallOIRatio%"]
MAX_PUT_CALL_RATIO_ROWS = 60

def _validate_positive_int(value, name, hard_max=None):
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    if hard_max is not None and value > hard_max:
        raise ValueError(f"{name} exceeds hard maximum {hard_max}")
    return value

def normalize_taifex_put_call_ratio(*, retrieved_at=None, fetcher=None, requested_trade_dates=None, latest_n=1, max_retained_rows=20):
    _validate_positive_int(latest_n, "latest_n")
    _validate_positive_int(max_retained_rows, "max_retained_rows", MAX_PUT_CALL_RATIO_ROWS)
    retention_limit = min(latest_n, max_retained_rows)
    res=empty_adapter_result(ENDPOINT, []); requested_dates=set(requested_trade_dates or [])
    try: data=(fetcher or fetch_endpoint)(ENDPOINT)
    except TaifexOpenApiError as e: res.update(batch_status=e.status, source_status=e.status, provenance=e.metadata); return complete_adapter_result(res)
    rows=data if isinstance(data,list) else data.get("rows",[]); res["row_count_received"]=len(rows); dates=set(); schema_valid_rows=0; matching_scope_rows=0; invalid_matching_rows=0; candidates=[]
    for i,row in enumerate(rows):
        res["row_count_examined"]+=1
        if not isinstance(row,dict): res["row_count_rejected"]+=1; continue
        ok_schema, missing_schema = validate_required_fields(row, FIELDS)
        if ok_schema: schema_valid_rows += 1
        else:
            res["row_count_rejected"]+=1; res["rejected_rows"].append({"index":i,"reason":"schema_drift","missing_fields":missing_schema}); continue
        td,dv=parse_yyyymmdd(row.get("Date"));
        if requested_dates and td not in requested_dates: continue
        matching_scope_rows += 1
        if not td: invalid_matching_rows += 1; res["row_count_rejected"]+=1; res["rejected_rows"].append({"index":i,"reason":"identity_parse_failure"}); continue
        fv={"Date":dv}; payload={}
        for f,k in [("PutVolume","put_volume"),("CallVolume","call_volume"),("PutOI","put_open_interest"),("CallOI","call_open_interest")]: payload[k],fv[f]=parse_non_negative_int(row.get(f),allow_missing=False)
        for f,k in [("PutCallVolumeRatio%","put_call_volume_ratio_percent"),("PutCallOIRatio%","put_call_open_interest_ratio_percent")]: payload[k],fv[f]=parse_decimal_text(row.get(f),allow_missing=False)
        derived=[]
        try:
            if payload.get("call_volume"): derived.append({"field":"put_call_volume_ratio_percent_consistency","computed":format(Decimal(payload["put_volume"])/Decimal(payload["call_volume"])*Decimal(100),"f"),"authoritative":False})
            if payload.get("call_open_interest"): derived.append({"field":"put_call_open_interest_ratio_percent_consistency","computed":format(Decimal(payload["put_open_interest"])/Decimal(payload["call_open_interest"])*Decimal(100),"f"),"authoritative":False})
        except Exception: pass
        core_fields=["PutVolume","CallVolume","PutOI","CallOI","PutCallVolumeRatio%","PutCallOIRatio%"]
        bad_fields=[k for k in core_fields if (fv.get(k) or {}).get("valid") is False]
        if bad_fields: invalid_matching_rows += 1; res["row_count_rejected"]+=1; res["rejected_rows"].append({"index":i,"reason":"invalid_required_fields","fields":bad_fields}); continue
        dates.add(td); present,omitted=source_field_presence(row,FIELDS)
        candidates.append(create_observation(endpoint_contract_id=ENDPOINT, context_type=CONTEXT_TYPES["put_call_ratio"], instrument_type="aggregate_statistics", aggregate_identity={"source_id":SOURCE_ID,"context_type":CONTEXT_TYPES["put_call_ratio"],"trade_date":td}, trade_date=td, retrieved_at_utc=retrieved_at, session="not_applicable", field_validation=fv, source_fields_present=present, omitted_source_fields=omitted, derived_fields=derived, caveats=["source-reported percentage values; not sentiment signal"], provenance={"endpoint":ENDPOINT,"raw_payload_retained":False}, payload={"put_call_ratio":payload}))
    candidates.sort(key=lambda o: o.get("trade_date") or "", reverse=True)
    pre_limit=len(candidates); res["observations"]=candidates[:retention_limit]
    truncated=pre_limit > len(res["observations"])
    finalize_adapter_result(res, rows, schema_valid_rows=schema_valid_rows, matching_scope_rows=matching_scope_rows, invalid_matching_rows=invalid_matching_rows, dates=dates, retention_limit=retention_limit, retention_truncated=truncated); return res

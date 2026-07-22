"""Catalog-only capability checks; no routes, adapters, or execution planning."""
def validate_capability(need, index, *, catalog, target_resolved):
    capid=need.get("type", "") if isinstance(need,dict) else ""; priority=need.get("priority", "required") if isinstance(need,dict) else "required"
    out={"data_need_index":index,"capability_id":capid,"priority":priority,"status":"unknown","reason_codes":[]}
    found=next((x for x in catalog.get("data_need_capabilities",[]) if x.get("capability_id")==capid),None)
    if not found: out["reason_codes"]=["CAPABILITY_UNKNOWN"]; return out
    params=need.get("parameters",{})
    allowed=found.get("allowed_parameters",{})
    bad=[]
    if not isinstance(params,dict): bad=["parameters_not_object"]
    else:
        for key,value in params.items():
            rule=allowed.get(key)
            if not rule: bad.append("unknown_parameter:"+key); continue
            expected=rule.get("type")
            valid=(expected=="integer" and isinstance(value,int) and not isinstance(value,bool)) or (expected=="number" and isinstance(value,(int,float)) and not isinstance(value,bool)) or (expected=="string" and isinstance(value,str)) or (expected=="boolean" and isinstance(value,bool))
            if not valid:
                bad.append("invalid_type:"+key); continue
            if "minimum" in rule and value < rule["minimum"]: bad.append("below_minimum:"+key)
            if "maximum" in rule and value > rule["maximum"]: bad.append("above_maximum:"+key)
            if rule.get("enum") and value not in rule["enum"]: bad.append("invalid_enum:"+key)
        for key, rule in allowed.items():
            if key not in params and (rule.get("required") is True or key in found.get("required_parameters", [])): bad.append("missing_parameter:"+key)
    if bad: out["status"]="invalid_parameters"; out["reason_codes"]=sorted(bad); return out
    if found.get("requires_target_resolution") and not target_resolved: out["status"]="requires_target_resolution"; return out
    markets=target_resolved or set()
    if markets and not all(m in found.get("supported_markets",[])+found.get("provisional_markets",[]) for m in markets): out["status"]="unsupported"; out["reason_codes"]=["CAPABILITY_MARKET_UNSUPPORTED"]; return out
    out["status"]="provisional" if markets and any(m in found.get("provisional_markets",[]) for m in markets) else found.get("support_status","unknown")
    out["known_limitations"]=found.get("known_limitations",[])
    return out

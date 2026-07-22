import copy
import jsonschema
from .request_validation_models import OUTPUT_SCHEMA_VERSION, TARGET_BLOCKER_BY_STATUS
from .target_validator import validate_target
from .capability_validator import validate_capability

def _issue(code,path,message=None): return {"code":code,"path":path,"message":message or code.replace("_"," ").lower()}
def _catalog_valid(catalog):
    if not isinstance(catalog,dict) or catalog.get("schema_version")!="unified_market_evidence_capability_catalog.v1": return False
    bounds=catalog.get("bounds"); markets=catalog.get("supported_markets"); caps=catalog.get("data_need_capabilities")
    if not isinstance(bounds,dict) or not isinstance(markets,dict) or not markets or not isinstance(caps,list): return False
    if not all(isinstance(k,str) and k and isinstance(v,dict) and v.get("support_level") in {"supported","supported_with_caveats","provisional"} for k,v in markets.items()): return False
    default=bounds.get("default_target_limit")
    if not isinstance(bounds.get("hard_target_limit"),int) or isinstance(bounds.get("hard_target_limit"),bool) or bounds["hard_target_limit"] < 1 or not isinstance(default,int) or isinstance(default,bool) or default < 1 or default > bounds["hard_target_limit"]: return False
    ids=[]
    for cap in caps:
        if not isinstance(cap,dict): return False
        rules=cap.get("allowed_parameters")
        if not isinstance(cap,dict) or not isinstance(cap.get("capability_id"),str) or not cap["capability_id"] or cap.get("support_status") not in {"contract_supported","runtime_executable","provisional","unsupported"} or not isinstance(cap.get("supported_markets"),list) or not isinstance(cap.get("provisional_markets"),list) or not all(isinstance(m,str) and m in markets for m in cap["supported_markets"]+cap["provisional_markets"]) or not isinstance(rules,dict) or not isinstance(cap.get("requires_target_resolution"),bool) or not isinstance(cap.get("known_limitations",[]),list) or not all(isinstance(x,str) for x in cap.get("known_limitations",[])): return False
        for key, rule in rules.items():
            typ=rule.get("type") if isinstance(rule,dict) else None
            if not isinstance(key,str) or not key or not isinstance(rule,dict) or typ not in {"integer","string","number","boolean"} or ("required" in rule and not isinstance(rule["required"],bool)) or ("enum" in rule and (not isinstance(rule["enum"],list) or not rule["enum"])): return False
            def matches(v): return (typ=="integer" and isinstance(v,int) and not isinstance(v,bool)) or (typ=="number" and isinstance(v,(int,float)) and not isinstance(v,bool)) or (typ=="string" and isinstance(v,str)) or (typ=="boolean" and isinstance(v,bool))
            if "enum" in rule and not all(matches(v) for v in rule["enum"]): return False
            if rule.get("type") in {"integer","number"}:
                numeric=int if typ=="integer" else (int,float)
                if any(k in rule and (not isinstance(rule[k],numeric) or isinstance(rule[k],bool)) for k in ("minimum","maximum")) or ("minimum" in rule and "maximum" in rule and rule["minimum"]>rule["maximum"]): return False
        ids.append(cap["capability_id"])
    return len(ids)==len(set(ids))
def validate_unified_market_evidence_request(request, *, security_master, capability_catalog, request_schema, allow_fixture_snapshot=False):
    normalized=copy.deepcopy(request) if isinstance(request,dict) else {}
    result={"schema_version":OUTPUT_SCHEMA_VERSION,"request_id":normalized.get("request_id","") if isinstance(normalized.get("request_id",""),str) else "","validation_status":"invalid","request_schema_status":"valid","target_validation_status":"valid","capability_validation_status":"valid","normalized_request":normalized,"target_results":[],"capability_results":[],"blocking_issues":[],"warnings":[],"limits":{"target_count":len(normalized.get("targets",[])) if isinstance(normalized.get("targets",[]),list) else 0,"hard_target_limit":0,"operation_count_computed":False,"operation_count":0,"orchestrator_projection_required":True},"validation_metadata":{"offline":True,"deterministic":True,"allow_fixture_snapshot":allow_fixture_snapshot}}
    errors=sorted(jsonschema.Draft7Validator(request_schema).iter_errors(request),key=lambda e:list(e.path)) if isinstance(request,dict) else [None]
    if errors:
        result["request_schema_status"]="invalid"; result["blocking_issues"]=[_issue("REQUEST_SCHEMA_INVALID", "$" if e is None else "$"+"".join("[%d]"%x if isinstance(x,int) else "."+x for x in e.path)) for e in errors]; return result
    bounds=capability_catalog.get("bounds") if isinstance(capability_catalog,dict) else None; markets=capability_catalog.get("supported_markets") if isinstance(capability_catalog,dict) else None
    if not _catalog_valid(capability_catalog): result["blocking_issues"]=[_issue("CAPABILITY_CATALOG_INVALID","$","capability catalog is malformed")]; return result
    result["limits"]["hard_target_limit"]=bounds.get("hard_target_limit",0)
    if not isinstance(bounds.get("hard_target_limit"),int) or isinstance(bounds.get("hard_target_limit"),bool) or bounds["hard_target_limit"] < 1 or len(request["targets"])>bounds["hard_target_limit"]: result["blocking_issues"]=[_issue("TARGET_LIMIT_EXCEEDED","$.targets")]; return result
    seen=set()
    recognized=request_schema.get("properties",{}).get("targets",{}).get("items",{}).get("properties",{}).get("market_hint",{}).get("enum",[])
    for i,t in enumerate(request["targets"]): result["target_results"].append(validate_target(t,i,security_master=security_master,supported_markets=sorted(markets.keys()),recognized_markets=recognized,seen=seen,allow_fixture_snapshot=allow_fixture_snapshot))
    statuses=[x["resolution_status"] for x in result["target_results"]]
    resolved={x["canonical_identity"]["market"] for x in result["target_results"] if x["resolution_status"]=="resolved"}
    invalid={"invalid_input","not_found","market_mismatch","invalid_market_hint","duplicate"}; unsupported={"unsupported_market","unsupported_security_type","quarantined"}
    for target in result["target_results"]:
        if target["resolution_status"] != "resolved": result["blocking_issues"].append(_issue(TARGET_BLOCKER_BY_STATUS[target["resolution_status"]], "$.targets[%d]" % target["target_index"], "target resolution status: "+target["resolution_status"]))
    if any(s in invalid for s in statuses): result["target_validation_status"]="invalid"
    elif "ambiguous" in statuses: result["target_validation_status"]="requires_clarification"
    elif any(s in unsupported for s in statuses): result["target_validation_status"]="unsupported"
    for i,n in enumerate(request["data_needs"]):
        target_context = resolved if all(s=="resolved" for s in statuses) else set()
        c=validate_capability(n,i,catalog=capability_catalog,target_resolved=target_context); result["capability_results"].append(c)
        if c["status"] in {"unsupported","invalid_parameters","unknown"}:
            item=_issue("REQUIRED_CAPABILITY_UNAVAILABLE" if n["priority"]=="required" else "OPTIONAL_CAPABILITY_UNAVAILABLE","$.data_needs[%d]"%i,"capability %s has status %s"%(c["capability_id"],c["status"]))
            (result["blocking_issues"] if n["priority"]=="required" else result["warnings"]).append(item)
    if any(c["status"] in {"invalid_parameters"} for c in result["capability_results"]): result["capability_validation_status"]="invalid"
    elif any(c["status"] in {"unsupported","unknown"} and c["priority"]=="required" for c in result["capability_results"]): result["capability_validation_status"]="unsupported"
    if result["target_validation_status"]=="invalid": result["validation_status"]="invalid"
    elif result["target_validation_status"]=="requires_clarification": result["validation_status"]="requires_clarification"
    elif result["target_validation_status"]=="unsupported": result["validation_status"]="unsupported"
    elif result["capability_validation_status"]=="invalid": result["validation_status"]="invalid"
    elif result["capability_validation_status"]=="unsupported": result["validation_status"]="unsupported"
    else: result["validation_status"]="valid"
    result["blocking_issues"].sort(key=lambda x:(x["path"],x["code"])); result["warnings"].sort(key=lambda x:(x["path"],x["code"]))
    return result

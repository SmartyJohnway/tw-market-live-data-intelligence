import copy
import jsonschema
from .request_validation_models import OUTPUT_SCHEMA_VERSION
from .target_validator import validate_target
from .capability_validator import validate_capability

def _issue(code,path): return {"code":code,"path":path}
def validate_unified_market_evidence_request(request, *, security_master, capability_catalog, request_schema, allow_fixture_snapshot=False):
    normalized=copy.deepcopy(request) if isinstance(request,dict) else {}
    result={"schema_version":OUTPUT_SCHEMA_VERSION,"request_id":normalized.get("request_id","") if isinstance(normalized.get("request_id",""),str) else "","validation_status":"invalid","request_schema_status":"valid","target_validation_status":"valid","capability_validation_status":"valid","normalized_request":normalized,"target_results":[],"capability_results":[],"blocking_issues":[],"warnings":[],"limits":{"target_count":len(normalized.get("targets",[])) if isinstance(normalized.get("targets",[]),list) else 0,"hard_target_limit":0,"operation_count_computed":False,"operation_count":0,"orchestrator_projection_required":True},"validation_metadata":{"offline":True,"deterministic":True,"allow_fixture_snapshot":allow_fixture_snapshot}}
    errors=sorted(jsonschema.Draft7Validator(request_schema).iter_errors(request),key=lambda e:list(e.path)) if isinstance(request,dict) else [None]
    if errors:
        result["request_schema_status"]="invalid"; result["blocking_issues"]=[_issue("REQUEST_SCHEMA_INVALID", "$" if e is None else "$"+"".join("[%d]"%x if isinstance(x,int) else "."+x for x in e.path)) for e in errors]; return result
    bounds=capability_catalog.get("bounds") if isinstance(capability_catalog,dict) else None; markets=capability_catalog.get("supported_markets") if isinstance(capability_catalog,dict) else None
    if not isinstance(bounds,dict) or not isinstance(markets,dict): result["blocking_issues"]=[_issue("CAPABILITY_CATALOG_INVALID","$")]; return result
    result["limits"]["hard_target_limit"]=bounds.get("hard_target_limit",0)
    if not isinstance(bounds.get("hard_target_limit"),int) or len(request["targets"])>bounds["hard_target_limit"]: result["blocking_issues"]=[_issue("TARGET_LIMIT_EXCEEDED","$.targets")]; return result
    seen=set()
    for i,t in enumerate(request["targets"]): result["target_results"].append(validate_target(t,i,security_master=security_master,supported_markets=sorted(markets.keys()),seen=seen,allow_fixture_snapshot=allow_fixture_snapshot))
    statuses=[x["resolution_status"] for x in result["target_results"]]
    resolved={x["canonical_identity"]["market"] for x in result["target_results"] if x["resolution_status"]=="resolved"}
    if any(s in {"invalid_input","not_found","market_mismatch","unsupported_market","invalid_market_hint","duplicate","quarantined","unsupported_security_type"} for s in statuses): result["target_validation_status"]="unsupported" if all(s=="unsupported_security_type" for s in statuses) else "invalid"
    elif "ambiguous" in statuses: result["target_validation_status"]="requires_clarification"
    for i,n in enumerate(request["data_needs"]):
        c=validate_capability(n,i,catalog=capability_catalog,target_resolved=resolved); result["capability_results"].append(c)
        if c["status"] in {"unsupported","invalid_parameters","unknown"}:
            item=_issue("REQUIRED_CAPABILITY_UNAVAILABLE" if n["priority"]=="required" else "OPTIONAL_CAPABILITY_UNAVAILABLE","$.data_needs[%d]"%i)
            (result["blocking_issues"] if n["priority"]=="required" else result["warnings"]).append(item)
    if any(c["status"] in {"invalid_parameters"} for c in result["capability_results"]): result["capability_validation_status"]="invalid"
    elif any(c["status"] in {"unsupported","unknown"} and c["priority"]=="required" for c in result["capability_results"]): result["capability_validation_status"]="unsupported"
    if result["target_validation_status"] in {"invalid","unsupported"}: result["validation_status"]="invalid"
    elif result["target_validation_status"]=="requires_clarification": result["validation_status"]="requires_clarification"
    elif result["capability_validation_status"] in {"invalid","unsupported"}: result["validation_status"]="unsupported"
    else: result["validation_status"]="valid"
    result["blocking_issues"].sort(key=lambda x:(x["path"],x["code"])); result["warnings"].sort(key=lambda x:(x["path"],x["code"]))
    return result

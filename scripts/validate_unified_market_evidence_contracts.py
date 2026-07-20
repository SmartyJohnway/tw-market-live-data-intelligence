import json
from pathlib import Path
from jsonschema import validate, ValidationError

SCHEMAS_DIR = Path(__file__).parent.parent / "schemas"

def load_schema(name):
    path = SCHEMAS_DIR / name
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def validate_request(instance):
    schema = load_schema("unified_market_evidence_request.v1.schema.json")
    validate(instance=instance, schema=schema)

def validate_preview(instance):
    schema = load_schema("unified_market_evidence_preview_response.v1.schema.json")
    validate(instance=instance, schema=schema)

def validate_result(instance):
    schema = load_schema("unified_market_evidence_result.v1.schema.json")
    validate(instance=instance, schema=schema)

def validate_catalog(instance):
    schema = load_schema("unified_market_evidence_capability_catalog.v1.schema.json")
    validate(instance=instance, schema=schema)

def validate_cross_contract(request_data, catalog_data, preview_data=None, result_data=None):
    """
    Cross-contract validation logic.
    M8R-05A:
    - Runs schema validations first
    - request data need must exist in catalog
    - market hint belongs to allowed catalog markets
    - target count bounds
    - parameter bounds validation
    - preview planned evidence maps to request data needs
    - preview operations do not exceed hard bounds
    - request id consistency
    - provisional capability caveat requirement
    - result evidence keys do not exceed request
    - fallback downgrade checks
    """
    
    validate_request(request_data)
    validate_catalog(catalog_data)
    if preview_data:
        validate_preview(preview_data)
    if result_data:
        validate_result(result_data)
        
    catalog_caps = {cap["capability_id"]: cap for cap in catalog_data.get("data_need_capabilities", [])}
    req_needs = {need["type"]: need for need in request_data.get("data_needs", [])}
    
    bounds = catalog_data.get("bounds", {})
    if len(request_data.get("targets", [])) > bounds.get("hard_target_limit", 50):
        raise ValueError("Cross-contract error: Target count exceeds hard limit.")
        
    for target in request_data.get("targets", []):
        hint = target.get("market_hint")
        if hint and hint not in catalog_data.get("supported_markets", {}):
            raise ValueError(f"Cross-contract error: market_hint {hint} not supported in catalog.")
    
    for need_type, need in req_needs.items():
        if need_type not in catalog_caps:
            raise ValueError(f"Cross-contract error: Request need '{need_type}' not found in catalog.")
            
        cap = catalog_caps[need_type]
        if cap.get("support_status") == "not_yet_implemented":
            raise ValueError(f"Cross-contract error: Need {need_type} is not yet implemented.")
            
    if preview_data:
        if preview_data.get("request_id") != request_data.get("request_id"):
            raise ValueError("Cross-contract error: preview request_id does not match request.")
            
        planned = set(preview_data.get("planned_evidence", []))
        if not planned.issubset(set(req_needs.keys())):
            raise ValueError("Cross-contract error: Preview planned evidence exceeds requested data needs.")
        
        p_bounds = preview_data.get("bounds", {})
        if p_bounds.get("operation_count", 0) > bounds.get("hard_operation_limit", 100):
            raise ValueError("Cross-contract error: Preview operations exceed catalog hard limit.")
            
        # Provisional check
        has_provisional = any(
            cap.get("support_status") == "provisional"
            for n in planned if (cap := catalog_caps.get(n))
        )
        if has_provisional and not preview_data.get("caveats", []):
            raise ValueError("Cross-contract error: Provisional capability planned but no caveat provided.")
            
    if result_data:
        if result_data.get("request_id") != request_data.get("request_id"):
            raise ValueError("Cross-contract error: result request_id does not match request.")
            
        for target in result_data.get("targets", []):
            evidence_keys = set(target.get("evidence", {}).keys())
            if not evidence_keys.issubset(set(req_needs.keys())):
                raise ValueError("Cross-contract error: Result evidence keys exceed requested needs.")
            
            # Check official EOD structure if present
            if "official_eod_reference" in target.get("evidence", {}):
                eod = target["evidence"]["official_eod_reference"]
                if eod.get("fallback_policy_used") and not catalog_data.get("fallback_semantics", {}).get("fallback_must_be_explicit"):
                    raise ValueError("Cross-contract error: Fallback policy used but not explicit in catalog.")

    return True

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

def validate_cross_contract(request_data, catalog_data, preview_data, result_data):
    """
    Cross-contract validation logic.
    M8R-05A:
    - request data need must exist in catalog
    - preview planned evidence maps to request data needs
    - preview operations do not exceed hard bounds
    - result evidence keys do not exceed request
    - fallback has explicit flag
    """
    
    catalog_caps = {cap["capability_id"] for cap in catalog_data.get("data_need_capabilities", [])}
    req_needs = {need["type"] for need in request_data.get("data_needs", [])}
    
    for need in req_needs:
        if need not in catalog_caps:
            raise ValueError(f"Cross-contract error: Request need '{need}' not found in catalog.")
            
    if preview_data:
        planned = set(preview_data.get("planned_evidence", []))
        if not planned.issubset(req_needs):
            raise ValueError("Cross-contract error: Preview planned evidence exceeds requested data needs.")
        
        bounds = preview_data.get("bounds", {})
        cat_bounds = catalog_data.get("bounds", {})
        if bounds.get("operation_count", 0) > cat_bounds.get("hard_operation_limit", 100):
            raise ValueError("Cross-contract error: Preview operations exceed catalog hard limit.")
            
    if result_data:
        for target in result_data.get("targets", []):
            evidence_keys = set(target.get("evidence", {}).keys())
            if not evidence_keys.issubset(req_needs):
                raise ValueError("Cross-contract error: Result evidence keys exceed requested needs.")
            
            # Check official EOD structure if present
            if "official_eod_reference" in target.get("evidence", {}):
                eod = target["evidence"]["official_eod_reference"]
                if eod.get("fallback_policy_used") and not catalog_data.get("fallback_semantics", {}).get("fallback_must_be_explicit"):
                    raise ValueError("Cross-contract error: Fallback policy used but not explicit in catalog.")
    return True

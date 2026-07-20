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


def check_forbidden_fields(data):
    forbidden_keys = {
        "buy", "sell", "hold", "bullish", "bearish", "target_price",
        "support", "resistance", "recommendation", "raw_payload",
        "cookies", "token", "local_path"
    }
    
    if isinstance(data, dict):
        for k, v in data.items():
            if k in forbidden_keys:
                raise ValueError(f"Cross-contract error: Forbidden key '{k}' found in result payload.")
            check_forbidden_fields(v)
    elif isinstance(data, list):
        for item in data:
            check_forbidden_fields(item)

def validate_cross_contract(request_data, catalog_data, preview_data=None, result_data=None):
    # Schema validations first
    validate_request(request_data)
    validate_catalog(catalog_data)
    if preview_data:
        validate_preview(preview_data)
    if result_data:
        validate_result(result_data)
        
    catalog_caps = {cap["capability_id"]: cap for cap in catalog_data.get("data_need_capabilities", [])}
    req_needs = {need["type"]: need for need in request_data.get("data_needs", [])}
    req_targets = request_data.get("targets", [])
    
    bounds = catalog_data.get("bounds", {})
    if len(req_targets) > bounds.get("hard_target_limit", 50):
        raise ValueError("Cross-contract error: Target count exceeds hard limit.")
        
    for target in req_targets:
        hint = target.get("market_hint")
        if hint and hint not in catalog_data.get("supported_markets", {}):
            raise ValueError(f"Cross-contract error: market_hint {hint} not supported in catalog.")
            
        # Capability x Target Market check
        if hint:
            for need_type in req_needs:
                cap = catalog_caps.get(need_type)
                if not cap:
                    continue
                supported = cap.get("supported_markets", [])
                provisional = cap.get("provisional_markets", [])
                if hint not in supported and hint not in provisional:
                    raise ValueError(f"Cross-contract error: capability {need_type} unsupported for market {hint}.")
    
    for need_type, need in req_needs.items():
        if need_type not in catalog_caps:
            raise ValueError(f"Cross-contract error: Request need '{need_type}' not found in catalog.")
            
    if preview_data:
        if preview_data.get("request_id") != request_data.get("request_id"):
            raise ValueError("Cross-contract error: preview request_id does not match request.")
            
        planned = set(preview_data.get("planned_evidence", []))
        if not planned.issubset(set(req_needs.keys())):
            raise ValueError("Cross-contract error: Preview planned evidence exceeds requested data needs.")
            
        # Block contract_supported / not_yet_implemented from being planned
        for plan in planned:
            cap = catalog_caps.get(plan)
            if cap and cap.get("support_status") not in ["runtime_executable", "runtime_available"]:
                raise ValueError(f"Cross-contract error: Planned evidence {plan} is not runtime executable.")
        
        preview_req_needs = set(preview_data.get("requested_data_needs", []))
        if preview_req_needs != set(req_needs.keys()):
            raise ValueError("Cross-contract error: Preview requested_data_needs must exactly match request data_needs.")
        
        p_bounds = preview_data.get("bounds", {})
        if p_bounds.get("target_count") != len(req_targets):
            raise ValueError("Cross-contract error: Preview target_count does not match request.")
        if p_bounds.get("operation_count", 0) > bounds.get("hard_operation_limit", 100):
            raise ValueError("Cross-contract error: Preview operations exceed catalog hard limit.")
            
        # Provisional caveat check per capability x target market
        has_provisional = False
        for target in req_targets:
            hint = target.get("market_hint")
            if hint:
                for plan in planned:
                    cap = catalog_caps.get(plan)
                    if cap and hint in cap.get("provisional_markets", []):
                        has_provisional = True
                        break
            if has_provisional:
                break
                
        if has_provisional and not preview_data.get("caveats", []):
            raise ValueError("Cross-contract error: Provisional market capability planned but no caveat provided.")
            
    if result_data:
        if result_data.get("request_id") != request_data.get("request_id"):
            raise ValueError("Cross-contract error: result request_id does not match request.")
            
        catalog_sources = {s["source_family"]: s for s in catalog_data.get("available_source_families", [])}
        catalog_timing_classes = set(catalog_data.get("timing_classes", []))
        
        timing_class_rank = {
            "liveish_intraday_snapshot": 3,
            "request_session_context": 2,
            "official_eod": 1,
            "official_statistics_eod": 1
        }
            
        citations = {c["citation_id"]: c for c in result_data.get("citations", [])}
            
        for target in result_data.get("targets", []):
            evidence = target.get("evidence", {})
            evidence_keys = set(evidence.keys())
            if not evidence_keys.issubset(set(req_needs.keys())):
                raise ValueError("Cross-contract error: Result evidence keys exceed requested needs.")
                
            for ev_key, env in evidence.items():
                if "status" in env:
                    check_forbidden_fields(env.get("observed_fields", {}))
                    check_forbidden_fields(env.get("currentness", {}))
                    
                    timing_class = env.get("currentness", {}).get("timing_class") or env.get("timing_class")
                    if timing_class and timing_class not in catalog_timing_classes:
                        raise ValueError(f"Cross-contract error: Result timing_class {timing_class} not found in catalog.")
                        
                    fallback_class = env.get("currentness", {}).get("fallback_timing_class")
                    if timing_class and fallback_class:
                        base_rank = timing_class_rank.get(timing_class, 0)
                        fall_rank = timing_class_rank.get(fallback_class, 0)
                        if fall_rank > base_rank:
                            raise ValueError("Cross-contract error: Fallback timing class cannot be an upgrade.")
                            
                    cit_ids = env.get("citations", [])
                    for cid in cit_ids:
                        if cid not in citations:
                            raise ValueError(f"Cross-contract error: Citation {cid} not defined in result citations block.")
                            
        for cid, citation in citations.items():
            src_family = citation.get("source_family")
            if src_family and src_family not in catalog_sources:
                raise ValueError(f"Cross-contract error: Source family {src_family} not defined in catalog.")

    return True

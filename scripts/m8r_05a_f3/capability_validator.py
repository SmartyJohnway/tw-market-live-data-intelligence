from typing import Dict, Any, List
from scripts.m8r_05a_f3.request_validation_models import (
    CapabilityResult, CAPABILITY_UNKNOWN,
    CAPABILITY_UNSUPPORTED_FOR_MARKET, CAPABILITY_PARAMETER_INVALID
)

def validate_capabilities(
    data_needs: List[Dict[str, Any]],
    capability_catalog: Dict[str, Any],
    resolved_markets: List[str]
) -> List[CapabilityResult]:
    
    results: List[CapabilityResult] = []
    
    # Pre-process capability catalog
    capabilities: Dict[str, Dict[str, Any]] = {}
    for cap in capability_catalog.get("data_need_capabilities", []):
        capabilities[cap["capability_id"]] = cap
        
    for need in data_needs:
        need_type = need.get("type", "")
        priority = need.get("priority", "optional")
        parameters = need.get("parameters", {})
        
        result: CapabilityResult = {
            "type": need_type,
            "priority": priority,
            "status": "unknown",
            "supported_markets": [],
            "reason_codes": []
        }
        
        if need_type not in capabilities:
            result["status"] = "unknown"
            result["reason_codes"].append(CAPABILITY_UNKNOWN)
            results.append(result)
            continue
            
        cap_info = capabilities[need_type]
        supported_markets = cap_info.get("supported_markets", [])
        result["supported_markets"] = supported_markets
        
        # Check market support
        unsupported_for_markets = [m for m in resolved_markets if m not in supported_markets]
        
        if unsupported_for_markets:
            result["status"] = "unsupported"
            result["reason_codes"].append(CAPABILITY_UNSUPPORTED_FOR_MARKET)
            results.append(result)
            continue
            
        # Check parameter validity (simplistic validation based on allowed_parameters in catalog)
        # Note: True JSON Schema validation is done by the top-level schema validation, 
        # but catalog can have additional limitations.
        allowed_params = cap_info.get("allowed_parameters", {})
        invalid_param = False
        for param_key in parameters.keys():
            if param_key not in allowed_params:
                invalid_param = True
                break
                
        if invalid_param:
            result["status"] = "invalid_parameters"
            result["reason_codes"].append(CAPABILITY_PARAMETER_INVALID)
            results.append(result)
            continue
            
        # If all checks pass
        result["status"] = "supported"
        results.append(result)
        
    return results

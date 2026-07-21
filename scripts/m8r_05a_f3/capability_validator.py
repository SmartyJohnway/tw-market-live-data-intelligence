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
        provisional_markets = cap_info.get("provisional_markets", [])
        result["supported_markets"] = supported_markets
        
        requires_resolution = cap_info.get("requires_target_resolution", False)
        if requires_resolution and not resolved_markets:
            result["status"] = "requires_target_resolution"
            results.append(result)
            continue

        # Check market support
        unsupported = False
        has_provisional = False
        
        for m in resolved_markets:
            if m in supported_markets:
                continue
            elif m in provisional_markets:
                has_provisional = True
            else:
                unsupported = True
                
        if unsupported:
            result["status"] = "unsupported"
            result["reason_codes"].append(CAPABILITY_UNSUPPORTED_FOR_MARKET)
            results.append(result)
            continue
            
        # Check parameter validity
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
            
        # Determine status based on support level and market type
        base_status = cap_info.get("support_status", "unsupported")
        
        if has_provisional:
            result["status"] = "provisional"
        else:
            result["status"] = base_status
            
        results.append(result)
        
    return results

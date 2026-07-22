import json
import jsonschema
import copy
from typing import Mapping, Sequence, Dict, Any, List

from scripts.m8r_05a_f3.request_validation_models import (
    UnifiedMarketEvidenceRequestValidation,
    REQUEST_SCHEMA_INVALID, UNSUPPORTED_SCHEMA_VERSION, 
    REQUIRED_TARGET_UNRESOLVED, REQUIRED_CAPABILITY_UNAVAILABLE,
    TARGET_LIMIT_EXCEEDED
)
from scripts.m8r_05a_f3.target_validator import validate_targets
from scripts.m8r_05a_f3.capability_validator import validate_capabilities
from scripts.m8r_03d_f1_security_master_snapshot_adapter import ValidatedVerifiedSecurityMasterSnapshot

def validate_unified_market_evidence_request(
    request: dict,
    *,
    security_master: ValidatedVerifiedSecurityMasterSnapshot,
    capability_catalog: dict,
    request_schema: dict,
    allow_fixture_snapshot: bool = False
) -> dict:
    """
    Main entry point for F3 Validation.
    """
    
    validation_result: UnifiedMarketEvidenceRequestValidation = {
        "schema_version": "unified_market_evidence_request_validation.v1",
        "request_id": request.get("request_id", ""),
        "validation_status": "valid",
        "request_schema_status": "valid",
        "capability_validation_status": "valid",
        "target_validation_status": "valid",
        "normalized_request": {},
        "target_results": [],
        "capability_results": [],
        "blocking_issues": [],
        "warnings": [],
        "limits": {
            "target_count": 0,
            "data_need_count": 0,
            "operation_count_computed": False,
            "operation_count": 0,
            "orchestrator_projection_required": True
        },
        "validation_metadata": {}
    }
    
    # 1. Schema Validation
    try:
        jsonschema.validate(instance=request, schema=request_schema)
    except jsonschema.exceptions.ValidationError as e:
        validation_result["validation_status"] = "invalid"
        validation_result["request_schema_status"] = "invalid"
        # Provide structural error
        json_path = "$"
        for p in e.path:
            if isinstance(p, int):
                json_path += f"[{p}]"
            else:
                json_path += f".{p}"
        validation_result["blocking_issues"].append({
            "reason_code": REQUEST_SCHEMA_INVALID,
            "json_path": json_path,
            "schema_path": ".".join([str(p) for p in e.absolute_schema_path]) if e.absolute_schema_path else "$",
            "message": e.message
        })
        # Short-circuit if schema is fundamentally broken
        return validation_result
        
    schema_version = request.get("schema_version")
    if schema_version != "unified_market_evidence_request.v1":
        validation_result["validation_status"] = "invalid"
        validation_result["request_schema_status"] = "invalid"
        validation_result["blocking_issues"].append({
            "reason_code": UNSUPPORTED_SCHEMA_VERSION,
            "json_path": "$.schema_version",
            "schema_path": "$.properties.schema_version",
            "message": f"Unsupported schema version: {schema_version}"
        })
        return validation_result

    # 2. Extract Data
    raw_targets = request.get("targets", [])
    data_needs = request.get("data_needs", [])
    validation_result["limits"]["target_count"] = len(raw_targets)
    validation_result["limits"]["data_need_count"] = len(data_needs)
    
    # Check limits against catalog
    bounds = capability_catalog.get("bounds", {})
    hard_target_limit = bounds.get("hard_target_limit", 50)
    if len(raw_targets) > hard_target_limit:
        validation_result["validation_status"] = "invalid"
        validation_result["target_validation_status"] = "invalid"
        validation_result["blocking_issues"].append({
            "reason_code": TARGET_LIMIT_EXCEEDED,
            "json_path": "$.targets",
            "schema_path": "$.properties.targets.maxItems",
            "message": f"Target count {len(raw_targets)} exceeds hard limit {hard_target_limit}"
        })
        return validation_result

    # 3. Validate Targets
    allowed_markets = sorted(capability_catalog.get("supported_markets", {}).keys())
    
    target_results = validate_targets(
        raw_targets, 
        security_master, 
        allowed_markets,
        allow_fixture_snapshot=allow_fixture_snapshot
    )
    validation_result["target_results"] = target_results
    
    # Deduce Target Validation Status
    resolved_markets = set()
    has_ambiguous = False
    has_invalid_targets = False
    
    for tr in target_results:
        res_status = tr["resolution_status"]
        if res_status == "resolved" and "canonical_identity" in tr:
            resolved_markets.add(tr["canonical_identity"]["market"])
        elif res_status == "ambiguous":
            has_ambiguous = True
        elif res_status == "duplicate":
            has_invalid_targets = True
            validation_result["blocking_issues"].append({
                "reason_code": "TARGET_DUPLICATE",
                "json_path": f"$.targets[{tr['target_index']}]",
                "schema_path": "",
                "message": f"Target index {tr['target_index']} is a duplicate."
            })
        else:
            has_invalid_targets = True
            validation_result["blocking_issues"].append({
                "reason_code": REQUIRED_TARGET_UNRESOLVED,
                "json_path": f"$.targets[{tr['target_index']}]",
                "schema_path": "",
                "message": f"Required target index {tr['target_index']} failed to resolve: {res_status}"
            })
            
    if has_invalid_targets:
        validation_result["target_validation_status"] = "invalid"
    elif has_ambiguous:
        validation_result["target_validation_status"] = "requires_clarification"
        
    # 4. Validate Capabilities
    capability_results = validate_capabilities(data_needs, capability_catalog, list(resolved_markets))
    validation_result["capability_results"] = capability_results
    
    has_unsupported_required = False
    has_unsupported_optional = False
    
    for cr in capability_results:
        status = cr["status"]
        priority = cr["priority"]
        if status in ["unsupported", "invalid_parameters", "unknown", "requires_target_resolution"]:
            if priority == "required":
                has_unsupported_required = True
                if status != "requires_target_resolution":
                    validation_result["blocking_issues"].append({
                        "reason_code": REQUIRED_CAPABILITY_UNAVAILABLE,
                        "json_path": "$.data_needs",
                        "schema_path": "",
                        "message": f"Required capability '{cr['type']}' is {status}"
                    })
            else:
                has_unsupported_optional = True
                validation_result["warnings"].append({
                    "reason_code": "OPTIONAL_CAPABILITY_UNAVAILABLE",
                    "message": f"Optional capability '{cr['type']}' is {status}"
                })
        
    if has_unsupported_required:
        validation_result["capability_validation_status"] = "unsupported"
    elif has_unsupported_optional:
        validation_result["capability_validation_status"] = "valid" # optional doesn't block valid
        
    # 5. Final Top-Level Status Deduction
    if validation_result["blocking_issues"]:
        # Precedence: 1. Schema/Bounds/Unresolved Invalid -> 2. Clarification -> 3. Unsupported
        if any(b["reason_code"] in [REQUEST_SCHEMA_INVALID, UNSUPPORTED_SCHEMA_VERSION, TARGET_LIMIT_EXCEEDED, REQUIRED_TARGET_UNRESOLVED] for b in validation_result["blocking_issues"]):
            validation_result["validation_status"] = "invalid"
        elif has_ambiguous:
            validation_result["validation_status"] = "requires_clarification"
        elif any(b["reason_code"] == REQUIRED_CAPABILITY_UNAVAILABLE for b in validation_result["blocking_issues"]):
            validation_result["validation_status"] = "unsupported"
        else:
            validation_result["validation_status"] = "invalid"
    elif has_ambiguous:
        validation_result["validation_status"] = "requires_clarification"
    else:
        validation_result["validation_status"] = "valid"
        
    # Normalized Request Population (Safe-copy)
    validation_result["normalized_request"] = copy.deepcopy(request)
        
    return validation_result

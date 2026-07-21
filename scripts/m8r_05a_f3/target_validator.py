from typing import Dict, Any, List
from scripts.m8r_05a_f3.request_validation_models import (
    TargetResult, CanonicalIdentity,
    TARGET_INPUT_EMPTY, TARGET_NOT_FOUND, TARGET_AMBIGUOUS,
    TARGET_MARKET_MISMATCH, MARKET_HINT_INVALID,
    TARGET_DUPLICATE, TARGET_MARKET_UNSUPPORTED,
    TARGET_SECURITY_TYPE_UNSUPPORTED
)
from scripts.m8r_03d_f1_security_master_snapshot_adapter import (
    ValidatedVerifiedSecurityMasterSnapshot,
    resolve_verified_security_identity
)

SUPPORTED_SECURITY_TYPES = {"equity", "etf"}
VALID_MARKETS = {"TWSE", "TPEX", "TAIFEX"}

def validate_targets(
    targets: List[Dict[str, Any]],
    security_master: ValidatedVerifiedSecurityMasterSnapshot,
    allowed_markets: List[str],
    *,
    allow_fixture_snapshot: bool = False
) -> List[TargetResult]:
    
    results: List[TargetResult] = []
    seen_targets = set()

    for index, target in enumerate(targets):
        input_str = target.get("input", "").strip()
        market_hint = target.get("market_hint")
        if market_hint:
            market_hint = market_hint.upper()
        res_req = target.get("resolution_requirement", "exact")
        
        result: TargetResult = {
            "target_index": index,
            "original_input": input_str,
            "resolution_requirement": res_req,
            "resolution_status": "not_found"
        }
        
        if market_hint is not None:
            result["market_hint"] = market_hint

        reason_codes = []
        
        if not input_str:
            result["resolution_status"] = "invalid_input"
            reason_codes.append(TARGET_INPUT_EMPTY)
            result["reason_codes"] = reason_codes
            results.append(result)
            continue

        if market_hint and market_hint not in VALID_MARKETS:
            result["resolution_status"] = "invalid_market_hint"
            reason_codes.append(MARKET_HINT_INVALID)
            result["reason_codes"] = reason_codes
            results.append(result)
            continue

        if market_hint and market_hint not in allowed_markets:
            result["resolution_status"] = "unsupported_market"
            reason_codes.append(TARGET_MARKET_UNSUPPORTED)
            result["reason_codes"] = reason_codes
            results.append(result)
            continue

        # Use M8R-03D-F1 resolver
        resolution = resolve_verified_security_identity(
            input_str, 
            security_master.lookup, 
            market_context=market_hint, 
            allow_fixture_snapshot=allow_fixture_snapshot, 
            execute_mode=True
        )

        res_status = resolution["resolution_status"]
        if res_status == "not_found":
            result["resolution_status"] = "not_found"
            if "market_mismatch" in resolution["reason_codes"]:
                reason_codes.append(TARGET_MARKET_MISMATCH)
            else:
                reason_codes.append(TARGET_NOT_FOUND)
        elif res_status == "ambiguous":
            result["resolution_status"] = "ambiguous"
            reason_codes.append(TARGET_AMBIGUOUS)
            # Map candidates to simplified F3 format
            candidate_matches = []
            for c in resolution["candidates"]:
                ident = c.get("identity", {})
                cls = c.get("classification", {})
                candidate_matches.append({
                    "security_code": ident.get("security_code"),
                    "market": cls.get("market"),
                    "security_name_zh": ident.get("security_name_zh"),
                    "security_type": cls.get("instrument_type")
                })
            candidate_matches.sort(key=lambda x: (x["market"] or "", x["security_code"] or ""))
            result["candidate_matches"] = candidate_matches
        elif res_status == "quarantined":
            result["resolution_status"] = "quarantined"
            # Keep reason code simple, could map to a specific one if needed
            reason_codes.append(TARGET_NOT_FOUND) 
        elif res_status == "resolved":
            selected = resolution["selected"]
            cls = selected.get("classification", {})
            sec_type = cls.get("instrument_type")
            
            if sec_type not in SUPPORTED_SECURITY_TYPES:
                result["resolution_status"] = "unsupported_security_type"
                reason_codes.append(TARGET_SECURITY_TYPE_UNSUPPORTED)
            else:
                canonical_id = selected.get("canonical_target_id")
                if canonical_id in seen_targets:
                    result["resolution_status"] = "duplicate"
                    reason_codes.append(TARGET_DUPLICATE)
                else:
                    result["resolution_status"] = "resolved"
                    seen_targets.add(canonical_id)
                    
                    ident = selected.get("identity", {})
                    lifecycle = selected.get("lifecycle", {})
                    
                    result["canonical_identity"] = {
                        "security_code": ident.get("security_code"),
                        "market": cls.get("market"),
                        "security_name_zh": ident.get("security_name_zh", ""),
                        "security_name_en": ident.get("security_name_en"),
                        "security_type": sec_type,
                        "listing_status": lifecycle.get("state"),
                        "effective_from": lifecycle.get("as_of"),
                        "effective_to": None,
                        "identity_source": "canonical_snapshot",
                        "identity_record_reference": selected.get("record_id")
                    }

        if reason_codes:
            result["reason_codes"] = reason_codes
            
        results.append(result)

    return results

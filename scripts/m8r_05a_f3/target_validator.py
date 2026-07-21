from typing import Sequence, Dict, Any, List, Optional
from scripts.m8r_05a_f3.request_validation_models import (
    TargetResult, CanonicalIdentity,
    TARGET_INPUT_EMPTY, TARGET_NOT_FOUND, TARGET_AMBIGUOUS,
    TARGET_MARKET_MISMATCH, MARKET_HINT_INVALID,
    TARGET_DUPLICATE, TARGET_MARKET_UNSUPPORTED,
    TARGET_SECURITY_TYPE_UNSUPPORTED
)
from scripts.m8r_05a_f3.security_master_loader import load_canonical_security_master

SUPPORTED_SECURITY_TYPES = {"equity", "etf"}
VALID_MARKETS = {"TWSE", "TPEX", "TAIFEX"}

def validate_targets(
    targets: List[Dict[str, Any]],
    security_master: Sequence[Dict[str, Any]],
    allowed_markets: List[str]
) -> List[TargetResult]:
    
    results: List[TargetResult] = []
    seen_targets = set()

    # Pre-process security master into a unified structure (handles dicts or already normalized lists)
    master_records = []
    for rec in security_master:
        if "security_name_zh" in rec and "security_code" in rec:
            master_records.append(rec) # Already normalized
        else:
            # Should not happen if passed through loader, but fallback safely
            master_records.append({
                "security_code": rec.get("security_code", rec.get("symbol", "")),
                "market": rec.get("market", "").upper(),
                "security_name_zh": rec.get("security_name_zh", rec.get("name", "")),
                "security_name_en": rec.get("security_name_en"),
                "security_type": rec.get("security_type", rec.get("instrument_type", "unknown")),
                "listing_status": rec.get("listing_status"),
                "effective_from": rec.get("effective_from"),
                "effective_to": rec.get("effective_to"),
                "identity_source": rec.get("identity_source"),
                "identity_record_reference": rec.get("identity_record_reference")
            })

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
        candidate_matches = []
        
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

        # Find matching candidates
        candidates = []
        for rec in master_records:
            match = False
            # Check exact code or exact name
            if rec["security_code"] == input_str:
                match = True
            elif rec["security_name_zh"] == input_str:
                match = True
            
            if match:
                candidates.append(rec)

        # Apply market hint if provided
        filtered_candidates = []
        if market_hint:
            filtered_candidates = [c for c in candidates if c["market"] == market_hint]
            if candidates and not filtered_candidates:
                # Code/Name exists but market does not match
                result["resolution_status"] = "market_mismatch"
                reason_codes.append(TARGET_MARKET_MISMATCH)
        else:
            filtered_candidates = candidates

        if not candidates:
            result["resolution_status"] = "not_found"
            reason_codes.append(TARGET_NOT_FOUND)
        elif candidates and not filtered_candidates:
            # handled by market_mismatch block above
            pass
        elif len(filtered_candidates) == 1:
            # Check security type
            canonical = filtered_candidates[0]
            if canonical["security_type"] not in SUPPORTED_SECURITY_TYPES:
                result["resolution_status"] = "unsupported_security_type"
                reason_codes.append(TARGET_SECURITY_TYPE_UNSUPPORTED)
            else:
                identity_key = f"{canonical['market']}:{canonical['security_code']}"
                if identity_key in seen_targets:
                    result["resolution_status"] = "duplicate"
                    reason_codes.append(TARGET_DUPLICATE)
                else:
                    result["resolution_status"] = "resolved"
                    result["canonical_identity"] = canonical
                    seen_targets.add(identity_key)
        else:
            # Multiple matches
            result["resolution_status"] = "ambiguous"
            reason_codes.append(TARGET_AMBIGUOUS)
            # Sort candidates for stable ordering
            filtered_candidates.sort(key=lambda x: (x["market"], x["security_code"]))
            candidate_matches = filtered_candidates

        if candidate_matches:
            result["candidate_matches"] = candidate_matches
        if reason_codes:
            result["reason_codes"] = reason_codes
            
        results.append(result)

    return results

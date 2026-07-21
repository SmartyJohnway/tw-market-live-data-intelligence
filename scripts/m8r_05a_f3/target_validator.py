from typing import Sequence, Dict, Any, List, Optional
from scripts.m8r_05a_f3.request_validation_models import (
    TargetResult, CanonicalIdentity,
    TARGET_INPUT_EMPTY, TARGET_NOT_FOUND, TARGET_AMBIGUOUS,
    TARGET_MARKET_MISMATCH, MARKET_HINT_INVALID,
    TARGET_DUPLICATE, TARGET_MARKET_UNSUPPORTED
)

def _extract_identity(record: Dict[str, Any]) -> CanonicalIdentity:
    """Extracts a CanonicalIdentity from a security master record.
    The record can come from m8a_official_eod_security_master.json or security_identity_snapshot.json.
    """
    if "identity" in record and "classification" in record:
        # Snapshot format
        identity = record["identity"]
        classification = record["classification"]
        return {
            "security_code": identity.get("security_code", ""),
            "market": classification.get("market", "").upper(),
            "security_name_zh": identity.get("security_name_zh", ""),
            "security_name_en": identity.get("security_name_en"),
            "security_type": classification.get("instrument_type", ""),
            "listing_status": record.get("lifecycle", {}).get("state"),
            "effective_from": None,
            "effective_to": None,
            "identity_source": record.get("snapshot_id"),
            "identity_record_reference": record.get("record_id")
        }
    elif "symbol" in record and "market" in record:
        # M8A config format
        market = record["market"].upper()
        if market == "LISTED":
            market = "TWSE"
        elif market == "TPEX_OTC":
            market = "TPEX"
        return {
            "security_code": record.get("symbol", ""),
            "market": market,
            "security_name_zh": record.get("name", record.get("symbol", "")),
            "security_name_en": None,
            "security_type": record.get("instrument_type", ""),
            "listing_status": None,
            "effective_from": None,
            "effective_to": None,
            "identity_source": "m8a_official_eod",
            "identity_record_reference": None
        }
    else:
        # Direct canonical identity fallback
        return {
            "security_code": record.get("security_code", ""),
            "market": record.get("market", "").upper(),
            "security_name_zh": record.get("security_name_zh", ""),
            "security_name_en": record.get("security_name_en"),
            "security_type": record.get("security_type", ""),
            "listing_status": record.get("listing_status"),
            "effective_from": record.get("effective_from"),
            "effective_to": record.get("effective_to"),
            "identity_source": record.get("identity_source"),
            "identity_record_reference": record.get("identity_record_reference")
        }

def validate_targets(
    targets: List[Dict[str, Any]],
    security_master: Sequence[Dict[str, Any]],
    allowed_markets: List[str]
) -> List[TargetResult]:
    
    results: List[TargetResult] = []
    seen_targets = set()

    # Pre-process security master into a unified structure
    master_records = [_extract_identity(rec) for rec in security_master]

    for index, target in enumerate(targets):
        input_str = target.get("input", "").strip()
        market_hint = target.get("market_hint")
        if market_hint:
            market_hint = market_hint.upper()
        res_req = target.get("resolution_requirement", "exact")
        
        result: TargetResult = {
            "target_index": index,
            "original_input": input_str,
            "market_hint": market_hint,
            "resolution_requirement": res_req,
            "resolution_status": "not_found",
            "canonical_identity": None,
            "candidate_matches": [],
            "reason_codes": [],
            "evidence_references": []
        }

        if not input_str:
            result["resolution_status"] = "invalid_input"
            result["reason_codes"].append(TARGET_INPUT_EMPTY)
            results.append(result)
            continue

        if market_hint and market_hint not in allowed_markets:
            result["resolution_status"] = "unsupported_market"
            result["reason_codes"].append(TARGET_MARKET_UNSUPPORTED)
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
                result["reason_codes"].append(TARGET_MARKET_MISMATCH)
        else:
            filtered_candidates = candidates

        if not candidates:
            result["resolution_status"] = "not_found"
            result["reason_codes"].append(TARGET_NOT_FOUND)
        elif candidates and not filtered_candidates:
            # handled by market_mismatch block above
            pass
        elif len(filtered_candidates) == 1:
            # Resolved
            canonical = filtered_candidates[0]
            identity_key = f"{canonical['market']}:{canonical['security_code']}"
            if identity_key in seen_targets:
                result["resolution_status"] = "duplicate"
                result["reason_codes"].append(TARGET_DUPLICATE)
            else:
                result["resolution_status"] = "resolved"
                result["canonical_identity"] = canonical
                seen_targets.add(identity_key)
        else:
            # Multiple matches
            result["resolution_status"] = "ambiguous"
            result["reason_codes"].append(TARGET_AMBIGUOUS)
            # Sort candidates for stable ordering
            filtered_candidates.sort(key=lambda x: (x["market"], x["security_code"]))
            result["candidate_matches"] = filtered_candidates

        results.append(result)

    return results

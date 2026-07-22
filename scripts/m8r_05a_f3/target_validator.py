"""F3 mapping layer over the governed M8R-03D-F1 canonical resolver."""
from scripts.m8r_03d_f1_security_master_snapshot_adapter import resolve_verified_security_identity
from .request_validation_models import *

def _identity(selected):
    identity = selected.get("identity") or {}; classification = selected.get("classification") or {}
    return {"canonical_target_id": selected.get("canonical_target_id"), "market": classification.get("market"), "security_code": identity.get("security_code"), "isin": identity.get("isin"), "security_name_zh": identity.get("security_name_zh"), "security_name_en": identity.get("security_name_en"), "instrument_type": classification.get("instrument_type"), "instrument_family": classification.get("instrument_family")}

def validate_target(target, index, *, security_master, supported_markets, seen, allow_fixture_snapshot):
    raw = target.get("input") if isinstance(target, dict) else None; hint = target.get("market_hint") if isinstance(target, dict) else None
    out = {"target_index": index, "original_input": raw if isinstance(raw, str) else "", "resolution_requirement": target.get("resolution_requirement", "exact") if isinstance(target, dict) else "exact", "resolution_status": "invalid_input"}
    if hint is not None: out["market_hint"] = hint
    if not isinstance(raw, str) or not raw.strip(): out["reason_codes"]=["TARGET_INPUT_INVALID"]; return out
    # The canonical request schema makes invalid hints unreachable in normal use.
    if hint is not None and hint not in supported_markets: out["resolution_status"]="invalid_market_hint"; out["reason_codes"]=["TARGET_MARKET_HINT_INVALID"]; return out
    resolved = resolve_verified_security_identity(raw.strip(), security_master.lookup, market_context=hint, allow_fixture_snapshot=allow_fixture_snapshot, execute_mode=True)
    status = resolved["resolution_status"]; candidates = sorted(resolved.get("candidates") or [], key=lambda x: ((x.get("classification") or {}).get("market") or "", (x.get("identity") or {}).get("security_code") or "", x.get("canonical_target_id") or ""))
    if candidates: out["candidate_matches"]=[_identity(x) for x in candidates]
    if status == "not_found":
        unscoped = resolve_verified_security_identity(raw.strip(), security_master.lookup, allow_fixture_snapshot=allow_fixture_snapshot, execute_mode=True) if hint else None
        mismatch = bool(unscoped and unscoped.get("candidate_count"))
        if mismatch: out["candidate_matches"]=[_identity(x) for x in sorted(unscoped.get("candidates") or [], key=lambda x: ((x.get("classification") or {}).get("market") or "", x.get("canonical_target_id") or ""))]
        out["resolution_status"]="market_mismatch" if mismatch else "not_found"; out["reason_codes"]=resolved.get("reason_codes",[]); return out
    if status == "ambiguous": out["resolution_status"]="ambiguous"; out["reason_codes"]=resolved.get("reason_codes",[]); return out
    selected=resolved.get("selected") or {}
    if selected: out["canonical_identity"]=_identity(selected)
    if status == "quarantined": out["resolution_status"]="quarantined"; out["reason_codes"]=resolved.get("reason_codes",[]); return out
    eligibility=selected.get("execution_eligibility") or {}; reasons=list(eligibility.get("reason_codes") or [])
    fixture=(security_master.lookup["by_canonical"].get(selected.get("canonical_target_id"),{}).get("observation") or {}).get("status")=="fixture_observation_only"
    effective=[x for x in reasons if not (fixture and allow_fixture_snapshot and x=="fixture_observation_only")]
    allowed=eligibility.get("status")=="allowed" or (fixture and allow_fixture_snapshot and eligibility.get("status")=="blocked" and not effective)
    if not allowed:
        unsupported="unsupported_instrument_type" in effective
        out["resolution_status"]="unsupported_security_type" if unsupported else "quarantined"; out["reason_codes"]=([REASON_SECURITY_TYPE_UNSUPPORTED] if unsupported else [REASON_IDENTITY_QUARANTINED])+effective; return out
    cid=selected.get("canonical_target_id")
    if cid in seen: out["resolution_status"]="duplicate"; out["reason_codes"]=[REASON_DUPLICATE]; return out
    seen.add(cid); out["resolution_status"]="resolved"; out["reason_codes"]=resolved.get("reason_codes",[]); return out

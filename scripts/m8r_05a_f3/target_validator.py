"""Deterministic, read-only resolution against a validated F1 snapshot."""
import re
from .request_validation_models import *

def _name(v): return re.sub(r"\s+", "", v or "").casefold()
def _identity(record):
    return {"canonical_target_id": record["canonical_target_id"], "market": (record.get("classification") or {}).get("market"), "security_code": (record.get("identity") or {}).get("security_code"), "isin": (record.get("identity") or {}).get("isin"), "security_name_zh": (record.get("identity") or {}).get("security_name_zh"), "security_name_en": (record.get("identity") or {}).get("security_name_en"), "instrument_type": (record.get("classification") or {}).get("instrument_type"), "instrument_family": (record.get("classification") or {}).get("instrument_family")}
def _sort(records): return sorted(records, key=lambda r: ((r.get("classification") or {}).get("market") or "", (r.get("identity") or {}).get("security_code") or "", r.get("canonical_target_id") or ""))

def validate_target(target, index, *, security_master, supported_markets, seen, allow_fixture_snapshot):
    raw = target.get("input") if isinstance(target, dict) else None
    requirement = target.get("resolution_requirement", "exact") if isinstance(target, dict) else "exact"
    out = {"target_index": index, "original_input": raw if isinstance(raw, str) else "", "resolution_requirement": requirement, "resolution_status": "invalid_input"}
    hint = target.get("market_hint") if isinstance(target, dict) else None
    if hint is not None: out["market_hint"] = hint
    if not isinstance(raw, str) or not raw.strip(): out["reason_codes"]=["TARGET_INPUT_INVALID"]; return out
    if hint is not None and (not isinstance(hint, str) or hint not in supported_markets):
        out["resolution_status"]="unsupported_market" if isinstance(hint,str) and hint.isupper() else "invalid_market_hint"; out["reason_codes"]=["TARGET_MARKET_UNSUPPORTED"]; return out
    records = security_master.snapshot.get("records", [])
    q=raw.strip(); uq=q.upper(); candidates=[]
    for r in records:
        i=r.get("identity") or {}
        if q == r.get("canonical_target_id") or uq == str(i.get("isin") or "").upper() or q == str(i.get("security_code") or "") or _name(q) in {_name(i.get("security_name_zh")), _name(i.get("security_name_en"))}:
            candidates.append(r)
    candidates=_sort(candidates)
    if not candidates: out["resolution_status"]="not_found"; out["reason_codes"]=["TARGET_NOT_FOUND"]; return out
    if hint and all((r.get("classification") or {}).get("market") != hint for r in candidates):
        out["resolution_status"]="market_mismatch"; out["candidate_matches"]=[_identity(r) for r in candidates]; out["reason_codes"]=["TARGET_MARKET_MISMATCH"]; return out
    if hint: candidates=[r for r in candidates if (r.get("classification") or {}).get("market")==hint]
    if len(candidates)>1:
        out["resolution_status"]="ambiguous"; out["candidate_matches"]=[_identity(r) for r in candidates]; out["reason_codes"]=["TARGET_AMBIGUOUS"]; return out
    r=candidates[0]; ident=_identity(r); out["canonical_identity"]=ident
    eligibility=r.get("execution_eligibility") or {}; reasons=list(eligibility.get("reason_codes") or [])
    fixture=(r.get("observation") or {}).get("status")=="fixture_observation_only"
    if fixture and not allow_fixture_snapshot: out["resolution_status"]="quarantined"; out["reason_codes"]=[REASON_FIXTURE_REJECTED]; return out
    effective=[x for x in reasons if not (fixture and allow_fixture_snapshot and x=="fixture_observation_only")]
    cls=r.get("classification") or {}; status=eligibility.get("status", "unknown")
    if fixture and allow_fixture_snapshot and status=="blocked" and not effective: status="allowed"
    if status != "allowed":
        unsupported="unsupported_instrument_type" in effective or "unsupported" in " ".join(effective).lower()
        out["resolution_status"]="unsupported_security_type" if unsupported else "quarantined"
        out["reason_codes"]=([REASON_SECURITY_TYPE_UNSUPPORTED] if unsupported else [REASON_IDENTITY_QUARANTINED])+effective
        return out
    cid=ident["canonical_target_id"]
    if cid in seen: out["resolution_status"]="duplicate"; out["reason_codes"]=[REASON_DUPLICATE]; return out
    seen.add(cid); out["resolution_status"]="resolved"; out["reason_codes"]=effective; return out

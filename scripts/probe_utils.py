import json
import hashlib
from datetime import datetime, timezone, timedelta

def get_taipei_time(utc_dt):
    # Taipei is UTC+8
    return utc_dt + timedelta(hours=8)

def generate_standard_envelope(
    probe_id,
    source,
    source_type,
    contract_status,
    http_status,
    url,
    method="GET",
    request_params=None,
    headers_used=None,
    requires_session=False,
    requires_auth=False,
    raw_sample=None,
    normalized_sample=None,
    freshness_status="unknown",
    staleness_seconds=None,
    delay_status="unknown",
    risk_level="low",
    risk_notes=None,
    ai_suitability="unknown",
    unsupported_targets=None,
    failed_targets=None,
    warnings=None,
    errors=None
):
    now_utc = datetime.now(timezone.utc)
    now_taipei = get_taipei_time(now_utc)

    # Calculate schema fingerprint if we have normalized sample
    schema_fingerprint = None
    schema_hash = None
    if normalized_sample:
        if isinstance(normalized_sample, dict):
            keys = sorted(normalized_sample.keys())
            schema_hash = hashlib.md5("".join(keys).encode()).hexdigest()
            schema_fingerprint = {"type": "dict", "keys": keys, "hash": schema_hash}
        elif isinstance(normalized_sample, list) and len(normalized_sample) > 0 and isinstance(normalized_sample[0], dict):
            keys = sorted(normalized_sample[0].keys())
            schema_hash = hashlib.md5("".join(keys).encode()).hexdigest()
            schema_fingerprint = {"type": "list_of_dict", "keys": keys, "hash": schema_hash}

    # Determine standard booleans and parsed statuses
    http_ok = str(http_status) == "200"
    parse_status = "success" if raw_sample is not None else "failed" if errors else "unknown"
    normalization_status = "success" if normalized_sample is not None else "failed" if (raw_sample is not None and not errors) else "failed" if errors else "unknown"

    if contract_status in ["doc_only", "auth_required"]:
        http_ok = False
        parse_status = "unknown"
        normalization_status = "unknown"

    is_usable_now = False
    if contract_status in ["http_pass", "parse_pass", "normalized_pass"]:
        is_usable_now = True

    potentially_usable_with_credentials = False
    if contract_status == "auth_required" or requires_auth:
        potentially_usable_with_credentials = True
        is_usable_now = False # Explicitly enforce

    if contract_status == "doc_only":
        is_usable_now = False

    envelope = {
        "probe_id": probe_id,
        "source": source,
        "source_type": source_type,
        "contract_status": contract_status,
        "retrieved_at_utc": now_utc.isoformat(),
        "retrieved_at_taipei": now_taipei.isoformat(),
        "request": {
            "url": url,
            "method": method,
            "params": request_params or {},
            "headers": headers_used or {}
        },
        "http_status": http_status,
        "http_ok": http_ok,
        "parse_status": parse_status,
        "normalization_status": normalization_status,
        "schema_fingerprint": schema_fingerprint,
        "schema_hash": schema_hash, # retained for legacy/compatibility
        "raw_sample_path": None, # Kept null unless actually saved to disk
        "normalized_sample_path": None, # Kept null unless actually saved to disk
        "raw_sample": raw_sample,
        "normalized_sample": normalized_sample,
        "freshness_status": freshness_status,
        "staleness_seconds": staleness_seconds,
        "delay_status": delay_status,
        "requires_auth": requires_auth,
        "requires_session": requires_session,
        "risk_level": risk_level,
        "risk_notes": risk_notes or [],
        "ai_suitability": ai_suitability,
        "is_usable_now": is_usable_now,
        "potentially_usable_with_credentials": potentially_usable_with_credentials,
        "unsupported_targets": unsupported_targets or [],
        "failed_targets": failed_targets or [],
        "warnings": warnings or [],
        "errors": errors or []
    }

    return envelope

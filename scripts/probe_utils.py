import json
import hashlib
from datetime import datetime, timezone

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
    risk_level="low",
    risk_notes=None,
    ai_suitability="unknown",
    error=None
):
    now_utc = datetime.now(timezone.utc)

    # Calculate a simple hash of the normalized sample schema keys if it exists
    schema_hash = None
    if normalized_sample and isinstance(normalized_sample, dict):
         schema_hash = hashlib.md5("".join(sorted(normalized_sample.keys())).encode()).hexdigest()
    elif normalized_sample and isinstance(normalized_sample, list) and len(normalized_sample) > 0 and isinstance(normalized_sample[0], dict):
         schema_hash = hashlib.md5("".join(sorted(normalized_sample[0].keys())).encode()).hexdigest()

    envelope = {
        "probe_id": probe_id,
        "source": source,
        "source_type": source_type,
        "contract_status": contract_status,
        "retrieved_at_utc": now_utc.isoformat(),
        "status": "pass" if error is None else "failed",
        "http_status": http_status,
        "url": url,
        "method": method,
        "request_params": request_params or {},
        "headers_used": headers_used or {},
        "requires_session": requires_session,
        "requires_auth": requires_auth,
        "schema_hash": schema_hash,
        "raw_sample": raw_sample,
        "normalized_sample": normalized_sample,
        "freshness_status": freshness_status,
        "staleness_seconds": staleness_seconds,
        "risk_level": risk_level,
        "risk_notes": risk_notes or [],
        "ai_suitability": ai_suitability
    }

    if error:
        envelope["error"] = str(error)

    return envelope

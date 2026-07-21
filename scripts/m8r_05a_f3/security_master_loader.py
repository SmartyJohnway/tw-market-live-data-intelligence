import json
import hashlib
from typing import Dict, Any, List

def load_canonical_security_master(source_path: str) -> List[Dict[str, Any]]:
    """
    Loads the canonical security master from the specified snapshot file.
    Validates structural integrity, deduplicates by target id, and returns valid records.
    """
    with open(source_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if "records" not in data:
        raise ValueError("Invalid security master format: missing 'records' array.")
    
    records = data["records"]
    valid_records = []
    seen_ids = set()

    for rec in records:
        target_id = rec.get("canonical_target_id")
        if not target_id:
            continue
        
        identity = rec.get("identity", {})
        classification = rec.get("classification", {})
        
        if not identity.get("security_code") or not classification.get("market"):
            continue # Malformed
            
        if target_id in seen_ids:
            continue # duplicate record governance
            
        seen_ids.add(target_id)
        
        valid_records.append({
            "security_code": identity["security_code"],
            "market": classification["market"],
            "security_name_zh": identity.get("security_name_zh", ""),
            "security_name_en": identity.get("security_name_en"),
            "security_type": classification.get("instrument_type", "unknown"),
            "listing_status": rec.get("lifecycle", {}).get("state"),
            "effective_from": rec.get("lifecycle", {}).get("as_of"),
            "effective_to": None,
            "identity_source": "canonical_snapshot",
            "identity_record_reference": rec.get("record_id")
        })

    return valid_records

#!/usr/bin/env python3
import json
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from generate_portable_catalog import (
    CANONICAL_PATH, 
    PORTABLE_JSON_PATH, 
    PORTABLE_GUIDE_PATH, 
    get_file_sha256,
    get_canonical_source_lineage,
    generate_portable_json_obj,
    generate_portable_markdown_text
)

def validate() -> bool:
    if not CANONICAL_PATH.exists():
        print("FAIL: Canonical catalog does not exist.")
        return False
    if not PORTABLE_JSON_PATH.exists():
        print("FAIL: Portable JSON catalog does not exist.")
        return False
    if not PORTABLE_GUIDE_PATH.exists():
        print("FAIL: Portable Quick Guide does not exist.")
        return False

    actual_canonical_hash = get_file_sha256(CANONICAL_PATH)

    try:
        with open(PORTABLE_JSON_PATH, "r", encoding="utf-8") as f:
            port = json.load(f)
    except Exception as e:
        print(f"FAIL: Failed to parse portable JSON. Error: {e}")
        return False

    recorded_hash = port.get("portable_metadata", {}).get("canonical_sha256")
    if actual_canonical_hash != recorded_hash:
        print(f"FAIL: Hash drift detected. Canonical hash: {actual_canonical_hash}, Portable recorded: {recorded_hash}")
        return False

    try:
        with open(CANONICAL_PATH, "r", encoding="utf-8") as f:
            canon = json.load(f)
    except Exception as e:
        print(f"FAIL: Failed to parse canonical JSON. Error: {e}")
        return False

    # Deep equality catches tampering. The direct checks below independently
    # protect Phase-G truth from a mutually reduced generator/validator.
    source_lineage = get_canonical_source_lineage(CANONICAL_PATH)
    expected_portable_data = generate_portable_json_obj(
        canon, actual_canonical_hash, source_lineage
    )
    
    # We compare the json dumps to ensure strict equivalence
    actual_json_str = json.dumps(port, sort_keys=True)
    expected_json_str = json.dumps(expected_portable_data, sort_keys=True)
    
    if actual_json_str != expected_json_str:
        print("FAIL: Deep equality validation failed. The portable JSON has been tampered with or is out of sync with the canonical source.")
        return False

    if port.get("contract_versions") != canon.get("contract_versions"):
        print("FAIL: Portable contract_versions drift from canonical Catalog.")
        return False
    for key in (
        "accepted_request_schema_versions",
        "preferred_request_schema_version",
        "emitted_result_schema_version",
    ):
        if port["contract_versions"].get(key) != canon["contract_versions"].get(key):
            print(f"FAIL: Portable contract version drift for {key}.")
            return False

    metadata = port.get("portable_metadata", {})
    for key, expected in source_lineage.items():
        if metadata.get(key) != expected:
            print(f"FAIL: Portable source-lineage drift for {key}.")
            return False

    canonical_capabilities = {
        item["capability_id"]: item for item in canon["data_need_capabilities"]
    }
    portable_capabilities = {
        item["capability_id"]: item for item in port["data_need_capabilities"]
    }
    for capability_id in (
        "material_disclosures", "monthly_revenue", "recent_performance"
    ):
        if portable_capabilities.get(capability_id, {}).get("support_status") != canonical_capabilities[capability_id]["support_status"]:
            print(f"FAIL: Portable support_status drift for {capability_id}.")
            return False
    for capability_id in ("material_disclosures", "monthly_revenue"):
        portable_capability = portable_capabilities[capability_id]
        canonical_capability = canonical_capabilities[capability_id]
        if portable_capability.get("historical_lookup_supported") is not False:
            print(f"FAIL: Portable historical lookup truth missing for {capability_id}.")
            return False
        if portable_capability.get("instrument_scope") != canonical_capability.get("instrument_scope"):
            print(f"FAIL: Portable instrument scope drift for {capability_id}.")
            return False

    # Byte-for-byte check for Markdown
    expected_md_text = generate_portable_markdown_text(expected_portable_data, actual_canonical_hash)
    actual_md_text = PORTABLE_GUIDE_PATH.read_text(encoding="utf-8")

    if expected_md_text != actual_md_text:
        print("FAIL: Portable Quick Guide markdown content mismatch. It has been tampered with or is out of sync.")
        return False

    print("PASS: Portable Skill catalog is fully synchronized with Canonical Catalog SoT (Deep Equality Verified).")
    return True

if __name__ == "__main__":
    if not validate():
        sys.exit(1)
    sys.exit(0)

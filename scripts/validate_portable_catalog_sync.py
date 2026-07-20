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

    commit_sha = port.get("portable_metadata", {}).get("generated_from_commit")
    if not commit_sha:
        print("FAIL: Missing generated_from_commit in portable metadata.")
        return False

    # Deep Equality Check for JSON
    expected_portable_data = generate_portable_json_obj(canon, actual_canonical_hash, commit_sha)
    
    # We compare the json dumps to ensure strict equivalence
    actual_json_str = json.dumps(port, sort_keys=True)
    expected_json_str = json.dumps(expected_portable_data, sort_keys=True)
    
    if actual_json_str != expected_json_str:
        print("FAIL: Deep equality validation failed. The portable JSON has been tampered with or is out of sync with the canonical source.")
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

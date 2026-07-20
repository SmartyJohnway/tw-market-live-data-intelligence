#!/usr/bin/env python3
import json
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_PATH = ROOT / "docs/data_capabilities/unified_market_evidence_capability_catalog.v1.json"
PORTABLE_JSON_PATH = ROOT / "skills/tw-market-evidence-agent/assets/unified_capability_catalog_portable.json"
PORTABLE_GUIDE_PATH = ROOT / "skills/tw-market-evidence-agent/references/capability_quick_guide.md"

def get_file_sha256(path: Path) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

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

    # Load Portable JSON
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

    # Load Canonical Source
    try:
        with open(CANONICAL_PATH, "r", encoding="utf-8") as f:
            canon = json.load(f)
    except Exception as e:
        print(f"FAIL: Failed to parse canonical JSON. Error: {e}")
        return False

    # Verify Capability Record Count and IDs
    canon_caps = {c["capability_id"]: c for c in canon.get("data_need_capabilities", [])}
    port_caps = {c["capability_id"]: c for c in port.get("data_need_capabilities", [])}

    if set(canon_caps.keys()) != set(port_caps.keys()):
        print(f"FAIL: Capability ID mismatch. Canonical: {list(canon_caps.keys())}, Portable: {list(port_caps.keys())}")
        return False

    # Verify Markdown contains the correct source hash
    guide_text = PORTABLE_GUIDE_PATH.read_text(encoding="utf-8")
    expected_hash_line = f"Source Registry Hash**: `{actual_canonical_hash}`"
    if expected_hash_line not in guide_text:
        print("FAIL: Portable Quick Guide markdown contains outdated source hash or is out of sync.")
        return False

    print("PASS: Portable Skill catalog is fully synchronized with Canonical Catalog SoT.")
    return True

if __name__ == "__main__":
    if not validate():
        sys.exit(1)
    sys.exit(0)

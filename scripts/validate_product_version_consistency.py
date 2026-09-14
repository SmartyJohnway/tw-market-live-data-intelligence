#!/usr/bin/env python3
"""Offline guard against divergent product-version claims."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.product_version import product_version

CURRENT_DOCUMENTS = (
    ROOT / "README.md",
    ROOT / "CHANGELOG.md",
    ROOT / "docs/contracts/v1_public_contracts.json",
    ROOT / "docs/release/V1_RELEASE.md",
)


def main() -> int:
    version = product_version()
    missing = [str(path.relative_to(ROOT)) for path in CURRENT_DOCUMENTS if version not in path.read_text(encoding="utf-8")]
    if missing:
        print(json.dumps({"status": "FAIL", "reason_code": "product_version_document_drift", "missing": missing}))
        return 1
    inventory = json.loads((ROOT / "docs/contracts/v1_public_contracts.json").read_text(encoding="utf-8"))
    if inventory.get("product_version_authority") != "VERSION":
        print(json.dumps({"status": "FAIL", "reason_code": "product_version_authority_drift"}))
        return 1
    print(json.dumps({"status": "PASS", "product_version": version, "authority": "VERSION"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

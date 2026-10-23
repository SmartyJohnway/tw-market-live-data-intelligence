"""Package-local entry dispatch; no initialization or acquisition side effects."""
from __future__ import annotations

import json
import os
from pathlib import Path
import runpy
import sys

from package_integrity import verify_bundle


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    report = verify_bundle(root)
    marker = json.loads((root / "runtime/runtime-marker.json").read_text(encoding="utf-8"))
    if marker != {"bundle_root": str(root), "manifest_canonical_sha256": report["manifest_canonical_sha256"]}:
        raise RuntimeError("stale runtime: remove derived runtime directory and bootstrap again")
    if Path(sys.prefix).resolve() != root / "runtime/venv":
        raise RuntimeError("bundle-local venv required")
    entries = {"market": "tw_market.py", "mcp": "run_unified_market_evidence_mcp.py", "security-master": "manage_security_master.py"}
    entry = entries[sys.argv[1]]
    os.environ.pop("PYTHONPATH", None)
    os.environ.pop("PYTHONHOME", None)
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    sys.dont_write_bytecode = True
    app = root / "app"
    sys.path.insert(0, str(app))
    sys.argv = [str(app / "scripts" / entry), *sys.argv[2:]]
    runpy.run_path(sys.argv[0], run_name="__main__")


if __name__ == "__main__":
    main()

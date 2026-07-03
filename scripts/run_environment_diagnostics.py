#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.operator_workbench import environment_checks

def main() -> int:
    ap = argparse.ArgumentParser(description="Readonly environment diagnostics; never modifies repository state.")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    checks = environment_checks()
    if args.json:
        print(json.dumps({"checks": [c.__dict__ for c in checks], "writes": False, "network_calls": False}, indent=2, sort_keys=True))
    else:
        print("Environment Diagnostics (readonly, no network, no writes)")
        for c in checks:
            print(f"[{c.status}] {c.name}: {c.detail}")
            if c.status != "PASS" and c.suggestion:
                print(f"  Suggested command: {c.suggestion}")
    return 0 if all(c.status in {"PASS", "CAVEAT"} for c in checks) else 1
if __name__ == "__main__": raise SystemExit(main())

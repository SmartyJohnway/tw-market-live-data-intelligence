#!/usr/bin/env python3
from __future__ import annotations
import argparse, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.operator_workbench import print_dashboard, status_report

def main() -> int:
    ap = argparse.ArgumentParser(description="Offline local operator workbench launcher and dashboard.")
    ap.add_argument("--json", action="store_true", help="Print machine-readable status.")
    ap.add_argument("--execute-live-observation", action="store_true", help="Not run by the workbench; prints the explicit bounded observation command instead.")
    args = ap.parse_args()
    report = status_report()
    if args.json:
        import json
        safe = report | {"checks": [c.__dict__ for c in report["checks"]]}
        print(json.dumps(safe, indent=2, sort_keys=True))
    else:
        print_dashboard(report)
        if args.execute_live_observation:
            print("\nLive observation remains explicit and bounded. Run manually:")
            print("python scripts/run_m5k_live_observation.py --watchlist config/m5k_default_watchlist.json --execute-live-observation --ssl-policy strict")
    return 0
if __name__ == "__main__": raise SystemExit(main())

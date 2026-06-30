#!/usr/bin/env python3
from __future__ import annotations
import argparse, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.m5k_common import dump_json
from scripts.m5q_source_health import build_report, execute_health_probe


def main() -> int:
    ap = argparse.ArgumentParser(description="Manual bounded M5Q source-health regression probe.")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check-only", action="store_true", help="No network, no writes; validate route plan and governance boundaries.")
    mode.add_argument("--execute-health-probe", action="store_true", help="Explicit bounded network probe and source-health artifact write.")
    args = ap.parse_args()
    report = build_report(execution_mode="check_only") if args.check_only else execute_health_probe()
    print(dump_json(report))
    return 0 if report.get("governance", {}).get("validation", {}).get("valid") and report.get("governance", {}).get("adapter_matrix_validation", {}).get("valid") else 2

if __name__ == "__main__":
    raise SystemExit(main())

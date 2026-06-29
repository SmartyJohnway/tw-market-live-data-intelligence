#!/usr/bin/env python3
from __future__ import annotations
import argparse, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.m5k_common import DEFAULT_WATCHLIST_PATH, dump_json, execute_live_observation, load_json, plan_live_observation


def main() -> int:
    ap = argparse.ArgumentParser(description="Execute one explicit bounded M5K live observation from a watchlist JSON file.")
    ap.add_argument("--watchlist", default=str(DEFAULT_WATCHLIST_PATH))
    ap.add_argument("--execute-live-observation", action="store_true")
    ap.add_argument("--plan-only", action="store_true")
    ap.add_argument("--no-write-latest", action="store_true")
    args = ap.parse_args()
    watchlist = load_json(Path(args.watchlist))
    if args.plan_only or not args.execute_live_observation:
        result = plan_live_observation(watchlist)
        if not args.plan_only:
            result["status"] = "check_only"
            result["execute_mode_available"] = True
        print(dump_json(result))
        return 0 if result.get("validation", {}).get("valid") is True else 2
    result = execute_live_observation(watchlist, write_latest=not args.no_write_latest)
    print(dump_json(result))
    return 0 if result.get("status") in {"ok", "completed_with_no_observations"} else 2

if __name__ == "__main__":
    raise SystemExit(main())

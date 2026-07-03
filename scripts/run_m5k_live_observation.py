#!/usr/bin/env python3
from __future__ import annotations
import argparse, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.m5k_common import DEFAULT_WATCHLIST_PATH, dump_json, execute_live_observation, load_json, plan_live_observation
from scripts.ssl_policy import VALID_SSL_POLICIES, resolve_ssl_policy, ssl_policy_diagnostics


def main() -> int:
    ap = argparse.ArgumentParser(description="Execute one explicit bounded M5K live observation from a watchlist JSON file.")
    ap.add_argument("--watchlist", default=str(DEFAULT_WATCHLIST_PATH))
    ap.add_argument("--execute-live-observation", action="store_true")
    ap.add_argument("--plan-only", action="store_true")
    ap.add_argument("--no-write-latest", action="store_true")
    ap.add_argument("--ssl-policy", choices=sorted(VALID_SSL_POLICIES), default=None, help="TLS policy for explicit live observation. CLI overrides TW_MARKET_SSL_POLICY; default is strict.")
    args = ap.parse_args()
    try:
        selected_ssl_policy = resolve_ssl_policy(args.ssl_policy)
    except ValueError as exc:
        ap.error(str(exc))
    watchlist = load_json(Path(args.watchlist))
    if args.plan_only or not args.execute_live_observation:
        result = plan_live_observation(watchlist)
        if not args.plan_only:
            result["status"] = "check_only"
            result["execute_mode_available"] = True
            result["diagnostics"] = result.get("diagnostics", {}) | {"ssl_policy": ssl_policy_diagnostics(selected_ssl_policy, network_calls_may_have_occurred=False)}
        print(dump_json(result))
        return 0 if result.get("validation", {}).get("valid") is True else 2
    result = execute_live_observation(watchlist, write_latest=not args.no_write_latest, ssl_policy=selected_ssl_policy)
    print(dump_json(result))
    return 0 if result.get("status") in {"ok", "completed_with_no_observations"} else 2

if __name__ == "__main__":
    raise SystemExit(main())

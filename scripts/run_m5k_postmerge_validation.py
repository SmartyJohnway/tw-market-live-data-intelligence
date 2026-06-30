#!/usr/bin/env python3
"""Non-network M5K post-merge validation checks."""
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.m5k_common import load_json, plan_live_observation, validate_watchlist, execute_live_observation


def changed_files() -> list[str]:
    out = subprocess.check_output(["git", "diff", "--name-only", "HEAD"], cwd=ROOT, text=True)
    return [x for x in out.splitlines() if x]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-only", action="store_true", help="run offline checks only; never execute network observation")
    args = ap.parse_args(argv)
    failures=[]
    watchlist = load_json(ROOT/"config/m5k_default_watchlist.json")
    validation=validate_watchlist(watchlist)
    plan=plan_live_observation(watchlist)
    invalid=execute_live_observation({"schema_version":"m5k_watchlist.v1","categories":[]}, write_latest=False)
    files=changed_files()
    def check(name, ok, detail=None):
        if not ok: failures.append({"check":name,"detail":detail})
    check("m5f_level_1_package_present", (ROOT/"research/staging/m5f/m5f_canonical_market_context_01/canonical_market_context.json").is_file())
    check("m5k_level_2_noncanonical", plan["governance"]["canonical"] is False and plan["governance"]["plan_only"] is True)
    check("m5k_no_m5f_mutation", not any(p.startswith("research/staging/m5f/") for p in files), files)
    check("m5k_no_frontend_public_write", not any(p.startswith("frontend/public/") for p in files), files)
    check("m5k_no_research_generated_write", not any(p.startswith("research/generated/") for p in files), files)
    check("startup_network_free", plan["governance"]["network_free_startup"] is True and plan["governance"]["network_calls"] is False)
    check("watchlist_valid", validation["valid"] is True, validation)
    check("live_observation_explicit_only", invalid["status"] == "failed_closed_invalid_watchlist")
    routes={r["symbol"]:r for r in plan["planned_routes"]}
    check("mode_a_b_c_documented", (ROOT/"docs/m5k_local_ai_workflow.md").read_text(encoding="utf-8").count("Mode ") >= 3)
    check("tx_futures_adapter_planned", routes.get("TX",{}).get("adapter_id") == "taifex_mis_tx_futures_quote" and routes.get("TX",{}).get("status") == "planned", routes.get("TX"))
    result={"ok": not failures, "check_only": args.check_only, "network_calls": False, "failures": failures}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not failures else 1
if __name__ == "__main__":
    raise SystemExit(main())

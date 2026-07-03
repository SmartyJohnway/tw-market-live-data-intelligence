#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.operator_workbench import OBS_PATH, SOURCE_HEALTH_JSON, SOURCE_HEALTH_MD, WATCHLIST_PATH, environment_checks, latest_artifact_time, repository_version

ROOT = Path(__file__).resolve().parents[1]
COMMANDS = [
    ("M5F validation", [sys.executable, "scripts/validate_m5f_canonical_market_context_package.py", "--package-dir", "research/staging/m5f/m5f_canonical_market_context_01"]),
    ("M5IJ acceptance", [sys.executable, "scripts/run_m5ij_end_to_end_acceptance.py", "--check-only"]),
    ("M5K postmerge", [sys.executable, "scripts/run_m5k_postmerge_validation.py", "--check-only"]),
    ("M5Q source health plan", [sys.executable, "scripts/run_m5q_source_health_probe.py", "--check-only"]),
    ("M6B source contract plan", [sys.executable, "scripts/run_m6b_source_contract_preflight.py", "--check-only"]),
]

def run_command(label: str, cmd: list[str]) -> dict:
    cp = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=60)
    return {"label": label, "command": " ".join(cmd).replace(sys.executable, "python", 1), "status": "PASS" if cp.returncode == 0 else "FAIL", "returncode": cp.returncode, "stdout_tail": cp.stdout[-1200:], "stderr_tail": cp.stderr[-1200:]}

def main() -> int:
    ap = argparse.ArgumentParser(description="Operator release preflight aggregator; no network and no duplicated validation logic.")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    env = environment_checks()
    results = [{"label": "Environment", "status": "PASS" if all(c.status in {"PASS", "CAVEAT"} for c in env) else "FAIL", "checks": [c.__dict__ for c in env]}]
    results.extend(run_command(label, cmd) for label, cmd in COMMANDS)
    caveats = []
    if not OBS_PATH.exists(): caveats.append("Latest observation missing; acceptable if no fresh Mode B context is needed.")
    if not (SOURCE_HEALTH_JSON.exists() or SOURCE_HEALTH_MD.exists()): caveats.append("Latest source-health artifact missing; execute M5Q only when release diagnostics require current health evidence.")
    status = "FAIL" if any(r["status"] == "FAIL" for r in results) else ("PASS WITH CAVEATS" if caveats or any(c.status == "CAVEAT" for c in env) else "PASS")
    payload = {"status": status, "repository": repository_version(), "latest_release_version": repository_version()["version"], "watchlist": WATCHLIST_PATH.relative_to(ROOT).as_posix(), "latest_observation": latest_artifact_time(OBS_PATH) if OBS_PATH.exists() else "missing", "latest_source_health": latest_artifact_time(SOURCE_HEALTH_JSON) if SOURCE_HEALTH_JSON.exists() else ("present markdown" if SOURCE_HEALTH_MD.exists() else "missing"), "results": results, "caveats": caveats, "network_calls": False, "writes": "only child validators with documented check-only behavior; no live observation executed"}
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Operator Release Preflight: {status}")
        print(f"Version: {payload['latest_release_version']} Branch: {payload['repository']['branch']} Commit: {payload['repository']['commit']}")
        for r in results:
            print(f"- [{r['status']}] {r['label']}")
            if r.get("command"): print(f"  command: {r['command']}")
        for caveat in caveats: print(f"- [CAVEAT] {caveat}")
        print(f"Latest observation: {payload['latest_observation']}")
        print(f"Latest source health: {payload['latest_source_health']}")
    return 0 if status != "FAIL" else 1
if __name__ == "__main__": raise SystemExit(main())

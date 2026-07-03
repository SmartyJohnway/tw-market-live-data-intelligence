#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.operator_workbench import OBS_PATH, SOURCE_HEALTH_JSON, SOURCE_HEALTH_MD, WATCHLIST_PATH, environment_checks, latest_artifact_time, repository_version

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TIMEOUT_SECONDS = 300
TIMEOUT_ENV_VAR = "TW_MARKET_OPERATOR_PREFLIGHT_TIMEOUT_SECONDS"
COMMANDS = [
    ("M5F validation", [sys.executable, "scripts/validate_m5f_canonical_market_context_package.py", "--package-dir", "research/staging/m5f/m5f_canonical_market_context_01"]),
    ("M5IJ acceptance", [sys.executable, "scripts/run_m5ij_end_to_end_acceptance.py", "--check-only"]),
    ("M5K postmerge", [sys.executable, "scripts/run_m5k_postmerge_validation.py", "--check-only"]),
    ("M5Q source health plan", [sys.executable, "scripts/run_m5q_source_health_probe.py", "--check-only"]),
    ("M6B source contract plan", [sys.executable, "scripts/run_m6b_source_contract_preflight.py", "--check-only"]),
]

def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise argparse.ArgumentTypeError("timeout must be a positive integer") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("timeout must be a positive integer")
    return parsed

def resolve_timeout_seconds(cli_timeout: int | None, environ: dict[str, str] | None = None) -> int:
    if cli_timeout is not None:
        return cli_timeout
    env = os.environ if environ is None else environ
    raw = env.get(TIMEOUT_ENV_VAR)
    if raw is None or raw == "":
        return DEFAULT_TIMEOUT_SECONDS
    try:
        return positive_int(raw)
    except argparse.ArgumentTypeError as exc:
        raise ValueError(f"Invalid {TIMEOUT_ENV_VAR}={raw!r}: {exc}") from exc

def command_display(cmd: list[str]) -> str:
    return " ".join(cmd).replace(sys.executable, "python", 1)

def run_command(label: str, cmd: list[str], timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS) -> dict:
    try:
        cp = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=timeout_seconds)
    except subprocess.TimeoutExpired as exc:
        message = f"Command timed out after {timeout_seconds} seconds. Increase --timeout-seconds or {TIMEOUT_ENV_VAR} if this machine is slow."
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        return {"label": label, "command": command_display(cmd), "status": "FAIL", "returncode": None, "timeout_seconds": timeout_seconds, "timed_out": True, "diagnostic": message, "stdout_tail": stdout[-1200:], "stderr_tail": (stderr + ("\n" if stderr else "") + message)[-1200:]}
    return {"label": label, "command": command_display(cmd), "status": "PASS" if cp.returncode == 0 else "FAIL", "returncode": cp.returncode, "timeout_seconds": timeout_seconds, "timed_out": False, "stdout_tail": cp.stdout[-1200:], "stderr_tail": cp.stderr[-1200:]}

def build_preflight(timeout_seconds: int) -> dict:
    env = environment_checks()
    results = [{"label": "Environment", "status": "PASS" if all(c.status in {"PASS", "CAVEAT"} for c in env) else "FAIL", "checks": [c.__dict__ for c in env]}]
    results.extend(run_command(label, cmd, timeout_seconds) for label, cmd in COMMANDS)
    caveats = []
    if not OBS_PATH.exists(): caveats.append("Latest observation missing; acceptable if no fresh Mode B context is needed.")
    if not (SOURCE_HEALTH_JSON.exists() or SOURCE_HEALTH_MD.exists()): caveats.append("Latest source-health artifact missing; execute M5Q only when release diagnostics require current health evidence.")
    status = "FAIL" if any(r["status"] == "FAIL" for r in results) else ("PASS WITH CAVEATS" if caveats or any(c.status == "CAVEAT" for c in env) else "PASS")
    return {"status": status, "timeout_seconds": timeout_seconds, "repository": repository_version(), "latest_release_version": repository_version()["version"], "watchlist": WATCHLIST_PATH.relative_to(ROOT).as_posix(), "latest_observation": latest_artifact_time(OBS_PATH) if OBS_PATH.exists() else "missing", "latest_source_health": latest_artifact_time(SOURCE_HEALTH_JSON) if SOURCE_HEALTH_JSON.exists() else ("present markdown" if SOURCE_HEALTH_MD.exists() else "missing"), "results": results, "caveats": caveats, "network_calls": False, "writes": "only child validators with documented check-only behavior; no live observation executed"}

def main() -> int:
    ap = argparse.ArgumentParser(description="Operator release preflight aggregator; no network and no duplicated validation logic.")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--timeout-seconds", type=positive_int, help=f"Positive per-command timeout. Defaults to {DEFAULT_TIMEOUT_SECONDS}; env override: {TIMEOUT_ENV_VAR}.")
    args = ap.parse_args()
    try:
        timeout_seconds = resolve_timeout_seconds(args.timeout_seconds)
    except ValueError as exc:
        ap.error(str(exc))
    payload = build_preflight(timeout_seconds)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Operator Release Preflight: {payload['status']}")
        print(f"Timeout seconds per command: {payload['timeout_seconds']}")
        print(f"Version: {payload['latest_release_version']} Branch: {payload['repository']['branch']} Commit: {payload['repository']['commit']}")
        for r in payload["results"]:
            print(f"- [{r['status']}] {r['label']}")
            if r.get("command"): print(f"  command: {r['command']}")
            if r.get("timed_out") or r.get("diagnostic"): print(f"  diagnostic: {r.get('diagnostic')}")
        for caveat in payload["caveats"]: print(f"- [CAVEAT] {caveat}")
        print(f"Latest observation: {payload['latest_observation']}")
        print(f"Latest source health: {payload['latest_source_health']}")
    return 0 if payload["status"] != "FAIL" else 1
if __name__ == "__main__": raise SystemExit(main())

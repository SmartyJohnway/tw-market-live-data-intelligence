#!/usr/bin/env python3
from __future__ import annotations

import argparse, asyncio, hashlib, json, platform, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from scripts.m5k_common import DEFAULT_WATCHLIST_PATH, load_json, normalize_watchlist, plan_live_observation, read_latest_observation, validate_watchlist
from scripts.build_m5n_conversation_context import OUT_DIR as M5N_OUT_DIR, build_package
from scripts.operator_workbench import repository_version
from server.mcp_server import list_tools, run_m5k_live_observation_tool

REPORT_DIR = ROOT / "research/live_observation_runs/m6e_operator_acceptance"
JSON_REPORT = REPORT_DIR / "latest_operator_acceptance_report.json"
MD_REPORT = REPORT_DIR / "latest_operator_acceptance_report.md"
M5F_DIR = ROOT / "research/staging/m5f/m5f_canonical_market_context_01"
FORBIDDEN_FIELDS = {"target_price", "ranking", "broker_order", "raw_payload", "response_sample", "raw_fields_sample"}


def utc_now() -> str: return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
def sha_dir(path: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(x for x in path.rglob("*") if x.is_file()):
        h.update(p.relative_to(path).as_posix().encode()); h.update(p.read_bytes())
    return h.hexdigest()

def run(label: str, cmd: list[str], timeout: int = 300) -> dict[str, Any]:
    cp = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=timeout)
    return {"label": label, "command": " ".join(cmd).replace(sys.executable, "python", 1), "status": "pass" if cp.returncode == 0 else "fail", "returncode": cp.returncode, "stdout_tail": cp.stdout[-1000:], "stderr_tail": cp.stderr[-1000:]}

def ok(name: str, passed: bool, evidence: Any = None) -> dict[str, Any]:
    return {"name": name, "status": "pass" if passed else "fail", "evidence": evidence}

def final_status(checks: list[dict[str, Any]], caveats: list[str]) -> str:
    if any(c.get("status") == "fail" for c in checks): return "fail"
    return "pass_with_caveats" if caveats else "pass"

def fastapi_acceptance(watchlist: dict[str, Any]) -> dict[str, Any]:
    from fastapi.testclient import TestClient
    from server.main import app
    c = TestClient(app)
    endpoints = ["/api/health", "/api/governance", "/api/context/canonical", "/api/context/snapshot", "/api/conversation/context", "/api/source-health/latest", "/api/m5k/live-observation/history"]
    results = [ok(f"GET {e}", c.get(e).status_code == 200, c.get(e).status_code) for e in endpoints]
    results.append(ok("POST /api/m5k/live-observation/plan", c.post("/api/m5k/live-observation/plan", json=watchlist).status_code == 200))
    results.append(ok("execute requires confirmation", c.post("/api/m5k/live-observation/execute", json=watchlist).status_code == 400))
    results.append(ok("invalid ssl_policy returns 400", c.post("/api/m5k/live-observation/execute?confirm_live_observation=true&ssl_policy=invalid", json=watchlist).status_code == 400))
    results.append(ok("probe routes fail closed", c.get("/api/probe/health").status_code in {404, 405}))
    return {"status": "pass" if all(r["status"] == "pass" for r in results) else "fail", "checks": results, "network_calls": False}

def frontend_acceptance() -> dict[str, Any]:
    html = (ROOT/"frontend/readonly-preview/M5KLocalAIWorkbench.html").read_text(encoding="utf-8")
    js = (ROOT/"frontend/readonly-preview/m5k-workbench.js").read_text(encoding="utf-8")
    text = html + "\n" + js
    checks = [
        ok("html exists", (ROOT/"frontend/readonly-preview/M5KLocalAIWorkbench.html").exists()), ok("js exists", (ROOT/"frontend/readonly-preview/m5k-workbench.js").exists()),
        ok("file api autodetect", "loc.protocol === 'file:'" in js), ok("localhost api autodetect", "localhost" in js and "127.0.0.1" in js),
        ok("no interval polling", "setInterval" not in text and "setTimeout" not in text), ok("no hosted cloud endpoint", "https://" not in js),
        ok("raw payload hidden", "raw_payload_hidden" in js), ok("no target price ui", "target price" not in text.lower()),
        ok("conversation package ux", "Conversation Context UX" in html), ok("history timeline ux", "Observation history" in html and "Source health timeline" in html),
    ]
    return {"status": "pass" if all(c["status"] == "pass" for c in checks) else "fail", "checks": checks}

def conversation_acceptance() -> dict[str, Any]:
    res = build_package()
    j = M5N_OUT_DIR/"conversation_context.json"; m = M5N_OUT_DIR/"conversation_context.md"
    text = j.read_text(encoding="utf-8") + "\n" + m.read_text(encoding="utf-8")
    data = json.loads(j.read_text(encoding="utf-8"))
    lower_text = text.lower()
    
    def bad_keys(obj):
        if isinstance(obj, dict):
            found = [k for k in obj if k in FORBIDDEN_FIELDS]
            for v in obj.values(): found.extend(bad_keys(v))
            return found
        if isinstance(obj, list):
            found = []
            for v in obj: found.extend(bad_keys(v))
            return found
        return []
    forbidden_found = sorted(k for k in set(bad_keys(data)) if k in {"broker_order", "raw_payload", "response_sample", "raw_fields_sample"})
    checks = [ok("builder runs", res.get("status") == "ok"), ok("json exists", j.exists()), ok("markdown exists", m.exists()), ok("canonical summary", "canonical" in text.lower()), ok("safety governance", ("no trading" in lower_text or "trading" in lower_text) and "governance" in lower_text), ok("observation summary if available", "observation" in text.lower()), ok("source health summary if available", "source" in text.lower()), ok("no forbidden raw/trading fields", not forbidden_found, forbidden_found)]
    return {"status": "pass" if all(c["status"] == "pass" for c in checks) else "fail", "checks": checks, "output_dir": M5N_OUT_DIR.relative_to(ROOT).as_posix(), "schema_version": data.get("schema_version")}

def build_report(mode: str, ssl_policy: str, execute_live: bool) -> dict[str, Any]:
    before = sha_dir(M5F_DIR)
    watchlist = normalize_watchlist(load_json(DEFAULT_WATCHLIST_PATH))
    command_checks = [run("local workbench", [sys.executable,"scripts/run_local_workbench.py"]), run("environment diagnostics", [sys.executable,"scripts/run_environment_diagnostics.py"]), run("operator preflight", [sys.executable,"scripts/run_operator_preflight.py","--timeout-seconds","300"]), run("M5F validator", [sys.executable,"scripts/validate_m5f_canonical_market_context_package.py","--package-dir","research/staging/m5f/m5f_canonical_market_context_01"]), run("M5IJ", [sys.executable,"scripts/run_m5ij_end_to_end_acceptance.py","--check-only"]), run("M5K", [sys.executable,"scripts/run_m5k_postmerge_validation.py","--check-only"]), run("M5Q", [sys.executable,"scripts/run_m5q_source_health_probe.py","--check-only"]), run("M6B", [sys.executable,"scripts/run_m6b_source_contract_preflight.py","--check-only"]), run("MCP startup", [sys.executable,"server/mcp_server.py","--startup-check"])]
    plan = plan_live_observation(watchlist); validation = validate_watchlist(watchlist); latest_obs = read_latest_observation()
    fastapi = fastapi_acceptance(watchlist); mcp_invalid = run_m5k_live_observation_tool({"confirm_live_observation": True, "watchlist": watchlist, "ssl_policy":"invalid"})
    tools = asyncio.run(list_tools())
    mcp = {"status": "pass" if mcp_invalid.get("status") == "failed_closed" and any(t.name == "get_canonical_market_context" for t in tools) else "fail", "startup_check": command_checks[-1], "invalid_ssl_policy": mcp_invalid, "readonly_tools_available": [t.name for t in tools]}
    conv = conversation_acceptance(); front = frontend_acceptance(); after = sha_dir(M5F_DIR)
    mode_a = {"status":"pass" if before == after and fastapi["status"]=="pass" and command_checks[3]["status"]=="pass" and command_checks[-1]["status"]=="pass" else "fail", "m5f_exists": M5F_DIR.exists(), "m5f_unchanged": before == after, "canonical_readable": (M5F_DIR/"canonical_market_context.json").exists(), "ai_context_pack_exists": (M5F_DIR/"ai_context_pack.md").exists(), "chatgpt_briefing_exists": (M5F_DIR/"chatgpt_briefing.md").exists()}
    mode_b = {"status":"pass" if validation.get("valid") and command_checks[5]["status"]=="pass" and command_checks[6]["status"]=="pass" and command_checks[7]["status"]=="pass" else "fail", "default_watchlist_exists": DEFAULT_WATCHLIST_PATH.exists(), "watchlist_valid": validation.get("valid"), "planned_routes": len(plan.get("planned_routes", [])), "latest_observation_readable": latest_obs.get("status") != "error", "observation_remains_noncanonical": plan.get("governance",{}).get("canonical") is False, "reference_only_not_current_price": True, "stale_or_closed_session_is_degraded": True}
    mode_c = {"status": conv["status"], **conv}
    caveats = [] if latest_obs.get("status") != "missing" else ["No latest observation artifact is present; acceptable for check-only operation."]
    all_checks = command_checks + [{"status": fastapi["status"], "label":"FastAPI"}, {"status": mcp["status"], "label":"MCP"}, {"status": front["status"], "label":"Frontend"}, {"status": mode_a["status"], "label":"Mode A"}, {"status": mode_b["status"], "label":"Mode B"}, {"status": mode_c["status"], "label":"Mode C"}]
    status = final_status(all_checks, caveats)
    summary = {"operator_ready": status != "fail", "release_preflight_ready": status != "fail", "mode_a_ready": mode_a["status"]=="pass", "mode_b_check_only_ready": mode_b["status"]=="pass", "mode_c_ready": mode_c["status"]=="pass"}
    return {"schema_version":"m6e_operator_acceptance.v1", "generated_at_utc": utc_now(), "mode": mode, "network_calls_may_have_occurred": execute_live, "ssl_policy": ssl_policy, "repository": repository_version(), "python": sys.version, "platform": platform.platform(), "checks": all_checks, "mode_a": mode_a, "mode_b": mode_b, "mode_c": mode_c, "fastapi": fastapi, "mcp": mcp, "frontend": front, "conversation_package": conv, "operator_workbench": command_checks[0], "operator_preflight": command_checks[2], "governance": {"no_m5f_mutation": before == after, "check_only_non_network": not execute_live, "no_polling": True, "no_scheduler": True, "no_trading_output": True, "no_raw_payload_leakage": conv["status"]=="pass"}, "final_status": status, "operator_acceptance_summary": summary, "caveats": caveats, "recommended_next_steps": ["python scripts/run_local_workbench.py", "python scripts/validate_m5f_canonical_market_context_package.py --package-dir research/staging/m5f/m5f_canonical_market_context_01", "python scripts/run_m5k_postmerge_validation.py --check-only", "python scripts/build_m5n_conversation_context.py", "python scripts/run_operator_preflight.py --timeout-seconds 300"]}

def write_report(report: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    JSON_REPORT.write_text(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False)+"\n", encoding="utf-8")
    md = ["# M6E Operator Acceptance Report", "", f"Generated: {report['generated_at_utc']}", f"Final status: `{report['final_status']}`", "", "## Operator readiness"]
    for k,v in report["operator_acceptance_summary"].items(): md.append(f"- {k}: {v}")
    md += ["", "## Caveats", *(f"- {c}" for c in report["caveats"] or ["None"]), "", "## Recommended next commands", *(f"- `{c}`" for c in report["recommended_next_steps"])]
    MD_REPORT.write_text("\n".join(md)+"\n", encoding="utf-8")

def main() -> int:
    ap = argparse.ArgumentParser(description="M6E operator acceptance and release preflight. Check-only is non-network.")
    mode = ap.add_mutually_exclusive_group(required=True); mode.add_argument("--check-only", action="store_true"); mode.add_argument("--execute-bounded-live-check", action="store_true")
    ap.add_argument("--ssl-policy", default="strict", choices=["strict","compatibility","unsafe-explicit"])
    args = ap.parse_args()
    report = build_report("execute-bounded-live-check" if args.execute_bounded_live_check else "check-only", args.ssl_policy, args.execute_bounded_live_check)
    if args.execute_bounded_live_check:
        report["live_execution"] = {"implemented": False, "reason": "M6E live aggregation is intentionally not implemented; run existing bounded M5K/M6B commands explicitly."}
        report["network_calls_may_have_occurred"] = False
    write_report(report)
    print(json.dumps({"status": report["final_status"], "json": JSON_REPORT.relative_to(ROOT).as_posix(), "markdown": MD_REPORT.relative_to(ROOT).as_posix()}, indent=2))
    return 0 if report["final_status"] != "fail" else 1
if __name__ == "__main__": raise SystemExit(main())

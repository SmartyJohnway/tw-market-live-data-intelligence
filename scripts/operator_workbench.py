from __future__ import annotations

import importlib.util
import json
import os
import platform
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.ssl_policy import platform_ssl_diagnostics, resolve_ssl_policy

REPO_ROOT = Path(__file__).resolve().parents[1]
M5F_DIR = REPO_ROOT / "research/staging/m5f/m5f_canonical_market_context_01"
OBS_PATH = REPO_ROOT / "research/live_observation_runs/m5k/latest_observation.json"
SOURCE_HEALTH_JSON = REPO_ROOT / "research/live_observation_runs/source_health/latest_source_health_report.json"
SOURCE_HEALTH_MD = REPO_ROOT / "research/live_observation_runs/source_health/latest_source_health_report.md"
CONVERSATION_DIR = REPO_ROOT / "research/live_observation_runs/current_conversation_context"
WATCHLIST_PATH = REPO_ROOT / "config/m5k_default_watchlist.json"
FRONTEND_WORKBENCH = REPO_ROOT / "frontend/readonly-preview/M5KLocalAIWorkbench.html"

@dataclass
class Check:
    name: str
    status: str
    detail: str
    suggestion: str = ""

    @property
    def ok(self) -> bool:
        return self.status == "PASS"

    @property
    def caveat(self) -> bool:
        return self.status == "CAVEAT"


def rel(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def git_value(args: list[str], default: str = "unknown") -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, stderr=subprocess.DEVNULL).strip() or default
    except Exception:
        return default


def repository_version() -> dict[str, str]:
    version = "unknown"
    changelog = REPO_ROOT / "CHANGELOG.md"
    if changelog.exists():
        for line in changelog.read_text(encoding="utf-8").splitlines():
            if line.startswith("## "):
                version = line.replace("##", "", 1).strip()
                break
    return {"version": version, "branch": git_value(["branch", "--show-current"]), "commit": git_value(["rev-parse", "--short", "HEAD"]), "release": "Local Release Candidate"}


def watchlist_symbols() -> list[str]:
    payload = load_json(WATCHLIST_PATH) or {}
    symbols: list[str] = []
    for category in payload.get("categories", []):
        for item in category.get("instruments", []):
            if item.get("enabled", True) and item.get("symbol"):
                symbols.append(str(item["symbol"]))
    return symbols


def file_summary(path: Path) -> str:
    if not path.exists():
        return "missing"
    size = path.stat().st_size
    return f"present ({rel(path)}, {size} bytes)"


def latest_artifact_time(path: Path) -> str:
    payload = load_json(path)
    if not payload:
        return "timestamp unavailable"
    for key in ("generated_at_utc", "retrieved_at_utc", "observation_time_utc", "created_at_utc"):
        if payload.get(key):
            return f"{key}={payload[key]}"
    return "timestamp field not found"


def environment_checks() -> list[Check]:
    checks: list[Check] = []
    py_ok = sys.version_info >= (3, 10)
    checks.append(Check("Python version", "PASS" if py_ok else "FAIL", platform.python_version(), "Use Python 3.10 or newer."))
    ssl_diag = platform_ssl_diagnostics()
    checks.append(Check("OS platform", "PASS", ssl_diag["os_platform"]))
    checks.append(Check("Python 3.13 detection", "CAVEAT" if ssl_diag["python_313_detected"] else "PASS", str(ssl_diag["python_313_detected"]), ssl_diag["operator_hint"] if ssl_diag["python_313_detected"] and ssl_diag["windows_detected"] else ""))
    checks.append(Check("Windows detection", "CAVEAT" if ssl_diag["windows_detected"] and ssl_diag["python_313_detected"] else "PASS", str(ssl_diag["windows_detected"]), ssl_diag["operator_hint"] if ssl_diag["windows_detected"] and ssl_diag["python_313_detected"] else ""))
    checks.append(Check("SSL default verify paths", "PASS", json.dumps(ssl_diag["ssl_default_verify_paths"], sort_keys=True)))
    checks.append(Check("Configured TW_MARKET_SSL_POLICY", "PASS", str(ssl_diag["configured_tw_market_ssl_policy"])))
    checks.append(Check("Effective SSL policy", "PASS" if ssl_diag["effective_ssl_policy"] != "unsafe-explicit" else "CAVEAT", ssl_diag["effective_ssl_policy"], ssl_diag["operator_hint"]))
    checks.append(Check("Virtual environment", "PASS" if sys.prefix != sys.base_prefix or os.environ.get("VIRTUAL_ENV") else "CAVEAT", os.environ.get("VIRTUAL_ENV") or "not detected", "Create and activate a virtual environment if dependency imports fail."))
    required = ["fastapi", "pytest", "pydantic"]
    missing = [pkg for pkg in required if importlib.util.find_spec(pkg) is None]
    checks.append(Check("Installed dependencies", "PASS" if not missing else "FAIL", "available" if not missing else "missing: " + ", ".join(missing), "Run: python -m pip install -r requirements.txt"))
    checks.append(Check("FastAPI import", "PASS" if importlib.util.find_spec("fastapi") else "FAIL", "fastapi importable" if importlib.util.find_spec("fastapi") else "fastapi unavailable", "Run: python -m pip install -r requirements.txt"))
    for label, path, suggestion in [
        ("M5F package", M5F_DIR / "canonical_market_context.json", "Run the M5F validator against research/staging/m5f/m5f_canonical_market_context_01."),
        ("Latest observation", OBS_PATH, "Observation not found. Suggested command: python scripts/run_m5k_live_observation.py --watchlist config/m5k_default_watchlist.json --execute-live-observation"),
        ("Source health", SOURCE_HEALTH_JSON if SOURCE_HEALTH_JSON.exists() else SOURCE_HEALTH_MD, "Run: python scripts/run_m5q_source_health_probe.py --execute-health-probe"),
        ("Conversation package", CONVERSATION_DIR / "conversation_context.md", "Run: python scripts/build_m5n_conversation_context.py"),
        ("Frontend workbench", FRONTEND_WORKBENCH, "Open frontend/readonly-preview/M5KLocalAIWorkbench.html after starting FastAPI if API-backed views are needed."),
    ]:
        checks.append(Check(label, "PASS" if path.exists() else "CAVEAT", file_summary(path), suggestion))
    writable = [p for p in [REPO_ROOT / "research/live_observation_runs", CONVERSATION_DIR] if p.exists() and os.access(p, os.W_OK)]
    checks.append(Check("Output folder permissions", "PASS" if writable else "CAVEAT", f"writable folders detected: {len(writable)}", "Ensure research/live_observation_runs is writable for observation and conversation outputs."))
    return checks


def status_report() -> dict[str, Any]:
    checks = environment_checks()
    obs_exists = OBS_PATH.exists()
    conv_exists = (CONVERSATION_DIR / "conversation_context.md").exists()
    source_health_exists = SOURCE_HEALTH_JSON.exists() or SOURCE_HEALTH_MD.exists()
    if not obs_exists:
        action = "Run bounded observation only if current temporary context is needed."
    elif not conv_exists:
        action = "Build the conversation package."
    elif not source_health_exists:
        action = "Run source-health probe if preparing release diagnostics."
    else:
        action = "Conversation package already available; review it and send to ChatGPT."
    return {"repository": repository_version(), "watchlist": watchlist_symbols(), "ssl_diagnostics": platform_ssl_diagnostics(), "checks": checks, "latest_observation": latest_artifact_time(OBS_PATH) if obs_exists else "missing", "latest_source_health": latest_artifact_time(SOURCE_HEALTH_JSON) if SOURCE_HEALTH_JSON.exists() else file_summary(SOURCE_HEALTH_MD), "latest_conversation_package": file_summary(CONVERSATION_DIR / "conversation_context.md"), "fastapi_command": "uvicorn server.main:app --host 127.0.0.1 --port 8000", "frontend_location": rel(FRONTEND_WORKBENCH), "mcp_command": "python server/mcp_server.py --startup-check", "recommended_next_action": action}


def print_dashboard(report: dict[str, Any]) -> None:
    repo = report["repository"]
    print("TW-Market Local Operator Workbench")
    print("=" * 38)
    print(f"Repository: {REPO_ROOT.name}")
    print(f"Version: {repo['version']}  Release: {repo['release']}")
    print(f"Branch: {repo['branch']}  Commit: {repo['commit']}")
    print(f"Current watchlist: {', '.join(report['watchlist']) or 'none'}")
    ssl_diag = report.get("ssl_diagnostics", {})
    print(f"SSL policy: effective={ssl_diag.get('effective_ssl_policy')} configured={ssl_diag.get('configured_tw_market_ssl_policy')}")
    print(f"Platform: {ssl_diag.get('os_platform')}  Python: {ssl_diag.get('python_version')}")
    print("\nDashboard")
    print(f"- Latest observation: {report['latest_observation']}")
    print(f"- Latest source health: {report['latest_source_health']}")
    print(f"- Latest conversation package: {report['latest_conversation_package']}")
    print(f"- FastAPI status: not started by this launcher; start with `{report['fastapi_command']}`")
    print(f"- Frontend location: {report['frontend_location']}")
    print(f"- MCP status: verify with `{report['mcp_command']}`")
    print("\nReadiness")
    for check in report["checks"]:
        marker = "PASS" if check.status == "PASS" else ("WARN" if check.status == "CAVEAT" else "FAIL")
        print(f"- [{marker}] {check.name}: {check.detail}")
        if check.status != "PASS" and check.suggestion:
            print(f"  Suggested next step: {check.suggestion}")
    print(f"\nRecommended next action: {report['recommended_next_action']}")
    print("\nMode reminders: Mode A = Canonical Context; Mode B = Bounded Observation; Mode C = Conversation Package.")
    print("Governance: Observation != Canonical; Reference-only != Current Price; stale_or_closed_session = degraded; no polling/scheduler/startup network/trading/recommendations/ranking/target price.")

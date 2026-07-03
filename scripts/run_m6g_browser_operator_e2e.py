#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.ssl_policy import VALID_SSL_POLICIES, resolve_ssl_policy

REPORT_DIR = ROOT / "research/live_observation_runs/m6g_browser_operator_e2e"
JSON_REPORT = REPORT_DIR / "latest_browser_operator_e2e_report.json"
MD_REPORT = REPORT_DIR / "latest_browser_operator_e2e_report.md"


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()
FRONTEND = ROOT / "frontend/readonly-preview/M5KLocalAIWorkbench.html"
DEFAULT_TARGETS = ["0050", "2330", "TX"]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def available_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def playwright_state() -> tuple[bool, str | None]:
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
    except Exception as exc:
        return False, f"Python Playwright is not importable: {exc}"
    return True, None


def wait_health(port: int, proc: subprocess.Popen[str], timeout: float = 15.0) -> bool:
    url = f"http://127.0.0.1:{port}/api/health"
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc.poll() is not None:
            return False
        try:
            with urllib.request.urlopen(url, timeout=1) as r:
                if r.status == 200:
                    return True
        except Exception:
            time.sleep(0.2)
    return False


def start_fastapi(env_policy: str | None = None) -> tuple[subprocess.Popen[str], int, bool]:
    port = available_port()
    env = os.environ.copy()
    if env_policy:
        env["TW_MARKET_SSL_POLICY"] = env_policy
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "server.main:app", "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning"],
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return proc, port, wait_health(port, proc)


def item_ok(item: dict[str, Any]) -> bool:
    required = ["id", "symbol", "category", "adapter", "preferred_sources", "enabled"]
    return all(k in item for k in required) and item.get("id") == f"{item.get('category')}:{item.get('symbol')}"


def ssl_policy_api_checks() -> dict[str, Any]:
    from fastapi.testclient import TestClient
    import server.main as main

    calls: list[dict[str, Any]] = []
    original = main._m5k_execute_live_observation

    def fake_execute(watchlist: dict, write_latest: bool = True, ssl_policy: str = "strict") -> dict[str, Any]:
        calls.append({"ssl_policy": ssl_policy, "watchlist": watchlist})
        return {"status": "ok", "diagnostics": {"ssl_policy": {"selected": ssl_policy}}}

    main._m5k_execute_live_observation = fake_execute
    try:
        watchlist = {"schema_version": "m5n_watchlist.v1", "items": []}
        with TestClient(main.app) as client:
            os.environ["TW_MARKET_SSL_POLICY"] = "compatibility"
            env_response = client.post("/api/m5k/live-observation/execute?confirm_live_observation=true", json=watchlist)
            query_response = client.post("/api/m5k/live-observation/execute?confirm_live_observation=true&ssl_policy=strict", json=watchlist)
            os.environ["TW_MARKET_SSL_POLICY"] = "bad-policy"
            invalid_env_response = client.post("/api/m5k/live-observation/execute?confirm_live_observation=true", json=watchlist)
            invalid_query_response = client.post("/api/m5k/live-observation/execute?confirm_live_observation=true&ssl_policy=bad-policy", json=watchlist)
    finally:
        main._m5k_execute_live_observation = original
        os.environ.pop("TW_MARKET_SSL_POLICY", None)
    return {
        "env_override": env_response.status_code == 200 and env_response.json()["diagnostics"]["ssl_policy"]["selected"] == "compatibility",
        "query_override": query_response.status_code == 200 and query_response.json()["diagnostics"]["ssl_policy"]["selected"] == "strict",
        "invalid_policy_fail_closed": invalid_env_response.status_code == 400 and invalid_query_response.status_code == 400,
        "execution_calls": calls,
    }


def server_env_policy_for_mode(*, execute_live: bool, selected_ssl_policy: str) -> tuple[str | None, str]:
    """Return temporary FastAPI env override and how browser execute policy is applied.

    The readonly frontend execute button does not include an ssl_policy query parameter.
    Therefore explicit non-strict browser-live policy is applied to the temporary
    FastAPI process environment. Strict uses the server default with no override.
    Check-only never executes and starts the server with no TLS env override.
    """
    if not execute_live:
        return None, "default"
    if selected_ssl_policy == "strict":
        return None, "default"
    return selected_ssl_policy, "env"


def run_browser_check(port: int, execute_live: bool, ssl_policy: str) -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    captured: dict[str, list[Any]] = {"validate": [], "plan": [], "execute": []}
    repeated_execute = False
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        def observe(route):
            url = route.request.url
            try:
                body = route.request.post_data_json
            except Exception:
                body = None
            if "/api/m5k/watchlist/validate" in url:
                captured["validate"].append(body)
            if "/api/m5k/live-observation/plan" in url:
                captured["plan"].append(body)
            if "/api/m5k/live-observation/execute" in url:
                captured["execute"].append(body)
            route.continue_()

        page.route("**/api/**", observe)
        page.goto(FRONTEND.as_uri(), wait_until="domcontentloaded")
        page.fill("#apiBase", f"http://127.0.0.1:{port}")
        page.click("#loadDefault")
        page.wait_for_selector('tr[data-item-row="true"]', timeout=10000)
        page.fill('tr[data-item-row="true"] [data-field="display_name"]', "M6G operator edited row")
        page.click("#planObservation")
        page.wait_for_function("document.querySelector('#observationStatus').textContent.includes('planned') || document.querySelector('#routePlanRows').children.length > 0", timeout=10000)
        if execute_live:
            page.click("#observe")
            page.wait_for_timeout(1000)
            repeated_execute = len(captured["execute"]) > 1
        validation_text = page.locator("#validation").inner_text(timeout=3000)
        status_text = page.locator("#observationStatus").inner_text(timeout=3000)
        browser.close()
    payloads = captured["plan"] or captured["validate"]
    items = payloads[-1].get("items", []) if payloads else []
    return {
        "browser_engine": "chromium",
        "frontend_loaded": True,
        "watchlist_payload_checked": bool(items),
        "watchlist_items_checked": len(items),
        "id_generation_status": "pass" if items and all(item_ok(i) for i in items) else "fail",
        "validate_request_status": "pass" if captured["validate"] and "valid" in validation_text.lower() else "fail",
        "plan_request_status": "pass" if captured["plan"] else "fail",
        "execute_request_status": "executed" if captured["execute"] else "not_executed",
        "unexpected_execute_requests": 0 if execute_live else len(captured["execute"]),
        "polling_detected": repeated_execute or (not execute_live and len(captured["execute"]) > 0),
        "operator_status_text": status_text,
        "targets": sorted({str(i.get("symbol")) for i in items if i.get("enabled") is not False}),
    }


def run_api_live_fallback(ssl_policy: str) -> dict[str, Any]:
    from fastapi.testclient import TestClient
    from server.main import app
    watchlist = {"schema_version": "m5n_watchlist.v1", "watchlist_id": "m6g_bounded", "name": "M6G bounded", "items": [
        {"id":"twse:0050","category":"twse","symbol":"0050","enabled":True,"market":"twse","instrument_type":"listed_etf","adapter":"TWSE_MIS","preferred_sources":["TWSE_MIS"]}
    ]}
    with TestClient(app) as client:
        r = client.post(f"/api/m5k/live-observation/execute?confirm_live_observation=true&ssl_policy={ssl_policy}", json=watchlist, timeout=30)
    return {"status_code": r.status_code, "body_status": r.json().get("status"), "targets": ["0050"]}


def final_status(report: dict[str, Any]) -> str:
    if not report["playwright_available"]:
        return "skipped_with_caveats"
    failures = [report["id_generation_status"] != "pass", report["validate_request_status"] != "pass", report["plan_request_status"] != "pass", report["unexpected_execute_requests"] != 0, report["polling_detected"]]
    ssl = report["mode_b_observation"].get("ssl_policy_api_checks", {})
    failures.extend([not ssl.get("env_override"), not ssl.get("query_override"), not ssl.get("invalid_policy_fail_closed")])
    return "fail" if any(failures) else ("pass_with_caveats" if report["caveats"] else "pass")


def write_report(report: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report["final_status"] = final_status(report)
    JSON_REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = ["# M6G Browser/Operator E2E Acceptance", "", f"Generated: {report['generated_at_utc']}", f"Mode: `{report['mode']}`", f"Final status: `{report['final_status']}`", "", "## Results"]
    for key in ["playwright_available", "fastapi_started", "frontend_loaded", "watchlist_payload_checked", "id_generation_status", "validate_request_status", "plan_request_status", "execute_request_status", "unexpected_execute_requests", "polling_detected", "network_calls_may_have_occurred", "ssl_policy", "requested_ssl_policy", "effective_server_env_ssl_policy", "browser_execute_ssl_policy_source"]:
        md.append(f"- {key}: `{report.get(key)}`")
    md += ["", "## Caveats", *(f"- {c}" for c in report.get("caveats") or ["None"]), "", "## Recommended next steps", *(f"- `{c}`" for c in report["recommended_next_steps"])]
    MD_REPORT.write_text("\n".join(md) + "\n", encoding="utf-8")


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    selected_ssl_policy = resolve_ssl_policy(args.ssl_policy)
    execute_live = bool(args.execute_bounded_live_check)
    available, missing_reason = playwright_state()
    caveats: list[str] = []
    base = {
        "schema_version": "m6g_browser_operator_e2e.v1",
        "generated_at_utc": utc_now(),
        "mode": "execute-bounded-live-check" if execute_live else "check-only",
        "browser_engine": "chromium" if available else None,
        "playwright_available": available,
        "fastapi_started": False,
        "frontend_loaded": False,
        "watchlist_payload_checked": False,
        "watchlist_items_checked": 0,
        "id_generation_status": "not_checked",
        "validate_request_status": "not_checked",
        "plan_request_status": "not_checked",
        "execute_request_status": "not_executed",
        "unexpected_execute_requests": 0,
        "polling_detected": False,
        "network_calls_may_have_occurred": execute_live,
        "ssl_policy": selected_ssl_policy,
        "requested_ssl_policy": selected_ssl_policy,
        "effective_server_env_ssl_policy": None,
        "browser_execute_ssl_policy_source": "default",
        "live_execution": {"executed": False, "explicit": execute_live, "bounded": True},
        "targets": DEFAULT_TARGETS,
        "artifacts_written": [display_path(JSON_REPORT), display_path(MD_REPORT)],
        "mode_a_reference": {"m5f_canonical": True, "mutated": False},
        "mode_b_observation": {"canonical": False, "reference_only_is_not_current_price": True, "ssl_policy_api_checks": ssl_policy_api_checks()},
        "mode_c_conversation": {"contract": "M5N conversation package", "parallel_contract_created": False},
        "governance": {"no_m5f_mutation": True, "no_polling": True, "no_scheduler": True, "no_startup_network_calls": True, "no_full_market_scan": True, "no_trading_output": True, "no_silent_tls_fallback": True},
        "caveats": caveats,
        "recommended_next_steps": ["python -m pip install playwright", "python -m playwright install chromium", "python scripts/run_m6g_browser_operator_e2e.py --check-only"],
    }
    server_env_policy, browser_policy_source = server_env_policy_for_mode(execute_live=execute_live, selected_ssl_policy=selected_ssl_policy)
    base["effective_server_env_ssl_policy"] = server_env_policy
    base["browser_execute_ssl_policy_source"] = browser_policy_source
    if not available:
        caveats.append(missing_reason or "Playwright/browser dependency unavailable.")
        caveats.append("Check-only mode skipped browser automation; install Playwright and Chromium, then rerun.")
        return base
    proc, port, started = start_fastapi(env_policy=server_env_policy)
    base["fastapi_started"] = started
    try:
        if not started:
            caveats.append("FastAPI did not become healthy before timeout.")
            return base
        base.update(run_browser_check(port, execute_live=execute_live, ssl_policy=selected_ssl_policy))
        if execute_live and base["execute_request_status"] != "executed":
            live = run_api_live_fallback(selected_ssl_policy)
            base["live_execution"] |= {"executed": live["status_code"] < 500, "fallback": "api_endpoint_after_browser_payload_validation", "result": live}
        elif execute_live:
            base["live_execution"] |= {"executed": True, "fallback": None}
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    return base


def main() -> int:
    ap = argparse.ArgumentParser(description="M6G browser/operator E2E acceptance. Check-only performs no live execution.")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check-only", action="store_true")
    mode.add_argument("--execute-bounded-live-check", action="store_true")
    ap.add_argument("--ssl-policy", choices=sorted(VALID_SSL_POLICIES), default="strict")
    args = ap.parse_args()
    report = build_report(args)
    write_report(report)
    print(json.dumps({"status": report["final_status"], "json": display_path(JSON_REPORT), "markdown": display_path(MD_REPORT)}, indent=2))
    return 0 if report["final_status"] in {"pass", "pass_with_caveats", "skipped_with_caveats"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

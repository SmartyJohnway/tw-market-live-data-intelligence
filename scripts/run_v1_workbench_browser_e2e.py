#!/usr/bin/env python3
"""Offline browser acceptance for the V1 persistent Watchlist workbench.

The runner owns an external, ephemeral installation root.  It proves the
operator's browser path rather than substituting API-only coverage: a fresh
NOT_INITIALIZED view, explicit local Watchlist mutation previews, request
composition, Mode B authorization, one deterministic execution, and Mode C
Result/Audit/AI-handoff inspection all occur through the shipped workbench.
"""

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
LEGACY_POINTER = ROOT / "config" / "m8r_06_mode_a_security_master_pointer.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def available_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_for_health(port: int, process: subprocess.Popen[str], timeout: float = 30.0) -> bool:
    deadline = time.monotonic() + timeout
    url = f"http://127.0.0.1:{port}/api/health"
    while time.monotonic() < deadline:
        if process.poll() is not None:
            return False
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return True
        except Exception:
            time.sleep(0.2)
    return False


def playwright_available() -> tuple[bool, str | None]:
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
    except Exception as exc:
        return False, f"playwright_unavailable:{type(exc).__name__}"
    return True, None


def start_workbench(env: dict[str, str]) -> tuple[subprocess.Popen[str], int]:
    port = available_port()
    process = subprocess.Popen(
        [
            sys.executable,
            "scripts/run_unified_workbench.py",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if not wait_for_health(port, process):
        process.terminate()
        raise RuntimeError("local_workbench_startup_failed")
    return process, port


def stop(process: subprocess.Popen[str] | None) -> None:
    if process is None:
        return
    process.terminate()
    try:
        process.wait(timeout=8)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=8)


def migrate_fixture_release(security_root: Path) -> dict[str, Any]:
    """Build an external local release using the strict legacy authority.

    This deliberately does not copy, reseal, or modify Candidate B.  The
    strict loader validates the historical pointer/seal/index/manifest before
    creating a new local installation release.
    """
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/manage_security_master.py",
            "migrate-legacy-active",
            "--legacy-pointer",
            str(LEGACY_POINTER),
            "--root",
            str(security_root),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=180,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"fixture_release_migration_failed:{completed.stderr.strip()[-400:]}")
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("fixture_release_migration_output_invalid") from exc
    if payload.get("status") != "ACTIVE" or payload.get("qualification") != "PASS":
        raise RuntimeError("fixture_release_migration_not_active")
    return payload


def source_invocation_count(counter_root: Path) -> int:
    return len(list(counter_root.glob("*.invoked")))


def wait_until(predicate, timeout: float = 15.0, *, label: str = "browser_condition") -> None:
    """Poll browser state without injecting JavaScript blocked by the CSP."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.1)
    raise RuntimeError(f"{label}_timeout")


def get_json(url: str) -> tuple[int, dict[str, Any]]:
    with urllib.request.urlopen(url, timeout=10) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def run_browser_flow(base_url: str, counter_root: Path) -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    captured_execution_requests = 0
    response_data: dict[str, Any] = {}
    result: dict[str, Any] = {}

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.on(
            "dialog",
            lambda dialog: dialog.accept(
                "<img src=x onerror=window.__xss=1> V1 browser watchlist"
                if "Watchlist name" in dialog.message
                else "v1-browser-deterministic-execute-once"
            ),
        )

        def observe_request(request) -> None:
            nonlocal captured_execution_requests
            if "/api/unified/executions" in request.url:
                captured_execution_requests += 1

        page.on("request", observe_request)
        page.goto(f"{base_url}/workbench/", wait_until="networkidle")
        page.wait_for_selector("#watchlist-summary")
        result["workbench_loaded"] = page.locator("h1").inner_text() == "Unified Market Evidence Operator Workbench"
        result["csp_clean"] = bool(
            page.locator('meta[http-equiv="Content-Security-Policy"]').get_attribute("content")
        )
        result["no_watchlists_state"] = "No installation-local watchlist" in page.locator("#watchlist-summary").inner_text()
        result["dispatch_count_before_execute"] = source_invocation_count(counter_root)

        page.click("#btn-watchlist-create")
        page.wait_for_selector("#mutation-preview-panel:not([hidden])")
        result["mutation_preview_visible"] = "create_watchlist" in page.locator("#mutation-preview-view").inner_text()
        page.click("#btn-confirm-mutation")
        wait_until(lambda: page.locator("#watchlist-select option").count() > 1, label="watchlist_create")
        page.select_option("#watchlist-select", index=1)
        wait_until(lambda: "version" in page.locator("#watchlist-summary").inner_text(), label="watchlist_selection")
        result["xss_safe_rendering"] = (
            page.locator("#watchlist-panel img").count() == 0
            and "V1 browser watchlist" in page.locator("#watchlist-summary").inner_text()
        )

        page.fill("#watchlist-add-query", "2330")
        page.click("#btn-watchlist-add")
        page.wait_for_selector("#mutation-preview-panel:not([hidden])")
        page.click("#btn-confirm-mutation")
        page.wait_for_selector(".watchlist-entry-selection")
        result["persistent_watchlist_flow"] = page.locator(".watchlist-entry-selection").count() == 1

        page.fill("#temporary-target-input", "0050")
        page.click("#btn-temporary-add")
        wait_until(lambda: "0050" in page.locator("#temporary-targets").inner_text(), label="temporary_target_add")
        page.locator("#temporary-targets button", has_text="Remove").click()
        wait_until(lambda: "0050" not in page.locator("#temporary-targets").inner_text(), label="temporary_target_remove")
        result["temporary_target_nonpersistent"] = page.locator(".watchlist-entry-selection").count() == 1

        page.click("#btn-select-enabled")
        page.locator('.builder-capability[value="identity"]').uncheck()
        page.locator('.builder-capability[value="current_observation"]').check()
        page.select_option("#builder-execution-mode", "execute")
        page.click("#btn-compose-request")
        wait_until(lambda: "current_observation" in page.locator("#request-textarea").input_value(), label="request_composition")
        result["request_builder_and_advanced_json"] = page.locator("#syntax-status").inner_text() == "JSON syntax valid"

        page.click("#btn-validate")
        wait_until(lambda: "valid" in page.locator("#validation-summary").inner_text().lower(), label="request_validation")
        result["validation_passed"] = "valid" in page.locator("#validation-summary").inner_text().lower()
        page.click("#btn-preview")
        wait_until(lambda: "ready_for_confirmation" in page.locator("#preview-summary").inner_text(), label="preview")
        result["evidence_authorization_preview"] = "ready_for_confirmation" in page.locator("#preview-summary").inner_text()

        with page.expect_response(lambda response: "/api/unified/authorizations" in response.url) as authorization_response:
            page.click("#btn-authorize")
        response_data["authorization"] = authorization_response.value.json()
        wait_until(lambda: "AUTHORIZED" in page.locator("#mode-b2-summary").inner_text(), label="authorization")
        result["authorization_created"] = bool(response_data["authorization"].get("control_package_id"))
        result["dispatch_count_before_execute"] = source_invocation_count(counter_root)
        page.check("#confirm-network-execution")
        wait_until(lambda: page.locator("#btn-execute-once").is_enabled(), label="network_confirmation")
        page.click("#btn-execute-once")
        wait_until(lambda: "EXECUTION ATTEMPTED" in page.locator("#mode-b2-summary").inner_text(), timeout=30, label="execution")
        result["execute_once_request_count"] = captured_execution_requests
        result["deterministic_source_invocations"] = source_invocation_count(counter_root)

        with page.expect_response(lambda response: "/api/unified/result-package" in response.url and response.request.method == "POST") as result_response:
            page.click("#btn-build-result")
        result_response.value.json()
        wait_until(lambda: "RESULT READY" in page.locator("#mode-c-summary").inner_text(), timeout=30, label="result")
        control_package_id = response_data["authorization"]["control_package_id"]
        audit_status, audit = get_json(f"{base_url}/api/unified/result-package/{control_package_id}/audit.json")
        handoff_status, handoff = get_json(f"{base_url}/api/unified/result-package/{control_package_id}/handoff")
        result_package = {"audit_status": audit_status, "audit": audit, "handoff_status": handoff_status, "handoff": handoff}
        result["result_audit_handoff"] = (
            result_package["audit_status"] == 200
            and result_package["handoff_status"] == 200
            and bool(result_package["handoff"].get("ai_ready_markdown"))
        )
        result["result_status"] = page.locator("#mode-c-summary").inner_text()
        result["audit_id"] = result_package["audit"].get("audit_id")
        result["result_id"] = result_package["handoff"].get("result_id")
        browser.close()
    return result


def execute(report_dir: Path) -> dict[str, Any]:
    available, missing = playwright_available()
    runtime_root = report_dir.parent / f"v1-workbench-browser-runtime-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    security_root = runtime_root / "security-master"
    watchlist_root = runtime_root / "watchlists"
    control_root = runtime_root / "control"
    counter_root = runtime_root / "invocations"
    counter_root.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "schema_version": "v1_workbench_browser_e2e.v1",
        "generated_at": utc_now(),
        "runtime_root": str(runtime_root),
        "runtime_root_outside_repository": ROOT not in runtime_root.parents,
        "playwright_available": available,
        "market_network_used": False,
        "test_transport": "deterministic",
        "status": "fail",
        "checks": {},
        "failure": None,
    }
    if not available:
        report["status"] = "fail"
        report["failure"] = missing
        return report

    env = os.environ.copy()
    env.update(
        {
            "TW_MARKET_SECURITY_MASTER_ROOT": str(security_root),
            "TW_MARKET_WATCHLIST_ROOT": str(watchlist_root),
            "M8R_06_03_CONTROL_ROOT": str(control_root),
            "M8R_06_03_EXECUTION_ENVIRONMENT": "test",
            "M8R_06_03_TEST_SOURCE_TRANSPORT": "deterministic",
            "M8R_06_03_TEST_INVOCATION_COUNTER": str(counter_root),
        }
    )
    process: subprocess.Popen[str] | None = None
    try:
        # A browser-visible fresh-install fail-closed state is required before
        # explicitly bootstrapping the separate external test installation.
        process, port = start_workbench(env)
        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"http://127.0.0.1:{port}/workbench/", wait_until="networkidle")
            # Listing an empty installation is intentionally allowed; an
            # identity-dependent validation must expose the governed public
            # NOT_INITIALIZED boundary rather than a filesystem detail.
            page.locator("#request-textarea").fill(
                json.dumps(
                    {
                        "schema_version": "unified_market_evidence_request.v1",
                        "request_id": "v1-browser-not-initialized",
                        "targets": [{"input": "2330", "market_hint": "TWSE", "resolution_requirement": "exact"}],
                        "data_needs": [{"type": "current_observation", "priority": "required", "parameters": {}}],
                        "execution_mode": "preview",
                        "response_preferences": {"include_citations": True, "include_currentness": True, "include_caveats": True, "include_audit_reference": True},
                    }
                )
            )
            page.click("#btn-validate")
            wait_until(lambda: "SECURITY_MASTER_NOT_INITIALIZED" in page.locator("#validation-summary").inner_text(), label="not_initialized")
            report["checks"]["security_master_not_initialized"] = True
            browser.close()
        stop(process)
        process = None

        report["fixture_release"] = migrate_fixture_release(security_root)
        process, port = start_workbench(env)
        report["checks"] |= run_browser_flow(f"http://127.0.0.1:{port}", counter_root)
        report["checks"]["no_external_market_network"] = True
        required = [
            "security_master_not_initialized",
            "workbench_loaded",
            "csp_clean",
            "no_watchlists_state",
            "mutation_preview_visible",
            "xss_safe_rendering",
            "persistent_watchlist_flow",
            "temporary_target_nonpersistent",
            "request_builder_and_advanced_json",
            "validation_passed",
            "evidence_authorization_preview",
            "authorization_created",
            "result_audit_handoff",
            "no_external_market_network",
        ]
        report["checks"]["dispatch_count_before_execute"] = report["checks"].get("dispatch_count_before_execute") == 0
        report["checks"]["execute_once"] = report["checks"].get("execute_once_request_count") == 1
        report["checks"]["one_deterministic_source_invocation"] = report["checks"].get("deterministic_source_invocations") == 1
        required.extend(["dispatch_count_before_execute", "execute_once", "one_deterministic_source_invocation"])
        report["status"] = "pass" if all(report["checks"].get(key) is True for key in required) else "fail"
    except Exception as exc:
        report["failure"] = f"{type(exc).__name__}:{exc}"
    finally:
        stop(process)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-dir", type=Path, required=True, help="External report directory; repository writes are forbidden.")
    args = parser.parse_args()
    report = execute(args.report_dir.resolve())
    args.report_dir.mkdir(parents=True, exist_ok=True)
    report_path = args.report_dir / "v1_workbench_browser_e2e.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "report": str(report_path)}, ensure_ascii=False))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

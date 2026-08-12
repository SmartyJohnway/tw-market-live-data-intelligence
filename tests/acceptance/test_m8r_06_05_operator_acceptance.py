"""M8R-06-05 operator acceptance through the real localhost workbench chain."""
from __future__ import annotations

import hashlib
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]


def _request(request_id: str, needs: list[dict] | None = None, targets: list[dict] | None = None) -> dict:
    return {
        "schema_version": "unified_market_evidence_request.v1", "request_id": request_id,
        "execution_mode": "preview",
        "targets": targets or [{"input": "2330", "market_hint": "TWSE"}, {"input": "6488", "market_hint": "TPEX"}],
        "data_needs": needs or [
            {"type": "current_observation", "priority": "required"},
            {"type": "official_eod_reference", "priority": "required"},
        ],
    }


def _json(url: str, payload: dict | None = None) -> tuple[int, dict]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    req = Request(url, data=body, method="POST" if body else "GET", headers={"Content-Type": "application/json"} if body else {})
    try:
        with urlopen(req, timeout=90) as response:
            return response.status, json.loads(response.read())
    except HTTPError as exc:
        return exc.code, json.loads(exc.read())


class LocalWorkbench:
    def __init__(self, tmp_path: Path, *, failure_capability: str | None = None):
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            self.port = probe.getsockname()[1]
        self.root, self.counter = tmp_path / "control", tmp_path / "counter"
        env = os.environ | {
            "M8R_06_03_CONTROL_ROOT": str(self.root), "M8R_06_03_EXECUTION_ENVIRONMENT": "test",
            "M8R_06_03_TEST_SOURCE_TRANSPORT": "deterministic", "M8R_06_03_TEST_INVOCATION_COUNTER": str(self.counter),
        }
        if failure_capability:
            env["M8R_06_03_TEST_SOURCE_FAILURE_CAPABILITY"] = failure_capability
        self.process = subprocess.Popen([sys.executable, "scripts/run_unified_workbench.py", "--host", "127.0.0.1", "--port", str(self.port)], cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.base = f"http://127.0.0.1:{self.port}"

    def start(self):
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            try:
                if _json(self.base + "/api/health")[0] == 200:
                    return self
            except URLError:
                time.sleep(.1)
        stderr = self.process.stderr.read()
        raise AssertionError(f"localhost launcher did not become healthy: {stderr}")

    def close(self):
        self.process.terminate()
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=10)


def _preview(server: LocalWorkbench, request: dict) -> dict:
    assert _json(server.base + "/api/unified/validate-request", {"request": request})[0] == 200
    status, package = _json(server.base + "/api/unified/preview-request", {"request": request})
    assert status == 200
    return package


def _authorize(server: LocalWorkbench, request: dict, preview: dict) -> dict:
    reference, plan = preview["preview"]["internal_execution_reference"], preview["orchestration_plan"]
    status, authorization = _json(server.base + "/api/unified/authorizations", {
        "request": request, "expected_preview_id": reference["preview_id"], "expected_plan_id": plan["plan_id"],
        "expected_plan_hash": plan["plan_hash"], "confirm_authorization": True, "approval_scope_mode": "whole_plan_executable_scope",
    })
    assert status == 200 and authorization["execution_ready"] is True
    return authorization


def test_m8r_06_05_localhost_operator_matrix(tmp_path):
    """Happy, refusal, replay, blocked, ambiguity, plan-only, and handoff closure."""
    server = LocalWorkbench(tmp_path / "happy").start()
    try:
        with urlopen(server.base + "/workbench/mode-a/", timeout=30) as response:
            assert response.status == 200
        request = _request("m8r-06-05-happy")
        preview = _preview(server, request)
        assert preview["preview"]["status"] == "ready_for_confirmation"
        plan = preview["orchestration_plan"]
        assert len(plan["operations"]) == 4 and len(plan["batch_groups"]) == 4
        reference = preview["preview"]["internal_execution_reference"]
        # Explicit consent and current preview/plan identity are non-negotiable.
        status, refusal = _json(server.base + "/api/unified/authorizations", {"request": request, "expected_preview_id": reference["preview_id"], "expected_plan_id": plan["plan_id"], "expected_plan_hash": plan["plan_hash"], "confirm_authorization": False})
        assert status == 422 and refusal["error"] == "authorization_confirmation_required"
        status, stale = _json(server.base + "/api/unified/authorizations", {"request": request, "expected_preview_id": "stale", "expected_plan_id": plan["plan_id"], "expected_plan_hash": plan["plan_hash"], "confirm_authorization": True})
        assert status == 409 and stale["error"] == "mode_b2_preview_stale"
        authorization = _authorize(server, request, preview)
        execution_payload = {"control_package_id": authorization["control_package_id"], "confirm_execution": True, "operator_confirmation_reference": "m8r-06-05", "confirm_network_execution": False}
        status, network_refusal = _json(server.base + "/api/unified/executions", execution_payload)
        assert status == 409 and network_refusal["error"] == "mode_b2_execution_unavailable"
        package = server.root / authorization["authorization_id"]
        assert not list((package / "claims").glob("*.json")) and not server.counter.exists()
        execution_payload["confirm_network_execution"] = True
        status, execution = _json(server.base + "/api/unified/executions", execution_payload)
        assert status == 200 and execution["transport_mode"] == "deterministic_test_transport"
        assert execution["external_market_network_executed"] is False
        assert len(list(server.counter.glob("*.invoked"))) == 4
        status, replay = _json(server.base + "/api/unified/executions", execution_payload)
        assert status == 409 and replay["error"] == "mode_b2_execution_unavailable"
        assert len(list(server.counter.glob("*.invoked"))) == 4
        status, result = _json(server.base + "/api/unified/result-package", {"control_package_id": authorization["control_package_id"]})
        assert status == 200 and result["result_status"] == "full_success"
        assert result["ai_ready_markdown"] and result["canonical_result"]["result_hash"] == result["result_hash"]
        assert "current_observation_not_guaranteed_realtime" in result["ai_ready_markdown"]
        status, audit = _json(server.base + f"/api/unified/result-package/{authorization['control_package_id']}/audit.json")
        assert status == 200 and audit["audit_package_id"] == result["audit_package_id"] and audit != result["canonical_result"]
        status, handoff = _json(server.base + f"/api/unified/result-package/{authorization['control_package_id']}/handoff")
        assert status == 200 and handoff["canonical_result"] == result["canonical_result"]
        assert {item["capability_id"] for item in handoff["citation_references"]} == {
            "current_observation", "official_eod_reference"
        }
        assert handoff["execution_outcome"] == "succeeded"
        claim = json.loads(next((package / "claims").glob("*.json")).read_text(encoding="utf-8"))
        receipt = json.loads(next((package / "receipts").glob("*.json")).read_text(encoding="utf-8"))
        bundle = json.loads(next((package / "bundles").glob("*.json")).read_text(encoding="utf-8"))
        assert plan["input_bindings"]["original_request_hash"] == hashlib.sha256(json.dumps(request, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        assert authorization["plan_id"] == plan["plan_id"] and authorization["plan_hash"] == plan["plan_hash"]
        assert claim["execution_receipt_id"] == receipt["execution_receipt_id"] and bundle["claim_id"] == claim["claim_id"]
        assert audit["authorization_identity"]["authorization_id"] == authorization["authorization_id"]

        # Existing vocabulary: recent_performance is plan-only, never silently dispatched.
        plan_only = _preview(server, _request("m8r-06-05-plan-only", [{"type": "current_observation", "priority": "required"}, {"type": "recent_performance", "priority": "optional", "parameters": {"lookback_trading_days": 5}}]))
        assert plan_only["preview"]["status"] == "partial_possible"
        assert any(item["operation_status"] == "plan_only_not_executable" for item in plan_only["orchestration_plan"]["operations"])
        assert all(item["capability_id"] != "recent_performance" for item in plan_only["orchestration_plan"]["operations"] if item["operation_status"] == "executable_pending_approval")
        # A blocked route never creates authority, claim, or dispatch.
        blocked = _preview(server, _request("m8r-06-05-blocked", [{"type": "session_status", "priority": "required"}]))
        assert blocked["preview"]["status"] == "unsupported_capability"
        status, denied = _json(server.base + "/api/unified/authorizations", {"request": _request("m8r-06-05-blocked", [{"type": "session_status", "priority": "required"}]), "expected_preview_id": blocked["preview"]["internal_execution_reference"]["preview_id"], "expected_plan_id": blocked["orchestration_plan"]["plan_id"], "expected_plan_hash": blocked["orchestration_plan"]["plan_hash"], "confirm_authorization": True})
        assert status == 409 and denied["error"] == "preview_not_authorizable"
        # The sealed production candidate intentionally contains no collision;
        # use the repository-owned deterministic F3 collision fixture without
        # guessing a production identity or creating an executable authority.
        from server.services.unified_mode_a import validate_mode_a_request
        ambiguity = validate_mode_a_request(_request("m8r-06-05-ambiguous", targets=[{"input": "3333"}]), allow_fixture_snapshot=True)
        assert ambiguity["validation_status"] == "requires_clarification"
        assert ambiguity["target_results"][0]["resolution_status"] == "ambiguous"
    finally:
        server.close()


def test_m8r_06_05_partial_source_failure_and_ui_bindings(tmp_path):
    """A deterministic source failure is preserved into Mode C and its authoritative handoff."""
    server = LocalWorkbench(tmp_path / "failure", failure_capability="official_eod_reference").start()
    try:
        request = _request("m8r-06-05-source-failure", targets=[{"input": "2330", "market_hint": "TWSE"}])
        authorization = _authorize(server, request, _preview(server, request))
        payload = {"control_package_id": authorization["control_package_id"], "confirm_execution": True, "operator_confirmation_reference": "source-failure", "confirm_network_execution": True}
        status, execution = _json(server.base + "/api/unified/executions", payload)
        assert status == 200 and execution["aggregation_status"] == "partial_success"
        assert len(list(server.counter.glob("*.invoked"))) == 2
        status, result = _json(server.base + "/api/unified/result-package", {"control_package_id": authorization["control_package_id"]})
        assert status == 200 and result["result_status"] == "partially_failed"
        assert "部分失敗" in result["ai_ready_markdown"] and "official_eod_reference" in result["ai_ready_markdown"]
        assert result["canonical_result"]["targets"][0]["evidence"]["official_eod_reference"]["caveats"] == ["operation_failed:official_eod_unavailable"]
        javascript = (ROOT / "frontend/unified-workbench/unified-workbench.js").read_text(encoding="utf-8")
        for snippet in ("const invalidateModeCState = () =>", "textarea.addEventListener('input', updateSyntaxStatus)", "fileInput.addEventListener('change'", "clearBtn.addEventListener('click'", "copyToClipboard(currentModeCResult?.ai_ready_markdown", "downloadText(currentModeCResult?.ai_ready_markdown", "downloadJson(currentModeCResult?.canonical_result", "/audit.json"):
            assert snippet in javascript
    finally:
        server.close()

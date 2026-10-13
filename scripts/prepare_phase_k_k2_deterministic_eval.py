"""Prepare a disposable, deterministic, market-network-free Phase K evaluation root."""
from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import json
import shutil
import socket
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import httpx
from fastapi.testclient import TestClient

from server.main import app
from server.services import unified_mode_a, unified_mode_c
from server.unified_mcp.local_service_client import UnifiedLocalServiceClient
from server.unified_mcp.tool_contracts import build_tool_contract_snapshot
from tests.helpers.phase_h_imp_7d_control_package import execute_fixture_package

KIT_VERSION = "phase-k-k2a-deterministic-eval-v1"
REAL_HTTPX_ASYNC_CLIENT = httpx.AsyncClient
EXPECTED_TOOLS = [
    "market_describe_capabilities",
    "market_validate_request",
    "market_preview_request",
    "market_read_result",
    "market_export_ai_handoff",
    "market_fetch_evidence",
]
SCENARIO_ASSETS = [
    {"scenario_id": "K1-01", "authority": "server/unified_mcp/tool_contracts.py::build_tool_contract_snapshot", "kind": "canonical_surface_contract", "root_asset": "scenario_assets/K1-01/mcp_tools.json"},
    {"scenario_id": "K1-02", "authority": "tests/fixtures/m8r_05a_f3/verified_security_master_snapshot.json; tests/acceptance/test_m8r_06_05_operator_acceptance.py::test_m8r_06_05_localhost_operator_matrix", "kind": "deterministic_ambiguous_identity", "root_asset": "scenario_assets/K1-02/verified_security_master_snapshot.json"},
    {"scenario_id": "K1-03", "authority": "tests/helpers/phase_h_imp_7d_control_package.py::fixture_request; fixture_plan; network_required=false", "kind": "resolved_execute_request_and_offline_preview_precondition", "root_asset": "scenario_assets/K1-03/execute_request.json"},
    {"scenario_id": "K1-04", "authority": "tests/helpers/phase_h_imp_7d_control_package.py::execute_fixture_package; server/services/unified_mode_c.py; server/unified_mcp/local_service_client.py", "kind": "freshly_prepared_finalized_result_audit_handoff", "package_key": "success"},
    {"scenario_id": "K1-05", "authority": "scripts/prepare_phase_k_k2_deterministic_eval.py::_prepare_stale_package; repository-owned deterministic raw-source path", "kind": "freshly_prepared_finalized_stale_result_audit_handoff", "package_key": "stale"},
    {"scenario_id": "K1-06", "authority": "tests/acceptance/test_m8r_06_05_operator_acceptance.py::test_m8r_06_05_partial_source_failure_and_ui_bindings", "kind": "deterministic_partial_source_failure", "package_key": "partial"},
    {"scenario_id": "K1-07", "authority": "tests/integration/test_phase_j_j2_deterministic_cross_layer.py::test_j1_10_financial_statements_fail_closed_through_local_service_and_mcp; schemas/unified_market_evidence_request.v3.schema.json", "kind": "schema_fail_closed_request_case", "root_asset": "scenario_assets/K1-07/unsupported_financial_statements_request.json"},
    {"scenario_id": "K1-08", "authority": "K2-A prepared representative Result/Audit/Handoff package", "kind": "representative_nontrivial_result_handoff", "package_key": "success"},
]


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_json_bytes(value))


def _lineage(result: dict, audit: dict, handoff: dict) -> None:
    result_id = result.get("result_id")
    if not result_id or audit.get("result_id") != result_id or handoff.get("result_id") != result_id:
        raise RuntimeError("prepared_result_audit_handoff_lineage_mismatch")
    if audit.get("audit_package_id") is None or handoff.get("audit_package_id") != audit.get("audit_package_id"):
        raise RuntimeError("prepared_audit_identity_mismatch")
    if result.get("schema_version") != "unified_market_evidence_result.v3":
        raise RuntimeError("prepared_result_schema_unexpected")
    if audit.get("schema_version") != "unified_market_evidence_audit_package.v3":
        raise RuntimeError("prepared_audit_schema_unexpected")
    if not handoff.get("ai_ready_markdown") or not handoff.get("citation_references"):
        raise RuntimeError("prepared_handoff_incomplete")


def _copy_fixture(source: str, root: Path, relative: str) -> Path:
    destination = root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / source, destination)
    return destination


def _prepare_package(package_root: Path, target_inputs: tuple[str, ...], *, expected_status: str) -> dict:
    execution = execute_fixture_package(package_root, target_inputs=target_inputs)
    if execution["plan"].get("accounting", {}).get("network_request_estimate") != 0 or any(op.get("network_required") is not False for op in execution["plan"].get("operations", [])):
        raise RuntimeError("fixture_execution_not_network_free")
    control_id = execution["authorization"]["authorization_id"]
    if control_id == "umea-v1-64317f4f3435611c2bb5":
        raise RuntimeError("prohibited_historical_package_id")
    response = TestClient(app).post("/api/unified/result-package", json={"control_package_id": control_id})
    if response.status_code != 200:
        raise RuntimeError(f"result_materialization_failed:{response.status_code}")
    result = response.json()["canonical_result"]
    audit_response = TestClient(app).get(f"/api/unified/result-package/{control_id}/audit.json")
    if audit_response.status_code != 200:
        raise RuntimeError(f"audit_materialization_failed:{audit_response.status_code}")
    audit = audit_response.json()
    if result.get("status") != expected_status:
        raise RuntimeError(f"prepared_result_status_unexpected:{result.get('status')}")

    async def consume(order: tuple[str, str]) -> dict:
        client = UnifiedLocalServiceClient("http://127.0.0.1:8000")
        response = {}
        for operation in order:
            if operation == "read_result":
                response[operation] = await client.read_result(control_id)
            else:
                response[operation] = await client.export_ai_handoff(control_id)
        return response

    read_first = asyncio.run(consume(("read_result", "export_ai_handoff")))
    export_first = asyncio.run(consume(("export_ai_handoff", "read_result")))
    if execution["invocations"]["count"] != 1:
        raise RuntimeError("read_only_result_consumption_invoked_fixture_executor")
    for observation in (read_first, export_first):
        if observation["read_result"].get("canonical_result", {}).get("result_id") != result["result_id"]:
            raise RuntimeError("read_result_verification_failed")
        if observation["export_ai_handoff"].get("result_id") != result["result_id"]:
            raise RuntimeError("export_ai_handoff_verification_failed")
    handoff = read_first["export_ai_handoff"]
    _lineage(result, audit, handoff)
    if expected_status == "partially_failed" and handoff.get("execution_outcome") != "partial_success":
        raise RuntimeError("partial_handoff_semantics_unexpected")
    package_dir = Path(execution["package"])
    return {"execution": execution, "control_id": control_id, "result": result, "audit": audit,
            "handoff": handoff, "package_dir": package_dir, "read_first": read_first,
            "export_first": export_first}


def _prepare_partial_failure_package(root: Path) -> dict:
    # Reuse the maintained, repository-owned deterministic test transport that
    # asserts the failed evidence family remains visibly unavailable in V3.
    from tests.acceptance.test_m8r_06_05_operator_acceptance import (
        LocalWorkbench, _authorize, _json, _preview, _request,
    )
    partial_root = root / "partial_test"
    server = LocalWorkbench(partial_root, failure_capability="official_eod_reference").start()
    try:
        request = _request("k2a-k1-06-source-failure", targets=[{"input": "2330", "market_hint": "TWSE"}])
        authorization = _authorize(server, request, _preview(server, request))
        status, execution = _json(server.base + "/api/unified/executions", {
            "control_package_id": authorization["control_package_id"],
            "confirm_execution": True,
            "operator_confirmation_reference": "k2a-deterministic-fixture",
            "confirm_network_execution": True,
        })
        if status != 200 or execution.get("external_market_network_executed") is not False:
            raise RuntimeError("deterministic_partial_execution_failed_or_networked")
        if len(list(server.counter.glob("*.invoked"))) != 2:
            raise RuntimeError("deterministic_partial_invocation_count_unexpected")
        fixture_invocations_before_reads = len(list(server.counter.glob("*.invoked")))

        control_id = authorization["control_package_id"]
        if control_id == "umea-v1-64317f4f3435611c2bb5":
            raise RuntimeError("prohibited_historical_package_id")
        status, result_package = _json(server.base + "/api/unified/result-package", {"control_package_id": control_id})
        if status != 200 or result_package.get("result_status") != "partially_failed":
            raise RuntimeError("partial_result_not_finalized")
        result = result_package["canonical_result"]
        expected_error = ["operation_failed:official_eod_unavailable"]
        result_evidence = result["targets"][0]["evidence"]
        evidence = result_evidence.get("official_eod_reference", {})
        if evidence.get("caveats") != expected_error or result_evidence.get("current_observation", {}).get("status") != "available":
            raise RuntimeError("partial_source_failure_not_preserved")
        status, audit = _json(server.base + f"/api/unified/result-package/{control_id}/audit.json")
        if status != 200:
            raise RuntimeError("partial_audit_unavailable")
        status, handoff = _json(server.base + f"/api/unified/result-package/{control_id}/handoff")
        if status != 200:
            raise RuntimeError("partial_handoff_unavailable")
        _lineage(result, audit, handoff)

        async def consume(order: tuple[str, str]) -> dict:
            response = {}
            client = UnifiedLocalServiceClient(server.base)
            for operation in order:
                if operation == "read_result":
                    response[operation] = await client.read_result(control_id)
                else:
                    response[operation] = await client.export_ai_handoff(control_id)
            return response
        # This test-service client uses loopback only; no MCP session or Agent
        # host is launched. Both orders are independent read-only probes.
        with patch("server.unified_mcp.local_service_client.httpx.AsyncClient", REAL_HTTPX_ASYNC_CLIENT):
            read_first = asyncio.run(consume(("read_result", "export_ai_handoff")))
            export_first = asyncio.run(consume(("export_ai_handoff", "read_result")))
        if any(item["read_result"]["canonical_result"]["result_id"] != result["result_id"] or item["export_ai_handoff"]["result_id"] != result["result_id"] for item in (read_first, export_first)):
            raise RuntimeError("partial_read_export_verification_failed")
        if len(list(server.counter.glob("*.invoked"))) != fixture_invocations_before_reads:
            raise RuntimeError("partial_read_only_consumption_invoked_fixture_transport")
        package_dir = server.root / control_id
        return {"control_id": control_id, "result": result, "audit": audit, "handoff": handoff,
                "package_dir": package_dir, "read_first": read_first, "export_first": export_first,
                "transport_invocations": len(list(server.counter.glob("*.invoked"))),
                "external_market_network_executed": execution["external_market_network_executed"],
                "fixture_executor_id": "m8r_06_03 deterministic_test_transport"}
    finally:
        server.close()


def _prepare_stale_package(root: Path) -> dict:
    # Regenerate the accepted stale semantics through the repository-owned
    # deterministic raw-source boundary. No historical Result/control package is reused.
    from tests.helpers.phase_j_closure_r1 import service

    stale_root = root / "stale_test"
    with service("J1-21", stale_root) as url:
        with httpx.Client(base_url=url, trust_env=False, timeout=140) as client:
            def post(path: str, payload: dict) -> dict:
                response = client.post(f"/api/unified/{path}", json=payload)
                if response.status_code != 200:
                    raise RuntimeError(f"stale_{path}_failed:{response.status_code}:{response.text}")
                return response.json()

            request = {
                "schema_version": "unified_market_evidence_request.v3",
                "request_id": "k2a-k1-05-finalized-stale",
                "targets": [{"input": "TWSE:2330", "resolution_requirement": "exact"}],
                "data_needs": [{"type": "current_observation", "priority": "required", "parameters": {}}],
                "execution_mode": "execute",
            }
            validation = post("validate-request", {"request": request})
            if validation.get("validation_status") != "valid":
                raise RuntimeError("stale_request_invalid")
            preview = post("preview-request", {"request": request})
            authorization = post("authorizations", {
                "request": request,
                "expected_preview_id": preview["preview"]["internal_execution_reference"]["preview_id"],
                "expected_plan_id": preview["orchestration_plan"]["plan_id"],
                "expected_plan_hash": preview["orchestration_plan"]["plan_hash"],
                "confirm_authorization": True,
                "approval_scope_mode": "whole_plan_executable_scope",
            })
            control_id = authorization["control_package_id"]
            execution = post("executions", {
                "control_package_id": control_id,
                "confirm_execution": True,
                "operator_confirmation_reference": "k2a-k1-05-deterministic-stale",
                "confirm_network_execution": True,
            })
            if execution.get("external_market_network_attempted") is not False or execution.get("external_market_network_executed") is not False:
                raise RuntimeError("stale_fixture_attempted_external_market_network")
            package = post("result-package", {"control_package_id": control_id})
            result = package["canonical_result"]
            audit_response = client.get(f"/api/unified/result-package/{control_id}/audit.json")
            handoff_response = client.get(f"/api/unified/result-package/{control_id}/handoff")
            if audit_response.status_code != 200 or handoff_response.status_code != 200:
                raise RuntimeError("stale_audit_or_handoff_unavailable")
            audit = audit_response.json()
            handoff = handoff_response.json()

        invocations_before_reads = len(list((stale_root / "invocations").glob("*.invoked")))

        async def consume(order: tuple[str, str]) -> dict:
            observed = {}
            client = UnifiedLocalServiceClient(url)
            for operation in order:
                if operation == "read_result":
                    observed[operation] = await client.read_result(control_id)
                else:
                    observed[operation] = await client.export_ai_handoff(control_id)
            return observed

        with patch("server.unified_mcp.local_service_client.httpx.AsyncClient", REAL_HTTPX_ASYNC_CLIENT):
            read_first = asyncio.run(consume(("read_result", "export_ai_handoff")))
            export_first = asyncio.run(consume(("export_ai_handoff", "read_result")))
        if len(list((stale_root / "invocations").glob("*.invoked"))) != invocations_before_reads:
            raise RuntimeError("stale_read_only_consumption_reexecuted_source")

    evidence = result["targets"][0]["evidence"]["current_observation"]
    currentness = evidence.get("currentness", {})
    if result.get("status") != "full_success" or evidence.get("status") != "available":
        raise RuntimeError("stale_result_not_available_full_success")
    if currentness.get("status") != "stale" or currentness.get("freshness_assessment") != "stale_intraday_snapshot":
        raise RuntimeError("stale_currentness_not_projected")
    if currentness.get("source_timestamp") != "2026-09-01T05:30:00Z" or currentness.get("retrieved_at_utc") != "2026-10-08T06:00:00Z":
        raise RuntimeError("stale_timestamps_not_preserved")
    if currentness.get("recommendation_allowed") is not False or currentness.get("trading_advice_allowed") is not False:
        raise RuntimeError("stale_safety_semantics_regressed")
    for observation in (read_first, export_first):
        if observation["read_result"]["canonical_result"]["result_id"] != result["result_id"] or observation["export_ai_handoff"]["result_id"] != result["result_id"]:
            raise RuntimeError("stale_read_export_verification_failed")
    _lineage(result, audit, handoff)

    source_invocations = [json.loads(path.read_text(encoding="utf-8")) for path in sorted((stale_root / "invocations").glob("*.invoked"))]
    if len(source_invocations) != 1 or any(item.get("external_dispatch") is not False for item in source_invocations):
        raise RuntimeError("stale_source_boundary_not_isolated")
    return {
        "control_id": control_id, "result": result, "audit": audit, "handoff": handoff,
        "package_dir": stale_root / "control" / control_id,
        "read_first": read_first, "export_first": export_first,
        "transport_invocations": len(source_invocations),
        "external_market_network_executed": False,
        "fixture_executor_id": "repository_deterministic_stale_source_boundary",
        "currentness": currentness,
    }


def prepare(root: Path) -> dict:
    root = root.expanduser().resolve()
    if root == ROOT or ROOT in root.parents:
        raise ValueError("evaluation_root_must_be_outside_repository")
    if root.exists() and any(root.iterdir()):
        raise FileExistsError("evaluation_root_must_be_new_or_empty")
    root.mkdir(parents=True, exist_ok=True)
    package_root = root / "packages"
    package_root.mkdir()

    surface = build_tool_contract_snapshot()
    tools = [tool.name for tool in surface.tools]
    if tools != EXPECTED_TOOLS:
        raise RuntimeError("canonical_mcp_surface_drift")
    _write_json(root / "scenario_assets" / "K1-01" / "mcp_tools.json", {
        "tools": [tool.model_dump(mode="json", exclude_none=True) for tool in surface.tools],
    })
    fixture_root = "tests/fixtures/m8r_05a_f3/verified_security_master_snapshot.json"
    _copy_fixture(fixture_root, root, "scenario_assets/K1-02/verified_security_master_snapshot.json")
    _copy_fixture("tests/fixtures/m8r_05a_f3/verified_security_master_snapshot_manifest.json", root,
                  "scenario_assets/K1-02/verified_security_master_snapshot_manifest.json")
    from tests.helpers.phase_h_imp_7d_control_package import fixture_request
    request = fixture_request(request_id="k2a-k1-03", target_inputs=("6488",))
    _write_json(root / "scenario_assets" / "K1-03" / "execute_request.json", request)
    unsupported_request = {
        "schema_version": "unified_market_evidence_request.v3",
        "request_id": "k2a-k1-07-unsupported-financial-statements",
        "targets": [{"input": "TWSE:2330", "market_hint": "TWSE", "resolution_requirement": "exact"}],
        "data_needs": [{"type": "financial_statements", "priority": "required", "parameters": {}}],
        "execution_mode": "preview",
    }
    _write_json(root / "scenario_assets" / "K1-07" / "unsupported_financial_statements_request.json", unsupported_request)
    schema = json.loads((ROOT / "schemas/unified_market_evidence_request.v3.schema.json").read_text(encoding="utf-8"))
    try:
        import jsonschema
        jsonschema.validate(unsupported_request, schema)
    except jsonschema.ValidationError:
        pass
    else:
        raise RuntimeError("unsupported_request_fixture_was_accepted")

    socket_attempts = {"external": 0, "loopback": 0}
    original_connect = socket.socket.connect
    def deny_external_socket(sock, address, *args, **kwargs):
        host = address[0] if isinstance(address, tuple) and address else ""
        if host in {"127.0.0.1", "::1", "localhost"}:
            socket_attempts["loopback"] += 1
            return original_connect(sock, address, *args, **kwargs)
        socket_attempts["external"] += 1
        raise AssertionError("external_network_socket_attempt_forbidden_during_k2a_preparation")

    original_create_connection = socket.create_connection
    def deny_external_create_connection(address, *args, **kwargs):
        host = address[0] if isinstance(address, tuple) and address else ""
        if host in {"127.0.0.1", "::1", "localhost"}:
            socket_attempts["loopback"] += 1
            return original_create_connection(address, *args, **kwargs)
        socket_attempts["external"] += 1
        raise AssertionError("external_network_socket_attempt_forbidden_during_k2a_preparation")

    original_async_client = httpx.AsyncClient
    class InProcessServiceClient(original_async_client):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = httpx.ASGITransport(app=app)
            kwargs.setdefault("base_url", "http://127.0.0.1:8000")
            super().__init__(*args, **kwargs)

    # Reuse the repository-owned deterministic fixture executor. It declares
    # network_required=false and reads only committed fixture rows.
    with patch.object(socket.socket, "connect", deny_external_socket), \
         patch.object(socket, "create_connection", deny_external_create_connection), \
         patch("server.unified_mcp.local_service_client.httpx.AsyncClient", InProcessServiceClient), \
         patch.object(unified_mode_c, "CONTROL_ROOT", package_root), \
         patch.object(unified_mode_c, "validate_mode_a_request", lambda request: unified_mode_a.validate_mode_a_request(request, allow_fixture_snapshot=True)):
        success = _prepare_package(package_root, ("6488",), expected_status="full_success")
        stale = _prepare_stale_package(root)
        partial = _prepare_partial_failure_package(root)
        if socket_attempts["external"]:
            raise RuntimeError("network_socket_attempt_observed")

    def sha(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    packages = {}
    for key, prepared in (("success", success), ("stale", stale), ("partial", partial)):
        package_dir = prepared["package_dir"]
        result_path = package_dir / "ai_context" / "unified_market_evidence_result.v3.json"
        audit_path = package_dir / "audit" / "unified_market_evidence_audit_package.v3.json"
        handoff_path = root / f"{key}_handoff.json"
        _write_json(handoff_path, prepared["handoff"])
        if not result_path.is_file() or not audit_path.is_file():
            raise RuntimeError("prepared_package_artifact_missing")
        invocation_count = (prepared["transport_invocations"] if "transport_invocations" in prepared
                            else prepared["execution"]["invocations"]["count"])
        packages[key] = {
            "control_package_id": prepared["control_id"],
            "package_path": package_dir.relative_to(root).as_posix(),
            "fixture_authority": "NON_AUTHORITATIVE_TEST_ONLY",
            "isolated_security_master_root": {"partial": "partial_test/security-master", "stale": "stale_test/security"}.get(key),
            "fixture_executor_id": prepared.get("fixture_executor_id", "phase_h_imp_7d_deterministic_fixture_executor"),
            "executor_invocations": invocation_count,
            "result_status": prepared["result"]["status"],
            "currentness": prepared.get("currentness"),
            "result": {"path": result_path.relative_to(root).as_posix(), "result_id": prepared["result"]["result_id"], "sha256": sha(result_path)},
            "audit": {"path": audit_path.relative_to(root).as_posix(), "audit_package_id": prepared["audit"]["audit_package_id"], "sha256": sha(audit_path)},
            "handoff": {"path": handoff_path.relative_to(root).as_posix(), "result_id": prepared["handoff"]["result_id"], "sha256": sha(handoff_path)},
            "lineage_verified": True,
        }

    manifest = {
        "kit_version": KIT_VERSION,
        "repository_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "preparation_utility_sha256": sha(Path(__file__).resolve()),
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "evaluation_root": ".",
        "scenario_asset_mapping": SCENARIO_ASSETS,
        "generated_package": {
            "packages": packages,
        },
        "read_only_order_checks": {"read_then_export": "PASS", "export_then_read": "PASS", "ordering_precondition_enforced": False},
        "network_counters": {"market_source_GET": 0, "market_source_HEAD": 0, "market_source_POST": 0, "external_socket_connect_attempts": socket_attempts["external"], "loopback_test_transport_connects": socket_attempts["loopback"], "fixture_executor_network_required": False, "stale_fixture_external_market_network_executed": stale["external_market_network_executed"], "partial_fixture_external_market_network_executed": partial["external_market_network_executed"]},
        "canonical_mcp_tools": tools,
        "generation_command": "python scripts/prepare_phase_k_k2_deterministic_eval.py --root <disposable-evaluation-root>",
        "known_preparation_gaps": [f"{item['scenario_id']}: {item['gap']}" for item in SCENARIO_ASSETS if item.get("gap")],
        "scenario_asset_hashes": {
            item["root_asset"]: sha(root / item["root_asset"])
            for item in SCENARIO_ASSETS if item.get("root_asset")
        },
        "host_evaluation_count": 0,
        "compatibility_outcome_claims": [],
    }
    _write_json(root / "preparation_manifest.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path, help="new or empty disposable evaluation root, outside the repository")
    args = parser.parse_args()
    manifest = prepare(args.root)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

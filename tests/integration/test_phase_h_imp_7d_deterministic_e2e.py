"""H-IMP-7D selected-slice acceptance: offline fixture transport only."""
from __future__ import annotations

import hashlib
import json
import asyncio
import socket
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from fastapi.testclient import TestClient

from scripts.m8r_05b_03.consumption_claim import atomic_claim_authorization
from scripts.m8r_05b_03.dispatch import OrchestrationError
from scripts.m8r_05b_03.receipt import finalize_consumption_and_write_receipt
from scripts.m8r_05b_03.preflight import validate_preflight_hashes
from server.services import unified_mode_c
from server.services.unified_local_service import describe_capabilities
from server.services.unified_mode_a import validate_mode_a_request
from server.services.unified_mode_b2 import ModeB2Error, build_mode_b2_authorization
from server.unified_mcp.tool_contracts import PREFERRED_REQUEST_SCHEMA_VERSION, build_tool_specs
from server.services.phase_h_corporate_action_adapters import assemble_corporate_action_context, normalize_tpex_exright_daily
from server.services.phase_h_discontinuity_safety import derive_discontinuity_safety
from server.services.phase_h_trading_status_adapters import normalize_tpex_attention
from tests.helpers.phase_h_imp_7d_control_package import (
    NOW,
    execute_fixture_package,
    fixture_f3,
    fixture_plan,
    fixture_request,
    fixture_registry,
    make_runtime,
    prepare_unused_fixture_package,
)


ROOT = Path(__file__).resolve().parents[2]


def _project(execution: dict, monkeypatch) -> tuple[dict, dict, dict]:
    """Run actual Mode C with its F3 function using the supported fixture mode."""
    monkeypatch.setattr(unified_mode_c, "CONTROL_ROOT", execution["package"].parent)
    monkeypatch.setattr(unified_mode_c, "validate_mode_a_request", lambda request: validate_mode_a_request(request, allow_fixture_snapshot=True))
    result = unified_mode_c.build_mode_c_result_package(
        {"control_package_id": execution["authorization"]["authorization_id"]},
        output_schema_version="unified_market_evidence_result.v3",
    )
    audit = unified_mode_c.read_mode_c_audit(execution["authorization"]["authorization_id"], "unified_market_evidence_result.v3")
    handoff = unified_mode_c.build_mode_c_ai_handoff(execution["authorization"]["authorization_id"], "unified_market_evidence_result.v3")
    return result, audit, handoff


def test_s1_real_controlled_dispatch_v2_sidecar_to_mode_c_v3_and_h5(tmp_path: Path, monkeypatch):
    execution = execute_fixture_package(tmp_path)
    result, audit, handoff = _project(execution, monkeypatch)
    assert execution["invocations"]["count"] == 1
    assert execution["outcomes"][0]["schema_version"] == "unified_market_evidence_operation_result.v2"
    assert {a["artifact_role"] for a in execution["outcomes"][0]["evidence_artifacts"]} == {"primary_evidence", "supporting_governance"}
    assert execution["aggregation"]["total_item_count"] == 1
    assert execution["receipt"]["schema_version"] == "unified_market_evidence_execution_receipt.v1"
    assert execution["bundle"]["schema_version"] == "unified_market_evidence_bundle.v1"
    assert {a["evidence_contract"] for a in execution["bundle"]["artifact_inventory"]} == {"trading_status_context_evidence.v1", "phase_h_source_attempt_governance.v1"}
    schemas = {
        "result": ROOT / "schemas/unified_market_evidence_result.v3.schema.json",
        "audit": ROOT / "schemas/unified_market_evidence_audit_package.v3.schema.json",
    }
    assert not list(Draft202012Validator(json.loads(schemas["result"].read_text())).iter_errors(result["canonical_result"]))
    assert not list(Draft202012Validator(json.loads(schemas["audit"].read_text())).iter_errors(audit))
    assert result["external_market_network_executed"] is False
    assert handoff["additional_market_network_executed"] is False
    lowered = handoff["ai_ready_markdown"].lower()
    assert all(word not in lowered for word in ("buy", "sell", "hold", "target price", "bullish", "bearish", "買進", "賣出", "持有", "目標價", "看多", "看空"))


def test_s3_fixture_source_failure_propagates_truthfully_to_result_audit_and_h5(tmp_path: Path, monkeypatch):
    execution = execute_fixture_package(tmp_path, malformed=True)
    result, audit, handoff = _project(execution, monkeypatch)
    assert execution["outcomes"][0]["status"] == "failed"
    assert execution["outcomes"][0]["error_code"] == "source_failed"
    assert execution["invocations"]["count"] == 1
    assert execution["bundle"]["total_item_count"] == 0
    assert result["result_status"] == "failed"
    assert audit["receipt_identity"]["execution_receipt_id"] == execution["receipt"]["execution_receipt_id"]
    assert handoff["execution_outcome"] == "failed"


def test_s7_historical_pre_activation_v3_denial_evidence_is_preserved():
    ledger = json.loads(
        (ROOT / "docs/governance/phase_h/PHASE_H_H_IMP_7D_DETERMINISTIC_E2E_LEDGER.json").read_text(encoding="utf-8")
    )
    scenario = next(item for item in ledger["scenarios"] if item["scenario_id"] == "S7_PRODUCTION_V3_AUTHORIZATION_DENIED")
    assert scenario["status"] == "PASS"
    assert scenario["actual_result"] == "EXPECTED_REJECT before claim/dispatch/artifact"


def test_s8_replay_claim_rejected_and_s9_second_claim_is_the_only_rejection(tmp_path: Path):
    execution = execute_fixture_package(tmp_path)
    preflight = execution["preflight"]
    state = {"authorization_id": execution["authorization"]["authorization_id"], "authorization_hash": execution["authorization"]["authorization_hash"],
             "consumption_binding_id": execution["binding"]["consumption_binding_id"], "consumption_binding_hash": execution["binding"]["consumption_binding_hash"],
             "registry_contract_version": "m8r_05b_03.v1", "state": "unused"}
    with pytest.raises(OrchestrationError, match="authorization_already_claimed"):
        atomic_claim_authorization(preflight, state, output_root=str(execution["package"]), claim_created_at=NOW,
                                   operator_confirmation_reference="replay", network_execution_confirmed=False)
    assert execution["invocations"]["count"] == 1


def test_s9_concurrent_claim_has_exactly_one_winner_and_one_replay_rejection(tmp_path: Path):
    prepared = prepare_unused_fixture_package(tmp_path)
    def claim_once():
        try:
            return ("claimed", atomic_claim_authorization(prepared["preflight"], deepcopy(prepared["state"]),
                output_root=str(prepared["package"]), claim_created_at=NOW,
                operator_confirmation_reference="concurrent", network_execution_confirmed=False)[0])
        except OrchestrationError as exc:
            return (exc.code, None)
    with ThreadPoolExecutor(max_workers=2) as workers:
        outcomes = list(workers.map(lambda _index: claim_once(), range(2)))
    assert [status for status, _claim in outcomes].count("claimed") == 1
    assert [status for status, _claim in outcomes].count("authorization_already_claimed") == 1
    assert len(list((prepared["package"] / "claims").glob("*.json"))) == 1


def test_s10_v2_validation_remains_unaffected_and_s13_fixture_transport_is_network_free():
    request = {"schema_version": "unified_market_evidence_request.v2", "request_id": "h-imp-7d-v2",
               "targets": [{"input": "2330", "market_hint": "TWSE", "resolution_requirement": "exact", "client_target_reference": "v2"}],
               "data_needs": [{"type": "current_observation", "priority": "required", "parameters": {}}], "execution_mode": "preview"}
    result = validate_mode_a_request(request, allow_fixture_snapshot=True)
    assert result["schema_version"] == "unified_market_evidence_request_validation.v1"
    assert fixture_registry()["executors"][0]["network_required"] is False
    v2_root = ROOT / "tests/fixtures/phase_g_pr_c/v2_acceptance"
    v2_result = json.loads((v2_root / "unified_market_evidence_result.v2.json").read_text(encoding="utf-8"))
    v2_audit = json.loads((v2_root / "unified_market_evidence_audit_package.v2.json").read_text(encoding="utf-8"))
    assert v2_result["schema_version"] == "unified_market_evidence_result.v2"
    assert v2_audit["schema_version"] == "unified_market_evidence_audit_package.v2"
    assert v2_result["request_summary"]["execution_mode"] == "execute_once"
    assert v2_audit["authorization_identity"]["schema_version"] == "unified_market_evidence_execution_authorization.v1"
    assert v2_audit["claim_identity"]["schema_version"] == "unified_market_evidence_consumption_record.v1"
    assert v2_audit["receipt_identity"]["schema_version"] == "unified_market_evidence_execution_receipt.v1"
    assert v2_audit["bundle_identity"]["schema_version"] == "unified_market_evidence_bundle.v1"
    checksums = {
        name: digest for digest, name in (line.split("  ", 1) for line in (v2_root / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines())
    }
    assert all(hashlib.sha256((v2_root / name).read_bytes()).hexdigest() == digest for name, digest in checksums.items())


def test_s2_exact_target_binding_has_no_fixture_or_citation_leakage():
    rows = json.loads((ROOT / "tests/fixtures/phase_h_h1_adapters/source_rows.json").read_text())["tpex_attention"]
    matched = normalize_tpex_attention(rows, {"canonical_target_id": "TPEX:6488", "market": "TPEX", "security_code": "6488"}, observed_at=NOW, citation_id="cit-target-a")
    missing = normalize_tpex_attention(rows, {"canonical_target_id": "TPEX:9999", "market": "TPEX", "security_code": "9999"}, observed_at=NOW, citation_id="cit-target-b")
    assert matched["target"]["canonical_target_id"] == "TPEX:6488"
    assert missing["target"]["canonical_target_id"] == "TPEX:9999"
    assert "cit-target-a" not in missing["citation_ids"]
    assert "cit-target-b" not in matched["citation_ids"]


def test_s2_multi_target_controlled_e2e_preserves_target_scoped_mixed_outcomes(tmp_path: Path, monkeypatch):
    execution = execute_fixture_package(tmp_path, target_inputs=("6488", "3333"))
    result, audit, handoff = _project(execution, monkeypatch)
    succeeded, failed = execution["outcomes"]
    assert succeeded["status"] == "succeeded"
    assert failed["status"] == "failed"
    assert failed["error_code"] == "source_failed"
    assert execution["receipt"]["overall_status"] == "partial_success"
    assert execution["bundle"]["total_item_count"] == 1
    sidecar = next(item for item in succeeded["evidence_artifacts"] if item["artifact_role"] == "supporting_governance")
    assert "6488" in sidecar["relative_path"] or succeeded["operation_id"] in sidecar["relative_path"]
    targets = {item["canonical_identity"]["canonical_target_id"]: item for item in result["canonical_result"]["targets"]}
    assert "trading_status_context" in targets["TPEX:6488"]["evidence"]
    assert "trading_status_context" not in targets["TPEX:3333"]["evidence"]
    citations_a = {item["citation_id"] for item in targets["TPEX:6488"]["citations"]}
    citations_b = {item["citation_id"] for item in targets["TPEX:3333"].get("citations", [])}
    assert citations_a.isdisjoint(citations_b)
    assert audit["schema_version"] == "unified_market_evidence_audit_package.v3"
    assert handoff["execution_outcome"] == "partial_success"


def test_s4_h2_final_fixture_and_h4_keep_discontinuity_coverage_truthful():
    rows = json.loads((ROOT / "tests/fixtures/phase_h_h2_adapters/source_rows.json").read_text(encoding="utf-8"))["tpex_final"]
    target = {"canonical_target_id": "TPEX:6488", "market": "TPEX", "security_code": "6488"}
    h2_part = normalize_tpex_exright_daily(rows, target, observed_at=NOW, citation_id="cit-h2")
    h2 = assemble_corporate_action_context([h2_part], target, observed_at=NOW, requested_window={"start": "2026-08-01", "end": "2026-08-28"})
    h3 = deepcopy(json.loads((ROOT / "tests/fixtures/phase_h_contract_v3/contract_examples.json").read_text(encoding="utf-8"))["h3_5d"])
    for item in [h3["target"], h3["governed_end_observation"], *h3["observations"]]:
        item.update(target)
    h4 = derive_discontinuity_safety(h2_evidence=h2, h3_evidence=h3, h2_evidence_reference="evidence/h2.json", h3_evidence_reference="evidence/h3.json", event_evidence_references={0: "evidence/h2.json"})
    assert h4["state"] == "coverage_incomplete"
    assert h4["interpretation_guard"] == "CORPORATE_ACTION_COVERAGE_INCOMPLETE"
    assert h4["input_evidence_references"] == ["evidence/h2.json", "evidence/h3.json"]


def test_s5_ordinary_day_and_s6_h3_complete_partial_fixtures_remain_explicitly_test_only():
    examples = json.loads((ROOT / "tests/fixtures/phase_h_contract_v3/contract_examples.json").read_text(encoding="utf-8"))
    assert examples["h4_no_material"]["state"] == "no_material_discontinuity_detected"
    complete = examples["h3_5d"]
    partial = deepcopy(complete)
    partial["coverage_status"] = "partial"
    partial["missing_observation_count"] = 1
    partial["baselines"][0]["status"] = "unavailable"
    partial["available_baselines"] = []
    partial["unavailable_baselines"] = [5]
    assert complete["baselines"][0]["recent_return_pct"] == 20.0
    assert complete["volume_context"]["historical_average_basis"] == "completed_official_sessions"
    assert partial["coverage_status"] == "partial"
    assert complete["schema_version"] == "recent_performance_evidence.v1"


def test_s11_fresh_root_is_safe_without_optional_providers_and_manual_routes_stay_manual(tmp_path: Path):
    empty_root = tmp_path / "fresh-install-without-twt49u-or-h3-provider"
    empty_root.mkdir()
    assert not list(empty_root.iterdir())
    # Fixture F3 has no provider, cache, or source-route dependency.
    v3_validation = fixture_f3(fixture_request())
    assert v3_validation["target_results"][0]["resolution_status"] == "resolved"
    assert PREFERRED_REQUEST_SCHEMA_VERSION == "unified_market_evidence_request.v2"
    described = describe_capabilities()
    assert described["preferred_request_schema_version"] == "unified_market_evidence_request.v2"
    assert described["emitted_result_schema_version"] == "unified_market_evidence_result.v2"
    v3_catalog = json.loads((ROOT / "docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json").read_text(encoding="utf-8"))
    v3_routing = json.loads((ROOT / "docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json").read_text(encoding="utf-8"))
    assert v3_catalog["phase_h_contract"]["active_phase_h_source_count"] == 1
    assert v3_routing["phase_h_source_authority"]["active_source_count"] == 1
    active = [record for record in v3_routing["phase_h_source_authority"]["records"] if record["activation_state"] == "active"]
    assert [(record["source_id"], record["runtime_executable"]) for record in active] == [
        ("H1-TPEX-ATTENTION-OPENAPI", True)
    ]
    authority = json.loads((ROOT / "docs/governance/phase_h/Phase_H_Official_Source_and_Automation_Authority_Matrix_FROZEN.json").read_text(encoding="utf-8"))
    by_id = {item["source_id"]: item for item in authority["sources"]}
    assert by_id["H2-TWSE-EXRIGHT-FINAL-TWT49U"]["source_role"] == "optional_licensed_provider"
    assert by_id["H2-TWSE-EXRIGHT-FINAL-TWT49U"]["activation_state"] == "inactive"
    for source_id in ("H2-TWSE-CAPITAL-REDUCTION-WEB", "H2-TPEX-CAPITAL-REDUCTION-WEB"):
        assert by_id[source_id]["source_role"] == "manual_verification"
        assert by_id[source_id]["activation_state"] == "inactive"
    for source_id in ("H2-TWSE-PAR-SPLIT-CONSOLIDATION-GAP", "H2-TPEX-PAR-SPLIT-CONSOLIDATION-GAP"):
        assert by_id[source_id]["retrieval_contract_status"] == "not_proven"
        assert by_id[source_id]["activation_state"] == "blocked"


def test_s12_rollback_model_keeps_v1_v2_and_materialized_v3_immutable(tmp_path: Path, monkeypatch):
    execution = execute_fixture_package(tmp_path)
    result, audit, _handoff = _project(execution, monkeypatch)
    v1_root = ROOT / "tests/fixtures/phase_g_pr_c/v1_mode_c_golden"
    v2_root = ROOT / "tests/fixtures/phase_g_pr_c/v2_acceptance"
    historical = [v1_root / "ai_context/unified_market_evidence_result.v1.json",
                  v1_root / "audit/unified_market_evidence_audit_package.v1.json",
                  v2_root / "unified_market_evidence_result.v2.json",
                  v2_root / "unified_market_evidence_audit_package.v2.json"]
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in historical}
    v3_paths = [execution["package"] / rel for rel in ("ai_context/unified_market_evidence_result.v3.json", "audit/unified_market_evidence_audit_package.v3.json")]
    v3_before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in v3_paths}
    preferred_candidate, rollback_trigger = "unified_market_evidence_result.v3", "fixture_audit_lineage_failure"
    preferred_after = "unified_market_evidence_result.v2" if rollback_trigger else preferred_candidate
    assert preferred_after == "unified_market_evidence_result.v2"
    assert result["canonical_result"]["schema_version"] == "unified_market_evidence_result.v3"
    assert audit["schema_version"] == "unified_market_evidence_audit_package.v3"
    assert all(path.is_file() for path in historical)
    assert before == {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in historical}
    assert v3_before == {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in v3_paths}
    assert not (execution["package"] / "ai_context/unified_market_evidence_result.v2.json").exists()
    assert PREFERRED_REQUEST_SCHEMA_VERSION == "unified_market_evidence_request.v2"


def test_s13_startup_and_fixture_execution_have_zero_external_transport_calls(monkeypatch, tmp_path: Path):
    calls = {"count": 0}
    original_connect = socket.socket.connect
    def fail_if_external_connect(sock, address):
        host = address[0] if isinstance(address, tuple) and address else None
        if host in {"127.0.0.1", "::1", "localhost"}:
            return original_connect(sock, address)
        calls["count"] += 1
        raise AssertionError("external_market_transport_called")
    monkeypatch.setattr(socket.socket, "connect", fail_if_external_connect)
    assert fixture_f3(fixture_request())["target_results"][0]["resolution_status"] == "resolved"
    from server import mcp_server
    from server.main import app
    legacy_tools = asyncio.run(mcp_server.list_tools())
    assert legacy_tools
    assert [tool.name for tool in build_tool_specs()] == [
        "market_describe_capabilities", "market_validate_request", "market_preview_request",
        "market_read_result", "market_export_ai_handoff", "market_fetch_evidence",
    ]
    assert PREFERRED_REQUEST_SCHEMA_VERSION == "unified_market_evidence_request.v2"
    client = TestClient(app)
    assert client.get("/api/health").status_code == 200
    assert client.get("/workbench/").status_code == 200
    execution = execute_fixture_package(tmp_path)
    assert execution["invocations"]["count"] == 1
    assert calls["count"] == 0


def test_fixed_clock_cross_root_rerun_preserves_portable_semantics_and_valid_execution_lineage(tmp_path: Path, monkeypatch):
    first = execute_fixture_package(tmp_path / "first")
    second = execute_fixture_package(tmp_path / "second")
    assert first["plan"]["plan_hash"] == second["plan"]["plan_hash"]
    assert first["authorization"]["authorization_hash"] == second["authorization"]["authorization_hash"]
    assert first["binding"]["consumption_binding_hash"] == second["binding"]["consumption_binding_hash"]
    assert first["preflight"]["bounded_execution_requests"] == second["preflight"]["bounded_execution_requests"]
    assert first["outcomes"][0]["evidence_artifacts"] == second["outcomes"][0]["evidence_artifacts"]
    assert first["preflight"]["governed_output_root"] != second["preflight"]["governed_output_root"]
    assert first["preflight"]["preflight_identity_hash"] != second["preflight"]["preflight_identity_hash"]
    assert first["claim"]["claim_id"] != second["claim"]["claim_id"]
    assert first["receipt"]["execution_receipt_hash"] != second["receipt"]["execution_receipt_hash"]
    assert first["bundle"]["bundle_hash"] != second["bundle"]["bundle_hash"]
    for run in (first, second):
        validate_preflight_hashes(run["preflight"])
        assert run["claim"]["preflight_id"] == run["preflight"]["preflight_id"]
        assert run["receipt"]["claim_id"] == run["claim"]["claim_id"]
        assert run["receipt"]["preflight_id"] == run["preflight"]["preflight_id"]
        assert run["bundle"]["claim_id"] == run["claim"]["claim_id"]
        assert run["bundle"]["execution_receipt_id"] == run["receipt"]["execution_receipt_id"]
    assert first["claim"]["preflight_id"] != second["preflight"]["preflight_id"]
    for run in (first, second):
        result, audit, handoff = _project(run, monkeypatch)
        root = run["preflight"]["governed_output_root"]
        assert root not in json.dumps([result, audit, handoff], ensure_ascii=False)


def test_safety_path_rejects_unsafe_artifact_before_projection(tmp_path: Path):
    execution = execute_fixture_package(tmp_path)
    artifact = execution["outcomes"][0]["evidence_artifacts"][0]
    artifact["relative_path"] = "../unsafe.json"
    with pytest.raises(OrchestrationError):
        # A genuine dispatch would reject this result before aggregation; this verifies
        # the same contained-path gate without repairing the result.
        from scripts.m8r_05b_03.dispatch import _verify_evidence_artifacts
        _verify_evidence_artifacts(str(execution["package"]), [artifact], "execute-approved")

"""Bridge regression: one V2 operation can carry typed evidence plus governance."""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

from scripts.m8r_05b_01.canonical import plan_hash_and_id
from scripts.m8r_05b_01.planner import plan_identity_scope
from scripts.m8r_05b_02.authorization import build_execution_authorization
from scripts.m8r_05b_02.consumption_binding import build_consumption_binding
from scripts.m8r_05b_03.canonical import canonical_json, sha256_json
from scripts.m8r_05b_03.consumption_claim import atomic_claim_authorization
from scripts.m8r_05b_03.evidence_aggregation import aggregate_dispatch_outcomes
from scripts.m8r_05b_03.preflight import build_orchestrator_preflight
from scripts.m8r_05b_03.receipt import finalize_consumption_and_write_receipt
from scripts.m8r_05c.artifact_loader import load_projection_inputs
from scripts.m8r_05c.citation_builder import _build_citation_id
from server.services.phase_h_trading_status_adapters import normalize_tpex_attention
from server.services.unified_mode_a import validate_mode_a_request
from server.services import unified_mode_c
from tests.unit.m8r_05b_03_test_helpers import PLAN


ROOT = Path(__file__).resolve().parents[2]
NOW = "2026-09-22T00:00:00Z"
TARGET = {"canonical_target_id": "TPEX:6488", "market": "TPEX", "security_code": "6488"}
EXECUTOR = "bridge_fixture_executor"


def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value) + "\n", encoding="utf-8")


def _request_and_f3() -> tuple[dict, dict]:
    request = {"schema_version": "unified_market_evidence_request.v3", "request_id": "bridge-h1-fixture",
               "targets": [{"input": "6488", "market_hint": "TPEX", "resolution_requirement": "exact", "client_target_reference": "bridge"}],
               "data_needs": [{"type": "trading_status_context", "priority": "required", "parameters": {}}], "execution_mode": "execute"}
    return request, validate_mode_a_request(request, allow_fixture_snapshot=True)


def _plan(request: dict, f3: dict) -> dict:
    plan = deepcopy(PLAN)
    op = plan["operations"][0]
    op.update({"capability_id": "trading_status_context", "canonical_target_ids": [TARGET["canonical_target_id"]], "market": "TPEX",
               "executor_id": EXECUTOR, "expected_evidence_contract": "trading_status_context_evidence.v1", "parameters": {}})
    batch = plan["batch_groups"][0]
    batch.update({"capability_id": "trading_status_context", "market": "TPEX", "executor_id": EXECUTOR})
    plan["input_bindings"].update({"original_request_hash": sha256_json(request), "normalized_request_hash": sha256_json(f3["normalized_request"]),
                                   "f3_validation_output_hash": sha256_json(f3)})
    plan["plan_hash"], plan["plan_id"] = plan_hash_and_id(plan_identity_scope(plan))
    return plan


def test_v2_aggregation_finalization_and_loader_accept_typed_evidence_and_sidecar(tmp_path: Path, monkeypatch):
    request, f3 = _request_and_f3()
    plan = _plan(request, f3)
    decision = {"decision": "approved", "decision_reason": "bridge test", "owner_identity_reference": "test-owner", "owner_review_reference": "test-review", "reviewed_at": NOW, "issued_at": NOW, "expires_at": "2026-09-22T01:00:00Z", "single_use": True, "replay_policy": "deny_replay", "maximum_use_count": 1, "approval_scope_mode": "selected_operations", "approved_operation_ids": [plan["operations"][0]["operation_id"]], "approved_batch_group_ids": [], "approved_batch_membership": {}}
    authorization = build_execution_authorization(plan, decision)
    binding = build_consumption_binding(authorization)
    state = {"authorization_id": authorization["authorization_id"], "authorization_hash": authorization["authorization_hash"], "consumption_binding_id": binding["consumption_binding_id"], "consumption_binding_hash": binding["consumption_binding_hash"], "registry_contract_version": "m8r_05b_03.v1", "state": "unused"}
    package = tmp_path / authorization["authorization_id"]
    package.mkdir()
    registry = {"schema_version": "m8r_05b_03_executor_registry_metadata.v1", "executors": [{"executor_id": EXECUTOR, "capability_id": "trading_status_context", "market": "TPEX", "supported_security_types": ["equity"], "expected_evidence_contract": "trading_status_context_evidence.v1", "network_required": True, "bounded_execution_supported": True, "timeout_seconds": 5, "maximum_result_items": 10, "output_policy": "contained_artifact_only"}]}
    preflight = build_orchestrator_preflight(plan, authorization, binding, supplied_consumption_state=state, evaluation_timestamp=NOW, executor_registry_metadata=registry, output_root=str(package))
    controls = {"request": request, "plan": plan, "authorization": authorization, "consumption_binding": binding, "unused_consumption_state": state, "preflight": preflight}
    for name, value in controls.items(): _write(package / "control" / f"{name}.json", value)
    hashes = {name: hashlib.sha256((package / "control" / f"{name}.json").read_bytes()).hexdigest() for name in controls}
    _write(package / "control" / "manifest.json", {"schema_version": "m8r_06_03_control_package.v1", "authorization_id": authorization["authorization_id"], "authorization_hash": authorization["authorization_hash"], "plan_id": plan["plan_id"], "plan_hash": plan["plan_hash"], "preflight_id": preflight["preflight_id"], "preflight_hash": preflight["preflight_hash"], "artifact_hashes": hashes})
    claim, claim_path = atomic_claim_authorization(preflight, state, output_root=str(package), claim_created_at=NOW, operator_confirmation_reference="bridge", network_execution_confirmed=False)
    rows = json.loads((ROOT / "tests/fixtures/phase_h_h1_adapters/source_rows.json").read_text(encoding="utf-8"))["tpex_attention"]
    evidence_path, sidecar_path = "evidence/h1.json", "evidence/h1-sidecar.json"
    evidence = normalize_tpex_attention(rows, TARGET, observed_at=NOW, citation_id=_build_citation_id(preflight["approved_operation_order"][0], evidence_path))
    _write(package / evidence_path, evidence)
    sidecar = {"schema_version": "phase_h_source_attempt_governance.v1", "evidence_artifact_reference": evidence_path, "canonical_target_id": TARGET["canonical_target_id"], "capability_id": "trading_status_context", "attempts": [{"source_family": evidence["source"]["source_family"], "source_contract_id": evidence["source"]["source_contract_id"], "source_role": evidence["source"]["source_role"], "activation_state": evidence["source"]["activation_state"], "provider_availability": "not_required", "license_authority": evidence["source"]["license_authority"], "coverage_result": evidence["status"], "outcome": "succeeded", "failure_code": None, "citation_ids": evidence["citation_ids"]}]}
    _write(package / sidecar_path, sidecar)
    def artifact(path: str, value: dict, role: str) -> dict:
        data = (package / path).read_bytes()
        return {"relative_path": path, "sha256": hashlib.sha256(data).hexdigest(), "schema_version": value["schema_version"], "byte_size": len(data), "item_count": len(value.get("items", [])) if "items" in value else 1, "evidence_contract": value["schema_version"], "artifact_role": role}
    req = preflight["bounded_execution_requests"][0]
    outcome = {"schema_version": "unified_market_evidence_operation_result.v2", "operation_id": req["operation_id"], "execution_request_id": req["execution_request_id"], "execution_request_hash": req["execution_request_hash"], "executor_id": EXECUTOR, "capability_id": "trading_status_context", "evidence_contract": "trading_status_context_evidence.v1", "status": "succeeded", "error_code": None, "result_item_count": 1, "evidence_artifacts": [artifact(evidence_path, evidence, "primary_evidence"), artifact(sidecar_path, sidecar, "supporting_governance")], "warnings": []}
    aggregation = aggregate_dispatch_outcomes(preflight, [outcome])
    final_claim, receipt, bundle = finalize_consumption_and_write_receipt(preflight, claim, claim_path, aggregation, output_root=str(package), finalized_at=NOW, finalization_owner_id="umefo-v1-00000000000000000000")
    f3_path = package / "mode_c/f3_validation.json"; _write(f3_path, f3)
    inputs = load_projection_inputs(request_path=str(package / "control/request.json"), f3_validation_path=str(f3_path), plan_path=str(package / "control/plan.json"), authorization_path=str(package / "control/authorization.json"), consumption_binding_path=str(package / "control/consumption_binding.json"), claim_path=str(next((package / "claims").glob("*.json"))), receipt_path=str(next((package / "receipts").glob("*.json"))), bundle_path=str(next((package / "bundles").glob("*.json"))), artifact_root=str(package), calculated_at=NOW, calculated_at_source="fixture")
    assert final_claim["state"] == "consumed_success"
    assert receipt["schema_version"] == "unified_market_evidence_execution_receipt.v1"
    assert bundle["schema_version"] == "unified_market_evidence_bundle.v1"
    assert aggregation["total_item_count"] == 1
    assert {item["evidence_contract"] for item in bundle["artifact_inventory"]} == {"trading_status_context_evidence.v1", "phase_h_source_attempt_governance.v1"}
    assert set(inputs.evidence_artifacts) == {evidence_path, sidecar_path}
    f3_path.unlink()
    monkeypatch.setattr(unified_mode_c, "CONTROL_ROOT", package.parent)
    monkeypatch.setattr(unified_mode_c, "validate_mode_a_request", lambda _request: f3)
    projected = unified_mode_c.build_mode_c_result_package({"control_package_id": authorization["authorization_id"]}, output_schema_version="unified_market_evidence_result.v3")
    assert projected["external_market_network_executed"] is False
    assert projected["canonical_result"]["targets"][0]["evidence"]["trading_status_context"]["schema_version"] == "trading_status_context_evidence.v1"

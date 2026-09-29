from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import jsonschema

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
from scripts.m8r_05c.audit_package_builder import build_audit_package
from scripts.m8r_05c.citation_builder import _build_citation_id, build_citation_index
from scripts.m8r_05c.lineage_resolver import build_lineage_map
from scripts.m8r_05c.result_builder import build_result
from server.services.phase_i_market_state_adapters import normalize_tpex_market_state
from server.services.unified_mode_a import validate_mode_a_request
from tests.unit.m8r_05b_03_test_helpers import PLAN


ROOT = Path(__file__).resolve().parents[2]
NOW = "2026-09-29T06:00:00Z"
FIXTURE = ROOT / "tests/fixtures/phase_i_i1/tpex_highlight.json"


def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value) + "\n", encoding="utf-8")


def test_i1_fixture_crosses_loader_lineage_result_v3_and_audit_v3(tmp_path: Path):
    request = {
        "schema_version": "unified_market_evidence_request.v3",
        "request_id": "i1-integration-fixture",
        "targets": [{"input": "6488", "market_hint": "TPEX", "resolution_requirement": "exact"}],
        "data_needs": [{"type": "market_state_context", "priority": "required", "parameters": {}}],
        "execution_mode": "execute",
    }
    f3 = validate_mode_a_request(request, allow_fixture_snapshot=True)
    target = f3["target_results"][0]["canonical_identity"]
    target_id = target["canonical_target_id"]

    plan = copy.deepcopy(PLAN)
    operation = plan["operations"][0]
    operation.update({
        "capability_id": "market_state_context",
        "canonical_target_ids": [target_id],
        "market": "TPEX",
        "executor_id": "fixture_only_i1_normalizer",
        "expected_evidence_contract": "market_state_context_evidence.v1",
        "parameters": {},
    })
    plan["batch_groups"][0].update({
        "capability_id": "market_state_context",
        "market": "TPEX",
        "executor_id": "fixture_only_i1_normalizer",
    })
    plan["input_bindings"].update({
        "original_request_hash": sha256_json(request),
        "normalized_request_hash": sha256_json(f3["normalized_request"]),
        "f3_validation_output_hash": sha256_json(f3),
    })
    plan["plan_hash"], plan["plan_id"] = plan_hash_and_id(plan_identity_scope(plan))

    decision = {
        "decision": "approved",
        "decision_reason": "offline projection integration fixture",
        "owner_identity_reference": "fixture-owner",
        "owner_review_reference": "fixture-only-not-authority",
        "reviewed_at": NOW,
        "issued_at": NOW,
        "expires_at": "2026-09-29T07:00:00Z",
        "single_use": True,
        "replay_policy": "deny_replay",
        "maximum_use_count": 1,
        "approval_scope_mode": "selected_operations",
        "approved_operation_ids": [operation["operation_id"]],
        "approved_batch_group_ids": [],
        "approved_batch_membership": {},
    }
    authorization = build_execution_authorization(plan, decision)
    binding = build_consumption_binding(authorization)
    unused_state = {
        "authorization_id": authorization["authorization_id"],
        "authorization_hash": authorization["authorization_hash"],
        "consumption_binding_id": binding["consumption_binding_id"],
        "consumption_binding_hash": binding["consumption_binding_hash"],
        "registry_contract_version": "m8r_05b_03.v1",
        "state": "unused",
    }
    package = tmp_path / authorization["authorization_id"]
    package.mkdir(parents=True)
    registry = {
        "schema_version": "m8r_05b_03_executor_registry_metadata.v1",
        "executors": [{
            "executor_id": "fixture_only_i1_normalizer",
            "capability_id": "market_state_context",
            "market": "TPEX",
            "supported_security_types": ["equity"],
            "expected_evidence_contract": "market_state_context_evidence.v1",
            "network_required": False,
            "bounded_execution_supported": True,
            "timeout_seconds": 1,
            "maximum_result_items": 1,
            "output_policy": "contained_artifact_only",
        }],
    }
    preflight = build_orchestrator_preflight(
        plan, authorization, binding,
        supplied_consumption_state=unused_state,
        evaluation_timestamp=NOW,
        executor_registry_metadata=registry,
        output_root=str(package),
    )
    controls = {
        "request": request,
        "plan": plan,
        "authorization": authorization,
        "consumption_binding": binding,
        "unused_consumption_state": unused_state,
        "preflight": preflight,
    }
    for name, value in controls.items():
        _write(package / "control" / f"{name}.json", value)
    hashes = {
        name: hashlib.sha256((package / "control" / f"{name}.json").read_bytes()).hexdigest()
        for name in controls
    }
    _write(package / "control/manifest.json", {
        "schema_version": "m8r_06_03_control_package.v1",
        "authorization_id": authorization["authorization_id"],
        "authorization_hash": authorization["authorization_hash"],
        "plan_id": plan["plan_id"],
        "plan_hash": plan["plan_hash"],
        "preflight_id": preflight["preflight_id"],
        "preflight_hash": preflight["preflight_hash"],
        "artifact_hashes": hashes,
    })
    claim, claim_path = atomic_claim_authorization(
        preflight, unused_state, output_root=str(package), claim_created_at=NOW,
        operator_confirmation_reference="offline-i1-projection-fixture",
        network_execution_confirmed=False,
    )

    relative_path = "evidence/phase_i/i1/TPEX_market_state.json"
    artifact = normalize_tpex_market_state(json.loads(FIXTURE.read_text(encoding="utf-8")), retrieved_at=NOW)
    artifact["citation_ids"] = [_build_citation_id(operation["operation_id"], relative_path)]
    artifact_path = package / relative_path
    _write(artifact_path, artifact)
    artifact_ref = {
        "relative_path": relative_path,
        "sha256": hashlib.sha256(artifact_path.read_bytes()).hexdigest(),
        "schema_version": artifact["schema_version"],
        "byte_size": artifact_path.stat().st_size,
        "item_count": 1,
        "evidence_contract": artifact["schema_version"],
        "artifact_role": "primary_evidence",
    }
    execution_request = preflight["bounded_execution_requests"][0]
    operation_result = {
        "schema_version": "unified_market_evidence_operation_result.v2",
        "operation_id": execution_request["operation_id"],
        "execution_request_id": execution_request["execution_request_id"],
        "execution_request_hash": execution_request["execution_request_hash"],
        "executor_id": "fixture_only_i1_normalizer",
        "capability_id": "market_state_context",
        "evidence_contract": artifact["schema_version"],
        "status": "succeeded",
        "error_code": None,
        "result_item_count": 1,
        "evidence_artifacts": [artifact_ref],
        "warnings": [],
    }
    aggregation = aggregate_dispatch_outcomes(preflight, [operation_result])
    _, receipt, bundle = finalize_consumption_and_write_receipt(
        preflight, claim, claim_path, aggregation,
        output_root=str(package), finalized_at=NOW,
        finalization_owner_id="umefo-v1-00000000000000000000",
    )
    f3_path = package / "mode_c/f3_validation.json"
    _write(f3_path, f3)
    inputs = load_projection_inputs(
        request_path=str(package / "control/request.json"),
        f3_validation_path=str(f3_path),
        plan_path=str(package / "control/plan.json"),
        authorization_path=str(package / "control/authorization.json"),
        consumption_binding_path=str(package / "control/consumption_binding.json"),
        claim_path=str(package / claim_path),
        receipt_path=str(next((package / "receipts").glob("*.json"))),
        bundle_path=str(next((package / "bundles").glob("*.json"))),
        artifact_root=str(package),
        calculated_at=NOW,
        calculated_at_source="fixture",
    )
    lineage = build_lineage_map(inputs)
    citations = build_citation_index(lineage, inputs.bundle, "unified_market_evidence_result.v3")
    result = build_result(inputs, output_schema_version="unified_market_evidence_result.v3")
    audit = build_audit_package(
        result, inputs, citations, "ai_context/unified_market_evidence_result.v3.json",
        output_schema_version="unified_market_evidence_audit_package.v3",
    )

    assert inputs.evidence_artifacts[relative_path]["schema_version"] == "market_state_context_evidence.v1"
    assert lineage.bindings[target_id]["market_state_context"].status == "succeeded"
    assert result["targets"][0]["evidence"]["market_state_context"]["citation_ids"] == [
        _build_citation_id(operation["operation_id"], relative_path)
    ]
    jsonschema.Draft7Validator(json.loads((ROOT / "schemas/unified_market_evidence_result.v3.schema.json").read_text(encoding="utf-8"))).validate(result)
    jsonschema.Draft7Validator(json.loads((ROOT / "schemas/unified_market_evidence_audit_package.v3.schema.json").read_text(encoding="utf-8"))).validate(audit)
    assert audit["phase_i_evidence"]["evidence_artifact_references"][0]["relative_path"] == relative_path

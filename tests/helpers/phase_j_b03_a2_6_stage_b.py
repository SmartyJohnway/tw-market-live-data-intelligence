from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any, Callable
from unittest.mock import patch

from jsonschema import Draft202012Validator

from scripts.m8r_05b_02.authorization import build_execution_authorization
from scripts.m8r_05b_02.consumption_binding import build_consumption_binding
from scripts.m8r_05b_03.canonical import canonical_json
from scripts.m8r_05b_03.consumption_claim import atomic_claim_authorization
from scripts.m8r_05b_03.dispatch import dispatch_prepared, prepare_dispatch
from scripts.m8r_05b_03.evidence_aggregation import aggregate_dispatch_outcomes
from scripts.m8r_05b_03.preflight import build_orchestrator_preflight
from scripts.m8r_05b_03.receipt import finalize_consumption_and_write_receipt
from scripts.m8r_05b_03.registry import ExecutorMetadataRegistry
from scripts.m8r_06_02_mode_b1_preview import build_mode_b1_preview_package
from scripts.m8r_06_03_production_adapter import (
    build_production_runtime_adapter_registry, load_production_executor_metadata,
)
from scripts.m8r_filesystem_safety import safe_destination
from tests.helpers.phase_h_imp_7d_control_package import fixture_f3, fixture_request
from tests.helpers.phase_j_b03_a2_6_integrated import fixture_responses

ROOT = Path(__file__).resolve().parents[2]
AUTHORITY = "USER_CHAT_2026-10-07_J_B03_A2_6_PRODUCTION_ACTIVATION_AUTHORIZATION"
FIXED_TIME = "2026-10-07T01:00:00Z"


class FakeSecurityMaster:
    pointer = {
        "index_path": "data/security_master/runtime_identity_indexes/sealed/index.json",
        "manifest_path": "data/security_master/runtime_identity_indexes/sealed/manifest.json",
        "compact_index_sha256": "a" * 64,
        "compact_manifest_sha256": "b" * 64,
    }


def _write(root: Path, relative_path: str, value: dict[str, Any]) -> None:
    path = safe_destination(str(root), relative_path, create_parent=True).path
    path.write_text(canonical_json(value) + "\n", encoding="utf-8")


def run_production_dispatch_fixture(
    package_root: Path, *, responses: dict[str, Any] | None = None,
    failure_source_id: str | None = None,
    official_transport: Callable[..., dict[str, Any]] | None = None,
    request_override: dict[str, Any] | None = None,
    f3_validation: dict[str, Any] | None = None,
    security_master: Any | None = None,
) -> dict[str, Any]:
    """Use canonical plan, metadata, production registry/dispatch and Mode C offline."""
    package_root.mkdir(parents=True, exist_ok=True)
    request = request_override or fixture_request(request_id="a26-stage-b-prod-6488")
    f3 = f3_validation or fixture_f3(request)
    preview = build_mode_b1_preview_package(request, f3, security_master or FakeSecurityMaster(), planning_timestamp=FIXED_TIME)
    plan = preview["orchestration_plan"]
    operation = plan["operations"][0]
    if (preview["preview"]["status"] != "ready_for_confirmation"
            or operation["executor_id"] != "phase_h_h1_tpex_composite_executor"
            or operation["expected_evidence_contract"] != "trading_status_context_composite.v1"
            or plan["accounting"]["network_request_estimate"] != 3):
        raise AssertionError("canonical_stage_b_route_selection_invalid")
    decision = {
        "decision": "approved", "decision_reason": "Owner-authorized A2.6 Stage-B offline production fixture",
        "owner_identity_reference": "A2.6-stage-b-owner", "owner_review_reference": AUTHORITY,
        "reviewed_at": FIXED_TIME, "issued_at": FIXED_TIME, "expires_at": "2026-10-08T01:00:00Z",
        "single_use": True, "replay_policy": "deny_replay", "maximum_use_count": 1,
        "approval_scope_mode": "selected_operations", "approved_operation_ids": [operation["operation_id"]],
        "approved_batch_group_ids": [], "approved_batch_membership": {},
    }
    authorization = build_execution_authorization(plan, decision)
    binding = build_consumption_binding(authorization)
    root = package_root / authorization["authorization_id"]
    root.mkdir(parents=True, exist_ok=True)
    state = {"authorization_id": authorization["authorization_id"], "authorization_hash": authorization["authorization_hash"],
             "consumption_binding_id": binding["consumption_binding_id"], "consumption_binding_hash": binding["consumption_binding_hash"],
             "registry_contract_version": "m8r_05b_03.v1", "state": "unused"}
    metadata = load_production_executor_metadata()
    runtime = build_production_runtime_adapter_registry()
    preflight = build_orchestrator_preflight(plan, authorization, binding, supplied_consumption_state=deepcopy(state),
        evaluation_timestamp=FIXED_TIME, executor_registry_metadata=metadata, output_root=str(root))
    prepared = prepare_dispatch(preflight, ExecutorMetadataRegistry.from_json(metadata), runtime, mode="execute-approved")
    for name, value in (("request", request), ("f3", f3), ("plan", plan), ("authorization", authorization),
                        ("consumption_binding", binding), ("preflight", preflight), ("unused_consumption_state", state)):
        _write(root, f"control/{name}.json", value)
    control_files = {name: root / "control" / f"{name}.json" for name in
                     ("request", "plan", "authorization", "consumption_binding", "preflight", "unused_consumption_state")}
    _write(root, "control/manifest.json", {
        "schema_version": "m8r_06_03_control_package.v1", "authorization_id": authorization["authorization_id"],
        "authorization_hash": authorization["authorization_hash"], "plan_id": plan["plan_id"], "plan_hash": plan["plan_hash"],
        "preflight_id": preflight["preflight_id"], "preflight_hash": preflight["preflight_hash"],
        "artifact_hashes": {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in control_files.items()},
    })
    claim, claim_path = atomic_claim_authorization(preflight, state, output_root=str(root), claim_created_at=FIXED_TIME,
        operator_confirmation_reference=AUTHORITY, network_execution_confirmed=True)
    from server.services import phase_h_h1_tpex_composite as shared
    response_map = responses if responses is not None else fixture_responses()
    response_log: list[dict[str, Any]] = []

    def fake_get(endpoint: str, *, timeout_seconds: int = 60) -> dict[str, Any]:
        from server.services.phase_h_h1_tpex_composite import SOURCES
        source = next(item for item in SOURCES if item["endpoint"] == endpoint)
        if source["source_id"] == failure_source_id:
            raise TimeoutError("fixture source timeout")
        obs = response_map[source["source_id"]]
        return {"raw_bytes": obs.raw_bytes, "status": obs.status, "content_type": obs.content_type,
                "effective_url": obs.effective_url, "retrieved_at": obs.retrieved_at,
                "tls_policy": obs.tls_policy, "redirect_count": obs.redirect_count}

    transport = official_transport or fake_get
    with patch.object(shared, "official_get", transport):
        outcomes = dispatch_prepared(prepared, governed_output_root=str(root), mode="execute-approved", accepted_preflight=preflight)
    aggregation = aggregate_dispatch_outcomes(preflight, outcomes)
    final_claim, receipt, bundle = finalize_consumption_and_write_receipt(preflight, claim, claim_path, aggregation,
        output_root=str(root), finalized_at=FIXED_TIME, finalization_owner_id="umefo-v1-bbbbbbbbbbbbbbbbbbbb")
    receipt_path = next((root / "receipts").glob("*.json"))
    bundle_path = next((root / "bundles").glob("*.json"))
    from server.services import unified_mode_c
    with patch.object(unified_mode_c, "CONTROL_ROOT", package_root), patch.object(unified_mode_c, "validate_mode_a_request", return_value=f3):
        result_package = unified_mode_c.build_mode_c_result_package({"control_package_id": authorization["authorization_id"]},
            output_schema_version="unified_market_evidence_result.v3")
        audit = unified_mode_c.read_mode_c_audit(authorization["authorization_id"], "unified_market_evidence_result.v3")
        handoff = unified_mode_c.build_mode_c_ai_handoff(authorization["authorization_id"], "unified_market_evidence_result.v3")
    result = result_package["canonical_result"]
    result_schema = json.loads((ROOT / "schemas/unified_market_evidence_result.v3.schema.json").read_text(encoding="utf-8"))
    audit_schema = json.loads((ROOT / "schemas/unified_market_evidence_audit_package.v3.schema.json").read_text(encoding="utf-8"))
    assert not list(Draft202012Validator(result_schema).iter_errors(result))
    assert not list(Draft202012Validator(audit_schema).iter_errors(audit))
    return {"request": request, "f3": f3, "preview": preview, "plan": plan, "authorization": authorization,
            "binding": binding, "preflight": preflight, "outcomes": outcomes, "aggregation": aggregation,
            "claim": final_claim, "receipt": receipt, "bundle": bundle, "result": result, "audit": audit,
            "handoff": handoff, "handoff_markdown": handoff["ai_ready_markdown"], "root": root,
            "registry": runtime, "metadata": metadata, "execution_requests": preflight["bounded_execution_requests"]}

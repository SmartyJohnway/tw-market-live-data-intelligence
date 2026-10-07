from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Callable

from jsonschema import Draft202012Validator

from scripts.m8r_05b_02.authorization import build_execution_authorization
from scripts.m8r_05b_02.consumption_binding import build_consumption_binding
from scripts.m8r_05b_03.canonical import canonical_json
from scripts.m8r_05b_03.consumption_claim import atomic_claim_authorization
from scripts.m8r_05b_03.dispatch import RuntimeAdapterRegistration, RuntimeAdapterRegistry, dispatch_prepared, prepare_dispatch
from scripts.m8r_05b_03.evidence_aggregation import aggregate_dispatch_outcomes
from scripts.m8r_05b_03.preflight import build_orchestrator_preflight
from scripts.m8r_05b_03.receipt import finalize_consumption_and_write_receipt
from scripts.m8r_05b_03.registry import ExecutorMetadataRegistry
from scripts.m8r_05c.artifact_loader import load_projection_inputs
from scripts.m8r_filesystem_safety import safe_destination
from server.services.phase_j_b03_a2_6_composite_candidate import (
    ACCEPTANCE_AUTHORITY,
    CANDIDATE_EXECUTOR_ID,
    TARGET,
    HTTPObservation,
    acceptance_authority_hash,
    bind_acceptance_authority_to_plan,
    make_candidate_adapter,
)
from tests.helpers.phase_h_imp_7d_control_package import fixture_f3, fixture_plan, fixture_request


ROOT = Path(__file__).resolve().parents[2]
NOW = "2026-10-07T01:00:00Z"


def _write(root: Path, rel: str, value: dict) -> None:
    dest = safe_destination(str(root), rel, create_parent=True).path
    dest.write_text(canonical_json(value) + "\n", encoding="utf-8")


def fixture_responses(*, cmode_value: str = "Ｙ", cmode_rows: list[dict] | None = None,
                      disposition_rows: list[dict] | None = None,
                      attention_rows: list[dict] | None = None) -> dict[str, HTTPObservation]:
    rows = json.loads((ROOT / "tests/fixtures/phase_h_h1_adapters/source_rows.json").read_text(encoding="utf-8"))
    attention = attention_rows if attention_rows is not None else rows["tpex_attention"]
    disposition = disposition_rows if disposition_rows is not None else rows["tpex_disposition"]
    cmode = cmode_rows if cmode_rows is not None else [{
        "Date": "1151007", "SecuritiesCompanyCode": "6488", "CompanyName": "Fixture TPEx",
        "AlteredTrading": "", "PeriodicTrading": "", "ManagedStock": "",
        "MatchingFrequency": "", "SuspensionOfTrading": cmode_value,
        " FinancialAnnouncements": "",
    }]
    payloads = (attention, disposition, cmode)
    return {source["source_id"]: HTTPObservation(
        raw_bytes=json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"),
        status=200, content_type="application/json; charset=utf-8", effective_url=source["endpoint"],
        retrieved_at=NOW, tls_policy="fixture-no-network", redirect_count=0,
    ) for source, payload in zip(ACCEPTANCE_AUTHORITY["ordered_sources"], payloads, strict=True)}


def _metadata() -> dict:
    return {"schema_version": "m8r_05b_03_executor_registry_metadata.v1", "executors": [{
        "executor_id": CANDIDATE_EXECUTOR_ID, "capability_id": "trading_status_context", "market": "TPEX",
        "supported_security_types": ["equity"], "expected_evidence_contract": "trading_status_context_composite.v1",
        "network_required": True, "bounded_execution_supported": True, "timeout_seconds": 60,
        "maximum_result_items": 500, "output_policy": "contained_artifact_only",
    }]}


def run_integrated_fixture(root: Path, *, responses: dict[str, HTTPObservation] | None = None,
                           failure_source_id: str | None = None,
                           authority: dict | None = None,
                           mutate_component: Callable[[dict], None] | None = None,
                           use_live_transport: bool = False) -> dict:
    """Exercise real approval, dispatch, bundle, lineage, Result, Audit and handoff offline."""
    root.mkdir(parents=True, exist_ok=True)
    control_root = root
    request = fixture_request(request_id="a26-offline-6488")
    f3 = fixture_f3(request)
    base_plan = fixture_plan(request, f3, operation_id="umeop-op-v1-aaaaaaaaaaaaaaaaaaaa")
    selected_authority = deepcopy(authority if authority is not None else ACCEPTANCE_AUTHORITY)
    plan = bind_acceptance_authority_to_plan(base_plan, selected_authority)
    plan_errors = list(__import__("jsonschema").Draft7Validator(
        json.loads((ROOT / "schemas/unified_market_evidence_orchestration_plan.v1.schema.json").read_text(encoding="utf-8"))
    ).iter_errors(plan))
    if plan_errors:
        raise AssertionError(f"candidate plan invalid: {plan_errors[0].message}")

    decision = {
        "decision": "approved", "decision_reason": "Owner-authorized A2.6 bounded integrated acceptance",
        "owner_identity_reference": "A2.6-stage-a-owner", "owner_review_reference": ACCEPTANCE_AUTHORITY["authority_reference"],
        "reviewed_at": NOW, "issued_at": NOW, "expires_at": "2026-10-08T01:00:00Z",
        "single_use": True, "replay_policy": "deny_replay", "maximum_use_count": 1,
        "approval_scope_mode": "selected_operations", "approved_operation_ids": [plan["operations"][0]["operation_id"]],
        "approved_batch_group_ids": [], "approved_batch_membership": {},
    }
    authorization = build_execution_authorization(plan, decision)
    binding = build_consumption_binding(authorization)
    root = control_root / authorization["authorization_id"]
    root.mkdir(parents=True, exist_ok=True)
    state = {"authorization_id": authorization["authorization_id"], "authorization_hash": authorization["authorization_hash"],
             "consumption_binding_id": binding["consumption_binding_id"], "consumption_binding_hash": binding["consumption_binding_hash"],
             "registry_contract_version": "m8r_05b_03.v1", "state": "unused"}
    response_map = responses or fixture_responses()
    response_log: list[dict] = []

    def provider(source):
        if source["source_id"] == failure_source_id:
            raise TimeoutError("fixture source timeout")
        return response_map[source["source_id"]]

    adapter = make_candidate_adapter(authority=selected_authority, bound_plan_hash=plan["plan_hash"],
                                     response_provider=None if use_live_transport else provider,
                                     response_log=response_log)
    metadata = _metadata()
    registration = RuntimeAdapterRegistration(
        CANDIDATE_EXECUTOR_ID, "trading_status_context", "TPEX", ("equity",),
        "trading_status_context_composite.v1", True, True, 60, 500,
        "contained_artifact_only", adapter, fake_adapter=False,
    )
    runtime = RuntimeAdapterRegistry([registration])
    supplied_state = deepcopy(state)
    preflight = build_orchestrator_preflight(
        plan, authorization, binding, supplied_consumption_state=supplied_state,
        evaluation_timestamp=NOW, executor_registry_metadata=metadata, output_root=str(root),
    )
    prepared = prepare_dispatch(preflight, ExecutorMetadataRegistry.from_json(metadata), runtime, mode="execute-approved")
    for rel, obj in (("control/request.json", request), ("control/f3.json", f3), ("control/plan.json", plan),
                     ("control/authorization.json", authorization), ("control/consumption_binding.json", binding),
                     ("control/preflight.json", preflight), ("control/unused_consumption_state.json", state)):
        _write(root, rel, obj)
    control_files = {
        "request": root / "control/request.json",
        "plan": root / "control/plan.json",
        "authorization": root / "control/authorization.json",
        "consumption_binding": root / "control/consumption_binding.json",
        "preflight": root / "control/preflight.json",
        "unused_consumption_state": root / "control/unused_consumption_state.json",
    }
    control_hashes = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in control_files.items()}
    _write(root, "control/manifest.json", {
        "schema_version": "m8r_06_03_control_package.v1",
        "authorization_id": authorization["authorization_id"],
        "authorization_hash": authorization["authorization_hash"],
        "plan_id": plan["plan_id"], "plan_hash": plan["plan_hash"],
        "preflight_id": preflight["preflight_id"], "preflight_hash": preflight["preflight_hash"],
        "artifact_hashes": control_hashes,
    })
    claim, claim_path = atomic_claim_authorization(
        preflight, supplied_state, output_root=str(root), claim_created_at=NOW,
        operator_confirmation_reference=ACCEPTANCE_AUTHORITY["authority_reference"],
        network_execution_confirmed=True,
    )
    outcomes = dispatch_prepared(prepared, governed_output_root=str(root), mode="execute-approved", accepted_preflight=preflight)
    aggregation = aggregate_dispatch_outcomes(preflight, outcomes)
    final_claim, receipt, bundle = finalize_consumption_and_write_receipt(
        preflight, claim, claim_path, aggregation, output_root=str(root), finalized_at=NOW,
        finalization_owner_id="umefo-v1-aaaaaaaaaaaaaaaaaaaa",
    )
    if mutate_component is not None:
        component_path = next(item["artifact_reference"]["relative_path"] for item in json.loads(
            (root / next(a["relative_path"] for a in outcomes[0]["evidence_artifacts"] if a["artifact_role"] == "primary_evidence")).read_text(encoding="utf-8")
        )["components"] if item["source_id"] == "H1-TPEX-ATTENTION-OPENAPI")
        composite_path = next(a["relative_path"] for a in outcomes[0]["evidence_artifacts"] if a["artifact_role"] == "primary_evidence")
        composite = json.loads((root / composite_path).read_text(encoding="utf-8"))
        mutate_component(composite["components"][0])
        _write(root, composite_path, composite)

    receipt_path = next(path for path in (root / "receipts").glob("*.json"))
    bundle_path = next(path for path in (root / "bundles").glob("*.json"))
    # Exercise the normal server-owned read/materialize/audit/export path.  The
    # fixture F3 is injected only at the existing validation seam; all persisted
    # control, claim, receipt, bundle, evidence and lineage checks remain real.
    from unittest.mock import patch
    from server.services import unified_mode_c

    with patch.object(unified_mode_c, "CONTROL_ROOT", control_root), patch.object(
        unified_mode_c, "validate_mode_a_request", return_value=f3,
    ):
        mode_c_result = unified_mode_c.build_mode_c_result_package(
            {"control_package_id": authorization["authorization_id"]},
            output_schema_version="unified_market_evidence_result.v3",
        )
        audit = unified_mode_c.read_mode_c_audit(
            authorization["authorization_id"], "unified_market_evidence_result.v3",
        )
        handoff = unified_mode_c.build_mode_c_ai_handoff(
            authorization["authorization_id"], "unified_market_evidence_result.v3",
        )
    result = mode_c_result["canonical_result"]
    inputs = load_projection_inputs(
        request_path=str(root / "control/request.json"), f3_validation_path=str(root / "mode_c/f3_validation.json"),
        plan_path=str(root / "control/plan.json"), authorization_path=str(root / "control/authorization.json"),
        consumption_binding_path=str(root / "control/consumption_binding.json"), claim_path=str(root / claim_path),
        receipt_path=str(receipt_path), bundle_path=str(bundle_path), artifact_root=str(root),
        calculated_at=NOW, calculated_at_source="a26_fixture_acceptance",
    )
    handoff_markdown = handoff["ai_ready_markdown"]
    result_schema = json.loads((ROOT / "schemas/unified_market_evidence_result.v3.schema.json").read_text(encoding="utf-8"))
    audit_schema = json.loads((ROOT / "schemas/unified_market_evidence_audit_package.v3.schema.json").read_text(encoding="utf-8"))
    assert not list(Draft202012Validator(result_schema).iter_errors(result))
    assert not list(Draft202012Validator(audit_schema).iter_errors(audit))
    return {
        "request": request, "f3": f3, "plan": plan, "authority_hash": acceptance_authority_hash(selected_authority),
        "authorization": authorization, "binding": binding, "preflight": preflight, "claim": final_claim,
        "outcomes": outcomes, "aggregation": aggregation, "receipt": receipt, "bundle": bundle,
        "inputs": inputs, "result": result, "audit": audit, "handoff": handoff,
        "mode_c_result": mode_c_result, "mode_c_handoff": handoff,
        "handoff_markdown": handoff_markdown,
        "response_log": response_log, "root": root,
    }

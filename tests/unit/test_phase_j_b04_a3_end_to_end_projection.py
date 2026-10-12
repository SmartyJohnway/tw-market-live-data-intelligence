"""Self-contained network-free H3 -> H2 -> H4 -> Result/Audit/handoff test."""
from __future__ import annotations

import json
import shutil
from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
import pytest

from scripts.m8r_05b_01.planner import build_plan
from scripts.m8r_05b_01.planner import plan_identity_scope
from scripts.m8r_05b_01.canonical import plan_hash_and_id
from scripts.m8r_05b_02.authorization import build_execution_authorization
from scripts.m8r_05b_02.consumption_binding import build_consumption_binding
from scripts.m8r_05b_03.preflight import build_orchestrator_preflight
from scripts.m8r_05b_03.orchestrator import execute_controlled_plan
from scripts.m8r_05b_03.errors import OrchestrationError
from scripts.m8r_05b_03.consumption_claim import claim_relative_path
from scripts.m8r_05b_03.dispatch import RuntimeAdapterRegistry
from scripts.m8r_05b_03.receipt import bundle_relative_path, receipt_relative_path
from scripts.m8r_05c.artifact_loader import load_projection_inputs
from scripts.m8r_05c.audit_package_builder import build_audit_package
from scripts.m8r_05c.citation_builder import build_citation_index
from scripts.m8r_05c.lineage_resolver import build_lineage_map
from scripts.m8r_05c.markdown_renderer import render_result_markdown
from scripts.m8r_05c.result_builder import build_result
from scripts.m8r_06_02_mode_b1_preview import build_planning_bindings, load_planning_authorities
from scripts.m8r_06_03_production_adapter import (
    build_production_runtime_adapter_registry,
    load_production_executor_metadata,
)
from server.services.phase_h_h3_twse_stock_day_adapter import (
    SOURCE_CONTRACT_ID,
    SOURCE_FAMILY,
    TWSEStockDayResult,
)
from tests.unit.test_phase_h_h3_activation_candidate_preview import (
    OfflineSecurityMaster,
    _production_preview,
    _request,
)
import scripts.m8r_06_03_production_adapter as production
import server.services.phase_h_h2_twse_exright_executor as h2_executor

ROOT = Path(__file__).resolve().parents[2]
STAMP = "2026-10-08T00:00:00Z"


class FixedDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        return datetime(2026, 10, 8, 0, 0, tzinfo=timezone.utc).astimezone(tz or timezone.utc)


def _decision() -> dict:
    return {
        "decision": "approved",
        "owner_identity_reference": "A3_TEST_ONLY_OVERLAY",
        "owner_review_reference": "A3_NETWORK_FREE_INTEGRATION_FIXTURE",
        "decision_reason": "test-only fixture overlay; not canonical route authority",
        "reviewed_at": STAMP,
        "issued_at": STAMP,
        "expires_at": "2026-10-08T01:00:00Z",
        "approval_scope_mode": "whole_plan_executable_scope",
        "approved_operation_ids": [],
        "approved_batch_group_ids": [],
        "approved_batch_membership": {},
        "single_use": True,
        "replay_policy": "deny_replay",
        "maximum_use_count": 1,
    }


def _set_test_h2_overlay(validation: dict, authorities: dict) -> None:
    cap = next(item for item in authorities["capability_catalog"]["data_need_capabilities"] if item["capability_id"] == "corporate_action_context")
    cap["support_status"] = "runtime_executable"
    cap["runtime_executable"] = True
    cap["phase_h_activation_state"] = "selected_route_active"
    route = next(item for item in authorities["routing_matrix"]["routes"] if item["capability_id"] == "corporate_action_context")
    route.update({
        "runtime_executable": True,
        "selected_executor_id": "phase_h_h2_twse_exright_pre_executor",
        "routing_status": "resolved",
        "network_required": True,
    })
    if not any(item.get("surface_id") == "phase_h_h2_twse_exright_pre_executor" for item in authorities["executor_disposition"]["surfaces"]):
        inventory = next(item for item in authorities["executor_disposition"]["surfaces"] if item["surface_id"] == "phase_h_h3_twse_recent_performance_executor")
        h2_inventory = deepcopy(inventory)
        h2_inventory.update({
            "surface_id": "phase_h_h2_twse_exright_pre_executor",
            "surface_type": "controlled_phase_h_h2_executor",
            "current_status": "test-only A3 overlay; the canonical route is independently governed",
            "reusable_for_05b": True,
            "disposition": "adapter_required",
        })
        authorities["executor_disposition"]["surfaces"].append(h2_inventory)
    f3_cap = next(item for item in validation["capability_results"] if item["capability_id"] == "corporate_action_context")
    f3_cap["status"] = "runtime_executable"


@pytest.mark.parametrize("h2_failure", [None, "source_failed", "binding_failed"])
def test_network_free_production_chain_projects_verified_h4_to_result_audit_and_handoff(tmp_path, monkeypatch, h2_failure):
    request = _request("TWSE", "1423") | {"execution_mode": "execute"}
    request["targets"].append({"input": "TWSE:2330", "market_hint": "TWSE"})
    request["data_needs"] = [
        {"type": "corporate_action_context", "priority": "required"},
        {"type": "recent_performance", "priority": "required", "parameters": {"lookback_trading_days": 1}},
    ]
    preview = _production_preview(request, "TWSE", "1423", additional_codes=("2330",))
    validation = deepcopy(preview["validation"])
    authorities = load_planning_authorities(request["schema_version"])
    _set_test_h2_overlay(validation, authorities)
    security_master = OfflineSecurityMaster("TWSE", "1423", ("2330",))
    bindings = build_planning_bindings(
        request, validation, security_master,
        capability_catalog=authorities["capability_catalog"],
        routing_matrix=authorities["routing_matrix"],
        handoff_contract=authorities["handoff_contract"],
    )
    plan = build_plan(
        validation,
        capability_catalog=authorities["capability_catalog"],
        routing_matrix=authorities["routing_matrix"],
        handoff_contract=authorities["handoff_contract"],
        executor_disposition=authorities["executor_disposition"],
        input_bindings=bindings,
        planning_timestamp=STAMP,
    )
    h2_plan = next(item for item in plan["operations"] if item["capability_id"] == "corporate_action_context")
    h3_plan = next(item for item in plan["operations"] if item["capability_id"] == "recent_performance")
    assert h2_plan["dependency_operation_ids"] == [h3_plan["operation_id"]]

    # Exercise selected_operations through real authorization and governed preflight.
    selected_h2_only = deepcopy(plan)
    scope_h2 = next(item for item in selected_h2_only["operations"] if item["capability_id"] == "corporate_action_context")
    scope_h3 = next(item for item in selected_h2_only["operations"] if item["capability_id"] == "recent_performance" and item["canonical_target_ids"] == scope_h2["canonical_target_ids"])

    def selected_scope(selected_plan, operation_ids, name, *, expect_rejection=False):
        selected_decision = _decision() | {
            "approval_scope_mode": "selected_operations",
            "approved_operation_ids": list(operation_ids),
        }
        selected_authorization = build_execution_authorization(selected_plan, selected_decision)
        selected_binding = build_consumption_binding(selected_authorization)
        selected_root = tmp_path / f"selected-{name}"
        selected_root.mkdir()
        (selected_root / "claims").mkdir()
        selected_state = {
            "authorization_id": selected_authorization["authorization_id"],
            "authorization_hash": selected_authorization["authorization_hash"],
            "consumption_binding_id": selected_binding["consumption_binding_id"],
            "consumption_binding_hash": selected_binding["consumption_binding_hash"],
            "registry_contract_version": "m8r_05b_03.v1", "state": "unused",
        }
        if expect_rejection:
            with pytest.raises(OrchestrationError, match="dependency_operation_not_approved"):
                build_orchestrator_preflight(
                    selected_plan, selected_authorization, selected_binding,
                    supplied_consumption_state=selected_state, evaluation_timestamp=STAMP,
                    executor_registry_metadata=load_production_executor_metadata(), output_root=str(selected_root),
                )
            assert not list((selected_root / "claims").iterdir())
            assert selected_state["state"] == "unused"
            return None
        result = build_orchestrator_preflight(
            selected_plan, selected_authorization, selected_binding,
            supplied_consumption_state=selected_state, evaluation_timestamp=STAMP,
            executor_registry_metadata=load_production_executor_metadata(), output_root=str(selected_root),
        )
        return result

    assert selected_scope(selected_h2_only, [scope_h2["operation_id"]], "h2-only", expect_rejection=True) is None
    h3_only_preflight = selected_scope(selected_h2_only, [scope_h3["operation_id"]], "h3-only")
    assert h3_only_preflight["approved_operation_order"] == [scope_h3["operation_id"]]
    assert scope_h2["operation_id"] not in h3_only_preflight["approved_operation_order"]
    unrelated_plan = deepcopy(plan)
    x_operation = deepcopy(h3_plan)
    x_operation["operation_id"] = "umeop-op-v1-ffffffffffffffffffff"
    x_operation["dependency_operation_ids"] = []
    unrelated_plan["operations"].append(x_operation)
    x_batch = next(item for item in unrelated_plan["batch_groups"]
                   if item["batch_group_id"] == x_operation["batch_group_id"])
    x_batch["operation_ids"] = sorted([*x_batch["operation_ids"], x_operation["operation_id"]])
    unrelated_plan["plan_hash"], unrelated_plan["plan_id"] = plan_hash_and_id(plan_identity_scope(unrelated_plan))
    x_preflight = selected_scope(unrelated_plan, [x_operation["operation_id"]], "unrelated-x")
    assert x_preflight["approved_operation_order"] == [x_operation["operation_id"]]
    pair_preflight = selected_scope(selected_h2_only, [scope_h2["operation_id"], scope_h3["operation_id"]], "h2-h3")
    assert set(pair_preflight["approved_operation_order"]) == {scope_h2["operation_id"], scope_h3["operation_id"]}

    invalid_plan = deepcopy(plan)
    invalid_h2 = next(item for item in invalid_plan["operations"] if item["capability_id"] == "corporate_action_context")
    invalid_h2["dependency_operation_ids"] = [invalid_h2["operation_id"]]
    invalid_plan["plan_hash"], invalid_plan["plan_id"] = plan_hash_and_id(plan_identity_scope(invalid_plan))
    invalid_authorization = build_execution_authorization(invalid_plan, _decision())
    invalid_binding = build_consumption_binding(invalid_authorization)
    invalid_root = tmp_path / "invalid-dependency-plan"
    invalid_root.mkdir()
    (invalid_root / "claims").mkdir()
    invalid_state = {
        "authorization_id": invalid_authorization["authorization_id"],
        "authorization_hash": invalid_authorization["authorization_hash"],
        "consumption_binding_id": invalid_binding["consumption_binding_id"],
        "consumption_binding_hash": invalid_binding["consumption_binding_hash"],
        "registry_contract_version": "m8r_05b_03.v1", "state": "unused",
    }
    blocked_calls: list[str] = []
    adapter_calls: list[str] = []
    monkeypatch.setattr(production, "fetch_twse_stock_day_month", lambda **kwargs: blocked_calls.append("H3"))
    monkeypatch.setattr(h2_executor, "official_get_once", lambda **kwargs: blocked_calls.append("H2"))
    production_registry = build_production_runtime_adapter_registry()
    guarded_registry = RuntimeAdapterRegistry([
        replace(registration, adapter=lambda request, context: adapter_calls.append(request["operation_id"]))
        for registration in production_registry._by_route.values()
    ])
    with pytest.raises(OrchestrationError, match="dependency_self_reference"):
        execute_controlled_plan(
            invalid_plan, invalid_authorization, invalid_binding,
            supplied_consumption_state=invalid_state, accepted_preflight={},
            evaluation_timestamp=STAMP, claim_created_at=STAMP, finalized_at=STAMP,
            executor_registry_metadata=load_production_executor_metadata(),
            runtime_adapter_registry=guarded_registry,
            output_root=str(invalid_root), mode="execute-approved", confirm_execution=True,
            operator_confirmation_reference="R1_INVALID_GRAPH", confirm_network_execution=True,
        )
    assert not (invalid_root / claim_relative_path(invalid_authorization["authorization_id"])).exists()
    assert invalid_state["state"] == "unused"
    assert adapter_calls == []
    assert blocked_calls == []

    authorization = build_execution_authorization(plan, _decision())
    consumption_binding = build_consumption_binding(authorization)
    output_root = tmp_path / authorization["authorization_id"]
    output_root.mkdir()
    (output_root / "claims").mkdir()
    metadata = load_production_executor_metadata()
    preflight = build_orchestrator_preflight(
        plan, authorization, consumption_binding,
        supplied_consumption_state={
            "authorization_id": authorization["authorization_id"],
            "authorization_hash": authorization["authorization_hash"],
            "consumption_binding_id": consumption_binding["consumption_binding_id"],
            "consumption_binding_hash": consumption_binding["consumption_binding_hash"],
            "registry_contract_version": "m8r_05b_03.v1",
            "state": "unused",
        },
        evaluation_timestamp=STAMP,
        executor_registry_metadata=metadata,
        output_root=str(output_root),
    )
    timestamps = []

    def fake_h3_month(**kwargs):
        timestamps.append(kwargs["requested_month"])
        target = kwargs["target"]
        code = target["security_code"]
        days = (("2026-10-06", 100.0), ("2026-10-07", 101.0)) if code == "1423" else (("2026-10-05", 90.0), ("2026-10-07", 91.0))
        rows = []
        for day, close in days:
            rows.append({
                "canonical_target_id": target["canonical_target_id"], "market": "TWSE", "security_code": code,
                "trade_date": day, "close": close, "volume": 1000,
                "source_family": SOURCE_FAMILY, "source_contract_id": SOURCE_CONTRACT_ID,
                "retrieved_at": kwargs["retrieved_at"], "citation_ids": [f"fixture-h3:{day}"],
            })
        return TWSEStockDayResult(
            status="available", requested_month=kwargs["requested_month"],
            requested_url=f"https://www.twse.com.tw/exchangeReport/STOCK_DAY?month={kwargs['requested_month']}",
            effective_url=f"https://www.twse.com.tw/exchangeReport/STOCK_DAY?month={kwargs['requested_month']}",
            http_status=200, content_type="text/html; charset=utf-8", retrieved_at=kwargs["retrieved_at"],
            response_byte_count=123, response_sha256="a" * 64, observations=tuple(rows),
        )

    h2_calls = []

    def fake_h2_get(**kwargs):
        h2_calls.append(kwargs)
        rows = [{
            "Code": code, "Date": "2026-10-07", "Exdividend": "除息",
            "StockDividendRatio": "0", "SubscriptionRatio": "0",
            "SubscriptionPricePerShare": "尚未公告", "CashDividend": "1",
        } for code in ("1423", "2330")]
        if h2_failure == "source_failed":
            return {"raw_bytes": b"{}", "status": 503, "content_type": "application/json",
                    "effective_url": h2_executor.ENDPOINT, "retrieved_at": STAMP}
        if h2_failure == "binding_failed":
            rows = [rows[0], rows[0], rows[1], rows[1]]
        return {
            "raw_bytes": json.dumps(rows, ensure_ascii=False).encode("utf-8"),
            "status": 200, "content_type": "application/json", "effective_url": h2_executor.ENDPOINT,
            "retrieved_at": STAMP,
        }

    monkeypatch.setattr(production, "datetime", FixedDateTime)
    monkeypatch.setattr(production, "fetch_twse_stock_day_month", fake_h3_month)
    monkeypatch.setattr(h2_executor, "official_get_once", fake_h2_get)
    supplied_state = {
        "authorization_id": authorization["authorization_id"],
        "authorization_hash": authorization["authorization_hash"],
        "consumption_binding_id": consumption_binding["consumption_binding_id"],
        "consumption_binding_hash": consumption_binding["consumption_binding_hash"],
        "registry_contract_version": "m8r_05b_03.v1",
        "state": "unused",
    }
    execution = execute_controlled_plan(
        plan, authorization, consumption_binding,
        supplied_consumption_state=supplied_state, accepted_preflight=preflight,
        evaluation_timestamp=STAMP, claim_created_at=STAMP, finalized_at=STAMP,
        executor_registry_metadata=metadata,
        runtime_adapter_registry=build_production_runtime_adapter_registry(),
        output_root=str(output_root), mode="execute-approved", confirm_execution=True,
        operator_confirmation_reference="A3_NETWORK_FREE_TEST_FIXTURE", confirm_network_execution=True,
    )
    assert len(h2_calls) == 2
    assert len(timestamps) == 2
    assert len(execution["dispatch_outcomes"]) == 4
    h2_outcomes = [item for item in execution["dispatch_outcomes"] if item["capability_id"] == "corporate_action_context"]
    h3_outcomes = [item for item in execution["dispatch_outcomes"] if item["capability_id"] == "recent_performance"]
    assert all(item["status"] == "succeeded" for item in h3_outcomes)
    if h2_failure is None:
        assert all(item["status"] == "succeeded" for item in h2_outcomes)
    else:
        assert all(item["status"] == "failed" and item["error_code"] == h2_failure for item in h2_outcomes)

    control = output_root / "control"
    control.mkdir()
    f3_path = control / "f3-validation.json"
    f3_path.write_text(json.dumps(validation, ensure_ascii=False), encoding="utf-8")
    for filename, value in (("request.json", request), ("plan.json", plan), ("authorization.json", authorization), ("consumption_binding.json", consumption_binding)):
        (control / filename).write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    inputs = load_projection_inputs(
        request_path=str(control / "request.json"), f3_validation_path=str(f3_path),
        plan_path=str(control / "plan.json"), authorization_path=str(control / "authorization.json"),
        consumption_binding_path=str(control / "consumption_binding.json"),
        claim_path=str(output_root / execution["claim_relative_path"]),
        receipt_path=str(output_root / receipt_relative_path(authorization["authorization_id"])),
        bundle_path=str(output_root / bundle_relative_path(authorization["authorization_id"])),
        artifact_root=str(output_root), calculated_at=STAMP,
    )
    h4_entries = [item for item in inputs.bundle["artifact_inventory"] if item["schema_version"] == "discontinuity_safety_evidence.v1"]
    assert len(h4_entries) == 2
    h2_entries = [item for item in inputs.bundle["artifact_inventory"] if item["schema_version"] == "corporate_action_context_evidence.v1"]
    h3_entries = [item for item in inputs.bundle["artifact_inventory"] if item["schema_version"] == "recent_performance_evidence.v1"]
    assert len(h2_entries) == len(h3_entries) == 2
    h4_by_target = {inputs.evidence_artifacts[item["relative_path"]]["target"]["canonical_target_id"]: inputs.evidence_artifacts[item["relative_path"]] for item in h4_entries}
    h2_by_target = {inputs.evidence_artifacts[item["relative_path"]]["target"]["canonical_target_id"]: inputs.evidence_artifacts[item["relative_path"]] for item in h2_entries}
    h3_by_target = {inputs.evidence_artifacts[item["relative_path"]]["target"]["canonical_target_id"]: inputs.evidence_artifacts[item["relative_path"]] for item in h3_entries}
    assert set(h4_by_target) == set(h2_by_target) == set(h3_by_target) == {"TWSE:1423", "TWSE:2330"}
    assert [item["relative_path"] for item in h4_entries] == sorted(item["relative_path"] for item in h4_entries)
    for target_id in ("TWSE:1423", "TWSE:2330"):
        h2, h3, h4 = h2_by_target[target_id], h3_by_target[target_id], h4_by_target[target_id]
        assert h2["coverage"]["requested_window"] == {
            "start": h3["baselines"][0]["start_observation_date"],
            "end": h3["baselines"][0]["end_observation_date"],
        }
        assert h2["coverage"]["declared_scope_complete"] is False
        assert h4["state"] == "coverage_incomplete"
        assert h4["ordinary_return_interpretation"] == "blocked"
        if h2_failure:
            assert h2["status"] == h2_failure
        h4_refs = h4["input_evidence_references"]
        assert len(h4_refs) == 2
        assert all(inputs.evidence_artifacts[ref.split("#", 1)[0]]["target"]["canonical_target_id"] == target_id for ref in h4_refs)
        expected_refs = {
            f"{entry['relative_path']}#{entry['sha256']}"
            for entry in (h2_entries + h3_entries)
            if inputs.evidence_artifacts[entry["relative_path"]]["target"]["canonical_target_id"] == target_id
        }
        assert set(h4_refs) == expected_refs
    assert h2_by_target["TWSE:1423"]["coverage"]["requested_window"] != h2_by_target["TWSE:2330"]["coverage"]["requested_window"]

    lineage = build_lineage_map(inputs)
    citations = build_citation_index(lineage, inputs.bundle, "unified_market_evidence_result.v3")
    result = build_result(inputs, output_schema_version="unified_market_evidence_result.v3")
    audit = build_audit_package(
        result, inputs, citations, "ai_context/unified_market_evidence_result.v3.json",
        output_schema_version="unified_market_evidence_audit_package.v3",
    )
    result_by_target = {item["resolution"]["canonical_target_id"]: item for item in result["targets"]}
    for target_id in ("TWSE:1423", "TWSE:2330"):
        evidence = result_by_target[target_id]["evidence"]
        assert evidence["corporate_action_context"] == h2_by_target[target_id]
        assert evidence["recent_performance"] == h3_by_target[target_id]
        assert evidence["discontinuity_safety"] == h4_by_target[target_id]
    audit_h4 = audit["phase_h_governance"]["h4_derivations"]
    assert [item["canonical_target_id"] for item in audit_h4] == ["TWSE:1423", "TWSE:2330"]
    for item in audit_h4:
        target_id = item["canonical_target_id"]
        assert all(inputs.evidence_artifacts[ref.split("#", 1)[0]]["target"]["canonical_target_id"] == target_id for ref in item["input_evidence_references"])

    partial_root = tmp_path / "partial-outcomes"
    partial_root.mkdir()
    for artifact in [*h2_entries, *h3_entries]:
        source = output_root / artifact["relative_path"]
        destination = partial_root / artifact["relative_path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    partial_outcomes = deepcopy(execution["dispatch_outcomes"])
    h3_b_plan = next(item for item in plan["operations"] if item["capability_id"] == "recent_performance" and item["canonical_target_ids"] == ["TWSE:2330"])
    h3_b = next(item for item in partial_outcomes if item["operation_id"] == h3_b_plan["operation_id"])
    h3_b["status"] = "failed"
    partial_h4 = h2_executor.derive_h4_for_completed_plan(plan, partial_outcomes, output_root=str(partial_root))
    partial_targets = {json.loads((partial_root / item["relative_path"]).read_text())["target"]["canonical_target_id"] for item in partial_h4}
    assert partial_targets == {"TWSE:1423"}
    h2_b_plan = next(item for item in plan["operations"] if item["capability_id"] == "corporate_action_context" and item["canonical_target_ids"] == ["TWSE:2330"])
    assert not (partial_root / f"evidence/phase_h/h4/{h2_b_plan['operation_id']}.json").exists()
    partial_projection_inputs = deepcopy(inputs)
    h4_b_path = next(entry["relative_path"] for entry in h4_entries if inputs.evidence_artifacts[entry["relative_path"]]["target"]["canonical_target_id"] == "TWSE:2330")
    partial_projection_inputs.bundle["artifact_inventory"] = [
        entry for entry in partial_projection_inputs.bundle["artifact_inventory"] if entry["relative_path"] != h4_b_path
    ]
    partial_projection_inputs.evidence_artifacts.pop(h4_b_path)
    partial_result = build_result(partial_projection_inputs, output_schema_version="unified_market_evidence_result.v3")
    partial_by_target = {item["resolution"]["canonical_target_id"]: item for item in partial_result["targets"]}
    assert partial_by_target["TWSE:1423"]["evidence"]["discontinuity_safety"] is not None
    assert partial_by_target["TWSE:2330"]["evidence"].get("discontinuity_safety") is None
    markdown = render_result_markdown(result)
    assert "coverage_incomplete" in markdown
    assert "blocked" in markdown
    assert "coverage" in markdown.lower() or "覆蓋" in markdown
    if h2_failure:
        assert "coverage_incomplete" in markdown and "blocked" in markdown.lower()

"""Owner-authorized I3 A4 activation proof using only injected source bytes."""
import hashlib
import json
import socket
import copy
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.phase_i_i3_execution_pipeline import prepare_i3_authorized_execution
from scripts.m8r_05b_03.preflight import build_orchestrator_preflight
from scripts.m8r_05b_03.orchestrator import execute_controlled_plan
from scripts.m8r_06_03_production_adapter import build_production_runtime_adapter_registry, load_production_executor_metadata
from server.services.phase_i_i3_production_transport import Acquisition
from server.unified_mcp.tool_contracts import build_tool_specs

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/fixtures/phase_i_i3_a0"
EXECUTOR = "phase_i_i3_cash_institutional_flow_context_executor"


@pytest.fixture(autouse=True)
def deny_market_sockets(monkeypatch):
    def denied(*_args, **_kwargs):
        raise AssertionError("i3_a4_market_socket_forbidden")
    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket, "create_connection", denied)


class _SecurityMaster:
    pointer = {"index_path": "sealed/index.json", "manifest_path": "sealed/manifest.json",
               "compact_index_sha256": "a" * 64, "compact_manifest_sha256": "b" * 64}


def _source(market: str) -> bytes:
    if market == "TWSE":
        value = json.loads((FIXTURES / "twse_synthetic.json").read_text(encoding="utf-8"))
    else:
        value = json.loads((FIXTURES / "dealer_sell_adjudication_scenarios.json").read_text(encoding="utf-8"))["unique_candidate_a"]
        # Synthetic official-body fixture projects to the independently
        # eligible fixture target TPEX:6488 for this activation-path test.
        for row in value:
            if row.get("SecuritiesCompanyCode") == "5347":
                row["SecuritiesCompanyCode"] = "6488"
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _preview(targets, *, request_id="i3-active-preview"):
    from scripts.m8r_06_02_mode_b1_preview import build_mode_b1_preview_package, load_planning_authorities
    from scripts.m8r_05a_f3.request_intake import validate_unified_market_evidence_request
    from scripts.m8r_05a_f3.security_master_loader import load_f3_verified_security_master
    from server.services.unified_contract_versions import REQUEST_SCHEMA_PATHS
    request = {"schema_version": "unified_market_evidence_request.v3", "request_id": request_id,
               "execution_mode": "preview", "targets": targets,
               "data_needs": [{"type": "cash_institutional_flow_context", "priority": "required"}]}
    fixture_root = ROOT / "tests/fixtures/m8r_05a_f3"
    test_master = load_f3_verified_security_master(fixture_root / "verified_security_master_snapshot.json",
        fixture_root / "verified_security_master_snapshot_manifest.json", allow_fixture_snapshot=True)
    # Build a process-local authorized identity fixture.  No installed
    # Security Master bytes or repository state are changed.
    # The committed F3 fixture includes TWSE:2330 and TPEX:6488.  Add two
    # process-local TWSE listing identities represented by the reviewed
    # synthetic T86 fixture; these are test-only Security Master records.
    base = copy.deepcopy(test_master.lookup["by_canonical"]["TWSE:2330"])
    for code in ("1101", "1102"):
        synthetic = copy.deepcopy(base)
        synthetic["canonical_target_id"] = f"TWSE:{code}"
        synthetic["listing_id"] = f"TWSE:{code}"
        synthetic["identity"]["security_code"] = code
        synthetic["identity"]["isin"] = f"TW{code}".ljust(12, "0")
        synthetic["instrument_id"] = synthetic["identity"]["isin"]
        test_master.lookup["by_canonical"][f"TWSE:{code}"] = synthetic
        test_master.lookup["by_code"].setdefault(("TWSE", code), []).append(synthetic)
    for canonical in ("TWSE:2330", "TWSE:1101", "TWSE:1102", "TPEX:6488"):
        record = test_master.lookup["by_canonical"][canonical]
        record["execution_eligibility"] = {"status": "allowed", "reason_codes": []}
        record["observation"] = {"status": "governed_test_identity"}
    class ActiveTestSecurityMaster:
        lookup = test_master.lookup
        pointer = {"index_path": "sealed/index.json", "manifest_path": "sealed/manifest.json",
                   "compact_index_sha256": "a" * 64, "compact_manifest_sha256": "b" * 64}
    authorities = load_planning_authorities(request["schema_version"])
    validation = validate_unified_market_evidence_request(request, security_master=ActiveTestSecurityMaster(),
        capability_catalog=authorities["capability_catalog"],
        request_schema=json.loads(REQUEST_SCHEMA_PATHS[request["schema_version"]].read_text(encoding="utf-8")),
        allow_fixture_snapshot=False)
    package = build_mode_b1_preview_package(request, validation, ActiveTestSecurityMaster(),
        planning_timestamp="2026-10-01T10:00:00Z", authorities=load_planning_authorities(request["schema_version"]))
    assert package["preview"]["status"] == "ready_for_confirmation"
    assert package["orchestration_plan"]["plan_status"] == "plan_ready"
    package["_request"] = request
    package["_validation"] = validation
    return request, validation, package


def _prepared(package, *, evaluation="2026-10-01T19:00:00+08:00"):
    from scripts.twse_trading_calendar import build_twse_trading_calendar_from_holiday_schedule
    operations = package["orchestration_plan"]["operations"]
    stamp = "2026-10-01T11:00:00Z"
    decision = {"decision": "approved", "decision_reason": "offline activation acceptance only",
        "owner_identity_reference": "offline-owner", "owner_review_reference": "I3-A4-offline-test",
        "reviewed_at": stamp, "issued_at": stamp, "expires_at": "2026-10-01T11:15:00Z",
        "single_use": True, "replay_policy": "deny_replay", "maximum_use_count": 1,
        "approval_scope_mode": "selected_operations", "approved_operation_ids": sorted(x["operation_id"] for x in operations),
        "approved_batch_group_ids": [], "approved_batch_membership": {}}
    calendar = build_twse_trading_calendar_from_holiday_schedule(year=2026,
        holiday_schedule_records=[], generated_at_utc="2026-01-01T00:00:00Z")
    return prepare_i3_authorized_execution(package, evaluation_time=evaluation, official_calendar=calendar,
        closure_events=[], calendar_authority_ref="fixture:twse-calendar-2026",
        closure_authority_ref="fixture:closure-complete", closure_authority_complete=True,
        decision_input=decision)


def _run(package, prepared, tmp_path, *, acquired_markets):
    stamp = "2026-10-01T11:00:00Z"
    output_root = tmp_path / "execution"
    output_root.mkdir()
    plan, authorization, binding = prepared["plan"], prepared["authorization"], prepared["consumption_binding"]
    unused = {"authorization_id": authorization["authorization_id"], "authorization_hash": authorization["authorization_hash"],
        "consumption_binding_id": binding["consumption_binding_id"], "consumption_binding_hash": binding["consumption_binding_hash"],
        "registry_contract_version": "m8r_05b_03.v1", "state": "unused"}
    metadata = load_production_executor_metadata()
    preflight = build_orchestrator_preflight(plan, authorization, binding, supplied_consumption_state=unused,
        evaluation_timestamp=stamp, executor_registry_metadata=metadata, output_root=str(output_root))
    acquired = []
    def fake_acquire(market, *, resolved_source_trade_date=None):
        acquired.append((market, resolved_source_trade_date))
        body = _source(market)
        telemetry = {"mode": "official_https_live", "network_get_count": 1, "retry_count": 0,
            "http_status": 200, "content_type": "application/json", "complete_body_received": True,
            "response_byte_count": len(body), "partial_response_byte_count": 0,
            "response_sha256": hashlib.sha256(body).hexdigest(),
            "tls_policy": "compatibility" if market == "TWSE" else "strict", "redirect_policy": "reject",
            "raw_payload_persisted": False, "failure_phase": None, "error_code": None,
            "retrieved_at": stamp}
        return Acquisition(body, telemetry)
    registry = build_production_runtime_adapter_registry(i3_acquire=fake_acquire)
    result = execute_controlled_plan(plan, authorization, binding, supplied_consumption_state=unused,
        accepted_preflight=preflight, evaluation_timestamp=stamp, claim_created_at=stamp, finalized_at=stamp,
        executor_registry_metadata=metadata, runtime_adapter_registry=registry, output_root=str(output_root),
        mode="execute-approved", confirm_execution=True, operator_confirmation_reference="I3-A4-offline-test",
        confirm_network_execution=True)
    assert {market for market, _ in acquired} == set(acquired_markets)
    assert len(acquired) == len(acquired_markets)
    for outcome in result["dispatch_outcomes"]:
        assert outcome["status"] == "succeeded", outcome
        assert outcome["evidence_contract"] == "cash_institutional_flow_context_evidence.v2"
        art = output_root / outcome["evidence_artifacts"][0]["relative_path"]
        evidence = json.loads(art.read_text(encoding="utf-8"))
        assert evidence["status"] == "complete" and evidence["unit"] == "share"
        assert evidence["transport"]["network_get_count"] == 1 and evidence["transport"]["retry_count"] == 0
        assert evidence["transport"]["raw_payload_persisted"] is False
    # Exercise the normal Unified Result/Audit V3 projection over the actual
    # activated-runtime artifacts, still with fixture bytes and denied sockets.
    from scripts.m8r_05c.artifact_loader import load_projection_inputs
    from scripts.m8r_05c.lineage_resolver import build_lineage_map
    from scripts.m8r_05c.citation_builder import build_citation_index
    from scripts.m8r_05c.result_builder import build_result
    from scripts.m8r_05c.audit_package_builder import build_audit_package
    from scripts.m8r_05b_03.canonical import canonical_json
    from scripts.m8r_filesystem_safety import atomic_write_bytes
    from jsonschema import Draft7Validator, FormatChecker
    import server.services.unified_mode_b2 as mode_b2
    mode_b2._write_control_package(output_root, {"request": package["_request"], "plan": plan,
        "authorization": authorization, "consumption_binding": binding,
        "unused_consumption_state": unused, "preflight": preflight})
    atomic_write_bytes(output_root, "f3_validation.json", canonical_json(package["_validation"]).encode("utf-8"))
    inputs = load_projection_inputs(request_path=str(output_root / "control/request.json"),
        f3_validation_path=str(output_root / "f3_validation.json"), plan_path=str(output_root / "control/plan.json"),
        authorization_path=str(output_root / "control/authorization.json"),
        consumption_binding_path=str(output_root / "control/consumption_binding.json"),
        claim_path=str(output_root / result["claim_relative_path"]),
        receipt_path=str(next((output_root / "receipts").glob("*.json"))),
        bundle_path=str(next((output_root / "bundles").glob("*.json"))), artifact_root=str(output_root),
        calculated_at=stamp, calculated_at_source="receipt.finalized_at")
    lineage = build_lineage_map(inputs)
    citations = build_citation_index(lineage, inputs.bundle, "unified_market_evidence_result.v3")
    unified_result = build_result(inputs, output_schema_version="unified_market_evidence_result.v3")
    audit = build_audit_package(unified_result, inputs, citations, "result.v3.json",
        output_schema_version="unified_market_evidence_audit_package.v3")
    for obj, schema_name in ((unified_result, "unified_market_evidence_result.v3"),
                             (audit, "unified_market_evidence_audit_package.v3")):
        schema = json.loads((ROOT / f"schemas/{schema_name}.schema.json").read_text(encoding="utf-8"))
        Draft7Validator(schema, format_checker=FormatChecker()).validate(obj)
    assert unified_result["schema_version"] == "unified_market_evidence_result.v3"
    assert audit["schema_version"] == "unified_market_evidence_audit_package.v3"
    result["unified_result"] = unified_result
    result["unified_audit"] = audit
    return result, acquired


def test_active_unified_mixed_market_path_is_prebound_and_dispatches_once_per_market(tmp_path):
    request, validation, package = _preview([
        {"input": "1101", "market_hint": "TWSE"}, {"input": "6488", "market_hint": "TPEX"}], request_id="i3-active-mixed")
    prepared = _prepared(package)
    assert prepared["resolved_source_trade_date"] == "2026-09-30"
    assert prepared["authorization"]["plan_hash"] == prepared["plan"]["plan_hash"]
    assert {req["market"] for req in prepared["execution_requests"]} == {"TWSE", "TPEX"}
    requests = {item["market"]: item for item in prepared["execution_requests"]}
    assert requests["TWSE"]["parameters"] == {"resolved_source_trade_date": "2026-09-30"}
    assert requests["TPEX"]["parameters"] == {}
    result, acquired = _run(package, prepared, tmp_path, acquired_markets={"TWSE", "TPEX"})
    assert len(result["dispatch_outcomes"]) == 2
    assert len(acquired) == 2
    assert len(build_tool_specs()) == 6


def test_same_market_batch_uses_one_acquisition_for_multiple_targets(tmp_path):
    _, _, package = _preview([{"input": "1101", "market_hint": "TWSE"},
                              {"input": "1102", "market_hint": "TWSE"}], request_id="i3-active-twse-batch")
    prepared = _prepared(package)
    _, acquired = _run(package, prepared, tmp_path, acquired_markets={"TWSE"})
    assert acquired == [("TWSE", "2026-09-30")]


def test_tpex_only_authorization_does_not_fabricate_twse_date():
    _, _, package = _preview([{ "input": "6488", "market_hint": "TPEX"}], request_id="i3-active-tpex-only")
    prepared = _prepared(package)
    assert prepared["resolved_source_trade_date"] is None
    assert prepared["execution_requests"][0]["market"] == "TPEX"
    assert prepared["execution_requests"][0]["parameters"] == {}


def test_unbound_twse_plan_cannot_be_authorized():
    _, _, package = _preview([{ "input": "2330", "market_hint": "TWSE"}], request_id="i3-unbound-auth")
    operations = package["orchestration_plan"]["operations"]
    stamp = "2026-10-01T11:00:00Z"
    decision = {"decision": "approved", "owner_identity_reference": "offline", "issued_at": stamp,
        "expires_at": "2026-10-01T11:15:00Z", "single_use": True, "replay_policy": "deny_replay",
        "maximum_use_count": 1, "approval_scope_mode": "selected_operations",
        "approved_operation_ids": [x["operation_id"] for x in operations], "approved_batch_group_ids": [],
        "approved_batch_membership": {}}
    from scripts.m8r_05b_02.authorization import build_execution_authorization
    from scripts.m8r_05b_02.models import AuthorizationError
    with pytest.raises(AuthorizationError, match="i3_source_date_binding_missing"):
        build_execution_authorization(package["orchestration_plan"], decision)

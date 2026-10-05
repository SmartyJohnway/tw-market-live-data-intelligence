"""Offline A4 authority/E2E/rollback proof helpers; never runtime imports."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
from functools import wraps
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

if not __debug__:
    raise RuntimeError("A4 offline validation requires assertions enabled")

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "7ffbdf7fb102668457b2a15877c10ad7673da9bf"
EXECUTOR = "phase_i_i2_index_futures_context_executor"
CAPABILITY = "index_futures_context"
AUTHORITY = "USER_CHAT_2026-10-01_PHASE_I_I2_A4_PRODUCTION_ACTIVATION_CANDIDATE_AND_ROLLBACK_AUTHORIZATION"
CATALOG = "docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json"
ROUTING = "docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json"
SOURCE = "docs/data_capabilities/phase_i_i2_source_authority.v1.json"
METADATA = "config/m8r_06_03_executor_registry_metadata.json"
DISPOSITION = "docs/data_capabilities/m8r_05b_existing_orchestrator_disposition.json"
AUTHORITY_FILES = (CATALOG, ROUTING, SOURCE, METADATA, DISPOSITION)


def baseline_json(path):
    return json.loads(subprocess.check_output(["git", "show", f"{BASELINE}:{path}"], cwd=ROOT).decode("utf-8"))


def current_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def record(obj, field):
    return next(x for x in obj[field] if x["capability_id"] == CAPABILITY)


def historical_gate(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        if record(current_json(CATALOG), "data_need_capabilities")["runtime_executable"]:
            if kwargs.get("write_candidate_record"):
                raise ValueError("historical_candidate_record_is_immutable_during_a4")
            with historical_dormant_authority():
                return function(*args, **kwargs)
        return function(*args, **kwargs)
    return wrapped


def verify_candidate_authority():
    """Exact current checks, independently of historical validator snapshots."""
    from scripts.m8r_06_03_production_adapter import build_production_runtime_adapter_registry
    from server.services.phase_i_i2_production_candidate import production_batch_operation_adapter_candidate, production_operation_adapter_candidate
    from server.unified_mcp.tool_contracts import build_tool_contract_snapshot
    c, r, s, m = (current_json(p) for p in (CATALOG, ROUTING, SOURCE, METADATA))
    cap, route = record(c, "data_need_capabilities"), record(r, "routes")
    assert (cap["support_status"], cap["runtime_executable"], cap["phase_i_activation_state"], cap["supported_markets"], cap["requires_approval_for_execution"]) == ("runtime_executable", True, "selected_route_active", ["TWSE"], True)
    assert cap["instrument_scope"] == {"instrument_families": ["company_share"], "instrument_types": ["common_share"]}
    assert cap["historical_lookup_supported"] is False
    assert (route["runtime_executable"], route["routing_status"], route["selected_executor_id"], route["candidate_executor_ids"], route["supported_markets"], route["batching_scope"], route["approval_required"], route["network_required"], route["blocking_reasons"]) == (True, "resolved", EXECUTOR, [EXECUTOR], ["TWSE"], "same_source", True, True, [])
    assert (s["active_source_count"], s["runtime_executable"], s["eligible_target_market"], s["activation_candidate_authority_ref"], s["final_owner_activation_acceptance"]) == (1, True, "TWSE", AUTHORITY, "PENDING")
    assert s["records"] == [{"source_id": "I2-TAIFEX-DAILYMARKETREPORTFUT-OPENAPI", "market": "TAIFEX", "source_family": "TAIFEX_DAILY_MARKET_REPORT_FUT", "source_contract_id": "TAIFEX_DAILY_MARKET_REPORT_FUT_OPENAPI_V1", "activation_state": "active", "runtime_executable": True}]
    expected = {"executor_id": EXECUTOR, "capability_id": CAPABILITY, "market": "TWSE", "supported_security_types": ["equity"], "expected_evidence_contract": "index_futures_context_evidence.v1", "network_required": True, "bounded_execution_supported": True, "timeout_seconds": 30, "maximum_result_items": 1, "output_policy": "contained_artifact_only"}
    assert [x for x in m["executors"] if x["capability_id"] == CAPABILITY] == [expected]
    registry = build_production_runtime_adapter_registry()
    regs = registry.routes_for_executor(EXECUTOR)
    assert len(regs) == 1 and regs[0].market == "TWSE" and regs[0].adapter is production_operation_adapter_candidate and regs[0].batch_adapter is production_batch_operation_adapter_candidate
    assert len(registry.routes_for_executor("phase_i_i1_market_state_executor")) == 2
    assert current_json("docs/data_capabilities/phase_i_i1_source_authority.v1.json")["active_source_count"] == 3
    assert len(build_tool_contract_snapshot().tools) == 6
    # All non-I2 authority records must equal the accepted dormant baseline.
    # I3-A4 is a separately authorized dormant candidate. Preserve its additive
    # catalog/route candidate while this historical I2 proof compares all other
    # authority rows to the I2-accepted baseline.
    i3_capability = "cash_institutional_flow_context"
    i3_executor = "phase_i_i3_cash_institutional_flow_context_executor"
    for path, field, id_key, excluded_ids in (
        (CATALOG, "data_need_capabilities", "capability_id", {CAPABILITY, i3_capability}),
        (ROUTING, "routes", "capability_id", {CAPABILITY, i3_capability}),
        (METADATA, "executors", "executor_id", {EXECUTOR, i3_executor}),
        (DISPOSITION, "surfaces", "surface_id", {EXECUTOR, i3_executor}),
    ):
        now, before = current_json(path), baseline_json(path)
        assert [x for x in now[field] if x.get(id_key) not in excluded_ids] == [x for x in before[field] if x.get(id_key) not in excluded_ids], path
    assert r["phase_h_source_authority"] == baseline_json(ROUTING)["phase_h_source_authority"]
    return registry


@contextmanager
def historical_dormant_authority():
    """Run historical A1/A2/A3 checks against their accepted dormant authority.

    Current A4 authority is checked first, never silently ignored. No canonical
    bytes are written. The normal baseline registry is reconstructed by removing
    only the new I2 registration, retaining every accepted G/H/I1 adapter.
    """
    registry = verify_candidate_authority()
    from scripts.m8r_05b_03.dispatch import RuntimeAdapterRegistry
    baseline_metadata = baseline_json(METADATA)
    registrations = [registry.get_route(x["executor_id"], x["capability_id"], x["market"]) for x in baseline_metadata["executors"]]
    assert all(registrations)
    dormant_registry = RuntimeAdapterRegistry(registrations)
    original = Path.read_text
    replacements = {(ROOT / p).resolve(): json.dumps(baseline_json(p), ensure_ascii=False) for p in AUTHORITY_FILES}
    def read_text(path, *args, **kwargs):
        if path.resolve() in replacements:
            return replacements[path.resolve()]
        return original(path, *args, **kwargs)
    with patch.object(Path, "read_text", read_text), patch("scripts.m8r_06_03_production_adapter.build_production_runtime_adapter_registry", return_value=dormant_registry):
        yield


def verify_a3_hashes():
    ledger_path = "docs/governance/phase_i/PHASE_I_I2_A3_BOUNDED_LIVE_ACCEPTANCE_LEDGER_2026-10-01.json"
    ledger = current_json(ledger_path)
    checks = {ledger_path: "c1b4e8e7f79de9d13bc1ce201f0228f49b883e10255801a73114fb5067008c13",
              ledger["projection"]["result_v3"]["path"]: "45bef90cc92866cd5af11c50bdce63b5b4e52cc16c7c3978cd93feb4162cb8ad",
              ledger["projection"]["audit_v3"]["path"]: "c91812dfb4c96df043d147df9ab7cbaae1c401e242565dca7fe1da9df7299ce7",
              ledger["acceptance_package"]["path"]: "6233659a08d0f49510a7300aa2b3027388dc127983364077426ec3d896301285"}
    for path, expected in checks.items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected
    # No frozen/live-tested semantics or accepted history may change.
    protected = ["server/services/phase_i_i2_index_futures_adapters.py", "server/services/phase_i_i2_offline_candidate.py", "server/services/phase_i_i2_live_acceptance_candidate.py", "schemas/index_futures_context_evidence.v1.schema.json"]
    historical = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", BASELINE, "--", "docs/governance/phase_i"], cwd=ROOT).decode().splitlines()
    subprocess.run(["git", "diff", "--exit-code", BASELINE, "--", *protected, *historical], cwd=ROOT, check=True, capture_output=True)
    return checks


def rollback_authority():
    """Deep-copy current authority, replacing only I2 with exact Git baseline."""
    from scripts.m8r_05b_03.dispatch import RuntimeAdapterRegistry
    registry = verify_candidate_authority()
    rolled = {p: copy.deepcopy(current_json(p)) for p in AUTHORITY_FILES}
    i3_capability = "cash_institutional_flow_context"
    i3_executor = "phase_i_i3_cash_institutional_flow_context_executor"
    for path, field, key, value in ((CATALOG, "data_need_capabilities", "capability_id", CAPABILITY), (ROUTING, "routes", "capability_id", CAPABILITY), (METADATA, "executors", "executor_id", EXECUTOR), (DISPOSITION, "surfaces", "surface_id", EXECUTOR)):
        baseline = baseline_json(path)
        if path in (CATALOG, ROUTING):
            baseline_i2 = next(x for x in baseline[field] if x.get(key) == value)
            restored = []
            for item in rolled[path][field]:
                if item.get(key) == i3_capability:
                    continue
                restored.append(copy.deepcopy(baseline_i2) if item.get(key) == value else item)
            rolled[path][field] = restored
        else:
            rolled[path][field] = [x for x in rolled[path][field] if x.get(key) not in {value, i3_executor}]
        assert rolled[path] == baseline, path
    rolled[SOURCE] = copy.deepcopy(baseline_json(SOURCE))
    regs = [registry.get_route(x["executor_id"], x["capability_id"], x["market"]) for x in rolled[METADATA]["executors"]]
    rolled_registry = RuntimeAdapterRegistry(regs)
    assert not rolled_registry.routes_for_executor(EXECUTOR)
    assert len(rolled_registry.routes_for_executor("phase_i_i1_market_state_executor")) == 2
    verify_a3_hashes()
    return rolled, rolled_registry


def production_preview(targets=("1101", "1102"), *, authorities=None):
    from scripts.m8r_06_01c2_mode_a_security_master_loader import load_active_mode_a_security_master
    from scripts.m8r_06_02_mode_b1_preview import build_mode_b1_preview_package
    from server.services.unified_mode_a import validate_mode_a_request
    request = {"schema_version": "unified_market_evidence_request.v3", "request_id": "i2-a4-offline-proof",
               "execution_mode": "execute", "targets": [{"input": code, "market_hint": "TWSE" if code != "6488" else "TPEX", "resolution_requirement": "exact"} for code in targets],
               "data_needs": [{"type": CAPABILITY, "priority": "required", "parameters": {}}]}
    runtime = load_active_mode_a_security_master(security_master_root=ROOT / "data/security_master")
    assert runtime.validation["valid"]
    # Installation-local exact identity authority, not a fixture identity fork.
    with patch.dict(os.environ, {"TW_MARKET_SECURITY_MASTER_ROOT": str(ROOT / "data/security_master")}):
        with patch("server.services.unified_mode_a.get_production_mode_a_security_master", return_value=runtime):
            validation = validate_mode_a_request(request)
            package = build_mode_b1_preview_package(request, validation, runtime,
                          planning_timestamp="2026-10-01T06:00:00Z", authorities=authorities)
    return request, runtime, validation, package


def run_production_offline_proof(output_root: Path, payload: bytes):
    """Normal current authority + normal production registry; fake I/O only."""
    from scripts.m8r_05b_02.authorization import build_execution_authorization
    from scripts.m8r_05b_02.consumption_binding import build_consumption_binding
    from scripts.m8r_05b_03.preflight import build_orchestrator_preflight, validate_preflight_hashes
    from scripts.m8r_05b_03.orchestrator import execute_controlled_plan
    from scripts.m8r_06_03_production_adapter import build_production_runtime_adapter_registry
    from scripts.m8r_05c.artifact_loader import load_projection_inputs
    from scripts.m8r_05c.lineage_resolver import build_lineage_map
    from scripts.m8r_05c.citation_builder import build_citation_index
    from scripts.m8r_05c.result_builder import build_result
    from scripts.m8r_05c.audit_package_builder import build_audit_package
    from scripts.m8r_05b_03.canonical import canonical_json
    from scripts.m8r_filesystem_safety import atomic_write_bytes
    from jsonschema import Draft7Validator, FormatChecker
    import server.services.unified_mode_b2 as m2
    stamp = "2026-10-01T06:00:00Z"
    request, runtime, validation, preview = production_preview()
    assert preview["preview"]["status"] == "ready_for_confirmation"
    plan = preview["orchestration_plan"]
    assert len(plan["operations"]) == 2 and len(plan["batch_groups"]) == 1 and plan["accounting"]["network_request_estimate"] == 1
    decision = {"decision": "approved", "decision_reason": "A4 offline fake-source production wiring proof only",
                "owner_identity_reference": "USER_CHAT_OWNER", "owner_review_reference": AUTHORITY,
                "reviewed_at": stamp, "issued_at": stamp, "expires_at": "2026-10-01T06:15:00Z",
                "single_use": True, "replay_policy": "deny_replay", "maximum_use_count": 1,
                "approval_scope_mode": "whole_plan_executable_scope", "approved_operation_ids": [],
                "approved_batch_group_ids": [], "approved_batch_membership": {}}
    authorization = build_execution_authorization(plan, decision)
    binding = build_consumption_binding(authorization)
    unused = {"authorization_id": authorization["authorization_id"], "authorization_hash": authorization["authorization_hash"],
              "consumption_binding_id": binding["consumption_binding_id"], "consumption_binding_hash": binding["consumption_binding_hash"],
              "registry_contract_version": "m8r_05b_03.v1", "state": "unused"}
    output_root.mkdir(parents=True, exist_ok=False)
    metadata = current_json(METADATA)
    preflight = build_orchestrator_preflight(plan, authorization, binding, supplied_consumption_state=unused,
                  evaluation_timestamp=stamp, executor_registry_metadata=metadata, output_root=str(output_root))
    validate_preflight_hashes(preflight)
    assert len(preflight["bounded_execution_requests"]) == 2
    m2._write_control_package(output_root, {"request": request, "plan": plan, "authorization": authorization,
         "consumption_binding": binding, "unused_consumption_state": unused, "preflight": preflight})
    atomic_write_bytes(output_root, "f3_validation.json", canonical_json(validation).encode("utf-8"))
    calls = []
    def fake(url, timeout):
        assert not calls and url == "https://openapi.taifex.com.tw/v1/DailyMarketReportFut" and timeout == 30
        calls.append((url, timeout))
        return 200, {"Content-Type": "application/octet-stream"}, payload
    def deny(*args, **kwargs):
        raise AssertionError("market network forbidden in A4")
    from server.services.phase_i_i2_production_transport import acquire_taifex_once
    def fake_clock_acquisition(*, transport):
        return acquire_taifex_once(transport=transport, clock=lambda: datetime(2026, 10, 1, 6, 0, 1, tzinfo=timezone.utc))
    with patch("socket.socket.connect", deny), patch("socket.create_connection", deny), patch("server.services.phase_i_i2_production_candidate._read_once", fake), patch("server.services.phase_i_i2_production_candidate._stamp", return_value=stamp), patch("server.services.phase_i_i2_production_candidate.acquire_taifex_once", fake_clock_acquisition):
        registry = build_production_runtime_adapter_registry()
        kwargs = dict(supplied_consumption_state=unused, accepted_preflight=preflight, evaluation_timestamp=stamp,
                      claim_created_at=stamp, finalized_at=stamp, executor_registry_metadata=metadata,
                      runtime_adapter_registry=registry, output_root=str(output_root), mode="execute-approved",
                      confirm_execution=True, operator_confirmation_reference=AUTHORITY, confirm_network_execution=True)
        execution = execute_controlled_plan(plan, authorization, binding, **kwargs)
        from scripts.m8r_05b_03.errors import OrchestrationError
        try:
            execute_controlled_plan(plan, authorization, binding, **kwargs)
        except OrchestrationError:
            pass
        else:
            raise AssertionError("replay accepted")
    assert len(calls) == 1 and execution["claim_record"]["attempt_count"] == 1
    inputs = load_projection_inputs(request_path=str(output_root / "control/request.json"),
        f3_validation_path=str(output_root / "f3_validation.json"), plan_path=str(output_root / "control/plan.json"),
        authorization_path=str(output_root / "control/authorization.json"), consumption_binding_path=str(output_root / "control/consumption_binding.json"),
        claim_path=str(output_root / execution["claim_relative_path"]), receipt_path=str(next((output_root / "receipts").glob("*.json"))),
        bundle_path=str(next((output_root / "bundles").glob("*.json"))), artifact_root=str(output_root),
        calculated_at=stamp, calculated_at_source="receipt.finalized_at")
    lineage = build_lineage_map(inputs)
    citations = build_citation_index(lineage, inputs.bundle, "unified_market_evidence_result.v3")
    result = build_result(inputs, output_schema_version="unified_market_evidence_result.v3")
    audit = build_audit_package(result, inputs, citations, "result.v3.json", output_schema_version="unified_market_evidence_audit_package.v3")
    for obj, name in ((result, "unified_market_evidence_result.v3"), (audit, "unified_market_evidence_audit_package.v3")):
        Draft7Validator(current_json(f"schemas/{name}.schema.json"), format_checker=FormatChecker()).validate(obj)
    assert result == build_result(inputs, output_schema_version="unified_market_evidence_result.v3")
    assert audit == build_audit_package(result, inputs, citations, "result.v3.json", output_schema_version="unified_market_evidence_audit_package.v3")
    artifacts = [a for op in execution["dispatch_outcomes"] for a in op["evidence_artifacts"]]
    evidence = [json.loads((output_root / a["relative_path"]).read_bytes()) for a in artifacts]
    for a in artifacts:
        assert hashlib.sha256((output_root / a["relative_path"]).read_bytes()).hexdigest() == a["sha256"]
    assert evidence[0]["transport"] == evidence[1]["transport"]
    for target in result["targets"]:
        typed = target["evidence"].get(CAPABILITY)
        if evidence[0]["status"] in {"source_failed", "binding_failed"}:
            assert typed is None
        else:
            assert typed["target"]["canonical_target_id"] == target["resolution"]["canonical_target_id"]
            assert typed["venue"] == "TAIFEX" and typed["product_code"] == "TX"
    assert all(payload not in p.read_bytes() for p in output_root.rglob("*") if p.is_file())
    return {"plan": plan, "execution_requests": preflight["bounded_execution_requests"], "execution": execution, "evidence": evidence, "fake_acquisitions": len(calls),
            "external_market_calls": 0, "raw_persistence": "NONE", "result": result, "audit": audit,
            "result_sha256": hashlib.sha256(canonical_json(result).encode()).hexdigest(),
            "audit_sha256": hashlib.sha256(canonical_json(audit).encode()).hexdigest(), "security_master": runtime.pointer}

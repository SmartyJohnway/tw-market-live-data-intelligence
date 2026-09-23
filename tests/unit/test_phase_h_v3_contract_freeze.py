"""H0-G exact V3 contract freeze validation; no runtime activation or network."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path

import jsonschema
import pytest

from server.unified_mcp.tool_contracts import PREFERRED_REQUEST_SCHEMA_VERSION, build_tool_specs
from scripts.validate_phase_h_v3_contracts import (
    PhaseHV3ContractValidationError,
    validate_corporate_action_context_semantics,
    validate_discontinuity_safety_semantics,
    validate_h2_h3_h4_cross_evidence,
    validate_recent_performance_semantics,
    validate_trading_status_context_semantics,
)


ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "schemas"
DATA = ROOT / "docs" / "data_capabilities"
FIXTURES = ROOT / "tests" / "fixtures" / "phase_h_contract_v3"
EXAMPLES = json.loads((FIXTURES / "contract_examples.json").read_text(encoding="utf-8"))

V3_SCHEMAS = {
    "request": "unified_market_evidence_request.v3.schema.json",
    "result": "unified_market_evidence_result.v3.schema.json",
    "audit": "unified_market_evidence_audit_package.v3.schema.json",
    "h1": "trading_status_context_evidence.v1.schema.json",
    "h2": "corporate_action_context_evidence.v1.schema.json",
    "h3": "recent_performance_evidence.v1.schema.json",
    "h4": "discontinuity_safety_evidence.v1.schema.json",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def schema(name: str) -> dict:
    return load(SCHEMAS / V3_SCHEMAS[name])


def validate(value: dict, name: str) -> None:
    jsonschema.Draft7Validator(schema(name), format_checker=jsonschema.FormatChecker()).validate(value)


def test_all_v3_schemas_are_draft7_meta_valid_and_json_assets_parse():
    for filename in V3_SCHEMAS.values():
        value = load(SCHEMAS / filename)
        assert value["$schema"] == "http://json-schema.org/draft-07/schema#"
        jsonschema.Draft7Validator.check_schema(value)
    load(DATA / "unified_market_evidence_capability_catalog.v3.json")
    load(DATA / "m8r_05b_capability_to_executor_routing_matrix.v3.json")


def test_request_v3_data_need_universe_and_bounds():
    request = copy.deepcopy(EXAMPLES["request_v3"])
    validate(request, "request")
    universe = schema("request")["properties"]["data_needs"]["items"]["properties"]["type"]["enum"]
    assert universe == [
        "identity", "current_observation", "official_eod_reference", "recent_performance",
        "session_status", "source_currentness", "evidence_quality", "material_disclosures",
        "monthly_revenue", "trading_status_context", "corporate_action_context",
    ]
    for need in ("trading_status_context", "corporate_action_context"):
        candidate = copy.deepcopy(request)
        candidate["data_needs"] = [{"type": need, "priority": "required", "parameters": {}}]
        validate(candidate, "request")
    for bad_need in ("discontinuity_safety", "historical_baseline", "price_history"):
        candidate = copy.deepcopy(request)
        candidate["data_needs"] = [{"type": bad_need, "priority": "required", "parameters": {}}]
        with pytest.raises(jsonschema.ValidationError):
            validate(candidate, "request")
    for bad in (None, 0, 21):
        candidate = copy.deepcopy(request)
        parameters = {} if bad is None else {"lookback_trading_days": bad}
        candidate["data_needs"] = [{"type": "recent_performance", "priority": "required", "parameters": parameters}]
        with pytest.raises(jsonschema.ValidationError):
            validate(candidate, "request")


def test_h1_available_no_evidence_partial_and_failures_are_typed_and_fail_closed():
    validate(EXAMPLES["h1_attention_available"], "h1")
    validate(EXAMPLES["h1_no_evidence_complete"], "h1")
    validate_trading_status_context_semantics(EXAMPLES["h1_attention_available"])
    validate_trading_status_context_semantics(EXAMPLES["h1_no_evidence_complete"])
    partial = copy.deepcopy(EXAMPLES["h1_attention_available"])
    partial["status"] = "partial"
    partial["coverage"].update({"status": "partial", "declared_scope_complete": False, "uncovered_status_types": ["suspension"]})
    validate(partial, "h1")
    for status, coverage_status in (("source_failed", "source_failed"), ("binding_failed", "binding_failed")):
        failed = copy.deepcopy(EXAMPLES["h1_no_evidence_complete"])
        failed["status"] = status
        failed["items"] = []
        failed["coverage"].update({"status": coverage_status, "declared_scope_complete": False, "retrieval_succeeded": status != "source_failed", "exact_target_search_succeeded": status != "binding_failed"})
        validate(failed, "h1")
    invalid = copy.deepcopy(EXAMPLES["h1_no_evidence_complete"])
    invalid["coverage"]["declared_scope_complete"] = False
    with pytest.raises(jsonschema.ValidationError):
        validate(invalid, "h1")
    invalid = copy.deepcopy(EXAMPLES["h1_no_evidence_complete"])
    invalid["coverage"]["declared_status_types"] = []
    with pytest.raises(jsonschema.ValidationError):
        validate(invalid, "h1")
    invalid = copy.deepcopy(EXAMPLES["h1_no_evidence_complete"])
    invalid["coverage"]["covered_status_types"] = ["attention"]
    with pytest.raises(PhaseHV3ContractValidationError):
        validate_trading_status_context_semantics(invalid)


def test_h2_stage_revision_missing_zero_and_coverage_semantics():
    value = copy.deepcopy(EXAMPLES["h2_preannouncement_and_final"])
    validate(value, "h2")
    validate_corporate_action_context_semantics(value)
    first, second = value["events"]
    assert first["source_evidence_stage"] == "preannouncement"
    assert second["source_evidence_stage"] == "official_reference_calculated"
    assert first["cash_dividend"] == {"state": "blank", "value": None}
    assert first["stock_dividend_ratio"] == {"state": "value", "value": 0}
    assert first["revision_relation"]["status"] == "unresolved"
    assert second["revision_relation"]["status"] == "officially_linked"
    invalid = copy.deepcopy(value)
    invalid["events"][0]["revision_relation"]["relation_type"] = "supersedes"
    with pytest.raises(jsonschema.ValidationError):
        validate(invalid, "h2")
    inferred_revision = copy.deepcopy(value)
    inferred_revision["events"][0]["event_lifecycle"] = "corrected"
    with pytest.raises(jsonschema.ValidationError):
        validate(inferred_revision, "h2")
    no_evidence = copy.deepcopy(value)
    no_evidence["status"] = "no_evidence_in_covered_scope"
    no_evidence["events"] = []
    no_evidence["coverage"].update({"status": "complete", "declared_scope_complete": True, "uncovered_event_subtypes": [], "failed_source_families": []})
    validate(no_evidence, "h2")
    no_evidence["coverage"]["uncovered_event_subtypes"] = ["split"]
    with pytest.raises(jsonschema.ValidationError):
        validate(no_evidence, "h2")
    invalid = copy.deepcopy(no_evidence)
    invalid["coverage"]["uncovered_event_subtypes"] = []
    invalid["coverage"]["declared_event_subtypes"] = []
    with pytest.raises(jsonschema.ValidationError):
        validate(invalid, "h2")


@pytest.mark.parametrize(("key", "n", "closes"), [("h3_1d", 1, 2), ("h3_5d", 5, 6), ("h3_20d", 20, 21)])
def test_h3_n_plus_one_and_completed_close_range(key, n, closes):
    value = EXAMPLES[key]
    validate(value, "h3")
    assert value["requested_observations"] == n
    assert value["valid_observation_count"] == n
    assert value["baselines"][0]["required_distinct_close_count"] == closes
    assert value["recent_close_range"] == {"range_basis": "completed_session_closing_price", "recent_close_high": 120, "recent_close_low": 100}
    assert value["volume_context"]["comparison_alignment"] == "partial_session_vs_completed_sessions"
    validate_recent_performance_semantics(value)
    invalid = copy.deepcopy(value)
    invalid["recent_close_range"]["range_basis"] = "intraday_high_low_envelope"
    with pytest.raises(jsonschema.ValidationError):
        validate(invalid, "h3")


def test_h3_available_baselines_bind_exact_nth_session_and_raw_return():
    for key, lookback in (("h3_1d", 1), ("h3_5d", 5), ("h3_20d", 20)):
        value = copy.deepcopy(EXAMPLES[key])
        baseline = value["baselines"][0]
        assert baseline["start_observation_date"] == value["observations"][-lookback]["trade_date"]
        assert baseline["end_observation_date"] == value["governed_end_observation"]["trade_date"]
        validate_recent_performance_semantics(value)
    for field, replacement in (("start_observation_date", "2026-01-01"), ("end_observation_date", "2026-01-01")):
        invalid = copy.deepcopy(EXAMPLES["h3_5d"])
        invalid["baselines"][0][field] = replacement
        with pytest.raises(PhaseHV3ContractValidationError):
            validate_recent_performance_semantics(invalid)
    invalid = copy.deepcopy(EXAMPLES["h3_5d"])
    invalid["baselines"][0]["start_observation_date"] = invalid["observations"][-4]["trade_date"]
    with pytest.raises(PhaseHV3ContractValidationError):
        validate_recent_performance_semantics(invalid)
    invalid = copy.deepcopy(EXAMPLES["h3_5d"])
    invalid["baselines"][0]["actual_distinct_close_count"] = 21
    with pytest.raises(PhaseHV3ContractValidationError):
        validate_recent_performance_semantics(invalid)
    invalid = copy.deepcopy(EXAMPLES["h3_5d"])
    invalid["baselines"][0]["recent_return_pct"] = 19.999
    with pytest.raises(PhaseHV3ContractValidationError):
        validate_recent_performance_semantics(invalid)
    invalid = copy.deepcopy(EXAMPLES["h3_5d"])
    invalid["observations"][-1]["trade_date"] = invalid["governed_end_observation"]["trade_date"]
    with pytest.raises(PhaseHV3ContractValidationError):
        validate_recent_performance_semantics(invalid)


def test_h3_partial_insufficient_unavailable_and_failures_remain_distinct():
    base = copy.deepcopy(EXAMPLES["h3_5d"])
    partial = copy.deepcopy(base)
    partial.update({"coverage_status": "partial", "valid_observation_count": 4, "missing_observation_count": 1})
    partial["observations"] = partial["observations"][:4]
    partial["last_observation_date"] = partial["observations"][-1]["trade_date"]
    partial["baselines"] = [
        {"lookback_trading_days": 4, "status": "available", "start_observation_date": partial["observations"][0]["trade_date"], "end_observation_date": partial["governed_end_observation"]["trade_date"], "required_distinct_close_count": 5, "actual_distinct_close_count": 5, "recent_return_pct": 20.0, "return_basis": "raw_unadjusted_close_to_close"},
        {"lookback_trading_days": 5, "status": "insufficient_coverage", "start_observation_date": None, "end_observation_date": partial["governed_end_observation"]["trade_date"], "required_distinct_close_count": 6, "actual_distinct_close_count": 5, "recent_return_pct": None, "return_basis": "raw_unadjusted_close_to_close"},
    ]
    partial["available_baselines"] = [4]
    partial["unavailable_baselines"] = [5]
    validate(partial, "h3")
    validate_recent_performance_semantics(partial)

    insufficient = copy.deepcopy(partial)
    insufficient["coverage_status"] = "insufficient"
    insufficient["baselines"] = [insufficient["baselines"][1]]
    insufficient["available_baselines"] = []
    validate(insufficient, "h3")
    validate_recent_performance_semantics(insufficient)

    for status in ("unavailable", "source_failed", "binding_failed"):
        value = copy.deepcopy(base)
        value.update({"coverage_status": status, "valid_observation_count": 0, "missing_observation_count": 5, "first_observation_date": None, "last_observation_date": None, "governed_end_observation": None, "observations": [], "available_baselines": [], "unavailable_baselines": [5], "recent_close_range": None})
        value["baselines"][0].update({"status": "unavailable", "start_observation_date": None, "end_observation_date": None, "actual_distinct_close_count": 0, "recent_return_pct": None})
        validate(value, "h3")
        validate_recent_performance_semantics(value)

    for contradictory_status in ("partial", "insufficient", "source_failed"):
        invalid = copy.deepcopy(base)
        invalid["coverage_status"] = contradictory_status
        with pytest.raises(PhaseHV3ContractValidationError):
            validate_recent_performance_semantics(invalid)


def test_h4_exact_states_schema_conditions_and_set_invariants():
    keys = ("h4_no_material", "h4_reference_available", "h4_reference_unavailable", "h4_coverage_incomplete")
    for key in keys:
        value = EXAMPLES[key]
        validate(value, "h4")
        validate_discontinuity_safety_semantics(value)
    for key in ("h4_reference_available", "h4_reference_unavailable", "h4_coverage_incomplete"):
        invalid = copy.deepcopy(EXAMPLES[key])
        invalid["ordinary_return_interpretation"] = "allowed"
        with pytest.raises(jsonschema.ValidationError):
            validate(invalid, "h4")
    for reason in ("unsupported_subtype", "source_failure", "binding_failure", "revision_unresolved"):
        value = copy.deepcopy(EXAMPLES["h4_coverage_incomplete"])
        value["caveats"] = [reason]
        if reason == "source_failure":
            value["failed_source_families"] = ["TWSE_PHASE_H_FIXTURE"]
            value["upstream_failures"] = [{"failure_type": "source_failed", "evidence_reference": "h2-evidence"}]
        elif reason == "binding_failure":
            value["upstream_failures"] = [{"failure_type": "binding_failed", "evidence_reference": "h2-evidence"}]
        elif reason == "revision_unresolved":
            value["upstream_failures"] = [{"failure_type": "unresolved_revision", "evidence_reference": "event-1"}]
        validate(value, "h4")
        assert value["ordinary_return_interpretation"] == "blocked"
        assert value["raw_metric_status"] == "available"
    invalid = copy.deepcopy(EXAMPLES["h4_no_material"])
    invalid["upstream_failures"] = [{"failure_type": "binding_failed", "evidence_reference": "h2-evidence"}]
    with pytest.raises(jsonschema.ValidationError):
        validate(invalid, "h4")
    relevant_gap = copy.deepcopy(EXAMPLES["h4_no_material"])
    relevant_gap["covered_event_subtypes"] = []
    with pytest.raises(PhaseHV3ContractValidationError):
        validate_discontinuity_safety_semantics(relevant_gap)
    no_reason = copy.deepcopy(EXAMPLES["h4_coverage_incomplete"])
    no_reason["covered_event_subtypes"] = no_reason["relevant_event_subtypes"]
    no_reason["uncovered_event_subtypes"] = []
    with pytest.raises(PhaseHV3ContractValidationError):
        validate_discontinuity_safety_semantics(no_reason)
    invalid = copy.deepcopy(EXAMPLES["h4_no_material"])
    invalid["comparison_window"]["start_observation_date"] = "2026-09-22"
    with pytest.raises(PhaseHV3ContractValidationError):
        validate_discontinuity_safety_semantics(invalid)


def test_h2_h3_h4_cross_evidence_is_target_window_and_coverage_consistent():
    h2 = copy.deepcopy(EXAMPLES["h2_preannouncement_and_final"])
    h3 = copy.deepcopy(EXAMPLES["h3_5d"])
    h4 = copy.deepcopy(EXAMPLES["h4_coverage_incomplete"])
    h4["comparison_window"] = {
        "start_observation_date": h3["baselines"][0]["start_observation_date"],
        "end_observation_date": h3["baselines"][0]["end_observation_date"],
        "start_price_basis": "official_close", "end_price_basis": "official_close",
    }
    validate_h2_h3_h4_cross_evidence(h2, h3, h4)
    h4["comparison_window"]["end_observation_date"] = "2026-09-21"
    with pytest.raises(PhaseHV3ContractValidationError):
        validate_h2_h3_h4_cross_evidence(h2, h3, h4)


def test_result_v3_embeds_typed_phase_h_contracts_and_audit_v3_binds_lineage():
    result_schema = schema("result")
    evidence = result_schema["properties"]["targets"]["items"]["properties"]["evidence"]["properties"]
    assert evidence["trading_status_context"]["$ref"].endswith("/trading_status_context")
    assert evidence["corporate_action_context"]["$ref"].endswith("/corporate_action_context")
    assert evidence["recent_performance"]["$ref"].endswith("/recent_performance_v3")
    assert evidence["discontinuity_safety"]["$ref"].endswith("/discontinuity_safety")
    standalone = {"trading_status_context": "h1", "corporate_action_context": "h2", "recent_performance_v3": "h3", "discontinuity_safety": "h4"}
    for definition_name, standalone_name in standalone.items():
        embedded = copy.deepcopy(result_schema["definitions"][definition_name])
        external = copy.deepcopy(schema(standalone_name))
        for key in ("$schema", "$id", "title"):
            external.pop(key, None)
        assert embedded == external
    audit_schema = schema("audit")
    assert "phase_h_governance" in audit_schema["required"]
    governance = audit_schema["properties"]["phase_h_governance"]
    assert set(governance["required"]) == {"source_attempts", "evidence_artifact_references", "h4_derivations"}
    assert "discontinuity_safety" in governance["properties"]["evidence_artifact_references"]["items"]["properties"]["capability_id"]["enum"]


def test_valid_result_v3_and_audit_v3_samples_validate_without_rewriting_v2():
    fixture_root = ROOT / "tests" / "fixtures" / "phase_g_pr_c" / "v2_acceptance"
    result = load(fixture_root / "unified_market_evidence_result.v2.json")
    result["schema_version"] = "unified_market_evidence_result.v3"
    result["result_id"] = result["result_id"].replace("umeresult-v2-", "umeresult-v3-")
    result["request_summary"]["request_schema_version"] = "unified_market_evidence_request.v3"
    result["audit_reference"]["audit_package_id"] = result["audit_reference"]["audit_package_id"].replace("umeap-v2-", "umeap-v3-")
    result["audit_reference"]["schema_version"] = "unified_market_evidence_audit_package.v3"
    target_evidence = result["targets"][0]["evidence"]
    target_evidence["recent_performance"] = copy.deepcopy(EXAMPLES["h3_5d"])
    target_evidence["trading_status_context"] = copy.deepcopy(EXAMPLES["h1_attention_available"])
    target_evidence["corporate_action_context"] = copy.deepcopy(EXAMPLES["h2_preannouncement_and_final"])
    target_evidence["discontinuity_safety"] = copy.deepcopy(EXAMPLES["h4_coverage_incomplete"])
    validate(result, "result")

    audit = load(fixture_root / "unified_market_evidence_audit_package.v2.json")
    audit["schema_version"] = "unified_market_evidence_audit_package.v3"
    audit["audit_package_id"] = audit["audit_package_id"].replace("umeap-v2-", "umeap-v3-")
    audit["result_id"] = audit["result_id"].replace("umeresult-v2-", "umeresult-v3-")
    audit["request_identity"]["schema_version"] = "unified_market_evidence_request.v3"
    audit["phase_h_governance"] = {
        "source_attempts": [{
            "source_family": "TWSE_PHASE_H_FIXTURE", "source_contract_id": "fixture-contract",
            "source_role": "default_candidate", "activation_state": "eligible",
            "provider_availability": "available", "license_authority": "ODGL",
            "canonical_target_id": "TWSE:2330", "market": "TWSE",
            "requested_window": {"start": "2026-09-01", "end": "2026-09-21"},
            "coverage_result": "partial", "outcome": "not_attempted", "failure_code": None,
        }],
        "evidence_artifact_references": [
            {"capability_id": "recent_performance", "schema_version": "recent_performance_evidence.v1", "relative_path": "evidence/recent-performance.json", "sha256": "a" * 64},
            {"capability_id": "discontinuity_safety", "schema_version": "discontinuity_safety_evidence.v1", "relative_path": "evidence/discontinuity-2330.json", "sha256": "b" * 64},
            {"capability_id": "discontinuity_safety", "schema_version": "discontinuity_safety_evidence.v1", "relative_path": "evidence/discontinuity-6488.json", "sha256": "c" * 64},
        ],
        "h4_derivations": [
            {"canonical_target_id": "TWSE:2330", "market": "TWSE", "comparison_window": {"start_observation_date": "2026-09-01", "end_observation_date": "2026-09-21"}, "input_evidence_references": ["h2-2330", "h3-2330"], "evidence_artifact_reference": {"relative_path": "evidence/discontinuity-2330.json", "sha256": "b" * 64}, "deterministic_rule_version": "phase_h_discontinuity_safety.v1", "derived_state": "coverage_incomplete", "interpretation_guard": "CORPORATE_ACTION_COVERAGE_INCOMPLETE"},
            {"canonical_target_id": "TPEX:6488", "market": "TPEX", "comparison_window": {"start_observation_date": "2026-09-01", "end_observation_date": "2026-09-21"}, "input_evidence_references": ["h2-6488", "h3-6488"], "evidence_artifact_reference": {"relative_path": "evidence/discontinuity-6488.json", "sha256": "c" * 64}, "deterministic_rule_version": "phase_h_discontinuity_safety.v1", "derived_state": "no_material_discontinuity_detected", "interpretation_guard": "none"},
        ],
    }
    validate(audit, "audit")
    assert {item["canonical_target_id"] for item in audit["phase_h_governance"]["h4_derivations"]} == {"TWSE:2330", "TPEX:6488"}
    for bad_path in (r"C:\evil.json", r"\\server\share\evil.json", "/absolute/evil.json", "file://evil.json", "../evil.json", r"..\evil.json", "safe/../../evil.json", ".", "..", "foo/./bar.json", "foo//bar.json", "foo/"):
        invalid = copy.deepcopy(audit)
        invalid["result_relative_path"] = bad_path
        with pytest.raises(jsonschema.ValidationError):
            validate(invalid, "audit")
        invalid = copy.deepcopy(audit)
        invalid["phase_h_governance"]["evidence_artifact_references"][0]["relative_path"] = bad_path
        with pytest.raises(jsonschema.ValidationError):
            validate(invalid, "audit")
        invalid = copy.deepcopy(audit)
        invalid["phase_h_governance"]["h4_derivations"][0]["evidence_artifact_reference"]["relative_path"] = bad_path
        with pytest.raises(jsonschema.ValidationError):
            validate(invalid, "audit")
        invalid = copy.deepcopy(audit)
        invalid["operation_lineage"][0]["artifact_references"][0]["relative_path"] = bad_path
        with pytest.raises(jsonschema.ValidationError):
            validate(invalid, "audit")
        invalid = copy.deepcopy(audit)
        invalid["artifact_inventory"][0]["relative_path"] = bad_path
        with pytest.raises(jsonschema.ValidationError):
            validate(invalid, "audit")
        invalid = copy.deepcopy(audit)
        invalid["citation_to_operation_map"][0]["artifact_relative_path"] = bad_path
        with pytest.raises(jsonschema.ValidationError):
            validate(invalid, "audit")
        invalid = copy.deepcopy(audit)
        invalid["integrity_verification"]["failed_artifact_paths"] = [bad_path]
        with pytest.raises(jsonschema.ValidationError):
            validate(invalid, "audit")
        invalid = copy.deepcopy(audit)
        invalid["replay_manifest"]["artifact_root_relative"] = bad_path
        with pytest.raises(jsonschema.ValidationError):
            validate(invalid, "audit")
    validate(audit, "audit")
    for good_path in ("artifacts/foo.json", "phase_h/h1/TWSE_2330.json", "audit/2026-09-21/package.json", "foo/.hidden.json"):
        candidate = copy.deepcopy(audit)
        candidate["result_relative_path"] = good_path
        candidate["operation_lineage"][0]["artifact_references"][0]["relative_path"] = good_path
        candidate["artifact_inventory"][0]["relative_path"] = good_path
        candidate["citation_to_operation_map"][0]["artifact_relative_path"] = good_path
        candidate["integrity_verification"]["failed_artifact_paths"] = [good_path]
        candidate["replay_manifest"]["artifact_root_relative"] = good_path
        candidate["phase_h_governance"]["evidence_artifact_references"][0]["relative_path"] = good_path
        candidate["phase_h_governance"]["h4_derivations"][0]["evidence_artifact_reference"]["relative_path"] = good_path
        validate(candidate, "audit")


def test_v1_v2_frozen_bytes_unchanged_and_remain_readable():
    manifest = load(ROOT / "tests" / "fixtures" / "phase_g_contract_v2" / "SCHEMA_FREEZE_MANIFEST.json")
    for name in (
        "unified_market_evidence_request.v2.schema.json",
        "unified_market_evidence_result.v2.schema.json",
        "unified_market_evidence_audit_package.v2.schema.json",
    ):
        path = SCHEMAS / name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == manifest["files"][name]["sha256"]
        jsonschema.validators.validator_for(load(path)).check_schema(load(path))
    for name in ("unified_market_evidence_request.v1.schema.json", "unified_market_evidence_result.v1.schema.json", "unified_market_evidence_audit_package.v1.schema.json"):
        jsonschema.validators.validator_for(load(SCHEMAS / name)).check_schema(load(SCHEMAS / name))


def test_catalog_routing_truth_exposes_only_selected_h1_route_while_v2_remains_preferred():
    catalog = load(DATA / "unified_market_evidence_capability_catalog.v3.json")
    routing = load(DATA / "m8r_05b_capability_to_executor_routing_matrix.v3.json")
    capabilities = {item["capability_id"]: item for item in catalog["data_need_capabilities"]}
    routes = {item["capability_id"]: item for item in routing["routes"]}
    request_needs = set(schema("request")["properties"]["data_needs"]["items"]["properties"]["type"]["enum"])
    assert request_needs == set(capabilities)

    h1 = capabilities["trading_status_context"]
    assert h1["support_status"] == "runtime_executable"
    assert h1["runtime_executable"] is True
    assert h1["phase_h_activation_state"] == "selected_route_active"
    assert routes["trading_status_context"]["runtime_executable"] is True
    assert routes["trading_status_context"]["selected_executor_id"] == "phase_h_h1_tpex_attention_executor"
    assert routes["trading_status_context"]["supported_markets"] == ["TPEX"]
    assert routes["trading_status_context"]["network_required"] is True

    for capability_id in ("corporate_action_context", "recent_performance"):
        assert capabilities[capability_id]["support_status"] == "contract_supported"
        assert capabilities[capability_id]["runtime_executable"] is False
        assert capabilities[capability_id]["phase_h_activation_state"] == "inactive"
        assert routes[capability_id]["runtime_executable"] is False
        assert routes[capability_id]["selected_executor_id"] is None

    assert catalog["contract_versions"]["v3_runtime_authority_status"] == "v3_preferred_selected_routes_active"
    assert catalog["phase_h_contract"]["active_phase_h_source_count"] == 1
    assert routing["phase_h_source_authority"]["active_source_count"] == 1
    active = [item for item in routing["phase_h_source_authority"]["records"] if item["activation_state"] == "active"]
    assert [(item["source_id"], item["runtime_executable"]) for item in active] == [
        ("H1-TPEX-ATTENTION-OPENAPI", True)
    ]
    assert "discontinuity_safety" not in request_needs
    assert routing["derived_contracts"][0]["network_required"] is False
    assert routing["derived_contracts"][0]["request_capability"] is False
    assert catalog["contract_versions"]["preferred_request_schema_version"] == "unified_market_evidence_request.v3"
    assert catalog["contract_versions"]["emitted_result_schema_version"] == "unified_market_evidence_result.v3"
    assert PREFERRED_REQUEST_SCHEMA_VERSION == "unified_market_evidence_request.v3"
    assert [tool.name for tool in build_tool_specs()] == [
        "market_describe_capabilities", "market_validate_request", "market_preview_request",
        "market_read_result", "market_export_ai_handoff", "market_fetch_evidence",
    ]


def test_no_scope_creep_tokens_in_v3_contract_authority():
    forbidden = ("moving_average", "rsi", "macd", "bollinger", "buy_signal", "sell_signal", "background_refresh", "automatic_backfill", "history_warehouse")
    paths = [SCHEMAS / name for name in V3_SCHEMAS.values()] + [DATA / "unified_market_evidence_capability_catalog.v3.json", DATA / "m8r_05b_capability_to_executor_routing_matrix.v3.json"]
    combined = "\n".join(path.read_text(encoding="utf-8").lower() for path in paths)
    for token in forbidden:
        assert re.search(rf"\b{re.escape(token)}\b", combined) is None

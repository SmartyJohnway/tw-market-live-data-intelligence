from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts.m8r_05b_03.component_artifact_roles import validate_operation_artifact_roles
from scripts.m8r_05c.errors import ProjectionError
from scripts.m8r_05c.trading_status_composer import (
    validate_component_artifact_bindings,
    validate_trading_status_context_composite,
)
from server.services.phase_j_b03_a2_6_composite_candidate import (
    ACCEPTANCE_AUTHORITY,
    SOURCE_PLAN,
    TARGET,
    make_candidate_adapter,
    validate_acceptance_authority,
)
from tests.helpers.phase_j_b03_a2_6_integrated import (
    fixture_responses,
    run_integrated_fixture,
)


def _composite(execution):
    path = next(item["relative_path"] for item in execution["outcomes"][0]["evidence_artifacts"]
                if item["artifact_role"] == "primary_evidence")
    return json.loads((execution["root"] / path).read_text(encoding="utf-8"))


def test_a26_c1_full_offline_controlled_pipeline_yields_composite_result_audit_handoff(tmp_path):
    execution = run_integrated_fixture(tmp_path / "c1")
    outcome = execution["outcomes"][0]
    composite = _composite(execution)
    assert outcome["schema_version"] == "unified_market_evidence_operation_result.v2"
    assert outcome["status"] == "succeeded" and outcome["error_code"] is None
    validate_operation_artifact_roles(outcome)
    assert [item["artifact_role"] for item in outcome["evidence_artifacts"]].count("primary_evidence") == 1
    assert [item["artifact_role"] for item in outcome["evidence_artifacts"]].count("component_evidence") == 3
    assert execution["receipt"]["schema_version"] == "unified_market_evidence_execution_receipt.v1"
    assert execution["bundle"]["schema_version"] == "unified_market_evidence_bundle.v1"
    assert execution["result"]["schema_version"] == "unified_market_evidence_result.v3"
    assert execution["audit"]["schema_version"] == "unified_market_evidence_audit_package.v3"
    assert composite["schema_version"] == "trading_status_context_composite.v1"
    assert composite["aggregate_coverage"]["covered_status_types"] == ["attention", "disposition"]
    assert composite["status"] == "partial"
    assert composite["canonical_item_count"] == 2
    assert composite["native_observation_count"] == 1
    projected = execution["result"]["targets"][0]["evidence"]["trading_status_context"]
    assert projected == composite
    assert execution["mode_c_result"]["external_market_network_executed"] is False
    assert execution["mode_c_handoff"]["additional_market_network_executed"] is False
    assert execution["mode_c_handoff"]["canonical_result"] == execution["result"]
    assert execution["mode_c_handoff"]["citation_references"]
    assert all(name in execution["handoff_markdown"] for name in ("TPEx Attention", "TPEx Disposition", "TPEx Current Special-Status Native Evidence"))
    assert "Ｙ" in execution["handoff_markdown"] and "unresolved" in execution["handoff_markdown"]
    assert "此原始值不可單獨解讀為停牌、停止交易或可／不可交易結論" in execution["handoff_markdown"]
    assert len(execution["response_log"]) == 3


def test_a26_c2_cmode_exact_no_match_survives_result_audit_and_handoff(tmp_path):
    responses = fixture_responses(cmode_rows=[{
        "Date": "1151007", "SecuritiesCompanyCode": "9999", "CompanyName": "other",
        "AlteredTrading": "", "PeriodicTrading": "", "ManagedStock": "",
        "MatchingFrequency": "", "SuspensionOfTrading": "", " FinancialAnnouncements": "",
    }])
    execution = run_integrated_fixture(tmp_path / "c2", responses=responses)
    composite = _composite(execution)
    cmode = composite["components"][2]["evidence"]
    assert cmode["status"] == "partial" and cmode["native_observations"] == []
    assert cmode["coverage"]["covered_status_types"] == []
    assert any(item.startswith("cmode_exact_no_match:") for item in cmode["caveats"])
    assert "no matching source row" in execution["handoff_markdown"].lower()
    assert "absence does not establish normal trading" in execution["handoff_markdown"].lower()
    assert composite["aggregate_coverage"]["covered_status_types"] == ["attention", "disposition"]


def test_a26_c3_disposition_multiple_rows_reach_result_audit_and_handoff(tmp_path):
    base = fixture_responses()["H1-TPEX-DISPOSITION-OPENAPI"]
    row = json.loads(base.raw_bytes.decode("utf-8"))[0]
    responses = fixture_responses(disposition_rows=[row, {**row, "Date": "1151006", "DispositionReasons": "second official reason"}])
    execution = run_integrated_fixture(tmp_path / "c3", responses=responses)
    composite = _composite(execution)
    disposition = composite["components"][1]["evidence"]
    assert len(disposition["items"]) == 2
    assert [item["source_record_date"] for item in disposition["items"]] == ["2026-09-21", "2026-10-06"]
    assert "second official reason" in execution["handoff_markdown"]
    audit_refs = execution["audit"]["phase_h_governance"]["evidence_artifact_references"]
    assert sum(item["schema_version"] == "trading_status_context_evidence.v1" for item in audit_refs) == 2


def test_a26_c4_disposition_failure_does_not_erase_attention_or_cmode(tmp_path):
    execution = run_integrated_fixture(tmp_path / "c4", failure_source_id="H1-TPEX-DISPOSITION-OPENAPI")
    composite = _composite(execution)
    assert execution["outcomes"][0]["status"] == "succeeded"
    assert [item["component_status"] for item in composite["components"]] == ["partial", "source_failed", "partial"]
    assert composite["aggregate_coverage"]["covered_status_types"] == ["attention"]
    assert composite["native_observation_count"] == 1
    audited_sources = {(item["source_family"], item["outcome"]) for item in execution["audit"]["phase_h_governance"]["source_attempts"]}
    assert ("TPEX_DISPOSITION_OPEN_DATA", "failed") in audited_sources
    assert len(audited_sources) == 3


def test_a26_c5_blank_cmode_value_remains_blank_and_unresolved(tmp_path):
    execution = run_integrated_fixture(tmp_path / "c5", responses=fixture_responses(cmode_value=""))
    observation = _composite(execution)["components"][2]["evidence"]["native_observations"][0]
    assert observation["source_native_value"] == ""
    assert observation["semantic_status"] == "unresolved"
    assert "do not infer not suspended" in observation["semantic_caveat"]
    assert '來源原始值**: `""`' in execution["handoff_markdown"]


def test_a26_c6_fullwidth_y_remains_native_and_never_promotes_suspension(tmp_path):
    execution = run_integrated_fixture(tmp_path / "c6")
    composite = _composite(execution)
    observation = composite["components"][2]["evidence"]["native_observations"][0]
    assert observation["source_native_value"] == "Ｙ"
    assert observation["source_native_value"].encode("utf-8").hex() == "efbcb9"
    assert "suspension" not in composite["aggregate_coverage"]["covered_status_types"]
    assert all(item["status_type"] != "suspension" for component in composite["components"] for item in component["evidence"]["items"])
    assert "Ｙ" in execution["handoff_markdown"]


def test_a26_c7_component_hash_mismatch_is_fail_closed(tmp_path):
    execution = run_integrated_fixture(tmp_path / "c7")
    composite = _composite(execution)
    artifacts = execution["inputs"].evidence_artifacts
    inventory = {item["relative_path"]: item for item in execution["bundle"]["artifact_inventory"]}
    first_path = composite["components"][0]["artifact_reference"]["relative_path"]
    inventory[first_path] = {**inventory[first_path], "sha256": "0" * 64}
    with pytest.raises(ProjectionError):
        validate_component_artifact_bindings(composite, artifacts, inventory)


def test_a26_c8_component_target_mismatch_is_fail_closed(tmp_path):
    execution = run_integrated_fixture(tmp_path / "c8")
    composite = deepcopy(_composite(execution))
    composite["components"][0]["evidence"]["target"]["canonical_target_id"] = "TPEX:9999"
    with pytest.raises(ProjectionError):
        validate_trading_status_context_composite(composite)


def test_a26_c9_component_source_identity_mismatch_is_fail_closed(tmp_path):
    execution = run_integrated_fixture(tmp_path / "c9")
    composite = deepcopy(_composite(execution))
    composite["components"][0]["evidence"]["source"]["source_family"] = "wrong-family"
    with pytest.raises(ProjectionError):
        validate_trading_status_context_composite(composite)


@pytest.mark.parametrize("mutation", ["order", "endpoint"])
def test_a26_c10_c11_authority_source_order_and_endpoint_substitution_rejected_before_fetch(mutation):
    authority = deepcopy(ACCEPTANCE_AUTHORITY)
    if mutation == "order":
        authority["ordered_sources"][0], authority["ordered_sources"][1] = authority["ordered_sources"][1], authority["ordered_sources"][0]
    else:
        authority["ordered_sources"][0]["endpoint"] = "https://example.invalid/market-data"
    fetched = []
    with pytest.raises(ValueError, match="a26_acceptance_authority_mismatch"):
        make_candidate_adapter(authority=authority, bound_plan_hash="x", response_provider=lambda source: fetched.append(source))
    assert fetched == []


def test_a26_c12_network_authorized_false_blocks_before_transport():
    fetched = []
    adapter = make_candidate_adapter(authority=ACCEPTANCE_AUTHORITY, bound_plan_hash="plan-hash",
                                     response_provider=lambda source: fetched.append(source))
    request = {"executor_id": "phase_j_j_b03_tpex_trading_status_composite_candidate",
               "capability_id": "trading_status_context", "market": "TPEX",
               "approved_security_identifiers": [TARGET["canonical_target_id"]],
               "plan_hash": "plan-hash", "network_authorized": False,
               "operation_id": "umeop-op-v1-aaaaaaaaaaaaaaaaaaaa", "execution_request_id": "x",
               "execution_request_hash": "y"}
    class Context:
        governed_output_root = "."
    with pytest.raises(ValueError, match="a26_network_not_authorized"):
        adapter(request, Context())
    assert fetched == []


def test_a26_c13_existing_attention_h1_v1_route_contract_unchanged():
    from tests.unit.test_phase_j_b03_a2_5_representative_adapters import _attention
    evidence = _attention()
    assert evidence["schema_version"] == "trading_status_context_evidence.v1"
    assert evidence["source"]["source_contract_id"] == "tpex_trading_warning_information"


def test_a26_authority_hash_is_bound_into_plan_and_operation_authorization(tmp_path):
    execution = run_integrated_fixture(tmp_path / "authority")
    operation = execution["plan"]["operations"][0]
    assert operation["parameters"]["acceptance_authority_sha256"] == execution["authority_hash"]
    assert execution["authorization"]["plan_hash"] == execution["plan"]["plan_hash"]
    assert execution["binding"]["plan_hash"] == execution["plan"]["plan_hash"]
    assert execution["preflight"]["bounded_execution_requests"][0]["plan_hash"] == execution["plan"]["plan_hash"]

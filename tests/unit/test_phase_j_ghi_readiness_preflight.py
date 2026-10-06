"""Mutation tests for the Phase J readiness record guardrails."""
import copy
import json

import pytest

from server.services.unified_local_service import describe_capabilities
from server.services.unified_mode_a import validate_mode_a_request
from scripts.validate_phase_j_ghi_readiness_preflight import RECORD, ROOT, validate, validate_record


@pytest.fixture
def inputs():
    record = json.loads(RECORD.read_text(encoding="utf-8"))
    closure = json.loads((ROOT / record["phase_i_closure"]["path"]).read_text(encoding="utf-8"))
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    return record, roadmap, closure


def test_current_record():
    result = validate()
    assert result["status"] == "PASS"
    assert (result["scenario_count"], result["blocker_count"], result["market_gets"]) == (27, 2, 0)


def test_conversational_groups_and_reclassification_preserved(inputs):
    record, _, _ = inputs
    assert [group["group_id"] for group in record["conversational_scenario_groups"]] == [f"J-C{i:02d}" for i in range(1, 9)]
    assert {row["scenario_id"] for row in record["golden_scenario_coverage_matrix"]} == {f"J1-{i:02d}" for i in range(1, 28)}
    assert {item["blocker_id"]: item["new_j_entry_blocker"] for item in record["reclassified_blockers"]} == {
        "J-B01": False, "J-B02": False, "J-B03": True, "J-B04": True}


@pytest.mark.parametrize("change", ["duplicate", "missing"])
def test_scenario_inventory_rejects_duplicate_or_missing(inputs, change):
    record, roadmap, closure = copy.deepcopy(inputs)
    if change == "duplicate":
        record["golden_scenario_coverage_matrix"][1]["scenario"] = record["golden_scenario_coverage_matrix"][0]["scenario"]
    else:
        record["golden_scenario_coverage_matrix"].pop()
    with pytest.raises(AssertionError):
        validate_record(record, roadmap, closure, 6)


def test_blocked_mandatory_scenario_prevents_pass(inputs):
    record, roadmap, closure = copy.deepcopy(inputs)
    record["final_disposition"] = "PHASE_J_READINESS_PREFLIGHT_PASS_READY_FOR_OWNER_J0_AUTHORIZATION"
    with pytest.raises(AssertionError):
        validate_record(record, roadmap, closure, 6)


def test_unchecked_g_h_do_not_themselves_block_pass(inputs):
    record, roadmap, closure = copy.deepcopy(inputs)
    record["j_blockers"] = []
    for row in record["golden_scenario_coverage_matrix"]:
        row.update(readiness_class="PRODUCTION_READY", runtime_readiness_class="PRODUCTION_READY",
                   j_entry_blocker=False, blocker_ids=[])
    for item in record["reclassified_blockers"]:
        item["new_j_entry_blocker"] = False
    record["final_disposition"] = "PHASE_J_READINESS_PREFLIGHT_PASS_READY_FOR_OWNER_J0_AUTHORIZATION"
    assert validate_record(record, roadmap, closure, 6)["status"] == "PASS"


def test_phase_j_checkbox_must_remain_unchecked(inputs):
    record, roadmap, closure = inputs
    with pytest.raises(AssertionError):
        validate_record(record, roadmap.replace("# [ ] Phase J", "# [x] Phase J"), closure, 6)


def test_market_gets_forbidden(inputs):
    record, roadmap, closure = copy.deepcopy(inputs)
    record["market_GETs"]["TWSE"] = 1
    with pytest.raises(AssertionError):
        validate_record(record, roadmap, closure, 6)


def test_mcp_tool_count_must_remain_six(inputs):
    with pytest.raises(AssertionError):
        validate_record(*inputs, 7)


@pytest.mark.parametrize("scenario_id", ["J1-08", "J1-10"])
def test_missing_runtime_can_be_nonblocking_when_safe_or_optional(inputs, scenario_id):
    record, roadmap, closure = inputs
    row = next(row for row in record["golden_scenario_coverage_matrix"] if row["scenario_id"] == scenario_id)
    assert row["runtime_readiness_class"] == "MISSING_REQUIRED_CAPABILITY"
    assert row["product_relevance_class"] in {"SAFE_FAIL_CLOSED_IS_SUFFICIENT", "OPTIONAL_EVIDENCE_NOT_J_BLOCKING"}
    assert row["j_entry_blocker"] is False
    assert validate_record(record, roadmap, closure, 6)["status"] == "PASS"


def test_financial_statement_need_is_described_as_absent_and_refused_before_execution(monkeypatch):
    import socket

    def deny_network(*_args, **_kwargs):
        raise AssertionError("market_network_forbidden")

    monkeypatch.setattr(socket.socket, "connect", deny_network)
    described = describe_capabilities()
    assert "financial_summary" not in {item["capability_id"] for item in described["capabilities"]}
    request = {
        "schema_version": "unified_market_evidence_request.v3",
        "request_id": "phase-j-financial-unsupported-offline",
        "execution_mode": "preview",
        "targets": [{"input": "2330", "market_hint": "TWSE"}],
        "data_needs": [{"type": "financial_summary", "priority": "optional"}],
    }
    result = validate_mode_a_request(request, allow_fixture_snapshot=True)
    assert result["validation_status"] == "invalid"
    assert any(issue["code"] == "REQUEST_SCHEMA_INVALID" for issue in result["blocking_issues"])


@pytest.mark.parametrize("scenario_id", ["J1-11", "J1-12", "J1-13", "J1-14", "J1-15", "J1-16"])
def test_unavailable_conversational_correctness_substrate_must_block(inputs, scenario_id):
    record, roadmap, closure = copy.deepcopy(inputs)
    row = next(row for row in record["golden_scenario_coverage_matrix"] if row["scenario_id"] == scenario_id)
    assert row["product_relevance_class"] == "MUST_HAVE_FOR_CONVERSATIONAL_J"
    row["j_entry_blocker"] = False
    row["blocker_ids"] = []
    with pytest.raises(AssertionError):
        validate_record(record, roadmap, closure, 6)


def test_optional_capability_cannot_be_a_j_entry_blocker(inputs):
    record, roadmap, closure = copy.deepcopy(inputs)
    row = next(row for row in record["golden_scenario_coverage_matrix"] if row["scenario_id"] == "J1-10")
    row["j_entry_blocker"] = True
    row["blocker_ids"] = ["J-B03"]
    with pytest.raises(AssertionError):
        validate_record(record, roadmap, closure, 6)


def test_safe_unresolved_correction_cannot_be_a_j_entry_blocker(inputs):
    record, roadmap, closure = copy.deepcopy(inputs)
    row = next(row for row in record["golden_scenario_coverage_matrix"] if row["scenario_id"] == "J1-08")
    row["j_entry_blocker"] = True
    row["blocker_ids"] = ["J-B03"]
    with pytest.raises(AssertionError):
        validate_record(record, roadmap, closure, 6)


def test_phase_j_stays_not_started_while_blockers_remain(inputs):
    record, roadmap, closure = copy.deepcopy(inputs)
    record["phase_j_started"] = True
    with pytest.raises(AssertionError):
        validate_record(record, roadmap, closure, 6)


def test_two_gap_realignment_cannot_revert_to_generic_hold(inputs):
    record, roadmap, closure = copy.deepcopy(inputs)
    record["final_disposition"] = "PHASE_J_READINESS_PREFLIGHT_HOLD_FOR_BOUNDED_PREDECESSOR_GAPS"
    with pytest.raises(AssertionError):
        validate_record(record, roadmap, closure, 6)


def test_every_j1_scenario_must_map_to_a_conversation_group(inputs):
    record, roadmap, closure = copy.deepcopy(inputs)
    for group in record["conversational_scenario_groups"]:
        group["scenario_ids"] = [scenario_id for scenario_id in group["scenario_ids"] if scenario_id != "J1-27"]
    with pytest.raises(AssertionError):
        validate_record(record, roadmap, closure, 6)


def test_original_preflight_tree_provenance_is_fixed(inputs):
    record, roadmap, closure = copy.deepcopy(inputs)
    record["original_preflight"]["tree"] = "0" * 40
    with pytest.raises(AssertionError):
        validate_record(record, roadmap, closure, 6)

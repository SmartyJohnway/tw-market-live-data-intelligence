"""Mutation tests for the Phase J readiness record guardrails."""
import copy
import json

import pytest

from scripts.validate_phase_j_ghi_readiness_preflight import RECORD, ROOT, validate, validate_record


@pytest.fixture
def inputs():
    record = json.loads(RECORD.read_text(encoding="utf-8"))
    closure = json.loads((ROOT / record["phase_i_closure"]["path"]).read_text(encoding="utf-8"))
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    return record, roadmap, closure


def check(inputs):
    return validate_record(*inputs, 6)


def test_current_record():
    assert validate()["status"] == "PASS"


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
        row.update(readiness_class="PRODUCTION_READY", j_entry_blocker=False, blocker_ids=[])
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

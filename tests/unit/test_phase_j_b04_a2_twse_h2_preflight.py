"""Mutation and repository-authority tests for J-B04-A2."""
from __future__ import annotations

import copy
import json

import pytest

from scripts.validate_phase_j_b04_a2_twse_h2_preflight import RECORD, validate, validate_contract


def _record():
    return json.loads(RECORD.read_text(encoding="utf-8"))


def test_current_a2_decision_matches_repository_authorities():
    assert validate() == {
        "status": "PASS",
        "gate": "J-B04-A2",
        "h2": "INACTIVE",
        "h3_twse": "ACTIVE",
        "market_requests": 0,
    }


@pytest.mark.parametrize(
    ("mutate", "reason"),
    [
        (lambda d: d["machine_assertions"].__setitem__("representative_market", "TPEX"), "TWSE remains the representative market"),
        (lambda d: d["machine_assertions"].__setitem__("twt49u_activation_required", True), "optional TWT49U is not mandatory"),
        (lambda d: d["temporal_coverage"].__setitem__("declared_scope_complete_for_twt48u_default", True), "current TWT48U does not prove historical completeness"),
        (lambda d: d["temporal_coverage"].__setitem__("no_row_proves_no_event_across_h3_window", True), "current no-row is not historical no-event"),
        (lambda d: d["temporal_coverage"].__setitem__("h2_network_query_uses_h3_window", True), "H3 dates are not H2 query parameters"),
        (lambda d: d["temporal_coverage"].__setitem__("prohibited_window_sources", []), "plan-time and guessed windows remain prohibited"),
        (lambda d: d["machine_assertions"].__setitem__("scheduled_may_be_promoted_to_effective", True), "preannouncement cannot be promoted"),
        (lambda d: d["machine_assertions"].__setitem__("final_reference_may_be_locally_calculated", True), "reference price cannot be calculated locally"),
        (lambda d: d["execution_contract"].__setitem__("h2_retry_count", 1), "H2 retry remains zero"),
        (lambda d: d["execution_contract"].__setitem__("max_h2_market_gets_per_execution", 2), "H2 source call bound is one GET"),
        (lambda d: d["execution_contract"].__setitem__("hidden_h2_acquisition_allowed", True), "H2 must be previewed and authorized"),
        (lambda d: d["execution_contract"].__setitem__("polling", True), "polling is prohibited"),
        (lambda d: d["execution_contract"].__setitem__("history_accumulation_allowed", True), "local history accumulation is prohibited"),
        (lambda d: d["scope_and_network"].__setitem__("h2_runtime_after_a2", "ACTIVE"), "A2 cannot activate H2"),
        (lambda d: d["scope_and_network"].__setitem__("j_b04_after_a2", "CLOSED"), "A2 cannot close J-B04"),
        (lambda d: d["scope_and_network"].__setitem__("phase_j_after_a2", "STARTED"), "A2 cannot start Phase J"),
        (lambda d: d["scope_and_network"].__setitem__("mcp_tool_count", 7), "MCP remains six tools"),
        (lambda d: d["scope_and_network"].__setitem__("market_GETs", 1), "A2 performs no market GET"),
        (lambda d: d["source_decision"]["source_cardinality"].__setitem__("decision", "ASSUME_UNIQUE_CODE"), "ambiguous rows remain fail-closed"),
        (lambda d: d["h3_preconditions"]["no_usable_available_baseline"].__setitem__("behavior", "Guess dates from today"), "H3 failure cannot invent a window"),
        (lambda d: d["h4_reconciliation"]["state_precedence"].reverse(), "H4 failure/uncovered precedence remains frozen"),
    ],
)
def test_false_a2_mutations_are_rejected(mutate, reason):
    record = copy.deepcopy(_record())
    mutate(record)
    with pytest.raises((AssertionError, KeyError)):
        validate_contract(record)


def test_file_inventory_protects_frozen_schemas_and_h4():
    record = _record()
    inventory = {item["path"]: item["classification"] for item in record["future_implementation_file_inventory"]}
    assert inventory["schemas/corporate_action_context_evidence.v1.schema.json"] == "MUST NOT MODIFY"
    assert inventory["schemas/discontinuity_safety_evidence.v1.schema.json"] == "MUST NOT MODIFY"
    assert inventory["server/services/phase_h_discontinuity_safety.py"] == "MUST NOT MODIFY"

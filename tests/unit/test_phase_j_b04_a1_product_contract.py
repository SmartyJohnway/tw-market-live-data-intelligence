"""Mutation and current-authority checks for the J-B04-A1 product freeze."""
from __future__ import annotations

import copy
import json

import pytest

from scripts.validate_phase_j_b04_a1_product_contract import RECORD, validate, validate_contract


def _record():
    return json.loads(RECORD.read_text(encoding="utf-8"))


def test_current_contract_matches_repository_authorities():
    assert validate() == {
        "status": "PASS",
        "contract": "J-B04-A1",
        "h2": "INACTIVE",
        "h3_twse": "ACTIVE",
        "h3_tpex": "BLOCKED",
        "market_requests": 0,
    }


@pytest.mark.parametrize(
    ("mutate", "path"),
    [
        (lambda d: d["product_exit_contract"].__setitem__("complete_h2_required_for_j_b04_closure", True), "complete H2 cannot become required"),
        (lambda d: d["product_exit_contract"].__setitem__("representative_market", "TPEX"), "market cannot silently change"),
        (lambda d: d["product_exit_contract"]["subtype_boundaries"].__setitem__("capital_reduction_source_gap_closed", True), "capital-reduction gap remains open"),
        (lambda d: d["product_exit_contract"]["event_and_coverage_semantics"].__setitem__("ordinary_return_interpretation_when_coverage_incomplete", "allowed"), "incomplete coverage blocks ordinary return interpretation"),
        (lambda d: d["product_exit_contract"]["event_and_coverage_semantics"].__setitem__("final_reference_required_for_all_j_b04_closure_paths", True), "final reference is not universally required"),
        (lambda d: d["product_exit_contract"]["event_and_coverage_semantics"].__setitem__("local_adjustment_allowed", True), "local adjustment is prohibited"),
        (lambda d: d["future_j_b04_exit_criteria"].__setitem__("reference_unavailable_state_may_be_proved_by_deterministic_fixture", False), "reference-unavailable H4 state may use a governed fixture"),
        (lambda d: d["future_j_b04_exit_criteria"].__setitem__("bounded_live_h2_must_encounter_effective_event", True), "bounded-live H2 does not require an effective event"),
        (lambda d: d["post_a1_state"].__setitem__("H2 runtime", "ACTIVE"), "A1 cannot activate H2"),
        (lambda d: d["post_a1_state"].__setitem__("J-B04", "CLOSED"), "A1 cannot close J-B04"),
        (lambda d: d["post_a1_state"].__setitem__("Phase J", "STARTED"), "A1 cannot start Phase J"),
        (lambda d: d["post_a1_state"].__setitem__("MCP", 7), "MCP remains six tools"),
        (lambda d: d["scope_and_network"].__setitem__("market_GETs", 1), "A1 performs no market requests"),
    ],
)
def test_false_contract_mutations_are_rejected(mutate, path):
    record = copy.deepcopy(_record())
    mutate(record)
    with pytest.raises(AssertionError):
        validate_contract(record)

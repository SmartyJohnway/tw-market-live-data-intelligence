from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.phase_j_j0_j1_semantic_harness import evaluate_scenario
from scripts.validate_phase_j_j0_j1_scenario_registry import (
    _validate_authority_roles,
    _validate_coverage_cell,
    _validate_current_semantics,
)


ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "docs/governance/phase_j/PHASE_J_J0_J1_GOVERNED_SCENARIO_REGISTRY_V1.json"
FIXTURE_PATH = ROOT / "tests/fixtures/phase_j/j0_j1_semantic_fixtures.json"


@pytest.fixture(scope="module")
def registry():
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def fixture_cases():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_synthetic_j0_j1_cases_satisfy_registered_semantics(registry, fixture_cases):
    scenarios = {row["scenario_id"]: row for row in registry["scenarios"]}
    assert len(fixture_cases) >= 12
    for fixture in fixture_cases:
        checked = evaluate_scenario(scenarios[fixture["scenario_id"]], fixture)
        assert checked


def test_harness_rejects_result_audit_lineage_mismatch(registry, fixture_cases):
    fixture = json.loads(json.dumps(fixture_cases[0]))
    fixture["audit_v3"]["result_id"] = "different-result"
    scenario = next(row for row in registry["scenarios"] if row["scenario_id"] == fixture["scenario_id"])
    with pytest.raises(AssertionError, match="identity mismatch"):
        evaluate_scenario(scenario, fixture)


def test_harness_rejects_semantic_violation(registry, fixture_cases):
    fixture = json.loads(json.dumps(fixture_cases[0]))
    fixture["semantic_facts"]["no_trade_action"] = False
    scenario = next(row for row in registry["scenarios"] if row["scenario_id"] == fixture["scenario_id"])
    with pytest.raises(AssertionError, match="no_trading_action"):
        evaluate_scenario(scenario, fixture)


def test_harness_rejects_forbidden_handoff_claim(registry, fixture_cases):
    fixture = json.loads(json.dumps(fixture_cases[0]))
    fixture["handoff"] += " BUY/SELL INSTRUCTION: buy now."
    scenario = next(row for row in registry["scenarios"] if row["scenario_id"] == fixture["scenario_id"])
    with pytest.raises(AssertionError, match="forbidden handoff claim"):
        evaluate_scenario(scenario, fixture)


def test_harness_rejects_unlabeled_or_live_fixture(registry, fixture_cases):
    fixture = json.loads(json.dumps(fixture_cases[0]))
    fixture["fixture_kind"] = "live_market_capture"
    scenario = next(row for row in registry["scenarios"] if row["scenario_id"] == fixture["scenario_id"])
    with pytest.raises(AssertionError, match="fixture must identify"):
        evaluate_scenario(scenario, fixture)


def test_harness_requires_citation_and_lineage_for_evidence_bearing_case(registry, fixture_cases):
    fixture = json.loads(json.dumps(next(item for item in fixture_cases if item["scenario_id"] == "J1-01")))
    fixture["semantic_facts"]["citation_present"] = False
    scenario = next(row for row in registry["scenarios"] if row["scenario_id"] == fixture["scenario_id"])
    with pytest.raises(AssertionError, match="lacks a citation"):
        evaluate_scenario(scenario, fixture)


def test_network_free_registry_validator_passes():
    result = subprocess.run(
        [sys.executable, "scripts/validate_phase_j_j0_j1_scenario_registry.py"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert '"status": "PASS"' in result.stdout


def test_current_semantics_are_separate_from_historical_readiness(registry):
    rows = {row["scenario_id"]: row for row in registry["scenarios"]}
    ex_right = rows["J1-14"]
    assert ex_right["current_purpose"] == ex_right["purpose"]
    assert ex_right["current_semantic_state"]["accepted_routes"] == ["phase_h_h2_twse_exright_pre_executor"]
    assert ex_right["historical_readiness_summary"]["preflight_reason"]
    assert ex_right["historical_readiness_summary"]["prior_candidate_purpose"] != ex_right["current_purpose"]
    _validate_current_semantics(ex_right)

    contradictory = json.loads(json.dumps(ex_right))
    contradictory["current_semantic_state"]["accepted_routes"] = []
    with pytest.raises(ValueError, match="exact accepted H2 route missing"):
        _validate_current_semantics(contradictory)
    stale_current = json.loads(json.dumps(ex_right))
    stale_current["purpose"] = stale_current["historical_readiness_summary"]["prior_candidate_purpose"]
    with pytest.raises(ValueError, match="purpose must state current semantics"):
        _validate_current_semantics(stale_current)


def test_j1_11_keeps_representative_scope_partial(registry):
    row = next(item for item in registry["scenarios"] if item["scenario_id"] == "J1-11")
    assert row["current_semantic_state"]["capability_state"] == "partial"
    assert row["current_semantic_state"]["accepted_routes"] == ["phase_h_h1_tpex_composite_executor"]
    assert row["current_semantic_state"]["complete_family_support_claimed"] is False
    _validate_current_semantics(row)


def test_j_b03_authority_cannot_be_misbound_to_j_b04_review(registry):
    rows = {row["scenario_id"]: row for row in registry["scenarios"]}
    _validate_authority_roles(rows["J1-11"])
    _validate_authority_roles(rows["J1-12"])
    _validate_authority_roles(rows["J1-14"])

    wrong = json.loads(json.dumps(rows["J1-11"]))
    wrong["superseding_authority_refs"][0]["review_id"] = "5479527453"
    with pytest.raises(ValueError, match="J-B04 review misbound"):
        _validate_authority_roles(wrong)

    missing = json.loads(json.dumps(rows["J1-11"]))
    missing["superseding_authority_refs"] = []
    with pytest.raises(ValueError, match="canonical J-B03 closure authority missing"):
        _validate_authority_roles(missing)


@pytest.mark.parametrize("kind", ["contract_authority", "routing_authority", "unit_test"])
def test_non_integration_evidence_cannot_launder_integration_coverage(kind):
    cell = {
        "status": "COVERED_EXISTING",
        "evidence_refs": [{
            "ref": {
                "contract_authority": "docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json",
                "routing_authority": "docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json",
                "unit_test": "tests/unit/test_phase_j_j0_j1_scenario_registry.py",
            }[kind],
            "kind": kind,
            "scenario_match": "Only supporting contract/unit evidence.",
        }],
    }
    with pytest.raises(ValueError, match="does not prove this layer"):
        _validate_coverage_cell("J1-01", "integration", cell)


def test_integration_test_qualifies_and_global_baseline_does_not_promote_scenario():
    ref = "tests/integration/test_phase_h_imp_7d_deterministic_e2e.py"
    _validate_coverage_cell("J1-03", "integration", {
        "status": "COVERED_EXISTING",
        "evidence_refs": [{"ref": ref, "kind": "integration_test", "scenario_match": "S2 exact multi-target partial outcome assertion."}],
    })
    registry_data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    matrix_path = ROOT / "docs/governance/phase_j/PHASE_J_J0_J1_COVERAGE_MATRIX_V1.json"
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    assert any(item["layer"] == "integration" and item["status"] == "COVERED_EXISTING" for item in matrix["layer_baselines"])
    assert next(row for row in matrix["scenarios"] if row["scenario_id"] == "J1-01")["layers"]["integration"]["status"] == "PLANNED"
    assert len(registry_data["scenarios"]) == 27


def test_accepted_exact_e2e_qualifies_integration_but_requires_scenario_match():
    _validate_coverage_cell("J1-16", "integration", {
        "status": "COVERED_EXISTING",
        "evidence_refs": [{
            "ref": "docs/governance/phase_j/PHASE_J_J_B04_A6_R2_TRANSPORT_LEDGER_VALIDATOR_REPAIR_AND_LIVE_REACCEPTANCE_2026-10-10.json",
            "kind": "e2e_acceptance",
            "scenario_match": "Integrated A6-R2 proves H4 incomplete coverage blocks ordinary-return interpretation.",
        }],
    })
    with pytest.raises(ValueError, match="scenario-level evidence match missing"):
        _validate_coverage_cell("J1-16", "integration", {
            "status": "COVERED_EXISTING",
            "evidence_refs": [{
                "ref": "docs/governance/phase_j/PHASE_J_J_B04_A6_R2_TRANSPORT_LEDGER_VALIDATOR_REPAIR_AND_LIVE_REACCEPTANCE_2026-10-10.json",
                "kind": "e2e_acceptance",
            }],
        })

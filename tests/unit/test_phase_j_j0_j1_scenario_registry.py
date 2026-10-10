from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.phase_j_j0_j1_semantic_harness import evaluate_scenario


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

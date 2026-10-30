from __future__ import annotations

import json
from pathlib import Path

import scripts.run_test_profile as rtp
from scripts.validate_test_governance_tg5 import validate_static


ROOT = Path(__file__).resolve().parents[2]


def test_tg5_static_cutover_contract_passes() -> None:
    result = validate_static()
    assert result == {
        "status": "PASS",
        "new_default_file_count": 93,
        "rollback_file_count": 156,
        "new_default_matches_historical_tg2_candidate": True,
        "rollback_execution_semantics_preserved": True,
        "tg4_unexplained_nodes": 0,
        "tg5_authority_state": "PROMOTED_ACTIVE",
        "tg2_semantic_manifest_current_authority": False,
        "phase_i_implementation": False,
    }


def test_tg5_default_and_rollback_profiles_both_resolve() -> None:
    for name in ("default-ci", "pre-tg5-default-ci"):
        commands = rtp.resolve_profile(name)
        assert commands
        assert all(command[0] for command in commands)


def test_tg5_frozen_evidence_preserves_cutover_identities_and_counts() -> None:
    folder = ROOT / "docs/governance/test_governance"
    ledger = json.loads((folder / "TG5_ACCEPTANCE_LEDGER_2026-09-23.json").read_text())
    rollback = json.loads((folder / "TG5_ROLLBACK_CONTRACT_2026-09-23.json").read_text())
    assert ledger["baseline_main"] == "2ff9707d901f40c1a108dd1317fce2f03cc79735"
    assert ledger["workflow"]["run_id"] == 35839936603
    assert ledger["promoted_default"]["file_paths"] == 93
    assert ledger["promoted_default"]["selected_nodes"] == 778
    assert ledger["lifecycle"]["full_current_selected_nodes"] == 1150
    assert ledger["lifecycle"]["historical_selected_nodes"] == 94
    assert ledger["lifecycle"]["release_selected_nodes"] == 5
    assert rollback["expected_node_counts"]["old_default_selected"] == 1245
    assert len(rollback["old_default_profile"]["pytest_paths"]) == 156
    assert ledger["containment"]["tests_deleted"] is False
    assert ledger["containment"]["phase_i_implementation"] is False

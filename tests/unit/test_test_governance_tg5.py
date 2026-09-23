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


def test_tg5_authority_manifest_separates_every_pr_and_lifecycle_profiles() -> None:
    authority = json.loads(
        (ROOT / "config/test_governance_authority.json").read_text(encoding="utf-8")
    )
    assert authority["authority_role"] == "CURRENT_ACTIVE_MACHINE_AUTHORITY"
    assert authority["state"] == "TG5_PROMOTED_ACTIVE"
    assert authority["current_authority_commit"] == "db3340da61ea6e1f3391cfc1728d42b5376157c7"
    assert authority["current_merge_authority"]["expected_file_paths"] == 93
    assert authority["current_merge_authority"]["expected_selected_nodes"] == 778
    assert authority["lifecycle_regression"]["broad_current_expected_nodes"] == 1150
    assert authority["lifecycle_regression"]["historical_expected_nodes"] == 94
    assert authority["lifecycle_regression"]["release_expected_nodes"] == 5
    assert authority["lifecycle_regression"]["mixed_historical_expected_nodes"] == 4
    assert authority["lifecycle_regression"]["broad_current_profile"] == "full-current"
    assert authority["lifecycle_regression"]["historical_profile"] == "historical-milestone-replay"
    assert authority["lifecycle_regression"]["release_profile"] == "release-preflight-current"
    assert authority["lifecycle_regression"]["mixed_historical_profile"] == "mixed-historical-diagnostic"
    assert authority["rollback"]["diagnostic_profile"] == "pre-tg5-default-ci"
    assert authority["rollback"]["authoritative_baseline_commit"] == "2ff9707d901f40c1a108dd1317fce2f03cc79735"
    history = authority["historical_migration_evidence"]["tg2_semantic_manifest"]
    assert history["classification"] == "HISTORICAL_MIGRATION_EVIDENCE"
    assert history["current_authority"] is False
    assert history["preserve_historical_facts"] is True
    assert authority["source_evidence"]["tg5_workflow_run_id"] == 35839936603
    assert authority["invariants"]["tests_deleted"] is False
    assert authority["invariants"]["phase_i_implementation"] is False

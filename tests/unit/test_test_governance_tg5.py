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
        "new_default_matches_tg2_shadow": True,
        "rollback_execution_semantics_preserved": True,
        "tg4_unexplained_nodes": 0,
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
    assert authority["current_merge_authority"]["expected_selected_nodes"] == 778
    assert authority["lifecycle_regression"]["broad_current_expected_nodes"] == 1150
    assert authority["lifecycle_regression"]["historical_expected_nodes"] == 94
    assert authority["lifecycle_regression"]["release_expected_nodes"] == 5
    assert authority["lifecycle_regression"]["mixed_historical_expected_nodes"] == 4
    assert authority["lifecycle_regression"]["broad_current_profile"] == "tg2-full-current-non-network-shadow"
    assert authority["lifecycle_regression"]["historical_profile"] == "tg2-historical-acceptance-shadow"
    assert authority["lifecycle_regression"]["release_profile"] == "tg2-release-preflight-shadow"
    assert authority["rollback"]["profile"] == "pre-tg5-default-ci"
    assert authority["invariants"]["tests_deleted"] is False
    assert authority["invariants"]["phase_i_implementation"] is False

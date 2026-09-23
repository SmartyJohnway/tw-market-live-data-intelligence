#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILES = ROOT / "config/test_execution_profiles.json"
AUTHORITY = ROOT / "config/test_governance_authority.json"
ROLLBACK = ROOT / "docs/governance/test_governance/TG5_ROLLBACK_CONTRACT_2026-09-23.json"
TG4 = ROOT / "docs/governance/test_governance/TG4_ACCEPTANCE_LEDGER_2026-09-23.json"

EXPECTED_EXPR = (
    "not network and not browser and not live and not release_preflight "
    "and not historical and not performance"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_static() -> dict:
    profiles = _load(PROFILES)["profiles"]
    authority = _load(AUTHORITY)
    rollback = _load(ROLLBACK)
    tg4 = _load(TG4)

    new_default = profiles["default-ci"]
    old_rehearsal = profiles["pre-tg5-default-ci"]
    tg2_current = profiles["tg2-default-ci-current-shadow"]

    assert new_default == rollback["candidate_default_profile"]
    assert new_default["pytest_expression"] == EXPECTED_EXPR
    assert new_default["automatic_ci_allowed"] is True
    assert len(new_default["pytest_paths"]) == 93
    assert new_default["pytest_paths"] == tg2_current["pytest_paths"]

    old_contract = rollback["old_default_profile"]
    assert len(old_contract["pytest_paths"]) == 156
    assert old_contract["pytest_expression"] == EXPECTED_EXPR
    assert old_rehearsal["pytest_paths"] == old_contract["pytest_paths"]
    assert old_rehearsal["pytest_expression"] == old_contract["pytest_expression"]
    assert old_rehearsal["automatic_ci_allowed"] is False

    # Deterministic rollback means replacing only the default profile body.
    restored = dict(profiles)
    restored["default-ci"] = old_contract
    assert restored["default-ci"] == old_contract

    assert authority["state"] == "TG5_CUTOVER_CANDIDATE"
    assert authority["current_merge_authority"]["profile"] == "default-ci"
    assert authority["current_merge_authority"]["expected_file_paths"] == 93
    assert authority["current_merge_authority"]["expected_selected_nodes"] == 778
    assert authority["rollback"]["expected_file_paths"] == 156
    assert authority["rollback"]["expected_selected_nodes"] == 1245

    assert tg4["status"] == "TG4_SHADOW_CI_PASS"
    assert tg4["node_analysis"]["legacy_layer_counts"]["unexplained"] == 0
    assert tg4["interpretation"]["shadow_protection_gap"] == "NONE_UNEXPLAINED"

    for name in (
        "tg2-full-current-non-network-shadow",
        "tg2-historical-acceptance-shadow",
        "tg2-release-preflight-shadow",
        "tg4-mixed-historical-shadow",
        "pre-tg5-default-ci",
    ):
        assert profiles[name]["automatic_ci_allowed"] is False

    for path in set(new_default["pytest_paths"]) | set(old_contract["pytest_paths"]):
        assert (ROOT / path).exists(), path

    return {
        "status": "PASS",
        "new_default_file_count": len(new_default["pytest_paths"]),
        "rollback_file_count": len(old_contract["pytest_paths"]),
        "new_default_matches_tg2_shadow": True,
        "rollback_execution_semantics_preserved": True,
        "tg4_unexplained_nodes": 0,
        "phase_i_implementation": False,
    }


if __name__ == "__main__":
    print(json.dumps(validate_static(), indent=2, sort_keys=True))

from __future__ import annotations

import json
from pathlib import Path

from scripts.validate_test_governance_tg2_tg3 import validate


ROOT = Path(__file__).resolve().parents[2]


def test_tg2_tg3_validator_passes_and_preserves_default_authority() -> None:
    result = validate()
    assert result["status"] == "PASS"
    assert result["source_pre_tg5_default_file_count"] == 156
    assert result["current_default_ci_file_count"] == 93
    assert result["current_candidate_count"] == 91
    assert result["mixed_count"] == 2
    assert result["full_current_nondefault_count"] == 46
    assert result["historical_candidate_count"] == 15
    assert result["release_candidate_count"] == 2
    assert result["default_ci_authority_changed"] is True
    assert result["tg5_cutover_candidate"] is True
    assert result["historical_tg2_sets_reproduced_by_current_profiles"] is True
    assert result["tg3_full_reproduction_retained"] is True


def test_tg2_historical_shadow_sets_map_to_stable_current_profiles() -> None:
    profiles = json.loads(
        (ROOT / "config/test_execution_profiles.json").read_text(encoding="utf-8")
    )["profiles"]

    stable = {
        "default-ci": 93,
        "full-current": 139,
        "historical-milestone-replay": 15,
        "release-preflight-current": 2,
        "mixed-historical-diagnostic": 2,
    }
    migration_names = {
        "tg2-default-ci-current-shadow",
        "tg2-full-current-non-network-shadow",
        "tg2-historical-acceptance-shadow",
        "tg2-release-preflight-shadow",
        "tg4-mixed-historical-shadow",
    }
    assert migration_names.isdisjoint(profiles)
    for name, count in stable.items():
        assert name in profiles
        assert len(profiles[name]["pytest_paths"]) == count
    assert profiles["default-ci"]["automatic_ci_allowed"] is True
    for name in stable.keys() - {"default-ci"}:
        assert profiles[name]["automatic_ci_allowed"] is False


def test_tg3_manifest_does_not_authorize_historical_removal() -> None:
    manifest = json.loads(
        (
            ROOT
            / "docs/governance/test_governance/HISTORICAL_EVIDENCE_INTEGRITY_MANIFEST.v1.json"
        ).read_text(encoding="utf-8")
    )
    assert manifest["replacement_for_tg4_shadow_ci"] is False
    assert manifest["historical_tests_deleted"] is False
    for item in manifest["entries"]:
        assert item["default_ci_removal_authorized"] is False
        assert item["manual_reproduction_profile"] == "tg2-historical-acceptance-shadow"

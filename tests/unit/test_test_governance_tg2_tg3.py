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
    assert result["tg2_shadow_profiles_automatic_ci_allowed"] is False
    assert result["tg3_full_reproduction_retained"] is True


def test_tg2_shadow_profiles_are_additive_and_manual_only() -> None:
    profiles = json.loads(
        (ROOT / "config/test_execution_profiles.json").read_text(encoding="utf-8")
    )["profiles"]

    expected = {
        "tg2-default-ci-current-shadow": 93,
        "tg2-full-current-non-network-shadow": 139,
        "tg2-historical-acceptance-shadow": 15,
        "tg2-release-preflight-shadow": 2,
    }
    for name, count in expected.items():
        assert name in profiles
        assert len(profiles[name]["pytest_paths"]) == count
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

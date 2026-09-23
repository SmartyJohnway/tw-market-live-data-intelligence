from __future__ import annotations

import json
from pathlib import Path

from scripts.validate_test_governance_tg4_shadow import validate_profile_config


ROOT = Path(__file__).resolve().parents[2]


def test_tg4_profile_config_changes_only_shadow_authority() -> None:
    result = validate_profile_config()
    assert result == {
        "default_ci_unchanged": True,
        "only_expected_shadow_profile_delta": True,
    }


def test_tg4_known_historical_gaps_are_exact_and_not_tg5_authority() -> None:
    payload = json.loads(
        (
            ROOT
            / "docs/governance/test_governance/TG4_KNOWN_HISTORICAL_REPLAY_GAPS.v1.json"
        ).read_text(encoding="utf-8")
    )
    assert payload["current_default_ci_affected"] is False
    assert payload["tg5_authorized"] is False
    assert len(payload["allowed_failed_nodes"]) == 2
    assert len(payload["expected_additional_historical_nodes"]) == 8
    assert all(
        item["node_id"].startswith(
            "tests/unit/test_m8r_06_04_mode_c.py::test_existing_"
        )
        for item in payload["allowed_failed_nodes"]
    )

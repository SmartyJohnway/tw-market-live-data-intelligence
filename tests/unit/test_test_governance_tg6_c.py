from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

import scripts.run_test_profile as rtp
from scripts.analyze_test_governance_tg4_nodes import analyze


ROOT = Path(__file__).resolve().parents[2]

ALIASES = {
    "tg2-default-ci-current-shadow": "default-ci",
    "tg2-full-current-non-network-shadow": "full-current",
    "tg2-historical-acceptance-shadow": "historical-milestone-replay",
    "tg2-release-preflight-shadow": "release-preflight-current",
    "tg4-mixed-historical-shadow": "mixed-historical-diagnostic",
}


def test_tg6_c_current_config_uses_only_stable_lifecycle_names() -> None:
    profiles = rtp.load_config()["profiles"]
    assert {
        "default-ci",
        "full-current",
        "historical-milestone-replay",
        "release-preflight-current",
        "mixed-historical-diagnostic",
        "pre-tg5-default-ci",
    } <= set(profiles)
    assert set(ALIASES).isdisjoint(profiles)
    assert rtp.DEPRECATED_PROFILE_ALIASES == ALIASES


@pytest.mark.parametrize(("legacy", "stable"), sorted(ALIASES.items()))
def test_tg6_c_deprecated_aliases_resolve_exactly(legacy: str, stable: str) -> None:
    assert rtp.resolve_profile_name(legacy) == stable
    assert rtp.resolve_profile(legacy) == rtp.resolve_profile(stable)


def test_tg6_c_alias_json_reports_requested_and_resolved_profile(monkeypatch, capsys) -> None:
    def fake_run(cmd, cwd, text, stdout, stderr):
        return subprocess.CompletedProcess(
            cmd,
            0,
            "============================= test session starts ==============================\n"
            "collected 1 item\n\n"
            "tests/unit/test_x.py .\n"
            "============================== 1 passed in 0.01s ===============================\n",
        )

    monkeypatch.setattr(rtp.subprocess, "run", fake_run)
    assert rtp.main(["tg2-full-current-non-network-shadow", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["profile"] == "tg2-full-current-non-network-shadow"
    assert payload["resolved_profile"] == "full-current"


def test_tg6_c_real_collection_preserves_exact_lifecycle_node_counts() -> None:
    result = analyze()
    assert result["legacy_node_count"] == 1245
    assert result["current_default_node_count"] == 778
    assert result["full_current_node_count"] == 1150
    assert result["historical_milestone_replay_node_count"] == 94
    assert result["release_preflight_current_node_count"] == 5
    assert result["mixed_historical_diagnostic_node_count"] == 4
    assert result["legacy_missing_from_layered_count"] == 0
    assert result["legacy_unexplained"] == []

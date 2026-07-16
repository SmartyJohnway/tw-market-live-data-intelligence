from __future__ import annotations

import json
from pathlib import Path

import scripts.validate_github_actions_execution_policy as validator

ROOT = Path(__file__).resolve().parents[2]


def test_ci_policy_validator_accepts_repository_workflows():
    result = validator.validate()
    assert result["status"] == "passed", result["violations"]
    assert result["policy_id"] == "CI_POLICY_V1"
    assert result["workflow_count"] == 5


def test_testing_workflows_are_manual_or_published_release_only():
    result = validator.validate()
    trigger_sets = {item["name"]: set(item["triggers"]) for item in result["workflows"]}
    assert trigger_sets["Default CI"] == {"workflow_dispatch"}
    assert trigger_sets["Full Non-Network Regression"] == {"workflow_dispatch"}
    assert trigger_sets["Windows Compatibility Smoke"] == {"workflow_dispatch"}
    assert trigger_sets["Browser Operator E2E"] == {"workflow_dispatch"}
    assert trigger_sets["Release Validation"] == {"workflow_dispatch", "release"}


def test_policy_keeps_historical_and_performance_profiles_manual():
    profiles = json.loads((ROOT / "config/test_execution_profiles.json").read_text())["profiles"]
    assert profiles["historical-acceptance"]["automatic_ci_allowed"] is False
    assert profiles["performance"]["automatic_ci_allowed"] is False

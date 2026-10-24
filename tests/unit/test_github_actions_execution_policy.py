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


def test_workflows_follow_prepublication_and_label_opt_in_policy():
    result = validator.validate()
    trigger_sets = {item["name"]: set(item["triggers"]) for item in result["workflows"]}
    assert trigger_sets["Default CI"] == {"workflow_dispatch"}
    assert trigger_sets["Full Non-Network Regression"] == {"workflow_dispatch"}
    assert trigger_sets["Windows Compatibility Smoke"] == {"workflow_dispatch", "pull_request"}
    assert trigger_sets["Browser Operator E2E"] == {"workflow_dispatch"}
    assert trigger_sets["Release Validation"] == {"workflow_dispatch"}


def test_windows_jobs_use_canonical_gate_instead_of_historical_step_names():
    windows = validator.load_workflow(ROOT / ".github/workflows/windows-compatibility-smoke.yml")
    release = validator.load_workflow(ROOT / ".github/workflows/release-validation.yml")
    for workflow in (windows, release):
        run_text = validator.job_run_text(workflow, "validation")
        assert "run_l7_a2_release_validation.py" in run_text
        assert "--gate" in run_text
        assert "--source-commit" in run_text and "--source-tree" in run_text
    assert "--native" in validator.job_run_text(release, "validation")
    assert "accept_l7_a2_docker.py" in validator.job_run_text(release, "docker-validation")


def test_policy_keeps_historical_and_performance_profiles_manual():
    profiles = json.loads((ROOT / "config/test_execution_profiles.json").read_text())["profiles"]
    assert profiles["historical-acceptance"]["automatic_ci_allowed"] is False
    assert profiles["performance"]["automatic_ci_allowed"] is False

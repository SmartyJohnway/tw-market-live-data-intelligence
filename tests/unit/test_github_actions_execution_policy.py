from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

import scripts.validate_github_actions_execution_policy as validator

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("module", [False, True], ids=["direct-script", "module"])
def test_validator_clean_subprocess_without_pythonpath(module):
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    target = (["-m", "scripts.validate_github_actions_execution_policy"] if module
              else ["scripts/validate_github_actions_execution_policy.py"])
    result = subprocess.run(
        [sys.executable, "-B", *target], cwd=ROOT, env=env,
        capture_output=True, text=True, encoding="utf-8", timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["status"] == "passed"


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


def test_windows_jobs_use_canonical_gate_instead_of_historical_step_names(tmp_path):
    windows = validator.load_workflow(ROOT / ".github/workflows/windows-compatibility-smoke.yml")
    release = validator.load_workflow(ROOT / ".github/workflows/release-validation.yml")
    for workflow in (windows, release):
        run_text = validator.job_run_text(workflow, "validation")
        assert "run_l7_a2_release_validation.py" in run_text
        assert "--gate" in run_text
        assert "--source-commit" in run_text and "--source-tree" in run_text
    assert "--native" in validator.job_run_text(release, "validation")
    assert "accept_l7_a2_docker.py" in validator.job_run_text(release, "docker-validation")

    # GHA-WIN-EOL-001: configure bytes before checkout; fail closed before CI.
    release_run = validator.job_run_text(release, "validation")
    assert release_run.index("config --local core.autocrlf false") < release_run.index("git checkout --detach")
    assert release_run.index("git checkout --detach") < release_run.index("verify_checkout_git_blob_identity.py")
    assert release_run.index("verify_checkout_git_blob_identity.py") < release_run.index("run_l7_a2_release_validation.py")
    assert release_run.index("run_l7_a2_release_validation.py") < release_run.index("NATIVE_ACCEPTANCE_STAGE_DIAGNOSTIC")
    assert "throw 'Release validation failed'" in release_run
    from scripts.verify_checkout_git_blob_identity import CheckoutByteMismatch, verify_file_bytes
    fixture_repo = tmp_path / "byte-fixture"
    fixture_repo.mkdir()
    subprocess.run(["git", "init", "-q", str(fixture_repo)], check=True)
    subprocess.run(["git", "-C", str(fixture_repo), "config", "core.autocrlf", "false"], check=True)
    subprocess.run(["git", "-C", str(fixture_repo), "config", "user.name", "CI test"], check=True)
    subprocess.run(["git", "-C", str(fixture_repo), "config", "user.email", "ci@example.invalid"], check=True)
    (fixture_repo / "blob.txt").write_bytes(b"first\nsecond\n")
    subprocess.run(["git", "-C", str(fixture_repo), "add", "blob.txt"], check=True)
    subprocess.run(["git", "-C", str(fixture_repo), "commit", "-q", "-m", "fixture"], check=True)
    assert len(verify_file_bytes(fixture_repo, "blob.txt")) == 64
    (fixture_repo / "blob.txt").write_bytes(b"first\r\nsecond\r\n")
    with pytest.raises(CheckoutByteMismatch, match="checkout_blob_bytes_mismatch"):
        verify_file_bytes(fixture_repo, "blob.txt")


def test_policy_keeps_historical_and_performance_profiles_manual():
    profiles = json.loads((ROOT / "config/test_execution_profiles.json").read_text())["profiles"]
    assert profiles["historical-acceptance"]["automatic_ci_allowed"] is False
    assert profiles["performance"]["automatic_ci_allowed"] is False

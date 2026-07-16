#!/usr/bin/env python3
"""Validate CI_POLICY_V1 workflow trigger boundaries deterministically."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
POLICY_PATH = ROOT / "config" / "github_actions_execution_policy.json"
RELEASE_WORKFLOW = "release-validation.yml"
WINDOWS_WORKFLOW = "windows-compatibility-smoke.yml"
REQUIRED_WINDOWS_STEP_NAMES = {
    "Compile Windows compatibility surfaces",
    "Run Windows non-network compatibility smoke tests",
    "Validate M5F package",
    "M5IJ Windows acceptance",
    "MCP startup check",
}
REQUIRED_WINDOWS_TEST_PATHS = {
    "tests/unit/test_m5f_canonical_market_context_package.py",
    "tests/unit/test_m5i_explicit_bounded_refresh.py",
    "tests/unit/test_m5ij_end_to_end_acceptance.py",
    "tests/unit/test_m5fgh_fastapi_context.py",
    "tests/unit/test_mcp_server.py",
    "tests/unit/test_m6d_ssl_policy.py",
    "tests/unit/test_m6d_operator_and_local_networking.py",
}


def job_step_names(workflow: dict[str, Any], job_name: str) -> set[str]:
    jobs = workflow.get("jobs", {})
    job = jobs.get(job_name, {}) if isinstance(jobs, dict) else {}
    steps = job.get("steps", []) if isinstance(job, dict) else []
    return {str(step.get("name")) for step in steps if isinstance(step, dict) and step.get("name")}


def job_run_text(workflow: dict[str, Any], job_name: str) -> str:
    jobs = workflow.get("jobs", {})
    job = jobs.get(job_name, {}) if isinstance(jobs, dict) else {}
    steps = job.get("steps", []) if isinstance(job, dict) else []
    return "\n".join(str(step.get("run", "")) for step in steps if isinstance(step, dict))


def validate_complete_windows_job(workflow: dict[str, Any], job_name: str, prefix: str, violations: list[str]) -> None:
    names = job_step_names(workflow, job_name)
    missing_names = REQUIRED_WINDOWS_STEP_NAMES - names
    for name in sorted(missing_names):
        violations.append(f"{prefix}:missing_step:{name}")
    run_text = job_run_text(workflow, job_name)
    for test_path in sorted(REQUIRED_WINDOWS_TEST_PATHS):
        if test_path not in run_text:
            violations.append(f"{prefix}:missing_test:{test_path}")
    if "component-security" in run_text:
        violations.append(f"{prefix}:filesystem_only_mislabeled_complete")


def load_workflow(path: Path) -> dict[str, Any]:
    """Use BaseLoader so GitHub's literal `on` is never coerced to boolean."""
    data = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    if not isinstance(data, dict):
        raise ValueError(f"workflow_not_mapping:{path.name}")
    return data


def trigger_keys(workflow: dict[str, Any]) -> set[str]:
    trigger = workflow.get("on")
    if trigger is None:
        return set()
    if isinstance(trigger, str):
        return {trigger}
    if isinstance(trigger, list):
        return {str(item) for item in trigger}
    if isinstance(trigger, dict):
        return {str(key) for key in trigger}
    return set()


def validate() -> dict[str, Any]:
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    violations: list[str] = []
    inspected: list[dict[str, Any]] = []
    expected = policy["workflows"]
    paths = sorted(WORKFLOWS.glob("*.yml"))

    expected_files = {details["file"].removeprefix(".github/workflows/") for details in expected.values()}
    actual_files = {path.name for path in paths}
    if expected_files != actual_files:
        violations.append("workflow_inventory_mismatch")

    release_files: list[str] = []
    for path in paths:
        workflow = load_workflow(path)
        name = str(workflow.get("name", ""))
        triggers = trigger_keys(workflow)
        inspected.append({"file": str(path.relative_to(ROOT)), "name": name, "triggers": sorted(triggers)})
        if "workflow_dispatch" not in triggers:
            violations.append(f"missing_workflow_dispatch:{path.name}")
        forbidden = triggers & {"pull_request", "pull_request_target", "merge_group", "workflow_run", "schedule"}
        for trigger in sorted(forbidden):
            violations.append(f"forbidden_automatic_trigger:{path.name}:{trigger}")
        if "push" in triggers:
            violations.append(f"forbidden_push_trigger:{path.name}")
        if "release" in triggers:
            release_files.append(path.name)
            if path.name != RELEASE_WORKFLOW:
                violations.append(f"duplicate_release_trigger:{path.name}")

    release_path = WORKFLOWS / RELEASE_WORKFLOW
    release = load_workflow(release_path) if release_path.exists() else {}
    if trigger_keys(release) != {"workflow_dispatch", "release"}:
        violations.append("release_validation_trigger_set_invalid")
    release_event = release.get("on", {}).get("release", {}) if isinstance(release.get("on"), dict) else {}
    if not isinstance(release_event, dict) or release_event.get("types") != ["published"]:
        violations.append("release_validation_not_published_only")
    if release_files != [RELEASE_WORKFLOW]:
        violations.append("release_validation_not_sole_release_workflow")

    windows_path = WORKFLOWS / WINDOWS_WORKFLOW
    windows = load_workflow(windows_path) if windows_path.exists() else {}
    validate_complete_windows_job(windows, "windows-compatibility-smoke", "windows_compatibility", violations)
    validate_complete_windows_job(release, "windows-compatibility", "release_windows_compatibility", violations)

    profiles = json.loads((ROOT / "config" / "test_execution_profiles.json").read_text(encoding="utf-8"))["profiles"]
    for profile in ("performance", "historical-acceptance"):
        if profiles[profile].get("automatic_ci_allowed") is not False:
            violations.append(f"manual_profile_marked_automatic:{profile}")

    return {
        "status": "passed" if not violations else "failed",
        "policy_id": policy["policy_id"],
        "workflow_count": len(paths),
        "workflows": inspected,
        "violations": violations,
    }


def main() -> int:
    result = validate()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

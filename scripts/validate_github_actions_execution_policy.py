#!/usr/bin/env python3
"""Validate CI_POLICY_V1 with the explicit L7-A2 pre-publication amendment."""
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
        forbidden = triggers & {"pull_request_target", "merge_group", "workflow_run", "schedule"}
        if "pull_request" in triggers and path.name != WINDOWS_WORKFLOW:
            forbidden.add("pull_request")
        for trigger in sorted(forbidden):
            violations.append(f"forbidden_automatic_trigger:{path.name}:{trigger}")
        if "push" in triggers:
            violations.append(f"forbidden_push_trigger:{path.name}")
        if "release" in triggers:
            release_files.append(path.name)
            if path.name != RELEASE_WORKFLOW:
                violations.append(f"duplicate_release_trigger:{path.name}")

    # The A2 authority prospectively supersedes published-release gating and
    # the old duplicated Windows step list with the canonical A1 gate runner.
    from scripts.validate_l7_a2_workflow_policy import validate as validate_a2
    try:
        validate_a2(ROOT)
    except (AssertionError, KeyError, TypeError, ValueError) as exc:
        violations.append("a2_integration_policy:" + str(exc))
    if policy.get("opt_in_windows_PR") != {"label":"windows-smoke", "activities":["opened","synchronize","reopened","labeled"], "unlabeled_expensive_job":False}:
        violations.append("opt_in_windows_policy_mismatch")
    release_mode = policy["authorization_modes"]["RELEASE_CI_REQUIRED"]
    if release_mode.get("release_or_tag_context_required") is not False or release_mode.get("pre_publication_validation_required") is not True:
        violations.append("pre_publication_policy_mismatch")
    if release_files:
        violations.append("post_publication_trigger_remains")

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

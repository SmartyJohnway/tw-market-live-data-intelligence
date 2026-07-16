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

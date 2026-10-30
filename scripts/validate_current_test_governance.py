#!/usr/bin/env python3
"""Validate current roles/selection policy, independently of TG cutover counts."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_ROLES = {
    "merge": "current-merge-gate", "ci": "default-ci", "broad_current": "full-current",
    "release_blocking": "release-blocking-ci", "release_preflight": "release-preflight-current",
    "historical": "historical-milestone-replay", "mixed_historical": "mixed-historical-diagnostic",
    "rollback": "pre-tg5-default-ci",
}
CURRENT_EXPRESSION = (
    "not network and not browser and not live and not release_preflight "
    "and not historical and not performance"
)
MANDATORY = {
    "tests/unit/test_current_v3_validation_authority.py",
    "tests/unit/test_current_test_governance.py",
    "tests/unit/test_test_governance_tg5.py",
    "tests/unit/test_run_test_profile.py",
    "tests/unit/test_governance_forbidden_path_guard.py",
    "tests/unit/test_forbidden_behavior_scanner.py",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


EXPECTED_WORKFLOWS = {
    ".github/workflows/ci.yml": {"trigger": "workflow_dispatch", "profile": "default-ci"},
    ".github/workflows/non-network-ci.yml": {"trigger": "workflow_dispatch", "profile": "full-non-network"},
}


def validate_workflows(authority: dict, root: Path) -> None:
    require(authority["ci_workflows"] == EXPECTED_WORKFLOWS, "workflow authority changed")
    for path, expected in EXPECTED_WORKFLOWS.items():
        text = (root / path).read_text(encoding="utf-8")
        trigger = re.search(r"^on:\n(.*?)(?=^[^ \n#])", text, re.MULTILINE | re.DOTALL)
        require(trigger is not None and trigger.group(1).strip() == "workflow_dispatch:",
                f"workflow trigger drift: {path}")
        invoked = re.findall(r"run_test_profile\.py ([^\n]+)", text)
        require(invoked == [expected["profile"] + " --json"], f"workflow profile drift: {path}")


def validate(authority: dict | None = None, config: dict | None = None, *, root: Path = ROOT) -> dict:
    authority = load(root / "config/test_governance_authority.json") if authority is None else authority
    config = load(root / "config/test_execution_profiles.json") if config is None else config
    require(authority["schema_version"] == "test_governance_authority.v2", "authority version")
    require(authority["authority_role"] == "CURRENT_OPERATIONAL_TEST_AUTHORITY", "authority role")
    require(authority["roles"] == EXPECTED_ROLES, "missing/invalid/illegally duplicated role")
    policy = authority["selection_policy"]
    require(policy["current_expression"] == CURRENT_EXPRESSION, "exclusion policy weakened")
    require(policy["current_counts"] == "OBSERVED_COLLECTION_FACTS_ONLY", "counts are observations")
    require(set(policy["mandatory_current_tests"]) == MANDATORY, "mandatory policy changed")
    require(policy["release_contract"] == "config/release_blocking_ci.v1.json", "release authority")
    # No fixed current count/old cutover fields may return to operational authority.
    require(set(authority) == {"schema_version", "date", "authority_role", "roles", "selection_policy",
                               "ci_workflows", "historical_evidence"}, "mixed historical/current fields")
    require(set(policy) == {"current_expression", "current_counts", "enrollment", "mandatory_current_tests",
                            "release_contract"}, "fixed count or unsupported selection policy")
    validate_workflows(authority, root)
    profiles = config["profiles"]
    for role, name in authority["roles"].items():
        if role == "merge":
            require(name == "current-merge-gate", "invalid merge gate")
            continue
        require(name in profiles, f"missing profile: {role}: {name}")
    for name, profile in profiles.items():
        paths = profile.get("pytest_paths", [])
        require(len(paths) == len(set(paths)), f"duplicate path: {name}")
        for path in paths:
            target = (root / path).resolve()
            require(target.is_relative_to(root.resolve()) and target.exists(), f"invalid path: {name}: {path}")
        if profile["execution_type"] == "pytest":
            require(bool(paths), f"implicit/unbounded pytest selection: {name}")
    for name in ("default-ci", "full-current"):
        profile = profiles[name]
        require(profile["execution_type"] == "pytest" and not profile.get("authoritative_runner"),
                f"unexpected runner: {name}")
        require(profile["pytest_expression"] == CURRENT_EXPRESSION, f"exclusion policy weakened: {name}")
        require(MANDATORY <= set(profile["pytest_paths"]), f"mandatory current test omitted: {name}")
        require(not (set(profile["pytest_paths"]) & set(profiles["release-preflight-current"]["pytest_paths"])),
                f"release-only enrollment: {name}")
        require(profile["network_policy"] == "no network", f"network policy: {name}")
        require(all((root / path).is_file() and path.startswith("tests/") and path.endswith(".py")
                    for path in profile["pytest_paths"]), f"non-explicit current test file: {name}")
    require(set(profiles["default-ci"]["pytest_paths"]) <= set(profiles["full-current"]["pytest_paths"]),
            "broad-current coverage lost")
    require(profiles["default-ci"]["automatic_ci_allowed"] is True, "default CI eligibility")
    for name in ("full-current", "historical-milestone-replay", "release-preflight-current",
                 "mixed-historical-diagnostic", "pre-tg5-default-ci", "browser-e2e", "bounded-live", "performance"):
        require(profiles[name]["automatic_ci_allowed"] is False, f"specialized automatic policy: {name}")
    historical = profiles["historical-milestone-replay"]
    require(historical["pytest_expression"] == "not network and not browser and not live and not performance",
            "historical replay policy")
    # Frozen diagnostic membership is not a current-suite count invariant.
    snapshots = load(root / "config/test_governance_semantic_profiles.json")["shadow_execution_sets"]
    require(set(snapshots["tg2-historical-acceptance-shadow"]["paths"]) <= set(historical["pytest_paths"]),
            "historical replay coverage lost")
    rollback = load(root / "docs/governance/test_governance/TG5_ROLLBACK_CONTRACT_2026-09-23.json")
    diagnostic = profiles["pre-tg5-default-ci"]
    require(diagnostic["pytest_paths"] == rollback["old_default_profile"]["pytest_paths"] and
            diagnostic["pytest_expression"] == rollback["old_default_profile"]["pytest_expression"],
            "rollback diagnostic semantics changed")
    release = profiles["release-blocking-ci"]
    require(release["execution_type"] == "authoritative_runner" and
            release["authoritative_runner"] == [["python", "scripts/run_deterministic_ci.py"]] and
            release["contract"] == policy["release_contract"], "release delegation changed")
    require(set(authority["historical_evidence"]) == {"tg4_acceptance", "tg5_acceptance", "rollback",
            "rollback_gaps", "tg4_gaps", "tg2"}, "missing historical evidence")
    for evidence in authority["historical_evidence"].values():
        path = (root / evidence["path"]).resolve()
        require(path.is_relative_to(root.resolve()) and path.is_file(), "historical evidence path")
        require(hashlib.sha256(path.read_bytes()).hexdigest() == evidence["sha256"],
                f"historical evidence changed: {evidence['path']}")
    coverage = validate_coverage(config, root=root)
    return {"status": "PASS", "roles": authority["roles"], "coverage": coverage,
            "observed_explicit_paths": {name: len(profiles[name]["pytest_paths"])
                                        for name in ("default-ci", "full-current")},
            "counts_policy": policy["current_counts"]}


def validate_coverage(config: dict, *, root: Path = ROOT) -> dict:
    from scripts.run_current_merge_gate import FLOOR, observe, check_selection
    require(hashlib.sha256((root / FLOOR).read_bytes()).hexdigest() == "071d9a24fcf432d55b5f6cbb5690cc6b2027a7afb0176b08167ab24a6c95eb67",
            "coverage floor changed without explicit governance handling")
    floor = load(root / FLOOR)
    require(floor["merge_gate"] == {"name": "current-merge-gate", "runner": "scripts/run_current_merge_gate.py",
            "raw_profile": "default-ci", "result_schema": "current_merge_verdict.v1"}, "invalid merge gate authority")
    require(floor["schema_version"] == "current_test_coverage_floor.v1", "floor schema")
    require(floor["baseline_commit"] == "13dc831f037e52da2ffe5a4f477f5c874817afa0", "floor provenance")
    require(bool(floor["owner"]) and "explicit Owner governance review" in floor["update_policy"], "floor ownership")
    require((root / floor["governance_record"]).is_file(), "floor governance record")
    source = floor["release_classification_source"]
    require(source["path"] == "config/release_blocking_ci.v1.json", "diagnostic authority source")
    release_path = root / source["path"]
    require(hashlib.sha256(release_path.read_bytes()).hexdigest() == source["sha256"], "diagnostic source changed")
    release = load(release_path)
    known = floor["known_diagnostics"]
    # Exact bounded S3-R1 authority, not an arbitrary failed-node waiver facility.
    require(known == EXPECTED_DIAGNOSTICS, "unknown diagnostic classifications")
    require(set(known) <= set(release["historical_diagnostics"]), "unowned diagnostics")
    require(floor["authorized_optional_skips"] == {n: v["expected_skip_reason"] for n, v in
            release["optional_historical_artifact_witnesses"].items()}, "skip authority drift")
    evidence = {}
    for name in ("default-ci", "full-current"):
        minimum = floor["profiles"][name]
        profile = config["profiles"][name]
        require(set(minimum["paths"]) <= set(profile["pytest_paths"]), f"coverage path floor lost: {name}")
        selected = observe(profile, collect=True, quiet=True, root=root)["selected"]
        check_selection(floor, name, selected)
        require(set(known) <= set(selected), f"known diagnostic not collectible: {name}")
        evidence[name] = {"floor_paths": len(minimum["paths"]), "actual_paths": len(profile["pytest_paths"]),
                          "floor_nodes": len(minimum["selected_nodes"]), "selected_nodes": len(selected),
                          "missing_paths": [], "missing_nodes": []}
    return evidence


EXPECTED_DIAGNOSTICS = {
    "tests/unit/test_phase_i_i3_a0_preflight.py::test_current_hold_record_and_runtime_containment": "KNOWN_TRANSITION_DIAGNOSTIC",
    "tests/unit/test_phase_i_i3_a0_preflight.py::test_p0_validator_cannot_claim_pass_or_rearm": "KNOWN_TRANSITION_DIAGNOSTIC",
    "tests/unit/test_phase_i_i3_a0_p1_adjudication.py::test_p1_governance_validator_passes_under_network_denial": "KNOWN_TRANSITION_DIAGNOSTIC",
    "tests/unit/test_phase_i_i3_a0_p3.py::test_p3_validator_production_containment_and_readiness": "KNOWN_TRANSITION_DIAGNOSTIC",
    "tests/unit/test_phase_i_i3_a0_p3_r1.py::test_r1_validator": "KNOWN_TRANSITION_DIAGNOSTIC",
    "tests/unit/test_phase_i_i3_a1.py::test_a1_validator_and_immutable_a0_anchors": "KNOWN_TRANSITION_DIAGNOSTIC",
    "tests/unit/test_phase_i_i3_a3_attempt_2_bounded_live.py::test_exact_mapping_and_frozen_candidate_and_production_containment": "KNOWN_HISTORICAL_DIAGNOSTIC",
    "tests/unit/test_phase_i_i3_a3_r3_http520_lifecycle.py::test_committed_attempt4_pass_lineage_and_containment": "KNOWN_HISTORICAL_DIAGNOSTIC",
    "tests/unit/test_phase_j_ghi_readiness_preflight.py::test_current_record": "KNOWN_HISTORICAL_DIAGNOSTIC",
    "tests/unit/test_phase_j_ghi_readiness_preflight.py::test_unchecked_g_h_do_not_themselves_block_pass": "KNOWN_HISTORICAL_DIAGNOSTIC",
    "tests/unit/test_phase_j_ghi_readiness_preflight.py::test_missing_runtime_can_be_nonblocking_when_safe_or_optional[J1-08]": "KNOWN_HISTORICAL_DIAGNOSTIC",
    "tests/unit/test_phase_j_ghi_readiness_preflight.py::test_missing_runtime_can_be_nonblocking_when_safe_or_optional[J1-10]": "KNOWN_HISTORICAL_DIAGNOSTIC",
}


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(ROOT))
    print(json.dumps(validate(), indent=2, sort_keys=True))

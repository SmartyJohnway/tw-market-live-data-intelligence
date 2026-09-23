#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILES = ROOT / "config/test_execution_profiles.json"
AUTHORITY = ROOT / "config/test_governance_authority.json"
ROLLBACK = ROOT / "docs/governance/test_governance/TG5_ROLLBACK_CONTRACT_2026-09-23.json"
TG4 = ROOT / "docs/governance/test_governance/TG4_ACCEPTANCE_LEDGER_2026-09-23.json"
GAPS = ROOT / "docs/governance/test_governance/TG4_KNOWN_HISTORICAL_REPLAY_GAPS.v1.json"
ROLLBACK_GAPS = ROOT / "docs/governance/test_governance/TG5_ROLLBACK_DIAGNOSTIC_GAPS.v1.json"
FAILED_RE = re.compile(r"^FAILED\\s+(\\S+)\\s+-", re.MULTILINE)

EXPECTED_EXPR = (
    "not network and not browser and not live and not release_preflight "
    "and not historical and not performance"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_static() -> dict:
    profiles = _load(PROFILES)["profiles"]
    authority = _load(AUTHORITY)
    rollback = _load(ROLLBACK)
    tg4 = _load(TG4)

    new_default = profiles["default-ci"]
    old_rehearsal = profiles["pre-tg5-default-ci"]
    tg2_current = profiles["tg2-default-ci-current-shadow"]

    assert new_default == rollback["candidate_default_profile"]
    assert new_default["pytest_expression"] == EXPECTED_EXPR
    assert new_default["automatic_ci_allowed"] is True
    assert len(new_default["pytest_paths"]) == 93
    assert new_default["pytest_paths"] == tg2_current["pytest_paths"]

    old_contract = rollback["old_default_profile"]
    assert len(old_contract["pytest_paths"]) == 156
    assert old_contract["pytest_expression"] == EXPECTED_EXPR
    assert old_rehearsal["pytest_paths"] == old_contract["pytest_paths"]
    assert old_rehearsal["pytest_expression"] == old_contract["pytest_expression"]
    assert old_rehearsal["automatic_ci_allowed"] is False

    # Deterministic rollback means replacing only the default profile body.
    restored = dict(profiles)
    restored["default-ci"] = old_contract
    assert restored["default-ci"] == old_contract

    assert authority["state"] == "TG5_CUTOVER_CANDIDATE"
    assert authority["current_merge_authority"]["profile"] == "default-ci"
    assert authority["current_merge_authority"]["expected_file_paths"] == 93
    assert authority["current_merge_authority"]["expected_selected_nodes"] == 778
    assert authority["rollback"]["expected_file_paths"] == 156
    assert authority["rollback"]["expected_selected_nodes"] == 1245

    assert tg4["status"] == "TG4_SHADOW_CI_PASS"
    assert tg4["node_analysis"]["legacy_layer_counts"]["unexplained"] == 0
    assert tg4["interpretation"]["shadow_protection_gap"] == "NONE_UNEXPLAINED"

    for name in (
        "tg2-full-current-non-network-shadow",
        "tg2-historical-acceptance-shadow",
        "tg2-release-preflight-shadow",
        "tg4-mixed-historical-shadow",
        "pre-tg5-default-ci",
    ):
        assert profiles[name]["automatic_ci_allowed"] is False

    for path in set(new_default["pytest_paths"]) | set(old_contract["pytest_paths"]):
        assert (ROOT / path).exists(), path

    assert authority["lifecycle_regression"]["broad_current_expected_nodes"] == 1150
    assert authority["lifecycle_regression"]["historical_expected_nodes"] == 94
    assert authority["lifecycle_regression"]["release_expected_nodes"] == 5
    assert authority["lifecycle_regression"]["mixed_historical_expected_nodes"] == 4

    return {
        "status": "PASS",
        "new_default_file_count": len(new_default["pytest_paths"]),
        "rollback_file_count": len(old_contract["pytest_paths"]),
        "new_default_matches_tg2_shadow": True,
        "rollback_execution_semantics_preserved": True,
        "tg4_unexplained_nodes": 0,
        "phase_i_implementation": False,
    }


def _failed_nodes(payload: dict) -> set[str]:
    return set(FAILED_RE.findall(str(payload.get("failure_output_tail") or "")))


def validate_runtime(
    *,
    new_default_path: Path,
    current_shadow_path: Path,
    baseline_default_path: Path,
    rollback_diagnostic_path: Path,
    full_current_path: Path,
    historical_path: Path,
    release_path: Path,
    mixed_path: Path,
    node_analysis_path: Path,
    full_non_network_path: Path,
) -> dict:
    payloads = {
        "new_default": _load(new_default_path),
        "current_shadow": _load(current_shadow_path),
        "baseline_default": _load(baseline_default_path),
        "rollback_diagnostic": _load(rollback_diagnostic_path),
        "full_current": _load(full_current_path),
        "historical": _load(historical_path),
        "release": _load(release_path),
        "mixed": _load(mixed_path),
        "full_non_network": _load(full_non_network_path),
    }
    nodes = _load(node_analysis_path)
    mixed_gaps = _load(GAPS)
    rollback_gaps = _load(ROLLBACK_GAPS)

    for name in (
        "new_default",
        "current_shadow",
        "baseline_default",
        "full_current",
        "historical",
        "release",
    ):
        assert payloads[name]["status"] == "pass", (name, payloads[name])

    assert int(payloads["new_default"]["selected"]) == 778
    assert int(payloads["current_shadow"]["selected"]) == 778
    assert int(payloads["baseline_default"]["selected"]) == 1245
    assert int(payloads["full_current"]["selected"]) == 1150
    assert int(payloads["historical"]["selected"]) == 94
    assert int(payloads["release"]["selected"]) == 5
    assert int(payloads["mixed"]["selected"]) == 4
    assert int(payloads["rollback_diagnostic"]["selected"]) == 1245

    assert payloads["mixed"]["status"] == "fail"
    mixed_allowed = {item["node_id"] for item in mixed_gaps["allowed_failed_nodes"]}
    mixed_actual = _failed_nodes(payloads["mixed"])
    assert mixed_actual == mixed_allowed, {
        "actual": sorted(mixed_actual),
        "allowed": sorted(mixed_allowed),
    }
    assert int(payloads["mixed"]["failed"]) == 2

    assert payloads["rollback_diagnostic"]["status"] == "fail"
    rollback_allowed = {item["node_id"] for item in rollback_gaps["allowed_failed_nodes"]}
    rollback_actual = _failed_nodes(payloads["rollback_diagnostic"])
    assert rollback_actual == rollback_allowed, {
        "actual": sorted(rollback_actual),
        "allowed": sorted(rollback_allowed),
    }
    assert int(payloads["rollback_diagnostic"]["failed"]) == 2

    assert nodes["promoted_default_matches_tg2_shadow"] is True
    assert nodes["legacy_node_count"] == 1245
    assert nodes["current_shadow_node_count"] == 778
    assert nodes["legacy_missing_from_layered_count"] == 0
    assert nodes["legacy_unexplained"] == []
    assert nodes["legacy_layer_counts"] == {
        "current_every_pr": 778,
        "broad_current_nondefault": 372,
        "historical_acceptance": 90,
        "release_preflight": 5,
        "unexplained": 0,
    }

    return {
        "status": "PASS",
        "new_default_selected": 778,
        "baseline_rollback_selected": 1245,
        "current_tree_rollback_diagnostic_failures": 2,
        "full_current_selected": 1150,
        "historical_selected": 94,
        "release_selected": 5,
        "known_mixed_historical_failures": 2,
        "unexplained_legacy_nodes": 0,
        "full_non_network_observation": {
            "status": payloads["full_non_network"]["status"],
            "selected": payloads["full_non_network"].get("selected"),
            "failed": payloads["full_non_network"].get("failed"),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--new-default", type=Path)
    ap.add_argument("--current-shadow", type=Path)
    ap.add_argument("--baseline-default", type=Path)
    ap.add_argument("--rollback-diagnostic", type=Path)
    ap.add_argument("--full-current", type=Path)
    ap.add_argument("--historical", type=Path)
    ap.add_argument("--release", type=Path)
    ap.add_argument("--mixed", type=Path)
    ap.add_argument("--node-analysis", type=Path)
    ap.add_argument("--full-non-network", type=Path)
    args = ap.parse_args()

    out = {"static": validate_static()}
    runtime_args = (
        args.new_default,
        args.current_shadow,
        args.baseline_default,
        args.rollback_diagnostic,
        args.full_current,
        args.historical,
        args.release,
        args.mixed,
        args.node_analysis,
        args.full_non_network,
    )
    if all(runtime_args):
        out["runtime"] = validate_runtime(
            new_default_path=args.new_default,
            current_shadow_path=args.current_shadow,
            baseline_default_path=args.baseline_default,
            rollback_diagnostic_path=args.rollback_diagnostic,
            full_current_path=args.full_current,
            historical_path=args.historical,
            release_path=args.release,
            mixed_path=args.mixed,
            node_analysis_path=args.node_analysis,
            full_non_network_path=args.full_non_network,
        )
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

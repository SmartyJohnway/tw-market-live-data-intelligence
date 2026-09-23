#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "b438e3b1d06698e2e702284abbdaf0bbc9340b40"
CONFIG = ROOT / "config/test_execution_profiles.json"
GAPS = ROOT / "docs/governance/test_governance/TG4_KNOWN_HISTORICAL_REPLAY_GAPS.v1.json"

FAILED_RE = re.compile(r"^FAILED\s+(\S+)\s+-", re.MULTILINE)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _baseline_profiles() -> dict[str, Any]:
    raw = subprocess.check_output(
        ["git", "show", f"{BASELINE}:config/test_execution_profiles.json"],
        cwd=ROOT,
        text=True,
    )
    return json.loads(raw)["profiles"]


def validate_profile_config() -> dict[str, Any]:
    baseline = _baseline_profiles()
    current = _load(CONFIG)["profiles"]

    assert current["default-ci"] == baseline["default-ci"]

    allowed_changed = {
        "tg2-default-ci-current-shadow",
        "tg2-full-current-non-network-shadow",
    }
    added = set(current) - set(baseline)
    assert added == {"tg4-mixed-historical-shadow"}

    for name in set(baseline) - allowed_changed:
        assert current[name] == baseline[name], name

    expected_expr = (
        "not network and not browser and not live and not release_preflight "
        "and not historical and not performance"
    )
    for name in allowed_changed:
        before = dict(baseline[name])
        after = dict(current[name])
        assert after["pytest_expression"] == expected_expr
        before.pop("pytest_expression")
        after.pop("pytest_expression")
        assert after == before

    mixed = current["tg4-mixed-historical-shadow"]
    assert mixed["automatic_ci_allowed"] is False
    assert mixed["pytest_expression"].startswith("historical and ")

    return {
        "default_ci_unchanged": True,
        "only_expected_shadow_profile_delta": True,
    }


def _failed_nodes(payload: dict[str, Any]) -> set[str]:
    return set(FAILED_RE.findall(str(payload.get("failure_output_tail") or "")))


def validate_runtime_results(
    *,
    summary_path: Path,
    node_analysis_path: Path,
    mixed_result_path: Path,
) -> dict[str, Any]:
    summary = _load(summary_path)
    nodes = _load(node_analysis_path)
    mixed = _load(mixed_result_path)
    gaps = _load(GAPS)

    for name in (
        "default-ci",
        "current-shadow",
        "full-current-shadow",
        "historical-shadow",
        "release-shadow",
    ):
        assert summary[name]["status"] == "pass", (name, summary[name])

    assert summary["mixed-historical-shadow"]["status"] == "fail"
    allowed = {item["node_id"] for item in gaps["allowed_failed_nodes"]}
    actual = _failed_nodes(mixed)
    assert actual == allowed, {"actual": sorted(actual), "allowed": sorted(allowed)}
    assert int(mixed.get("failed") or 0) == len(allowed)

    assert nodes["legacy_node_count"] == 1245
    assert nodes["legacy_missing_from_layered_count"] == 0
    assert nodes["legacy_unexplained"] == []
    assert nodes["legacy_layer_counts"] == {
        "current_every_pr": 778,
        "broad_current_nondefault": 372,
        "historical_acceptance": 90,
        "release_preflight": 5,
        "unexplained": 0,
    }
    assert nodes["layered_extra_vs_legacy"] == sorted(
        gaps["expected_additional_historical_nodes"]
    )
    assert nodes["layered_extra_vs_legacy_count"] == 8
    assert nodes["current_shadow_node_count"] == 778
    assert nodes["full_current_shadow_node_count"] == 1150
    assert nodes["historical_shadow_node_count"] == 94
    assert nodes["release_shadow_node_count"] == 5
    assert nodes["mixed_historical_node_count"] == 4

    return {
        "status": "PASS",
        "legacy_nodes": 1245,
        "legacy_current_every_pr_nodes": 778,
        "legacy_broad_current_nondefault_nodes": 372,
        "legacy_historical_nodes": 90,
        "legacy_release_nodes": 5,
        "legacy_unexplained_nodes": 0,
        "additional_historical_only_nodes": 8,
        "known_historical_replay_failures": len(allowed),
        "tg5_authorized": False,
    }


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--summary", type=Path)
    ap.add_argument("--node-analysis", type=Path)
    ap.add_argument("--mixed-result", type=Path)
    args=ap.parse_args()

    out={"profile_config": validate_profile_config()}
    if args.summary and args.node_analysis and args.mixed_result:
        out["runtime_shadow"] = validate_runtime_results(
            summary_path=args.summary,
            node_analysis_path=args.node_analysis,
            mixed_result_path=args.mixed_result,
        )
    print(json.dumps(out,indent=2,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/test_execution_profiles.json"

PROFILE_NAMES = (
    "pre-tg5-default-ci",
    "default-ci",
    "tg2-default-ci-current-shadow",
    "tg2-full-current-non-network-shadow",
    "tg2-historical-acceptance-shadow",
    "tg2-release-preflight-shadow",
    "tg4-mixed-historical-shadow",
)


def _load_profiles() -> dict:
    return json.loads(CONFIG.read_text(encoding="utf-8"))["profiles"]


def collect_nodes(profile_name: str) -> list[str]:
    p = _load_profiles()[profile_name]
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "--collect-only",
        "-q",
        "-m",
        p["pytest_expression"],
        *p["pytest_paths"],
    ]
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"collect failed for {profile_name}:\n{proc.stdout[-8000:]}")
    nodes = []
    for raw in proc.stdout.splitlines():
        line = raw.strip()
        if "::" in line and not line.startswith(("=", "<")):
            nodes.append(line)
    return sorted(set(nodes))


def analyze() -> dict:
    nodes = {name: collect_nodes(name) for name in PROFILE_NAMES}
    sets = {name: set(items) for name, items in nodes.items()}

    legacy = sets["pre-tg5-default-ci"]
    current = sets["default-ci"]
    current_shadow = sets["tg2-default-ci-current-shadow"]
    full_current = sets["tg2-full-current-non-network-shadow"]
    historical = sets["tg2-historical-acceptance-shadow"]
    release = sets["tg2-release-preflight-shadow"]
    mixed_hist = sets["tg4-mixed-historical-shadow"]

    layered_union = full_current | historical | release | mixed_hist
    legacy_missing_from_layered = sorted(legacy - layered_union)
    layered_extra_vs_legacy = sorted(layered_union - legacy)
    current_missing_vs_legacy = sorted(legacy - current)

    legacy_current = legacy & current
    legacy_broad_only = legacy & (full_current - current)
    legacy_historical = legacy & historical
    legacy_release = legacy & release
    explained_legacy = legacy_current | legacy_broad_only | legacy_historical | legacy_release
    legacy_unexplained = sorted(legacy - explained_legacy)

    assert not legacy_missing_from_layered
    assert not legacy_unexplained
    assert current == current_shadow
    assert current <= full_current
    assert not (mixed_hist & current)
    assert not (mixed_hist & full_current)
    assert not (legacy_historical & full_current)
    assert not (legacy_release & full_current)
    assert not (legacy_historical & legacy_release)

    return {
        "schema_version": "tg4_test_node_shadow_analysis.v1",
        "profiles": {name: {"node_count": len(items)} for name, items in nodes.items()},
        "legacy_node_count": len(legacy),
        "current_shadow_node_count": len(current),
        "promoted_default_matches_tg2_shadow": current == current_shadow,
        "full_current_shadow_node_count": len(full_current),
        "historical_shadow_node_count": len(historical),
        "release_shadow_node_count": len(release),
        "mixed_historical_node_count": len(mixed_hist),
        "legacy_missing_from_layered_count": len(legacy_missing_from_layered),
        "legacy_missing_from_layered": legacy_missing_from_layered,
        "layered_extra_vs_legacy_count": len(layered_extra_vs_legacy),
        "layered_extra_vs_legacy": layered_extra_vs_legacy,
        "current_missing_vs_legacy_count": len(current_missing_vs_legacy),
        "current_missing_vs_legacy": current_missing_vs_legacy,
        "legacy_layer_counts": {
            "current_every_pr": len(legacy_current),
            "broad_current_nondefault": len(legacy_broad_only),
            "historical_acceptance": len(legacy_historical),
            "release_preflight": len(legacy_release),
            "unexplained": len(legacy_unexplained),
        },
        "legacy_unexplained": legacy_unexplained,
        "tg5_authorized": False,
    }


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output", type=Path)
    args=ap.parse_args()
    payload=analyze()
    rendered=json.dumps(payload,indent=2,sort_keys=True)+"\n"
    if args.output:
        args.output.write_text(rendered,encoding="utf-8")
    else:
        print(rendered,end="")
    return 0


if __name__=="__main__":
    raise SystemExit(main())

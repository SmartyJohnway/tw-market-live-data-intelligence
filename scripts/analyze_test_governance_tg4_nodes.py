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

    legacy = sets["default-ci"]
    current = sets["tg2-default-ci-current-shadow"]
    full_current = sets["tg2-full-current-non-network-shadow"]
    historical = sets["tg2-historical-acceptance-shadow"]
    release = sets["tg2-release-preflight-shadow"]
    mixed_hist = sets["tg4-mixed-historical-shadow"]

    layered_union = full_current | historical | release | mixed_hist
    legacy_missing_from_layered = sorted(legacy - layered_union)
    layered_extra_vs_legacy = sorted(layered_union - legacy)
    current_missing_vs_legacy = sorted(legacy - current)

    assert not legacy_missing_from_layered
    assert current <= full_current
    assert not (mixed_hist & current)
    assert not (mixed_hist & full_current)

    return {
        "schema_version": "tg4_test_node_shadow_analysis.v1",
        "profiles": {name: {"node_count": len(items)} for name, items in nodes.items()},
        "legacy_node_count": len(legacy),
        "current_shadow_node_count": len(current),
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

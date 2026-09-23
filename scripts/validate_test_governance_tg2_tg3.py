#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILES = ROOT / "config/test_execution_profiles.json"
SEMANTIC = ROOT / "config/test_governance_semantic_profiles.json"
TG1 = ROOT / "docs/governance/test_governance/TG1_TEST_AUTHORITY_DISPOSITION_LEDGER_2026-09-23.json"
HIST = ROOT / "docs/governance/test_governance/HISTORICAL_EVIDENCE_INTEGRITY_MANIFEST.v1.json"
ROLLBACK = ROOT / "docs/governance/test_governance/TG5_ROLLBACK_CONTRACT_2026-09-23.json"

EXPECTED_DEFAULT_EXPR = "not network and not browser and not live and not release_preflight and not historical and not performance"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _blob_sha(path: str) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", f"HEAD:{path}"],
        cwd=ROOT,
        text=True,
    ).strip()


def validate() -> dict:
    profiles = _load(PROFILES)["profiles"]
    semantic = _load(SEMANTIC)
    tg1 = _load(TG1)
    hist = _load(HIST)
    rollback = _load(ROLLBACK)

    source_paths = rollback["old_default_profile"]["pytest_paths"]
    current_default_paths = profiles["default-ci"]["pytest_paths"]
    tg1_paths = [item["path"] for item in tg1["records"]]
    assert len(source_paths) == 156
    assert source_paths == tg1_paths
    assert rollback["old_default_profile"]["pytest_expression"] == EXPECTED_DEFAULT_EXPR
    assert profiles["default-ci"]["pytest_expression"] == EXPECTED_DEFAULT_EXPR
    assert len(current_default_paths) == 93

    partitions = semantic["partitions"]
    partition_lists = [item["paths"] for item in partitions.values()]
    flattened = [path for group in partition_lists for path in group]
    assert len(flattened) == 156
    assert len(set(flattened)) == 156
    assert set(flattened) == set(source_paths)

    assert partitions["default_ci_current_candidate"]["count"] == 91
    assert partitions["mixed_current_historical_requires_split"]["count"] == 2
    assert partitions["full_current_nondefault_candidate"]["count"] == 46
    assert partitions["historical_acceptance_candidate"]["count"] == 15
    assert partitions["release_preflight_candidate"]["count"] == 2

    refined = "tests/unit/test_m8c_taifex_mis_currentness_preflight.py"
    assert refined in partitions["full_current_nondefault_candidate"]["paths"]
    assert refined not in partitions["historical_acceptance_candidate"]["paths"]

    for profile_name, shadow in semantic["shadow_execution_sets"].items():
        actual = profiles[profile_name]
        assert actual["pytest_paths"] == shadow["paths"]
        assert actual["automatic_ci_allowed"] is False
        assert "not network" in actual["pytest_expression"]

    historical_paths = partitions["historical_acceptance_candidate"]["paths"]
    assert hist["candidate_count"] == 15
    assert [item["candidate_test_path"] for item in hist["entries"]] == historical_paths
    assert hist["default_ci_authority_changed"] is False
    assert hist["historical_tests_deleted"] is False
    assert hist["full_reproduction_retained"] is True

    evidence_count = 0
    for item in hist["entries"]:
        assert _blob_sha(item["candidate_test_path"]) == item["candidate_test_git_blob_sha"]
        for evidence in item["primary_evidence"]:
            evidence_count += 1
            assert _blob_sha(evidence["path"]) == evidence["git_blob_sha"]

    return {
        "status": "PASS",
        "source_pre_tg5_default_file_count": len(source_paths),
        "current_default_ci_file_count": len(current_default_paths),
        "current_candidate_count": partitions["default_ci_current_candidate"]["count"],
        "mixed_count": partitions["mixed_current_historical_requires_split"]["count"],
        "full_current_nondefault_count": partitions["full_current_nondefault_candidate"]["count"],
        "historical_candidate_count": hist["candidate_count"],
        "release_candidate_count": partitions["release_preflight_candidate"]["count"],
        "historical_primary_evidence_count": evidence_count,
        "default_ci_authority_changed": True,
        "tg5_cutover_candidate": True,
        "tg2_shadow_profiles_automatic_ci_allowed": False,
        "tg3_full_reproduction_retained": True,
    }


if __name__ == "__main__":
    print(json.dumps(validate(), indent=2, sort_keys=True))

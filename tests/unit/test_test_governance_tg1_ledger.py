from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROFILE = ROOT / "config/test_execution_profiles.json"
LEDGER = ROOT / "docs/governance/test_governance/TG1_TEST_AUTHORITY_DISPOSITION_LEDGER_2026-09-23.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_tg1_ledger_covers_exact_pre_tg5_default_ci_file_set() -> None:
    profile = _load(PROFILE)["profiles"]["pre-tg5-default-ci"]
    ledger = _load(LEDGER)

    source_paths = profile["pytest_paths"]
    ledger_paths = [item["path"] for item in ledger["records"]]

    assert len(source_paths) == 156
    assert len(ledger_paths) == 156
    assert len(set(ledger_paths)) == 156
    assert set(ledger_paths) == set(source_paths)

    assert ledger["proposal_only"] is True
    assert ledger["profile_change_performed"] is False
    assert ledger["test_deletion_performed"] is False
    assert ledger["phase_i_implementation"] is False
    assert ledger["source_activation_mutation"] is False
    assert ledger["summary"]["pending_manual_review_count"] == 0


def test_tg1_high_risk_dispositions_are_fail_safe() -> None:
    ledger = _load(LEDGER)
    records = {item["path"]: item for item in ledger["records"]}

    assert records[
        "tests/unit/test_m8_through_m8b_consolidated_acceptance.py"
    ]["proposed_disposition"] == "MOVE_HISTORICAL_AFTER_TG3"

    assert records[
        "tests/unit/test_validate_v1_public_contracts.py"
    ]["proposed_disposition"] == "KEEP_DEFAULT_REWRITE_BRITTLE"

    assert records[
        "tests/unit/test_phase_g_pr_d_closure.py"
    ]["proposed_disposition"] == "SPLIT_MIXED_CURRENT_HISTORICAL"

    assert records[
        "tests/integration/test_phase_h_imp_7d_deterministic_e2e.py"
    ]["proposed_disposition"] == "KEEP_DEFAULT_REWRITE_BRITTLE"

    assert records[
        "tests/unit/test_m8r_06_04_mode_c.py"
    ]["proposed_disposition"] == "SPLIT_MIXED_CURRENT_HISTORICAL"

    for item in ledger["records"]:
        if item["proposed_disposition"] == "MOVE_HISTORICAL_AFTER_TG3":
            assert "TG-3 historical integrity" in item[
                "prerequisites_before_profile_change"
            ]
        if item["proposed_disposition"] == "MOVE_FULL_CURRENT_NONDEFAULT":
            assert "TG-4 shadow CI" in item[
                "prerequisites_before_profile_change"
            ]


def test_tg1_summary_matches_expected_proposal_shape() -> None:
    summary = _load(LEDGER)["summary"]
    assert summary["proposed_target_profile_counts"] == {
        "default-ci-current": 91,
        "default-ci-current + historical-acceptance": 2,
        "full-current-non-network": 45,
        "historical-acceptance": 16,
        "release-preflight": 2,
    }
    assert sum(summary["proposed_disposition_counts"].values()) == 156

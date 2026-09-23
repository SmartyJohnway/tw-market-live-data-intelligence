from __future__ import annotations

from scripts.audit_test_governance import build_report


def test_tg0_inventory_covers_every_default_ci_path_without_mutating_selection() -> None:
    report = build_report("pre-tg5-default-ci")
    assert report["schema_version"] == "test_governance_inventory.v1"
    assert report["classification_is_advisory"] is True
    assert report["baseline_profile"] == "pre-tg5-default-ci"
    assert report["selection_change_performed"] is False

    metrics = report["metrics"]
    assert metrics["default_ci_file_count"] == 156
    assert metrics["existing_file_count"] == 156
    assert metrics["missing_file_count"] == 0
    assert len(report["records"]) == 156


def test_tg0_inventory_exposes_governance_debt_signals() -> None:
    report = build_report("pre-tg5-default-ci")
    metrics = report["metrics"]

    assert metrics["files_reading_docs"] > 0
    assert metrics["files_with_exact_path_assertion_signal"] > 0
    assert metrics["files_with_next_task_literal_signal"] > 0
    assert metrics["manual_review_required"] > 0

    paths = {record["path"]: record for record in report["records"]}
    historical = paths["tests/unit/test_m8_through_m8b_consolidated_acceptance.py"]
    assert historical["reads_docs"] is True
    assert historical["suggested_class"] in {
        "HISTORICAL_ACCEPTANCE",
        "DOCUMENTATION_GOVERNANCE",
        "REVIEW_REQUIRED",
    }

    public_contracts = paths["tests/unit/test_validate_v1_public_contracts.py"]
    assert public_contracts["reads_readme"] is True
    assert public_contracts["suggested_class"] in {
        "RELEASE_PRECHECK",
        "DOCUMENTATION_GOVERNANCE",
    }

import ast
import csv
from pathlib import Path

from scripts import analyze_test_risk_inventory as analyzer


def _write_test(tmp_path: Path, source: str) -> Path:
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    path = tests_dir / "test_sample.py"
    path.write_text(source, encoding="utf-8")
    return path


def test_inventory_script_detects_test_functions(tmp_path):
    path = _write_test(tmp_path, "def helper():\n    pass\n\ndef test_detected():\n    assert 1 == 1\n")

    rows = analyzer.analyze_file(path, tmp_path, include_assertions=True)

    assert [row.values["test_function"] for row in rows] == ["test_detected"]
    assert rows[0].values["assert_count"] == "1"


def test_inventory_script_detects_parametrized_tests(tmp_path):
    path = _write_test(
        tmp_path,
        "import pytest\n\n@pytest.mark.parametrize('value', [1, 2, 3])\ndef test_param(value):\n    assert value\n",
    )

    row = analyzer.analyze_file(path, tmp_path, include_assertions=False)[0]

    assert row.values["is_parametrized"] == "true"
    assert row.values["parametrize_case_count_estimate"] == "3"
    assert "pytest.mark.parametrize" in row.values["pytest_markers"]


def test_inventory_script_extracts_basic_risk_tags(tmp_path):
    path = _write_test(
        tmp_path,
        "def test_ssl_policy_fail_closed():\n    assert 'invalid ssl_policy fails closed'\n",
    )

    row = analyzer.analyze_file(path, tmp_path, include_assertions=False)[0]

    assert "ssl_policy" in row.values["risk_tags"]
    assert row.values["likely_authoritative_owner"] == "scripts/ssl_policy.py"


def test_inventory_script_emits_required_csv_columns(tmp_path):
    path = _write_test(tmp_path, "def test_one():\n    assert 'conversation context'\n")
    rows = analyzer.analyze_file(path, tmp_path, include_assertions=False)
    output = tmp_path / "inventory.csv"

    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=analyzer.INVENTORY_COLUMNS)
        writer.writeheader()
        writer.writerows([row.values for row in rows])

    header = output.read_text(encoding="utf-8").splitlines()[0].split(",")
    assert header == analyzer.INVENTORY_COLUMNS


def test_inventory_script_marks_tautological_or_true_as_safe_to_auto_retire(tmp_path):
    path = _write_test(
        tmp_path,
        "def test_briefing_wrapper_one():\n    assert 'source_health m5q' or True\n\ndef test_briefing_wrapper_two():\n    assert 'source_health m5q' or True\n",
    )
    rows = analyzer.analyze_file(path, tmp_path, include_assertions=True)

    clusters = analyzer.build_clusters(rows)

    assert clusters[0]["semantic_equivalence_guess"] == "true"
    assert clusters[0]["safe_to_auto_retire"] == "yes"


def test_inventory_script_does_not_mark_partial_or_unknown_clusters_as_safe(tmp_path):
    path = _write_test(
        tmp_path,
        "def test_unknown_one():\n    assert make_value() == 1\n\ndef test_unknown_two():\n    assert make_value() == 2\n",
    )
    rows = analyzer.analyze_file(path, tmp_path, include_assertions=True)

    clusters = analyzer.build_clusters(rows)

    assert {cluster["safe_to_auto_retire"] for cluster in clusters} <= {"no", "manual_review_required"}
    assert "yes" not in {cluster["safe_to_auto_retire"] for cluster in clusters}

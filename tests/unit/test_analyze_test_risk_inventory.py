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


def _tags_for_source(tmp_path: Path, source: str) -> set[str]:
    path = _write_test(tmp_path, source)
    rows = analyzer.analyze_file(path, tmp_path, include_assertions=True)
    return set(rows[0].values["risk_tags"].split(";"))


def test_precision_keyword_fail_alone_is_not_mcp_fail_closed(tmp_path):
    tags = _tags_for_source(tmp_path, "def test_plain_failure_word():\n    assert 'this can fail sometimes'\n")

    assert "mcp_fail_closed" not in tags


def test_precision_keyword_contract_alone_is_not_frontend_static_contract(tmp_path):
    tags = _tags_for_source(tmp_path, "def test_contract_word_only():\n    assert 'source contract exists'\n")

    assert "frontend_static_contract" not in tags


def test_precision_keyword_public_alone_is_not_frontend_public_write(tmp_path):
    tags = _tags_for_source(tmp_path, "def test_public_word_only():\n    assert 'public information'\n")

    assert "frontend_public_write" not in tags


def test_precision_mcp_invalid_request_fail_closed_is_mcp_fail_closed(tmp_path):
    tags = _tags_for_source(
        tmp_path,
        "def test_mcp_invalid_request_fails_closed():\n    result = call_mcp_tool('invalid')\n    assert result['status'] == 'rejected'\n",
    )

    assert "mcp_fail_closed" in tags


def test_precision_ssl_policy_invalid_http_400_is_invalid_ssl_fail_closed(tmp_path):
    tags = _tags_for_source(
        tmp_path,
        "def test_ssl_policy_invalid_returns_http_400():\n    response = client.post('/api/execute', json={'ssl_policy': 'bad'})\n    assert response.status_code == 400\n",
    )

    assert "invalid_ssl_fail_closed" in tags


def test_precision_frontend_public_exact_path_tags_write(tmp_path):
    tags = _tags_for_source(
        tmp_path,
        "def test_frontend_public_output_rejected():\n    assert 'frontend/public/latest.json'\n",
    )

    assert "frontend_public_write" in tags


def test_precision_frontend_static_requires_frontend_and_static_contract(tmp_path):
    tags = _tags_for_source(
        tmp_path,
        "def test_frontend_static_contract_tokens():\n    assert '<script src=app.js></script>'\n",
    )

    assert "frontend_static_contract" in tags


def test_cluster_key_uses_primary_risk_target_and_assertion_shape(tmp_path):
    path = _write_test(
        tmp_path,
        "def test_mcp_invalid_request_fails_closed():\n    result = call_mcp_tool('invalid')\n    assert result['status'] == 'rejected'\n",
    )

    row = analyzer.analyze_file(path, tmp_path, include_assertions=True)[0]

    assert row.values["risk_cluster_key"] == "mcp_fail_closed:call_mcp_tool:equals"

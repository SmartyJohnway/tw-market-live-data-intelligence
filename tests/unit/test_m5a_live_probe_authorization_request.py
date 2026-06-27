from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.validate_live_probe_authorization_request import validate_request, validate_request_file

SCHEMA = json.loads((ROOT / "docs/authorization/live_probe_authorization_request_schema.json").read_text(encoding="utf-8"))
REGISTRY = json.loads((ROOT / "docs/source_registry/source_authority_registry.json").read_text(encoding="utf-8"))
VALID_FIXTURE = ROOT / "tests/fixtures/authorization/valid_m5a_live_probe_request.json"
INVALID_FIXTURE = ROOT / "tests/fixtures/authorization/invalid_m5a_live_probe_requests.json"
NOW = datetime(2026, 6, 27, tzinfo=timezone.utc)


def load_valid():
    return json.loads(VALID_FIXTURE.read_text(encoding="utf-8"))


def test_valid_m5a_request_is_ready_for_user_authorization_review():
    result = validate_request_file(VALID_FIXTURE, now=NOW)
    assert result["ok"] is True
    assert result["result"] == "ready_for_user_authorization_review"
    assert result["live_probe_authorized"] is False
    assert result["authorization_token_issued"] is False
    assert result["execution_performed"] is False
    assert result["writes"] is False
    assert result["network_used"] is False


def test_invalid_fixture_cases_fail_with_expected_structured_codes():
    cases = json.loads(INVALID_FIXTURE.read_text(encoding="utf-8"))
    for case in cases:
        errors = validate_request(case["request"], SCHEMA, REGISTRY, now=NOW)
        codes = {error["code"] for error in errors}
        assert errors, case["case_id"]
        assert set(case["expected_codes"]).issubset(codes), case["case_id"]


def test_rejects_unknown_empty_duplicate_and_too_many_targets():
    request = load_valid()
    request["targets"] = ["2330", "", "2330", "8069", "TAIEX", "0050"]
    errors = validate_request(request, SCHEMA, REGISTRY, now=NOW)
    codes = {error["code"] for error in errors}
    assert "schema_validation_failed" in codes
    assert "too_many_targets" in codes
    assert "duplicate_targets" in codes
    assert "source_target_mapping_unresolved" in codes


def test_rejects_source_not_requiring_live_authorization():
    request = load_valid()
    request["source_id"] = "Fixture_Synthetic"
    request["source_risk_flags"] = ["fixture_only", "validation_only"]
    errors = validate_request(request, SCHEMA, REGISTRY, now=NOW)
    codes = {error["code"] for error in errors}
    assert "schema_validation_failed" in codes
    assert "source_not_live_probe_authorization_required" in codes


def test_malformed_request_returns_structured_failure_without_traceback(tmp_path):
    malformed = tmp_path / "malformed.json"
    malformed.write_text('{"request_id": ', encoding="utf-8")
    result = validate_request_file(malformed, now=NOW)
    assert result["ok"] is False
    assert result["errors"][0]["code"] == "malformed_json"
    assert result["execution_performed"] is False
    assert result["writes"] is False
    assert result["network_used"] is False


def test_cli_check_only_valid_request_passes():
    completed = subprocess.run(
        [sys.executable, "scripts/validate_live_probe_authorization_request.py", "--request", str(VALID_FIXTURE)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["ok"] is True
    assert payload["execution_performed"] is False
    assert payload["writes"] is False
    assert payload["network_used"] is False


def test_cli_malformed_request_fails_without_traceback(tmp_path):
    malformed = tmp_path / "malformed.json"
    malformed.write_text("{", encoding="utf-8")
    completed = subprocess.run(
        [sys.executable, "scripts/validate_live_probe_authorization_request.py", "--request", str(malformed)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 1
    assert "Traceback" not in completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["errors"][0]["code"] == "malformed_json"


def test_m3g04_runner_cannot_be_marked_ready_for_m5b_output_path():
    request = load_valid()
    request["proposed_probe_script"] = "scripts/run_m3g04_controlled_live_probe.py"
    errors = validate_request(request, SCHEMA, REGISTRY, now=NOW)
    assert any(error["code"] == "probe_script_output_dir_unsupported" for error in errors)


def test_absolute_and_traversal_script_paths_are_rejected_before_normalization():
    for script_path in ["/scripts/run_m5b_controlled_live_probe.py", "../scripts/run_m5b_controlled_live_probe.py", "C:/scripts/run_m5b_controlled_live_probe.py"]:
        request = load_valid()
        request["proposed_probe_script"] = script_path
        errors = validate_request(request, SCHEMA, REGISTRY, now=NOW)
        assert any(error["code"] == "probe_script_path_not_relative_safe" for error in errors), script_path


def test_file_level_errors_have_complete_result_envelope(tmp_path):
    missing_schema = tmp_path / "missing_schema.json"
    result = validate_request_file(VALID_FIXTURE, schema_path=missing_schema, now=NOW)
    assert result["ok"] is False
    assert result["result"] == "blocked"
    assert result["live_probe_authorized"] is False
    assert result["authorization_token_issued"] is False
    assert result["execution_performed"] is False
    assert result["writes"] is False
    assert result["network_used"] is False


def test_malformed_request_result_is_repair_required_with_complete_envelope(tmp_path):
    malformed = tmp_path / "malformed.json"
    malformed.write_text("{", encoding="utf-8")
    result = validate_request_file(malformed, now=NOW)
    assert result["ok"] is False
    assert result["result"] == "repair_required"
    assert result["live_probe_authorized"] is False
    assert result["authorization_token_issued"] is False
    assert result["execution_performed"] is False
    assert result["writes"] is False
    assert result["network_used"] is False


def test_bounded_mapping_consistency_with_existing_controlled_runner_for_mis_and_yahoo():
    from scripts.run_m3g04_controlled_live_probe import map_targets_for_source
    from scripts.validate_live_probe_authorization_request import SOURCE_TARGET_MAP

    targets = ["2330", "0050", "00929", "8069", "TAIEX"]
    assert set(targets).issubset(SOURCE_TARGET_MAP["TWSE_MIS"])
    assert map_targets_for_source("TWSE_MIS", targets) == ["tse_2330.tw", "tse_0050.tw", "tse_00929.tw", "otc_8069.tw", "tse_t00.tw"]
    assert set(targets).issubset(SOURCE_TARGET_MAP["Yahoo_Finance"])
    assert map_targets_for_source("Yahoo_Finance", targets) == ["2330.TW", "0050.TW", "00929.TW", "8069.TWO", "^TWII"]

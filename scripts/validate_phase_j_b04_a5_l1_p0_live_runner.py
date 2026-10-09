"""Machine-check network-free L1-P0 live-runner controls and dormant state."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
STARTING_HEAD = "0aa73c9369200ec855143f26de16bf58430af5d3"
STARTING_TREE = "a4a691b47205236d950fb9ed4e6c85a6d79877fc"
STARTING_MAIN = "6daf6e2dcc6fd34e00e7e3831c25e98bb4d2399a"
IMPLEMENTATION_HEAD = "6675b64a2a84632edd64e948e1adf6a2b88fc24e"
IMPLEMENTATION_TREE = "b22adc8c96de9446a3b82e1c90f1396c827eaf98"
RECORD = ROOT / "docs/governance/phase_j/PHASE_J_J_B04_A5_L1_P0_LIVE_RUNNER_HARDENING_2026-10-09.json"
P0_RECORD = ROOT / "docs/governance/phase_j/PHASE_J_J_B04_A5_BOUNDED_LIVE_PREFLIGHT_2026-10-09.json"
RULE = "prefer normalizable TWSE:2330; otherwise lexicographically smallest (Code, Date, canonical raw-row SHA-256) among normalizable rows"
FORBIDDEN = {"raw_bytes", "rows", "rows_in_memory", "raw_payload", "raw_body", "source_rows", "full_payload"}


def _strict(path: Path) -> dict[str, Any]:
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise AssertionError(f"duplicate_json_key:{key}")
            out[key] = value
        return out
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs)


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def validate_contract(record: dict[str, Any]) -> dict[str, Any]:
    assert record["gate"] == "J-B04-A5-L1-P0"
    assert record["starting_head"] == STARTING_HEAD
    assert record["starting_tree"] == STARTING_TREE
    assert record["starting_main"] == STARTING_MAIN
    assert record["P0_R2"] == "PASS"
    assert record["live_runner_implemented"] is True
    assert record["real_live_execution"] is False
    assert record["owner_live_authorization"] == "NOT PRESENT"
    assert record["network_calls"] == {"market_GET": 0, "market_HEAD": 0, "market_POST": 0,
        "security_master_live_acquisition": 0}
    assert record["canonical_state"] == {"H2_runtime": "INACTIVE", "selected_executor_id": None,
        "J-B04": "BLOCKING", "Phase J": "NOT_STARTED", "MCP": 6}
    assert record["authorization_contract"]["required_cli_flags"] == ["--live-acceptance",
        "--execution-environment", "--owner-authorization-json", "--execution-lease-file"]
    assert record["authorization_contract"]["external_file_required"] is True
    assert record["authorization_contract"]["execution_lease_required"] is True
    assert record["authorization_contract"]["max_market_gets"] == 10
    assert record["authorization_contract"]["consumed_field_required"] is False
    assert "execution_instance_lease_sha256" in record["authorization_contract"]["record_fields"]
    assert record["authority_consumption"]["historical_state"] == "CONSUMED_BEFORE_TRANSPORT"
    assert record["authority_consumption"]["state"] == "HISTORICAL_R1_SINGLE_USE_CONTRACT_SUPERSEDED_BY_R2_SESSION_POLICY"
    assert record["authority_consumption"]["current_state"] == "ATTEMPT_RESERVED_BEFORE_TRANSPORT"
    assert "execution_instance_lease_sha256" in record["authority_consumption"]["attempt_receipt_fields"]
    assert record["authority_consumption"]["exclusive_atomic_create"] is True
    assert record["stage_witness_selection_policy"] == RULE
    assert record["raw_payload_persistence"] == "NONE"
    assert record["persistable_telemetry_fields"] == ["http_status", "content_type", "effective_url",
        "response_byte_count", "response_sha256", "json_root_type", "root_row_count", "retrieved_at",
        "logical_get_attempts", "http_dispatch_attempts", "retry_count", "redirect_result"]
    assert record["forbidden_persisted_raw_fields"] == sorted(FORBIDDEN)
    default_ci = record["default_ci_comparison"]
    assert default_ci["base"] == STARTING_MAIN
    assert default_ci["head"] == IMPLEMENTATION_HEAD and default_ci["head_tree"] == IMPLEMENTATION_TREE
    assert default_ci["environment"] == {"TZ": "Etc/UTC", "PYTHONHASHSEED": "0"}
    assert default_ci["base_collected"] == default_ci["head_collected"] == 1230
    assert default_ci["base_selected"] == default_ci["head_selected"] == 1225
    assert default_ci["base_collection_errors"] == default_ci["head_collection_errors"] == 5
    assert default_ci["base_test_passes"] is None and default_ci["head_test_passes"] is None
    assert default_ci["shared_failed_node_ids"] == [
        "tests/unit/test_twse_mis_normalization_v2.py", "tests/unit/test_twse_openapi_normalization_v1.py",
        "tests/unit/test_tpex_openapi_normalization_v1.py", "tests/unit/test_yahoo_normalized_chart_v1.py",
        "tests/unit/test_m8c_01_taifex_mis_runtime.py"]
    assert default_ci["new_failed_node_ids"] == [] and default_ci["resolved_failed_node_ids"] == []
    assert default_ci["new_failure_delta"] == 0
    return {"status": "PASS", "disposition": record["disposition"]}


def validate_repository() -> dict[str, Any]:
    record = _strict(RECORD)
    p0 = _strict(P0_RECORD)
    assert p0["preflight_status"] == "J_B04_A5_P0_R2_READY_FOR_EXACT_HEAD_INDEPENDENT_REVIEW"
    assert p0["execution_environment_class"] == "cloud_clean_source_acceptance"
    assert p0["security_master_status"] == "NOT_INITIALIZED"
    assert p0["identity_assurance_level"] == "acceptance_only_predeclared_source_target"
    assert p0["production_identity_verified"] is False and p0["A6_identity_reverification_required"] is True
    assert p0["secondary_stage_witness_policy"] == RULE

    from scripts.phase_j_b04_a5_bounded_live_acceptance import (
        ENDPOINT, MAX_BYTES, STARTING_MAIN as RUNNER_MAIN, STAGE_WITNESS_POLICY,
        TIMEOUT, _safe_capture_response, validate_live_runtime_invariants,
    )
    from scripts.phase_j_b04_a5_bounded_live_acceptance import run_live_acceptance
    assert RUNNER_MAIN == STARTING_MAIN and ENDPOINT == "https://openapi.twse.com.tw/v1/exchangeReport/TWT48U_ALL"
    assert MAX_BYTES == 4 * 1024 * 1024 and TIMEOUT <= 15
    assert STAGE_WITNESS_POLICY == RULE
    source = (ROOT / "scripts/phase_j_b04_a5_bounded_live_acceptance.py").read_text(encoding="utf-8")
    live_source = __import__("inspect").getsource(run_live_acceptance)
    assert 'parser.add_argument("--live-acceptance"' in source
    assert 'parser.add_argument("--execution-environment"' in source
    assert 'parser.add_argument("--owner-authorization-json"' in source
    assert 'parser.add_argument("--prepare-execution-lease"' in source
    assert 'parser.add_argument("--execution-lease-file"' in source
    assert "official_get_once" in source
    assert source.count("official_get_once") == 2
    assert live_source.count("response = transport(timeout_seconds=TIMEOUT)") == 1
    assert "derive_h4_for_completed_plan" in source
    assert "reserve_next_session_attempt" in live_source
    assert live_source.index("load_execution_lease(Path(") < live_source.index("reserve_next_session_attempt(session_root")
    assert "attempt_reserved.json" in source
    assert live_source.index("reserve_next_session_attempt(session_root") < live_source.index("transport(timeout_seconds=TIMEOUT)")
    assert "retry_count\": 0" in live_source and "redirect_follow_count\": 0" in live_source

    fake_response = {"raw_bytes": b"[]", "status": 200, "content_type": "application/json",
        "effective_url": ENDPOINT, "retrieved_at": "2026-10-09T00:00:00Z"}
    capture = _safe_capture_response(fake_response)
    assert capture.rows == []
    assert not (FORBIDDEN & set(capture.telemetry))
    assert set(capture.telemetry) == {"http_status", "content_type", "effective_url", "response_byte_count",
        "response_sha256", "json_root_type", "root_row_count", "retrieved_at"}
    capture.release()
    assert capture.raw_bytes == b"" and capture.rows is None

    validate_live_runtime_invariants({"preflight_status": p0["preflight_status"],
        "security_master_status": "NOT_INITIALIZED", "identity_assurance_level": p0["identity_assurance_level"],
        "production_identity_verified": False, "A6_identity_reverification_required": True})
    from scripts.validate_phase_j_b04_a5_bounded_live_acceptance import validate_repository as validate_p0
    validate_p0()
    assert _git("rev-parse", "origin/main") == STARTING_MAIN
    assert _git("rev-parse", f"{IMPLEMENTATION_HEAD}^{{tree}}") == IMPLEMENTATION_TREE
    for frozen in ("server/services/phase_h_h2_twse_exright_executor.py",
        "server/services/phase_h_corporate_action_adapters.py", "server/services/phase_h_discontinuity_safety.py",
        "schemas/corporate_action_context_evidence.v1.schema.json", "schemas/recent_performance_evidence.v1.schema.json",
        "schemas/discontinuity_safety_evidence.v1.schema.json", "schemas/unified_market_evidence_result.v3.schema.json",
        "schemas/unified_market_evidence_audit_package.v3.schema.json"):
        assert _git("diff", "--quiet", STARTING_MAIN, "HEAD", "--", frozen) == ""

    test_text = (ROOT / "tests/unit/test_phase_j_b04_a5_l1_runner.py").read_text(encoding="utf-8")
    for required in ("test_fake_e2e_pass", "test_fake_zero_rows", "test_primary_row_is_preferred",
        "test_secondary_stage_witness_selection", "test_ambiguous_primary_rows", "test_fake_transport_failure",
        "test_stale_head_tree_or_main", "test_invalid_security_master", "test_cloud_not_initialized",
        "test_raw_key_persistence_mutation"):
        assert required in test_text
    assert not any(path.is_file() for path in (ROOT / "docs/governance/phase_j/acceptance_runs").rglob("*"))
    return validate_contract(record) | {"p0_validator": "PASS", "market_GET_HEAD_POST": "0/0/0",
        "security_master_live_calls": 0, "mcp_tool_count": 6}


if __name__ == "__main__":
    print(json.dumps(validate_repository(), indent=2, sort_keys=True))

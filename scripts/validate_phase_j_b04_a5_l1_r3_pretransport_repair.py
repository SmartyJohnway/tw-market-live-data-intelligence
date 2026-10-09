"""Validate the A5 cold-start adapter repair and immutable Session #1 evidence."""
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
RECORD = ROOT / "docs/governance/phase_j/PHASE_J_J_B04_A5_L1_R3_PRETRANSPORT_INCIDENT_AND_REPAIR_2026-10-09.json"
SESSION = ROOT / "docs/governance/phase_j/acceptance_runs/j-b04-a5-session-78e1b2c1db127926"
BASE = "e70f866fb6192ca0f0386c18ee55d56284d2ced2"
TREE = "5e4036f82e1be1174459b3bd89319bae97f08832"
MAIN = "6daf6e2dcc6fd34e00e7e3831c25e98bb4d2399a"


def _strict(path: Path) -> Any:
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise AssertionError(f"duplicate_json_key:{path}:{key}")
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs)


def validate_contract(record: dict[str, Any]) -> dict[str, str]:
    assert record["gate"] == "J-B04-A5-L1-R3"
    assert record["starting_head"] == BASE and record["starting_tree"] == TREE and record["main"] == MAIN
    incident = record["incident"]
    assert incident == {"session_directory": "j-b04-a5-session-78e1b2c1db127926",
        "disposition": "J_B04_A5_BLOCKED_SOURCE_CONTRACT_OR_IMPLEMENTATION_REVIEW_REQUIRED",
        "terminal_reason": "HARD_BLOCK", "attempt_reserved": 1, "transport_attempted": False,
        "logical_GET": 0, "HTTP_dispatch": 0, "source_contacted": False,
        "incident_class": "PRETRANSPORT_RUNNER_OR_RUNTIME_DEFECT", "session_remains_terminal": True}
    diagnostics = record["cold_start_diagnostics"]
    assert diagnostics["diagnostic_A_direct_h2_import"] == {"result": "FAIL", "exception_module": "builtins",
        "exception_type": "ImportError", "exception_message": "cannot import name 'derive_h4_for_completed_plan' from partially initialized module 'server.services.phase_h_h2_twse_exright_executor' (most likely due to a circular import) (/workspace/tw-market-a5/server/services/phase_h_h2_twse_exright_executor.py)"}
    assert diagnostics["diagnostic_B_package_first_import"] == {"result": "PASS", "callable": True}
    assert diagnostics["pretransport_artifact_init"] == "PASS"
    assert diagnostics["root_cause"] == "J_B04_A5_R3_ROOT_CAUSE_CONFIRMED_COLD_START_IMPORT_ORDER"
    repair = record["repair"]
    assert repair["resolver_before_attempt_reservation"] is True
    assert repair["adapter_resolution_failure_disposition"] == "J_B04_A5_LIVE_TRANSPORT_ADAPTER_UNAVAILABLE"
    assert repair["adapter_failure_reserves_attempt"] is False and repair["adapter_failure_logical_GET"] == 0
    assert repair["session_1_modified"] is False
    assert record["real_R3_live_calls"] == 0
    assert record["new_production_execution_lease_prepared"] is False
    assert record["new_owner_authorization_created"] is False
    assert record["network_calls"] == {"market_GET": 0, "market_HEAD": 0, "market_POST": 0,
        "security_master_live_acquisition": 0}
    assert record["canonical_state"] == {"H2_runtime": "INACTIVE", "selected_executor_id": None,
        "J-B04": "BLOCKING", "Phase J": "NOT_STARTED", "MCP": 6}
    return {"status": "PASS", "root_cause": diagnostics["root_cause"]}


def validate_repository() -> dict[str, Any]:
    record = _strict(RECORD)
    validate_contract(record)
    from scripts.phase_j_b04_a5_bounded_live_acceptance import (
        FAILURE_STAGES, MAX_SESSION_GETS, ENDPOINT, STARTING_MAIN,
        resolve_production_transport_adapter, run_live_acceptance,
        _verify_session_package, _canonical_runtime_state,
    )
    assert STARTING_MAIN == MAIN and MAX_SESSION_GETS == 10
    assert ENDPOINT == "https://openapi.twse.com.tw/v1/exchangeReport/TWT48U_ALL"
    expected_stages = {"authorization_validation", "runtime_preflight", "lease_validation",
        "transport_adapter_resolution", "session_initialization", "attempt_reservation",
        "attempt_artifact_initialization", "transport", "source_decode", "h2_replay",
        "h4_replay", "evidence_finalization"}
    assert FAILURE_STAGES == expected_stages

    resolver_source = __import__("inspect").getsource(resolve_production_transport_adapter)
    live_source = __import__("inspect").getsource(run_live_acceptance)
    assert "import scripts.m8r_05b_03" in resolver_source
    assert "from server.services.phase_h_h2_twse_exright_executor import official_get_once" in resolver_source
    assert "callable(official_get_once)" in resolver_source and "return official_get_once" in resolver_source
    assert "official_get_once(" not in resolver_source
    for marker in ("load_execution_lease(Path(", "resolve_production_transport_adapter",
                   "final_head, final_tree, final_main", "ensure_session_authorization(session_root",
                   "reserve_next_session_attempt(session_root", "response = transport(timeout_seconds=TIMEOUT)"):
        assert marker in live_source
    positions = [live_source.index(marker) for marker in ("load_execution_lease(Path(",
        "resolve_production_transport_adapter", "final_head, final_tree, final_main",
        "ensure_session_authorization(session_root", "reserve_next_session_attempt(session_root",
        "response = transport(timeout_seconds=TIMEOUT)")]
    assert positions == sorted(positions)
    assert live_source.count("response = transport(timeout_seconds=TIMEOUT)") == 1

    source = (ROOT / "scripts/phase_j_b04_a5_bounded_live_acceptance.py").read_text(encoding="utf-8")
    assert '"J_B04_A5_LIVE_TRANSPORT_ADAPTER_UNAVAILABLE"' in source
    assert '"failure_stage": exc.failure_stage or fallback_stage' in source
    assert '"exception_module"' in source and '"exception_type"' in source
    assert _canonical_runtime_state() == {"H2_source_runtime_executable": False,
        "corporate_action_context_routing": "plan_only", "selected_executor_id": None,
        "H2_runtime": "INACTIVE", "J-B04": "BLOCKING", "Phase J": "NOT_STARTED", "MCP": 6}

    expected_hashes = record["session_1_artifact_sha256"]
    actual_paths = {path.relative_to(SESSION).as_posix(): path for path in SESSION.rglob("*") if path.is_file()}
    assert set(actual_paths) == set(expected_hashes)
    actual_hashes = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in actual_paths.items()}
    assert actual_hashes == expected_hashes
    assert _verify_session_package(SESSION) is True
    terminal = _strict(SESSION / "session_terminal.json")
    assert terminal["terminal"] is True and terminal["terminal_reason"] == "HARD_BLOCK"
    attempt = _strict(SESSION / "attempt-001/transport_attempt.json")
    assert attempt["transport_attempted"] is False and attempt["logical_get_attempts"] == 0
    assert attempt["actual_http_dispatch_attempts"] == 0
    assert attempt["failure_class"] == "runner_or_source_failure"

    tests = (ROOT / "tests/unit/test_phase_j_b04_a5_l1_runner.py").read_text(encoding="utf-8")
    assert "test_cold_start_subprocess_resolves_production_adapter_without_network" in tests
    assert "test_adapter_resolution_failure_precedes_attempt_reservation" in tests
    assert "test_live_cli_reports_sanitized_pretransport_failure_stage" in tests
    for frozen in ("server/services/phase_h_h2_twse_exright_executor.py",
        "server/services/phase_h_corporate_action_adapters.py", "server/services/phase_h_discontinuity_safety.py"):
        assert subprocess.check_output(["git", "diff", "--quiet", BASE, "HEAD", "--", frozen], cwd=ROOT) == b""
    assert subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=ROOT, text=True).strip() == MAIN

    from scripts.validate_phase_j_b04_a5_bounded_live_acceptance import validate_repository as validate_p0
    from scripts.validate_phase_j_b04_a5_l1_p0_live_runner import validate_repository as validate_l1
    from scripts.validate_phase_j_b04_a5_l1_p0_r1_execution_lease import validate_repository as validate_r1
    from scripts.validate_phase_j_b04_a5_l1_p0_r2_bounded_session import validate_repository as validate_r2
    validate_p0()
    validate_l1()
    validate_r1()
    validate_r2()
    return {"status": "PASS", "Session_1_immutable_terminal": True,
        "Session_1_raw_body_absence": True, "P0_L1_R1_R2_validators": "PASS",
        "Market_GET_HEAD_POST": "0/0/0", "Security_Master_live_calls": 0, "MCP": 6}


if __name__ == "__main__":
    print(json.dumps(validate_repository(), indent=2, sort_keys=True))

"""Machine-check the network-free A5 bounded-session authority contract."""
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
BASE = "1e84554c250d92e05b44eb8a543cd76fc154e55b"
TREE = "e334c92f20db5be0813b254665c7ebdada4552ca"
MAIN = "6daf6e2dcc6fd34e00e7e3831c25e98bb4d2399a"
MAX_GETS = 10
ENDPOINT = "https://openapi.twse.com.tw/v1/exchangeReport/TWT48U_ALL"
RECORD = ROOT / "docs/governance/phase_j/PHASE_J_J_B04_A5_L1_P0_R2_BOUNDED_LIVE_SESSION_2026-10-09.json"
L1_RECORD = ROOT / "docs/governance/phase_j/PHASE_J_J_B04_A5_L1_P0_LIVE_RUNNER_HARDENING_2026-10-09.json"
R1_RECORD = ROOT / "docs/governance/phase_j/PHASE_J_J_B04_A5_L1_P0_R1_EXECUTION_INSTANCE_LEASE_HARDENING_2026-10-09.json"
RULE = "prefer normalizable TWSE:2330; otherwise lexicographically smallest (Code, Date, canonical raw-row SHA-256) among normalizable rows"


def _json(path: Path) -> Any:
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise AssertionError(f"duplicate_json_key:{path}:{key}")
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs)


def validate_contract(record: dict[str, Any]) -> dict[str, str]:
    assert record["gate"] == "J-B04-A5-L1-P0-R2"
    assert record["starting_head"] == BASE and record["starting_tree"] == TREE
    assert record["main"] == MAIN
    assert record["owner_policy_change"] == "one exact-head, tree, and execution-lease-bound authorization permits up to 10 total TWT48U GET attempts in one session"
    assert record["max_market_gets"] == MAX_GETS
    assert record["per_attempt_get_maximum"] == record["per_attempt_http_dispatch_maximum"] == 1
    assert record["per_attempt_internal_retry"] == 0 and record["redirect_follow"] == 0
    assert record["stop_on_pass"] is True and record["stop_on_hard_block"] is True
    assert record["reattempt_eligible_dispositions"] == [
        "J_B04_A5_INCONCLUSIVE_TRANSIENT_SOURCE_FAILURE_NO_ACTIVATION",
        "J_B04_A5_INCONCLUSIVE_LIVE_STAGE_SAMPLE_UNAVAILABLE"]
    assert record["execution_instance_lease_required"] is True
    assert record["production_execution_lease_prepared"] is False
    assert record["owner_live_authorization"] == "NOT PRESENT"
    assert record["real_live_execution"] is False
    assert record["network_calls"] == {"market_GET": 0, "market_HEAD": 0, "market_POST": 0,
        "security_master_live_acquisition": 0}
    assert record["canonical_state"] == {"H2_runtime": "INACTIVE", "selected_executor_id": None,
        "J-B04": "BLOCKING", "Phase J": "NOT_STARTED", "MCP": 6}
    assert record["future_authorization_schema"]["required_fields"] == ["gate", "authorized_head_sha",
        "authorized_tree_sha", "execution_environment_class", "execution_instance_lease_sha256",
        "max_market_gets", "statement", "statement_sha256"]
    assert record["future_authorization_schema"]["max_market_gets"] == MAX_GETS
    assert record["future_authorization_schema"]["consumed_field"] == "not present"
    assert record["future_owner_statement_template"].startswith(
        "AUTHORIZE J-B04-A5 BOUNDED LIVE SESSION ON HEAD <EXACT_HEAD_SHA>\nWITH EXECUTION LEASE <EXECUTION_INSTANCE_LEASE_SHA256>:")
    assert "up to 10 GET attempts total" in record["future_owner_statement_template"]
    assert record["session_directory_pattern"] == "j-b04-a5-session-<STATEMENT_SHA_PREFIX>"
    assert record["attempt_reservation"]["path_pattern"] == "attempt-NNN/attempt_reserved.json"
    assert record["attempt_reservation"]["state"] == "RESERVED_BEFORE_TRANSPORT"
    assert record["attempt_reservation"]["authoritative_for_budget"] is True
    assert record["attempt_reservation"]["numbers"] == "contiguous 1..10; crash-reserved slots count"
    assert record["terminal_states"] == {"PASS": True, "HARD_BLOCK": True, "BUDGET_EXHAUSTED": True}
    assert record["session_state_policy"]["derived_from_attempt_receipts"] is True
    assert record["session_state_policy"]["same_authorization_reused_for_eligible_inconclusive"] is True
    assert record["session_state_policy"]["attempt_11_possible"] is False
    assert record["stage_witness_rule"] == RULE
    assert record["raw_payload_persistence"] == "NONE"
    assert record["historical_policy"]["R1_single_use"] == "superseded in attempt-budget policy only"
    assert record["historical_policy"]["execution_lease"] == "preserved"
    return {"status": "PASS", "disposition": record["disposition"]}


def validate_repository() -> dict[str, Any]:
    record = _json(RECORD)
    validate_contract(record)
    l1 = _json(L1_RECORD)
    r1 = _json(R1_RECORD)
    assert l1["authority_consumption"]["state"] == "HISTORICAL_R1_SINGLE_USE_CONTRACT_SUPERSEDED_BY_R2_SESSION_POLICY"
    assert l1["authority_consumption"]["current_state"] == "ATTEMPT_RESERVED_BEFORE_TRANSPORT"
    assert l1["authorization_contract"]["max_market_gets"] == MAX_GETS
    assert r1["attempt_budget_policy_status"] == "HISTORICAL_SINGLE_USE_MODEL_SUPERSEDED_BY_R2_BOUNDED_SESSION"
    assert r1["R1_lease_protection_status"] == "PRESERVED"

    from scripts.phase_j_b04_a5_bounded_live_acceptance import (
        ENDPOINT as RUNNER_ENDPOINT, MAX_SESSION_GETS, BoundedSessionAuthority,
        expected_owner_statement, reserve_next_session_attempt, run_live_acceptance,
    )
    assert RUNNER_ENDPOINT == ENDPOINT and MAX_SESSION_GETS == MAX_GETS
    lease_hash = hashlib.sha256(b"R2 validator fixture only").hexdigest()
    statement = expected_owner_statement("a" * 40, lease_hash)
    assert statement == record["future_owner_statement_example"]
    auth = {"gate": "J-B04-A5", "authorized_head_sha": "a" * 40, "authorized_tree_sha": "b" * 40,
        "execution_environment_class": "cloud_clean_source_acceptance", "execution_instance_lease_sha256": lease_hash,
        "max_market_gets": 10, "statement": statement,
        "statement_sha256": hashlib.sha256(statement.encode("utf-8")).hexdigest()}
    assert BoundedSessionAuthority(auth, head="a" * 40, tree="b" * 40)
    for maximum in (0, -1, 11, True, 10.0, "10"):
        altered = {**auth, "max_market_gets": maximum}
        try:
            BoundedSessionAuthority(altered, head="a" * 40, tree="b" * 40)
        except Exception:
            pass
        else:
            raise AssertionError(f"invalid_maximum_accepted:{maximum!r}")
    old_statement = statement.replace("BOUNDED LIVE SESSION", "LIVE")
    altered = {**auth, "statement": old_statement,
        "statement_sha256": hashlib.sha256(old_statement.encode()).hexdigest()}
    try:
        BoundedSessionAuthority(altered, head="a" * 40, tree="b" * 40)
    except Exception:
        pass
    else:
        raise AssertionError("old_single_get_statement_accepted")

    source = (ROOT / "scripts/phase_j_b04_a5_bounded_live_acceptance.py").read_text(encoding="utf-8")
    live = __import__("inspect").getsource(run_live_acceptance)
    assert 'parser.add_argument("--live-acceptance"' in source
    assert 'parser.add_argument("--owner-authorization-json"' in source
    assert 'parser.add_argument("--execution-lease-file"' in source
    assert "reserve_next_session_attempt" in live
    assert live.count("response = transport(timeout_seconds=TIMEOUT)") == 1
    assert live.index("reserve_next_session_attempt(session_root") < live.index("transport(timeout_seconds=TIMEOUT)")
    assert "session_execution_lock" in source
    assert 'f"attempt-{number:03d}"' in source and "RESERVED_BEFORE_TRANSPORT" in source
    assert "attempts_completed" in source and "attempts_remaining" in source
    assert '"PASS"' in source and '"HARD_BLOCK"' in source and '"BUDGET_EXHAUSTED"' in source
    assert "list(range(1, len(numbers) + 1))" in source
    assert "MAX_SESSION_GETS = 10" in source
    assert '"retry_count": 0' in live and '"redirect_follow_count": 0' in live

    tests = (ROOT / "tests/unit/test_phase_j_b04_a5_l1_runner.py").read_text(encoding="utf-8")
    required = ["test_transient_attempt_one_then_pass_attempt_two_terminates_session",
        "test_ten_inconclusive_attempts_exhaust_budget_and_attempt_eleven_is_blocked",
        "test_fake_e2e_pass_reserves_attempt_replays_h2_h4_and_persists_no_raw",
        "test_hard_block_on_attempt_two_terminates_without_attempt_three",
        "test_crash_after_reservation_counts_slot_and_next_invocation_uses_two",
        "test_concurrent_attempt_reservations_allocate_distinct_slots",
        "test_cloud_workspace_loss_replay_requires_original_lease",
        "test_git_change_after_first_attempt_terminalizes_session_before_next_get"]
    assert all(name in tests for name in required)
    from scripts.validate_phase_j_b04_a5_bounded_live_acceptance import validate_repository as validate_p0
    from scripts.validate_phase_j_b04_a5_l1_p0_live_runner import validate_repository as validate_l1
    from scripts.validate_phase_j_b04_a5_l1_p0_r1_execution_lease import validate_repository as validate_r1
    validate_p0()
    validate_l1()
    validate_r1()
    runs = ROOT / "docs/governance/phase_j/acceptance_runs"
    assert not any(path.is_file() for path in runs.rglob("*")) if runs.exists() else True
    main = subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=ROOT, text=True).strip()
    assert main == MAIN
    return {"status": "PASS", "P0_validator": "PASS", "L1_validator": "PASS", "R1_validator": "PASS",
        "origin_main": main, "market_GET_HEAD_POST": "0/0/0", "Security_Master_live_calls": 0, "MCP": 6}


if __name__ == "__main__":
    print(json.dumps(validate_repository(), indent=2, sort_keys=True))

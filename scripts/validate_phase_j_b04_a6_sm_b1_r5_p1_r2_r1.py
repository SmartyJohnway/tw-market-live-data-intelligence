#!/usr/bin/env python3
"""Validate the network-free TPEx fail-closed implementation repair."""
from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "docs/governance/phase_j/PHASE_J_J_B04_A6_SM_B1_R5_P1_R2_R1_PRODUCTION_FAIL_CLOSED_REPAIR_2026-10-10.json"
MATERIALIZER = ROOT / "scripts/m8r_06_01b_materialize_production_inputs.py"
TESTS = ROOT / "tests/unit/test_m8r_06_01b_bootstrap_dispatch_budget.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    record = json.loads(RECORD.read_text(encoding="utf-8"))
    assert record["gate"] == "J-B04-A6-SM-B1-R5-P1-R2-R1"
    assert record["starting_authority"] == {
        "head": "6bc39b5a86a6af3ac3bc726117ef62a9bed2e35f",
        "tree": "0fd18c1c6f83f5919bcc87a3083d9cd64cb5534e",
        "main": "6daf6e2dcc6fd34e00e7e3831c25e98bb4d2399a",
        "tracked_worktree_clean": True,
    }
    assert record["review_id"] == "5478330630"
    assert record["implementation"]["commit"] == "76e60b50ca835f56f52d7e6efec77191057cfde0"

    source = MATERIALIZER.read_text(encoding="utf-8")
    tree = ast.parse(source)
    main_fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
    loops = sorted((n for n in ast.walk(main_fn) if isinstance(n, ast.For)), key=lambda n: n.lineno)
    identity_loop = next(n for n in loops if isinstance(n.target, ast.Name) and n.target.id == "mode")
    lifecycle_loop = next(n for n in loops if isinstance(n.target, ast.Tuple) and "source_id" in ast.dump(n.target))
    identity_names = {n.id for n in ast.walk(identity_loop) if isinstance(n, ast.Name)}
    lifecycle_names = {n.id for n in ast.walk(lifecycle_loop) if isinstance(n, ast.Name)}
    assert "is_tpex_api" not in identity_names
    assert "is_tpex_api" in lifecycle_names
    lifecycle_source = ast.get_source_segment(source, lifecycle_loop)
    assert lifecycle_source.index('is_tpex_api = source_id == "tpex_delisted"') < lifecycle_source.index(
        "BOOTSTRAP_TPEX_LIFECYCLE_SOURCE_FAILURE"
    )
    assert 'probe_result["bootstrap_failure_code"] = BOOTSTRAP_TPEX_LIFECYCLE_SOURCE_FAILURE' in lifecycle_source
    assert '"BLOCKED_BY_TPEX_LIFECYCLE_SOURCE_FAILURE"' in lifecycle_source
    assert '"BOOTSTRAP_TPEX_LIFECYCLE_SOURCE_FAILURE"' in source
    assert lifecycle_source.index('"BLOCKED_BY_TPEX_LIFECYCLE_SOURCE_FAILURE"') < lifecycle_source.index("return 1")

    tests = TESTS.read_text(encoding="utf-8")
    for name in (
        "test_identity_source_transport_failure_remains_source_generic",
        "test_tpex_transport_failure_stops_before_next_probe_and_phase_e",
        "test_tpex_schema_drift_stops_before_next_probe_and_phase_e",
    ):
        assert f"def {name}(" in tests
    assert '"BOOTSTRAP_TPEX_LIFECYCLE_SOURCE_FAILURE"' in tests
    assert '"BOOTSTRAP_LIFECYCLE_SCHEMA_DRIFT"' in tests
    assert 'b"code=&date=ALL&reason=-1&response=json&paging-offset=0&paging-size=1000"' in tests
    assert "test_tpex_lifecycle_drift_or_transport_failure" not in tests

    for path, digest in record["validation"]["historical_evidence_sha256"].items():
        assert sha256(ROOT / path) == digest, path

    ci = record["validation"]["default_ci_comparison"]
    assert ci["base"] == "6bc39b5a86a6af3ac3bc726117ef62a9bed2e35f"
    assert ci["candidate"] == record["implementation"]["commit"]
    assert ci["base_counts"] == ci["candidate_counts"] == {
        "collected": 1288, "selected": 1283, "passed": 1234, "failed": 45,
        "skipped": 4, "deselected": 5,
    }
    assert ci["new_failure_delta"] == 0
    assert ci["candidate_failure_node_ids_subset_of_base"] is True
    assert ci["network_denied"] is True
    focused = record["validation"]["focused_tests"]
    assert [(item["passed"], item["failed"], item["skipped"]) for item in focused] == [
        (57, 0, 0), (17, 0, 0),
    ]
    replay = record["validation"]["local_582_row_replay"]
    assert replay["sha256"] == "d70bcef49999ffb4c6642ae1e55910e26636d02fd4eb90f8eab84094b98de4a5"
    assert replay["bytes"] == 71065 and replay["events_parsed"] == 582
    assert replay["all_LifecycleEvent_schema_valid"] is True
    assert replay["duplicate_identity_count"] == 0
    assert record["validation"]["compileall"] == "PASS for scripts, tests, and skills"
    assert record["validation"]["ast_phase_boundary_assertions"] == "PASS"
    assert record["validation"]["git_diff_check"] == "PASS"
    assert len(record["validation"]["governance_validators"]["passed"]) == 6
    assert record["validation"]["snapshot_suite_base_candidate_failures_equal"] is True

    state = subprocess.run(
        [sys.executable, str(ROOT / "scripts/manage_security_master.py"), "status"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    assert json.loads(state.stdout)["status"] == "NOT_INITIALIZED"
    assert not (ROOT / "data/security_master/active.json").exists()
    assert record["network_counts"] == {
        "market_GET_HEAD_POST": "0/0/0", "security_master_live_acquisition": 0,
    }
    assert record["TWSE_307_blockers_remain"] is True
    assert record["canonical_state"] == {
        "production_identity_verified": False,
        "bootstrap_attempt_2": "NOT_AUTHORIZED",
        "H2": "INACTIVE",
        "routing": "plan_only",
        "selected_executor": None,
        "J-B04": "BLOCKING",
        "Phase_J": "NOT_STARTED",
        "MCP": 6,
    }
    print("J-B04-A6-SM-B1-R5-P1-R2-R1 validator: PASS (network-free; bootstrap unauthorized)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

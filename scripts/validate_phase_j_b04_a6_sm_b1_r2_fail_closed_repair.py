#!/usr/bin/env python3
"""Validate the network-free SM-B1 R2 stop and redirect-diagnostic repair."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "docs/governance/phase_j/PHASE_J_J_B04_A6_SM_B1_R2_FAIL_CLOSED_REPAIR_2026-10-10.json"
SM_B1_JSON = ROOT / "docs/governance/phase_j/PHASE_J_J_B04_A6_SM_B1_SECURITY_MASTER_BOOTSTRAP_2026-10-10.json"
SM_B1_MD = ROOT / "docs/governance/phase_j/PHASE_J_J_B04_A6_SM_B1_SECURITY_MASTER_BOOTSTRAP_2026-10-10.md"
MATERIALIZER = ROOT / "scripts/m8r_06_01b_materialize_production_inputs.py"
PROBE = ROOT / "skills/tw-security-master-classifier/scripts/probe_sources.py"
TEST = ROOT / "tests/unit/test_m8r_06_01b_bootstrap_dispatch_budget.py"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    record = json.loads(RECORD.read_text(encoding="utf-8"))
    sm_b1 = json.loads(SM_B1_JSON.read_text(encoding="utf-8"))
    assert record["gate"] == "J-B04-A6-SM-B1-R2"
    assert record["starting_head"] == "039b421e4d53be770f2a37124d01d4a16d31f452"
    assert record["starting_tree"] == "d2fa9ddf83f793bc6eabea57d91a395d8e6d6154"
    assert record["starting_main"] == "6daf6e2dcc6fd34e00e7e3831c25e98bb4d2399a"
    assert record["independent_review_id"] == "5476829857"
    assert sm_b1["terminal_disposition"] == "J_B04_A6_SM_B1_BOOTSTRAP_HARD_BLOCK_AWAITING_INDEPENDENT_REVIEW"
    assert sm_b1["hard_block"]["production_immediate_stop_enforced"] is False
    assert record["historical_hard_block_preserved"] is True
    assert record["historical_evidence_sha256"] == {
        "json": "2922ec11b6ef167d775e629885d032ee8b1dc07bfea284b4323c16e82e318226",
        "markdown": "385f5bca6b262ae993e5fa1e0ff2542c421a36333cbf3492fcbe3ddc8b1a7e7d",
    }
    assert sha(SM_B1_JSON) == record["historical_evidence_sha256"]["json"]
    assert sha(SM_B1_MD) == record["historical_evidence_sha256"]["markdown"]

    materializer = MATERIALIZER.read_text(encoding="utf-8")
    probe = PROBE.read_text(encoding="utf-8")
    tests = TEST.read_text(encoding="utf-8")
    assert 'BOOTSTRAP_LIFECYCLE_SCHEMA_DRIFT = "BOOTSTRAP_LIFECYCLE_SCHEMA_DRIFT"' in materializer
    drift = materializer.index("except LifecycleSchemaDrift as exc:")
    stop_return = materializer.index("return 1", drift)
    next_merge = materializer.index("# Merge lifecycle events", drift)
    assert stop_return < next_merge
    assert '"lifecycle_schema_drift"' in materializer
    assert 'probe_result["bootstrap_failure_code"] = BOOTSTRAP_LIFECYCLE_SCHEMA_DRIFT' in materializer
    assert '"parser": parser_name' in materializer
    assert '"issue_code": exc.issue_code' in materializer
    assert "_sanitize_lifecycle_drift_detail(exc)" in materializer
    assert "observed_header_candidate_count" in materializer
    assert '"bootstrap_failure_code": reason if reason.startswith("BOOTSTRAP_") else None' in materializer
    assert "independent_review_required_no_bootstrap_retry" in materializer
    assert "probe #5 called = false" in record["fail_closed_regression"]["asserted"]
    assert "BOOTSTRAP_HTTP_REDIRECT_NOT_FOLLOWED" in probe
    for field in (
        "redirect_location_present",
        "redirect_location_scheme",
        "redirect_location_host",
        "redirect_location_path_or_sanitized_url",
        "redirect_location_allowed",
        "redirect_followed",
    ):
        assert f'"{field}"' in probe
    assert "Exclude query, fragment, username, and password" in probe
    for test_name in (
        "test_lifecycle_schema_drift_stops_materializer_before_next_probe_and_phase_e",
        "test_lifecycle_drift_detail_retains_shape_without_source_header_text",
        "test_http_307_is_sanitized_and_never_followed",
        "test_307_disallowed_location_is_reported_not_dispatched",
        "test_non_redirect_http_errors_keep_ordinary_classification",
    ):
        assert test_name in tests

    limits = record["dispatch_limits"]
    assert limits == {
        "logical_probes": 5,
        "max_followed_redirects_per_probe": 1,
        "max_dispatches_per_probe": 2,
        "max_dispatches_total": 10,
        "automatic_retry": 0,
        "shared_budget_across_all_probes": True,
        "reservation_before_dispatch": True,
    }
    assert record["network_counts"] == {"market_GET_HEAD_POST": "0/0/0", "security_master_live_acquisition": 0}
    assert record["security_master_state"] == "NOT_INITIALIZED"
    status = subprocess.run(
        [sys.executable, str(ROOT / "scripts/manage_security_master.py"), "status"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(status.stdout)["status"] == "NOT_INITIALIZED"
    assert not (ROOT / "data/security_master/active.json").exists()
    assert record["bootstrap_retry"] == "NOT_AUTHORIZED"
    assert record["bootstrap_executed_in_r2"] is False
    ci = record["validation"]["default_ci_comparison"]
    assert ci["base"] == "039b421e4d53be770f2a37124d01d4a16d31f452"
    assert ci["candidate_implementation_commit"] == record["implementation_head"]
    assert ci["new_failure_delta"] == 0
    assert ci["new_failure_node_ids"] == []
    assert ci["resolved_failure_node_ids"] == []
    assert ci["shared_failure_count"] == 45
    assert ci["base_counts"] == ci["candidate_counts"]
    assert ci["network_may_have_occurred"] is False
    assert record["canonical_runtime_state"] == {
        "H2": "INACTIVE",
        "selected_executor": None,
        "routing": "plan_only",
        "J-B04": "BLOCKING",
        "Phase_J": "NOT_STARTED",
        "MCP": 6,
    }
    print("A6-SM-B1-R2 validator: PASS (network-free; retry unauthorized)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

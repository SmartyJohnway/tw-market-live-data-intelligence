from __future__ import annotations

import json
from pathlib import Path

from server.services.unified_mode_b2_execution import MAX_CHILD_TIMEOUT_SECONDS, _timeout_seconds
from server.unified_mcp.local_service_client import ACTION_TIMEOUT_SECONDS, TIMEOUT_SECONDS


ROOT = Path(__file__).resolve().parents[2]
RUN_DIR = ROOT / "docs/governance/phase_l/acceptance_runs/l4-a6-r3-20261017T150419Z"


def test_timeout_matrix_covers_active_registry_and_externally_reachable_actions():
    matrix = json.loads((RUN_DIR / "timeout_budget_matrix.json").read_text(encoding="utf-8"))
    registry = json.loads((ROOT / "config/m8r_06_03_executor_registry_metadata.json").read_text(encoding="utf-8"))
    executor_rows = [row for row in matrix["entries"] if row["category"] == "active_executor_registry"]
    active = [row for row in registry["executors"] if row.get("network_required") is True]

    assert len(active) == 17
    assert len(executor_rows) == len(active)
    assert {row["registry_key"] for row in executor_rows} == {
        f"{item['executor_id']}|{item['capability_id']}|{item['market']}" for item in active
    }
    assert all(isinstance(item.get("timeout_seconds"), (int, float)) and item["timeout_seconds"] > 0 for item in active)
    assert all(row["inner_timeout_seconds"] > 0 for row in executor_rows)
    assert all(row["automatic_retry_count"] == 0 for row in executor_rows)

    by_id = {row["entrypoint_id"]: row for row in matrix["entries"]}
    assert by_id["mcp_ordinary_local_service"]["outer_timeout_seconds"] == TIMEOUT_SECONDS == 15.0
    assert by_id["mcp_fetch_action_local_service"]["outer_timeout_seconds"] == ACTION_TIMEOUT_SECONDS == 145.0
    assert by_id["api_unified_executions"]["inner_timeout_seconds"] == _timeout_seconds({}) == 130
    assert MAX_CHILD_TIMEOUT_SECONDS == 130 < ACTION_TIMEOUT_SECONDS
    assert by_id["api_unified_fetch_evidence"]["inner_timeout_seconds"] > 0
    assert matrix["whole_server_global_hard_deadline"] == "NOT_USED_BY_DESIGN"
    assert matrix["all_active_network_action_paths_finitely_bounded"] is True


def test_r3_memory_matrix_has_long_horizon_equal_window_stabilization_evidence():
    matrix = json.loads((RUN_DIR / "memory_stabilization_matrix.json").read_text(encoding="utf-8"))
    m8 = next(row for row in matrix["scenarios"] if row["scenario"] == "M8_long_horizon_identical_bounded_workload")
    windows = m8["equal_windows"]
    slopes = [row["retained_growth_bytes_per_cycle"] for row in windows]

    assert m8["warmup_cycles"] == 30
    assert m8["measured_cycles"] == 1000
    assert [row["window"] for row in windows] == ["W1", "W2", "W3", "W4"]
    assert len(m8["checkpoints"]) >= 10
    assert m8["functional_output_deterministic"] is True
    assert m8["slopes_decline_across_equal_windows"] is True
    assert all(left > right for left, right in zip(slopes, slopes[1:]))
    assert m8["late_half_slope_lower_than_early_half"] is True
    assert m8["product_defined_type_growth_detected"] is False
    assert m8["positive_product_traceback_growth_detected"] is False
    assert m8["rss_independent_linear_growth_pattern"] is False
    assert m8["scenario_status"] == "PASS_BOUNDED_CACHE_STABILIZATION"


def test_timeout_contract_does_not_add_generic_asgi_force_cancellation():
    source = (ROOT / "server/main.py").read_text(encoding="utf-8")
    assert "asyncio.wait_for(call_next" not in source
    assert "WholeServerTimeoutMiddleware" not in source
    assert "WHOLE_SERVER_GLOBAL_HARD_DEADLINE" not in source

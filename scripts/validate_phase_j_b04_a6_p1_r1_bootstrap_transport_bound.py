#!/usr/bin/env python3
"""Validate the network-free A6-P1-R1 bootstrap transport hardening."""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.phase_j_b04_a6_p1_prerequisite_authority import (  # noqa: E402
    EXPECTED_LOGICAL_PROBES,
    classify_bootstrap_dispatch,
    h2_activation_current_state,
    inspect_redirect_runtime_bounds,
    load_json,
    source_inventory,
)

RECORD = ROOT / "docs/governance/phase_j/PHASE_J_J_B04_A6_P1_R1_BOOTSTRAP_TRANSPORT_BOUND_HARDENING_2026-10-09.json"
P1 = ROOT / "docs/governance/phase_j/PHASE_J_J_B04_A6_P1_PREREQUISITE_AUTHORITY_CLOSURE_2026-10-09.json"


def main() -> int:
    record = load_json(RECORD)
    p1 = load_json(P1)
    assert record["gate"] == "J-B04-A6-P1-R1"
    assert record["starting_head"] == "3944c1330e29b3f20132fe4ca0a04cc604f26094"
    assert record["starting_tree"] == "ce3b7d12b70cea395e31a672fd1d45d6be59b1d8"
    assert record["starting_main"] == "6daf6e2dcc6fd34e00e7e3831c25e98bb4d2399a"
    assert p1["overall_disposition"] == "J_B04_A6_P1_BOOTSTRAP_DISPATCH_BOUND_NOT_PROVEN"
    correction = record["p1_correction"]
    assert correction["history_rewritten"] is False
    assert correction["prior_disposition_superseded_for"] == "redirect-bound classification only"
    assert "inherited CPython urllib redirect ceiling exists" in correction["corrected_statement"]

    runtime = inspect_redirect_runtime_bounds()
    parent = urllib.request.HTTPRedirectHandler
    assert runtime["is_subclass"] is True
    assert runtime["max_repeats"] == parent.max_repeats
    assert runtime["max_redirections"] == parent.max_redirections
    assert runtime["max_repeats"] == record["runtime_redirect_analysis"]["effective_inherited_max_repeats"]
    assert runtime["max_redirections"] == record["runtime_redirect_analysis"]["effective_inherited_max_redirections"]
    assert record["runtime_redirect_analysis"]["values_read_from_runtime"] is True
    assert record["runtime_redirect_analysis"]["universal_python_claim"] is False

    bound = record["project_owned_bootstrap_transport_bound"]
    assert classify_bootstrap_dispatch() == "PROJECT_OWNED_BOUNDED"
    assert bound["logical_probes"] == 5
    assert bound["max_redirects_followed_per_probe"] == 1
    assert bound["max_http_dispatches_per_probe"] == 2
    assert bound["bootstrap_http_dispatch_hard_ceiling"] == 10
    assert bound["single_shared_budget_object_across_all_probes"] is True
    assert bound["automatic_retry"] == 0
    assert bound["dispatch_11_possible"] is False
    assert bound["initial_request_reservation"] == "before opener.open"
    assert bound["redirect_target_reservation"] == "before returning redirect request to urllib"

    inventory = source_inventory()
    assert [item["source_id"] for item in inventory] == [item["source_id"] for item in EXPECTED_LOGICAL_PROBES]
    assert [item["source_id"] for item in record["logical_probe_inventory_preserved"]] == [
        "twse_isin_mode2_zh", "twse_isin_mode4_zh", "twse_delisted", "tpex_delisted", "twse_etn_expired"
    ]
    assert all(item["maximum_redirects_followed_per_probe"] == 1 for item in inventory)
    assert all(item["maximum_http_dispatches_per_probe"] == 2 for item in inventory)

    probe_source = (ROOT / "skills/tw-security-master-classifier/scripts/probe_sources.py").read_text(encoding="utf-8")
    materializer = (ROOT / "scripts/m8r_06_01b_materialize_production_inputs.py").read_text(encoding="utf-8")
    assert "class BootstrapDispatchBudget:" in probe_source
    assert probe_source.index("dispatch_budget.reserve_before_dispatch()") < probe_source.index("with opener.open(request")
    assert probe_source.index("self.dispatch_budget.reserve_before_dispatch()") < probe_source.index("return super().redirect_request")
    assert materializer.count("dispatch_budget=dispatch_budget") == 2
    assert "BootstrapDispatchBudget(BOOTSTRAP_MAX_TOTAL_DISPATCHES)" in materializer
    assert "BOOTSTRAP_MAX_TOTAL_DISPATCHES = 10" in materializer
    assert "BOOTSTRAP_MAX_REDIRECTS_PER_PROBE = 1" in materializer
    assert "BOOTSTRAP_MAX_DISPATCHES_PER_PROBE = 1 + BOOTSTRAP_MAX_REDIRECTS_PER_PROBE" in materializer
    for code in bound["failure_codes"]:
        assert code in probe_source

    template = record["future_bootstrap_authorization_template"]
    assert template["template_type"] == "FUTURE_OWNER_AUTHORIZATION_METADATA_ONLY"
    assert template["authorization_status"] == "NOT_AUTHORIZED"
    assert template["is_authorization"] is False
    assert template["max_redirects_followed_per_probe"] == 1
    assert template["max_http_dispatches_per_probe"] == 2
    assert template["bootstrap_http_dispatch_hard_ceiling"] == 10
    assert len(template["stop_conditions"]) >= 8

    status = subprocess.run(
        [sys.executable, str(ROOT / "scripts/manage_security_master.py"), "status"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(status.stdout)["status"] == "NOT_INITIALIZED"
    assert record["security_master"]["bootstrap_executed"] is False
    assert record["network_counts"] == {"market_GET_HEAD_POST": "0/0/0", "security_master_live_acquisition": 0}

    ci = record["default_ci_comparison"]
    assert ci["base"] == "3944c1330e29b3f20132fe4ca0a04cc604f26094"
    assert ci["candidate"] == record["implementation_head"]
    assert ci["new_failure_delta"] == 0
    assert ci["new_failure_node_ids"] == []
    assert ci["resolved_failure_node_ids"] == []
    assert ci["shared_failure_count"] == 45
    assert ci["base_counts"] == ci["head_counts"]
    assert ci["network_may_have_occurred"] is False
    assert len(ci["base_failed_node_ids"]) == 45
    assert ci["base_failed_node_ids"] == ci["head_failed_node_ids"]

    h3 = record["h3_authority"]
    assert h3["disposition"] == "ACCEPTED_AT_OWNER_PRODUCT_AUTHORITY_LEVEL"
    assert h3["provider_automation_permission"] == "NOT_ESTABLISHED_TERMS_CONFLICTED"
    assert h3["provider_approval_claimed"] is False
    assert h3["redistribution_permission"] == "NOT_ESTABLISHED"

    state = h2_activation_current_state()
    catalog, routing = state["catalog"], state["routing"]
    assert catalog["runtime_executable"] is False
    assert catalog["phase_h_activation_state"] == "inactive"
    assert routing["runtime_executable"] is False
    assert routing["routing_status"] == "plan_only"
    assert routing["selected_executor_id"] is None
    canonical = record["canonical_runtime_state"]
    assert canonical == {
        "H2_runtime": "INACTIVE",
        "H2_runtime_executable": False,
        "H2_phase_h_activation_state": "inactive",
        "H2_routing_status": "plan_only",
        "selected_executor_id": None,
        "J-B04": "BLOCKING",
        "Phase_J": "NOT_STARTED",
        "MCP": 6,
    }
    print("A6-P1-R1 validator: PASS (network-free; bootstrap remains unexecuted)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

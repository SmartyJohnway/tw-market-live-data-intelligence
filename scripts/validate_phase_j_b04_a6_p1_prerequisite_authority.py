#!/usr/bin/env python3
"""Validate the network-free A6-P1 authority closure record against the repo."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.phase_j_b04_a6_p1_prerequisite_authority import (  # noqa: E402
    EXPECTED_LOGICAL_PROBES,
    classify_bootstrap_dispatch,
    h2_activation_current_state,
    h3_automation_authority,
    load_json,
    source_inventory,
)

RECORD = ROOT / "docs/governance/phase_j/PHASE_J_J_B04_A6_P1_PREREQUISITE_AUTHORITY_CLOSURE_2026-10-09.json"
P0 = ROOT / "docs/governance/phase_j/PHASE_J_J_B04_A6_P0_INTEGRATED_ACCEPTANCE_PREFLIGHT_2026-10-09.json"
R1 = ROOT / "docs/governance/phase_j/PHASE_J_J_B04_A6_P1_R1_BOOTSTRAP_TRANSPORT_BOUND_HARDENING_2026-10-09.json"


def main() -> int:
    record = load_json(RECORD)
    p0 = load_json(P0)
    assert p0["disposition"] == "J_B04_A6_P0_BLOCKED_SECURITY_MASTER_NOT_INITIALIZED"
    assert record["p0_disposition"] == p0["disposition"]
    assert record["security_master"]["current_state"] == "NOT_INITIALIZED"
    assert record["security_master"]["production_identity_verified"] is False
    assert p0["production_identity_required"] is True
    assert p0["acceptance_only_identity_fallback"] is False

    inventory = source_inventory()
    assert len(inventory) == 5 == record["security_master"]["logical_official_source_probes"]
    declared = record["security_master"]["probes"]
    assert [p["source_id"] for p in declared] == [p["source_id"] for p in EXPECTED_LOGICAL_PROBES]
    assert [p["initial_url"] for p in declared] == [p["initial_url"] for p in inventory]
    assert all(p["method"] == "GET" for p in declared)
    assert all(p["source_contract_identifier"] is None for p in declared)
    # Keep P1's original disposition as history; R1 supersedes only the
    # redirect-bound classification and supplies the project-owned budget.
    correction = load_json(R1)
    assert record["overall_disposition"] == "J_B04_A6_P1_BOOTSTRAP_DISPATCH_BOUND_NOT_PROVEN"
    assert correction["p1_correction"]["history_rewritten"] is False
    assert correction["p1_correction"]["prior_disposition_superseded_for"] == "redirect-bound classification only"
    assert correction["runtime_redirect_analysis"]["inherited_redirect_bound_exists"] is True
    assert correction["project_owned_bootstrap_transport_bound"]["bootstrap_http_dispatch_hard_ceiling"] == 10
    assert classify_bootstrap_dispatch() == "PROJECT_OWNED_BOUNDED"
    assert record["security_master"]["maximum_actual_http_dispatches"] == "NOT_PROVEN"
    assert record["bootstrap_authorization"]["template_emitted"] is False
    assert record["bootstrap_authorization"]["reason"]
    assert record["security_master"]["bootstrap_formal_operator_command"] == "python scripts/manage_security_master.py update --live"
    assert record["network_and_canonical_state"]["security_master_bootstrap_performed"] is False
    status = subprocess.run(
        [sys.executable, str(ROOT / "scripts/manage_security_master.py"), "status"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(status.stdout)["status"] == "NOT_INITIALIZED"

    owner_h3 = load_json(ROOT / "docs/governance/phase_h/PHASE_H_H3_TWSE_CONTROLLED_USE_OWNER_DECISION_2026-09-24.json")
    expected_h3 = h3_automation_authority(owner_h3)
    assert record["h3_automation_authority"]["disposition"] == expected_h3["disposition"]
    assert expected_h3["disposition"] == "J_B04_A6_H3_AUTOMATION_AUTHORITY_ACCEPTED"
    assert record["h3_automation_authority"]["provider_automation_permission"] == "NOT_ESTABLISHED_TERMS_CONFLICTED"
    assert record["h3_automation_authority"]["provider_approval_claimed"] is False
    assert record["h3_automation_authority"]["source_id"] == "H3-TWSE-DEFAULT-BOUNDED"
    assert "no TPEx" in record["h3_automation_authority"]["scope"]
    assert "Yahoo" in record["h3_automation_authority"]["scope"]
    assert "browser" in record["h3_automation_authority"]["scope"]

    state = h2_activation_current_state()
    assert state["catalog"]["runtime_executable"] is False
    assert state["catalog"]["phase_h_activation_state"] == "inactive"
    assert state["routing"]["runtime_executable"] is False
    assert state["routing"]["routing_status"] == "plan_only"
    assert state["routing"]["selected_executor_id"] is None
    assert record["h2_activation"]["performed"] is False
    assert record["network_and_canonical_state"] == {
        "market_GET_HEAD_POST": "0/0/0",
        "security_master_live_acquisition": 0,
        "security_master_bootstrap_performed": False,
        "H2_runtime": "INACTIVE",
        "selected_executor_id": None,
        "J-B04": "BLOCKING",
        "Phase_J": "NOT_STARTED",
        "MCP": 6,
    }
    assert record["overall_disposition"] == "J_B04_A6_P1_BOOTSTRAP_DISPATCH_BOUND_NOT_PROVEN"
    assert correction["future_bootstrap_authorization_template"]["authorization_status"] == "NOT_AUTHORIZED"
    assert correction["future_bootstrap_authorization_template"]["is_authorization"] is False
    print("A6-P1 historical validator: PASS (R1 correction is additive; bootstrap remains unexecuted)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

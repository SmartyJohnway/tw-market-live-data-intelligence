"""Offline, invariant-based Phase I Roadmap exit review validator."""
from __future__ import annotations

import json
import socket
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
EXIT_REVIEW = "docs/governance/phase_i/PHASE_I_FINAL_EXIT_REVIEW_2026-10-05.json"
FINAL_CLOSURE = "docs/governance/phase_i/PHASE_I_FINAL_CLOSURE_2026-10-05.json"
CAPABILITIES = {
    "market_state_context": ("phase_i_i1_market_state_executor", 3, 2),
    "index_futures_context": ("phase_i_i2_index_futures_context_executor", 1, 1),
    "cash_institutional_flow_context": ("phase_i_i3_cash_institutional_flow_context_executor", 2, 2),
}
ALLOWED_FAMILY_DISPOSITIONS = {
    "IMPLEMENTED_AND_REQUIRED",
    "IMPLEMENTED_OPTIONAL",
    "DEFERRED_NOT_REQUIRED_FOR_PHASE_I_EXIT",
    "REJECTED_FOR_V1",
    "FUTURE_EVIDENCE_VALUE_GATE_REQUIRED",
}


def _json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def validate() -> dict:
    def deny(*_args, **_kwargs):
        raise AssertionError("phase_i_exit_market_network_forbidden")

    with patch.object(socket.socket, "connect", deny), patch.object(socket, "create_connection", deny):
        review = _json(EXIT_REVIEW)
        closure = _json(FINAL_CLOSURE)
        assert review["status"] == "PHASE_I_OWNER_ACCEPTANCE_CANDIDATE_EXIT_PASS"
        assert closure["status"] == "PHASE_I_COMPLETED_INDEPENDENT_EXIT_REVIEW_PASS"
        assert review["market_GETs"] == closure["market_GETs"] == {"TWSE": 0, "TPEX": 0, "TAIFEX": 0, "other": 0}
        assert review["phase_j_authorized"] is False and closure["phase_j_authorized"] is False
        assert review["validation"]["network_may_have_occurred"] is False
        assert closure["validation"]["network_may_have_occurred"] is False
        assert "0 failed" in review["validation"]["default_ci"] and "0 failed" in review["validation"]["full_current"]

        matrix = review["exit_review_matrix"]
        for key in ("I.1_evidence_value_gate", "I.2_spot_derivatives_descriptive_context",
                    "I.3_derivatives_identity_boundary", "I.4_optional_context_candidate_disposition",
                    "I.5_default_result_minimalism", "phase_i_expected_product_outcome"):
            assert matrix[key]["status"] == "PASS", key

        family_dispositions = review["deferred_family_dispositions"]
        assert family_dispositions and all(x["disposition"] in ALLOWED_FAMILY_DISPOSITIONS for x in family_dispositions.values())
        expected = {
            "TX_after_hours": "FUTURE_EVIDENCE_VALUE_GATE_REQUIRED",
            "options_context": "FUTURE_EVIDENCE_VALUE_GATE_REQUIRED",
            "put_call_ratio": "FUTURE_EVIDENCE_VALUE_GATE_REQUIRED",
            "TAIFEX_institutional_positioning": "FUTURE_EVIDENCE_VALUE_GATE_REQUIRED",
            "margin_financing": "FUTURE_EVIDENCE_VALUE_GATE_REQUIRED",
            "short_SBL": "FUTURE_EVIDENCE_VALUE_GATE_REQUIRED",
            "large_trader_OI": "FUTURE_EVIDENCE_VALUE_GATE_REQUIRED",
            "industry_price_performance": "FUTURE_EVIDENCE_VALUE_GATE_REQUIRED",
            "ETF_AUM_beneficiaries": "DEFERRED_NOT_REQUIRED_FOR_PHASE_I_EXIT",
            "ETF_exact_holdings": "REJECTED_FOR_V1",
            "day_trading_context": "REJECTED_FOR_V1",
        }
        assert {key: family_dispositions[key]["disposition"] for key in expected} == expected

        catalog = _json("docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json")
        assert catalog["contract_versions"]["preferred_request_schema_version"] == "unified_market_evidence_request.v3"
        caps = {item["capability_id"]: item for item in catalog["data_need_capabilities"]}
        routing = _json("docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json")
        routes = {item["capability_id"]: item for item in routing["routes"]}
        registry = _json("config/m8r_06_03_executor_registry_metadata.json")["executors"]
        for capability, (executor, sources_expected, runtime_routes_expected) in CAPABILITIES.items():
            cap = caps[capability]
            route = routes[capability]
            assert cap["support_status"] == "runtime_executable" and cap["runtime_executable"] is True
            assert cap.get("selected_executor_id", executor) == executor
            assert cap["requires_approval_for_execution"] is True
            assert route["runtime_executable"] is True and route["selected_executor_id"] == executor
            assert route["capability_requires_execution_approval"] is True
            actual_routes = [item for item in registry if item["capability_id"] == capability]
            assert len(actual_routes) == runtime_routes_expected
            assert review["accepted_runtime_topology"][capability]["active_source_count"] == sources_expected
            assert review["accepted_runtime_topology"][capability]["runtime_market_executor_registrations"] == runtime_routes_expected

        i3_source_authority = _json("docs/data_capabilities/phase_i_i3_source_authority.v1.json")
        assert i3_source_authority["active_source_count"] == 2
        assert i3_source_authority["evidence_contract"] == "cash_institutional_flow_context_evidence.v2"
        assert review["accepted_runtime_topology"]["logical_capability_routes"] == 3

        i1_ledger = _json("docs/governance/phase_i/PHASE_I_I1_PRODUCTION_ROUTE_ACTIVATION_ACCEPTANCE_LEDGER_2026-09-30.json")
        i2_ledger = _json("docs/governance/phase_i/PHASE_I_I2_A4_PRODUCTION_ROUTE_ACTIVATION_ACCEPTANCE_LEDGER_2026-10-01.json")
        i3_ledger = _json("docs/governance/phase_i/PHASE_I_I3_A4_FINAL_OWNER_ACCEPTANCE_AND_CLOSURE_2026-10-05.json")
        assert i1_ledger["status"] == "OWNER_ACTIVATION_ACCEPTED"
        assert i2_ledger["status"] == "OWNER_ACTIVATION_ACCEPTED"
        assert i3_ledger["final_acceptance"]["owner_acceptance"] == "ACCEPTED"
        assert i3_ledger["final_acceptance"]["I3_ROLL_001"] == "PASS"

        request_schema = _json("schemas/unified_market_evidence_request.v3.schema.json")
        assert "data_needs" in request_schema["properties"]
        planner_source = (ROOT / "scripts/m8r_05b_01/planner.py").read_text(encoding="utf-8")
        assert "for cap in sorted(validation.get('capability_results',[])" in planner_source
        assert "requested_data_needs" in (ROOT / "scripts/m8r_05c/result_builder.py").read_text(encoding="utf-8")
        from server.unified_mcp.tool_contracts import build_tool_specs

        assert len(build_tool_specs()) == 6
        roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
        phase_i_lines = [line.strip() for line in roadmap.splitlines() if "Phase I — Cross-Market & Optional Context" in line]
        assert len(phase_i_lines) == 2 and all(line.startswith("[x]") or line.startswith("# [x]") for line in phase_i_lines)
        for path in ("PROJECT.md", "HANDOFF.md", "AGENTS.md", "ROADMAP.md", "docs/governance/INDEX.md"):
            text = (ROOT / path).read_text(encoding="utf-8").lower()
            assert "pr #301 merge remains unauthorized" not in text
            assert "i3 production remains inactive" not in text
        assert review["default_result_minimalism"]["explicit_data_needs_drive_planning"] is True
        assert all(review["default_result_minimalism"][key] is False for key in (
            "I1_automatically_loaded", "I2_automatically_loaded", "I3_automatically_loaded",
            "automatic_TAIFEX_full_context", "automatic_institutional_context",
            "automatic_ETF_margin_options_context", "background_scheduler_polling"))
        assert review["unified_public_surface"]["mcp_tool_count"] == 6
        return {"status": "PASS", "phase_i_exit": review["status"], "i1_sources_routes": "3/2",
                "i2_sources_routes": "1/1", "i3_sources": 2, "i3_logical_routes": 1,
                "i3_runtime_market_routes": 2, "mcp_tool_count": 6, "market_gets": 0}


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))

#!/usr/bin/env python3
"""Network-free validator for the J-B04-A6-R1 H3 close parsing repair."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "server/services/phase_h_h3_twse_stock_day_adapter.py"
TESTS = ROOT / "tests/unit/test_phase_h_h3_i2a_twse_stock_day_adapter.py"
A6_JSON = ROOT / "docs/governance/phase_j/PHASE_J_J_B04_A6_INTEGRATED_MARKET_RESEARCH_INTERPRETATION_LIVE_ACCEPTANCE_2026-10-10.json"
A6_MD = ROOT / "docs/governance/phase_j/PHASE_J_J_B04_A6_INTEGRATED_MARKET_RESEARCH_INTERPRETATION_LIVE_ACCEPTANCE_2026-10-10.md"
ROUTING = ROOT / "docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json"
R1_RECORD = ROOT / "docs/governance/phase_j/PHASE_J_J_B04_A6_R1_H3_STOCK_DAY_CLOSE_NUMERIC_CONTRACT_REPAIR_2026-10-10.json"

EXPECTED_A6_JSON_SHA = "1e3382bedc876fa0578ff0716c1e42a0d2a11209d2eef26e5f5d13e513571aba"
EXPECTED_A6_MD_SHA = "f9b0ded99236246fc00ab45183a7c2d71a3d08f576a97aac4fad5bc29b571d5f"


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require(test: bool, message: str) -> None:
    if not test:
        raise AssertionError(message)


def main() -> int:
    sys.path.insert(0, str(ROOT))
    from server.services.phase_h_h3_twse_stock_day_adapter import (  # noqa: PLC0415
        ENDPOINT,
        SOURCE_CONTRACT_ID,
        SOURCE_FAMILY,
        _close_lexical_class,
        _parse_close,
    )

    _require(_sha(A6_JSON) == EXPECTED_A6_JSON_SHA, "historical A6 JSON changed")
    _require(_sha(A6_MD) == EXPECTED_A6_MD_SHA, "historical A6 Markdown changed")
    a6 = _json(A6_JSON)
    r1 = _json(R1_RECORD)
    _require(r1["terminal_disposition"] == "J_B04_A6_R1_H3_CLOSE_NUMERIC_CONTRACT_REPAIR_PASS", "R1 disposition mismatch")
    _require(r1["authority"]["starting_head"] == "70b7c376b42185620a5d7f07c62e088f902c76a1", "R1 starting HEAD mismatch")
    _require(r1["authority"]["starting_tree"] == "0d5b058a90e2f4bbe7d7b03d993d97a3dd02e4cf", "R1 starting TREE mismatch")
    _require(r1["authority"]["owner_authorization_sha256"] == "155c031e8065d115c5ccfde684316c69b178cc82885e06f39257a83ebbf1dfc7", "R1 authorization mismatch")
    _require(r1["network"]["TWSE_GET_HEAD_POST"] == {"GET": 0, "HEAD": 0, "POST": 0}, "R1 source network was not zero")
    _require(r1["network"]["security_master_acquisition"] == 0 and r1["network"]["a6_live_executions"] == 0, "R1 performed a prohibited live action")
    _require(r1["validation"]["default_ci"]["failed_node_sets_equal"] is True and r1["validation"]["default_ci"]["new_failure_delta"] == 0, "default-CI parity failed")
    _require(r1["implementation"]["commit"] == "065460132ea9d5b81b241e252c7e2bcc627bccf6", "implementation commit mismatch")
    _require(r1["historical_a6"]["a6_json_sha256"] == EXPECTED_A6_JSON_SHA, "R1 did not bind the historical A6 JSON")
    _require(r1["historical_a6"]["a6_markdown_sha256"] == EXPECTED_A6_MD_SHA, "R1 did not bind the historical A6 Markdown")
    _require(a6["terminal_disposition"] == "J_B04_A6_INTEGRATED_LIVE_ACCEPTANCE_HARD_BLOCK", "historical A6 disposition changed")
    _require(a6["h3"]["failure_code"] == "invalid_close", "historical A6 failure observation changed")
    _require(a6["h3"]["numeric_close_observation_count"] == 0, "historical A6 count changed")

    _require(SOURCE_FAMILY == "TWSE_STOCK_DAY_OFFICIAL_WEB", "H3 source family changed")
    _require(SOURCE_CONTRACT_ID == "TWSE_STOCK_DAY_HTML_MONTHLY_V1", "H3 source contract changed")
    _require(ENDPOINT == "https://www.twse.com.tw/exchangeReport/STOCK_DAY", "H3 endpoint changed")

    accepted = {
        "0": 0.0,
        "15": 15.0,
        "15.80": 15.8,
        "999.99": 999.99,
        "1000": 1000.0,
        "1000.00": 1000.0,
        "1,000": 1000.0,
        "1,000.00": 1000.0,
        "12,345": 12345.0,
        "12,345.67": 12345.67,
        "999,999.99": 999999.99,
        "1,234,567.89": 1234567.89,
        "1,440.00": 1440.0,
    }
    for token, expected in accepted.items():
        _require(_parse_close(token) == expected, f"accepted close mismatch: {token}")
    malformed = (
        "1,00", "12,34.56", "1,234,56", "1,,000", ",1000", "1000,",
        "1,000,", "1 000.00", "1，000.00", "+1,000.00", "-1,000.00",
        "1,000.", "ABC", "NaN", "Infinity",
    )
    for token in malformed:
        try:
            _parse_close(token)
        except ValueError as exc:
            _require(str(exc) == "source_failed:invalid_close:invalid_numeric_token", "malformed close diagnostic mismatch")
        else:
            raise AssertionError("malformed close accepted")
    _require(_close_lexical_class("--") == "unavailable_marker", "unavailable marker classification changed")
    _require("if row[6] == \"--\":" in ADAPTER.read_text(encoding="utf-8"), "close_unavailable path missing")

    tests = TESTS.read_text(encoding="utf-8")
    for token in ("1,000.00", "12,345.67", "1,234,567.89", "1,440.00", "12,34.56", "close=\"1000.00\""):
        _require(token in tests, f"required close regression absent: {token}")
    _require("raw source row" in tests, "raw-row duplicate semantics not documented in regression")
    _require("test_verified_unavailable_close_is_excluded_with_source_provenance_in_mixed_month" in tests, "unavailable close regression missing")

    routing = _json(ROUTING)
    route = next(item for item in routing["routes"] if item.get("capability_id") == "corporate_action_context")
    h3_route = next(item for item in routing["routes"] if item.get("capability_id") == "recent_performance")
    _require(route["runtime_executable"] is True and route["routing_status"] == "resolved", "bounded H2 route is not active")
    _require(route["candidate_executor_ids"] == ["phase_h_h2_twse_exright_pre_executor"], "H2 executor scope changed")
    _require(route["selected_executor_id"] == "phase_h_h2_twse_exright_pre_executor", "selected H2 executor changed")
    _require("TWT49U final" in route["known_limitations"][0], "blocked H2 route scope changed")
    _require(h3_route["selected_executor_id"] == "phase_h_h3_twse_recent_performance_executor", "H3 route changed")
    _require(a6["stage_1"]["mcp_tool_count"] == 6 and a6["final_state"]["mcp"] == 6, "MCP tool count evidence changed")
    _require(a6["final_state"]["j_b04"] == "BLOCKING_PENDING_EXACT_HEAD_CLOSURE_REVIEW", "J-B04 state changed")
    _require(a6["final_state"]["phase_j"] == "NOT_STARTED", "Phase J state changed")
    _require(a6["final_state"]["a6_pass"] is False, "historical A6 was relabeled PASS")
    _require(r1["final_state"]["a6_rerun_authorized"] is False, "R1 claims A6 rerun authority")

    print("J-B04-A6-R1 H3 close repair validator: PASS (network-free)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"J-B04-A6-R1 H3 close repair validator: FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)

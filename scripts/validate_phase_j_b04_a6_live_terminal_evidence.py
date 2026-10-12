#!/usr/bin/env python3
"""Validate the sanitized, terminal J-B04-A6 live evidence without network access."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "docs/governance/phase_j/PHASE_J_J_B04_A6_INTEGRATED_MARKET_RESEARCH_INTERPRETATION_LIVE_ACCEPTANCE_2026-10-10.json"
SESSION = Path("/tmp/j-b04-a6/session.json")
OUTPUT = Path("/tmp/j-b04-a6/acceptance-result.json")
LEDGER = Path("/tmp/j-b04-a6/transport-ledger.jsonl")
SUMMARY = ROOT / "artifacts/m8r_06_03_workbench/umea-v1-bb05e56d22c264938616/h3-live-transport-summary.json"


def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    record = load_json(RECORD)
    session = load_json(SESSION)
    output = load_json(OUTPUT)
    summary = load_json(SUMMARY)

    require(record["terminal_disposition"] == "J_B04_A6_INTEGRATED_LIVE_ACCEPTANCE_HARD_BLOCK", "terminal disposition mismatch")
    require(record["authority"]["owner_authorization_sha256"] == "4e43340f45f2eec12f0eefd38b8b0a2f4cd2f074b8fcc06be2500648d77a3c74", "authorization binding mismatch")
    require(record["authority"]["implementation_head"] == session["implementation_head"], "implementation HEAD mismatch")
    require(record["authority"]["implementation_tree"] == session["implementation_tree"], "implementation TREE mismatch")
    require(record["live_session"]["attempt_count"] == 1 and session["attempt_count"] == 1, "unexpected attempt count")
    require(record["live_session"]["attempt_2_used"] is False, "attempt 2 was used")
    require(session["network_enabled"] is False, "network is not frozen")
    require(record["live_session"]["network_enabled_after_run"] is False, "record does not show network frozen")
    require(session["actual_dispatches"] == 1 and record["transport"]["actual_dispatches_total"] == 1, "dispatch count mismatch")
    require(session["attempt_h3"] == {"1": 1} and session["attempt_h2"] == {}, "H3/H2 attempt accounting mismatch")
    require(record["transport"]["redirects_followed"] == 0 and record["transport"]["retries"] == 0, "redirect or retry observed")
    require(record["h3"]["http_status"] == 200 and record["h3"]["failure_code"] == "invalid_close", "H3 failure evidence mismatch")
    month_attempt = summary["month_attempts"][0]
    require(record["h3"]["response_sha256"] == month_attempt["response_sha256"], "H3 response hash mismatch")
    require(record["h3"]["requested_url"] == month_attempt["requested_url"], "H3 URL mismatch")
    require(record["h2"]["source_request_attempted"] is False and record["h2"]["get_dispatches"] == 0, "H2 source should not have run")
    require(record["h4"]["derived"] is False and record["h4"]["ordinary_return_interpretation"] == "BLOCKED", "H4 safety state mismatch")
    require(record["result_v3"]["status"] == "failed" and record["result_v3"]["schema_valid"] is True, "Result V3 state mismatch")
    require(record["audit_v3"]["schema_valid"] is True, "Audit V3 schema was not validated")
    require(record["handoff"]["ordinary_return_guard_visible"] is True, "handoff guard missing")
    require(record["handoff"]["additional_market_execution_from_read_export_workbench"] == 0, "stored result caused another execution")
    require(sha256(OUTPUT) == session["terminal_output_sha256"], "terminal output hash mismatch")
    require(record["live_session"]["terminal_output_sha256"] == session["terminal_output_sha256"], "recorded terminal output hash mismatch")
    require(sha256(LEDGER) == record["transport"]["transport_ledger_sha256"], "transport ledger hash mismatch")
    require(sha256(SUMMARY) == record["h3"]["transport_summary_sha256"], "H3 summary hash mismatch")
    require(output["fetch"]["execution_outcome"] == "failed", "raw session result outcome mismatch")
    print("J-B04-A6 terminal evidence validation: PASS (network-free)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # concise validator diagnostics
        print(f"J-B04-A6 terminal evidence validation: FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)

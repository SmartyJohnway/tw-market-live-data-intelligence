"""Offline I3-A3-R1 validator; historical live authority is never rearmed."""
from __future__ import annotations

import ast
import json
import socket
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import phase_i_i3_a0_source_transport as transport
from scripts import run_phase_i_i3_a3_bounded_live_acceptance as a3
from scripts import validate_phase_i_i3_a3_live_acceptance as historical
from scripts.phase_i_i3_transport_mapping import CANONICAL_TO_TRANSPORT_MARKET, transport_market_key

OWNER = "USER_INSTRUCTION:I3-A3-R1 Transport-Key Mapping & HTTP Dispatch Accounting Closure"
RECORD = "docs/governance/phase_i/PHASE_I_I3_A3_R1_TRANSPORT_KEY_MAPPING_HTTP_DISPATCH_ACCOUNTING_CLOSURE_2026-10-04.json"
HISTORICAL_SHA = {
    a3.PRE_NETWORK: "0675d434bf82105937cd6a5f1a56d916362049d49906e4fb80c9346705aa1bd0",
    a3.ATTEMPT: "43de8c468aed8476487ce9c22ff20ba210d1392e3c22c871d1813e6576c223d4",
    "docs/governance/phase_i/PHASE_I_I3_A3_BOUNDED_LIVE_ADAPTER_ACCEPTANCE_ATTEMPT_ERRATUM_2026-10-04.json": "05a56a5b8902ffa75d7f5c163164ac79e2e3330aa03df827548810e91a29bc96",
    a3.RESERVATION: "ac8a80a62e23223d53b327d1626383900efc14df66ed536765b0905e0d5d6b4e",
    a3.CONSUMED: "a9475d4d7ef62696cb1a2c3239a628d3ec48c56fcf306373fc6331146cd89e17",
}
CANDIDATE_SHA = {
    "server/services/phase_i_i3_cash_institutional_flow_adapters.py": "401b3b56d48c690ea1634e9285f7a7857531e1b0dbbcba3a179d11420dc4ab2e",
    "server/services/phase_i_i3_cash_institutional_flow_offline_candidate.py": "5d297b1d8faf3eb829edbbfed82c8f3327de3f1ca0483adf1e437099d14d917c",
    "schemas/cash_institutional_flow_context_evidence.v1.schema.json": "3be9a0ca3cf0e0bb5badb427231d47ce86fdb604ae28cb31582b0f9612c76f7c",
}


def require(condition: bool, code: str) -> None:
    if not condition:
        raise ValueError(code)


def validate_dispatch_seam() -> None:
    source = (ROOT / "scripts/phase_i_i3_a0_source_transport.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    read_once = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "read_once")
    sites = []
    for node in ast.walk(read_once):
        if isinstance(node, ast.Try) and len(node.body) >= 2:
            guard, dispatch = node.body[:2]
            if isinstance(guard, ast.If) and isinstance(dispatch, ast.Assign):
                if ast.unparse(guard.test) == "on_http_dispatch is not None" and ast.unparse(dispatch.value) == "opener.open(request, timeout=TIMEOUT_SECONDS)":
                    sites.append(guard)
    require(len(sites) == 1 and len(sites[0].body) == 1
            and ast.unparse(sites[0].body[0]) == "on_http_dispatch()", "dispatch_observer_not_at_open_boundary")
    calls = [node for node in ast.walk(read_once) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Name) and node.func.id == "on_http_dispatch"]
    require(len(calls) == 1, "dispatch_observer_multiple_sites")


def validate() -> dict:
    def deny(*args, **kwargs):
        raise AssertionError("r1_validator_external_socket_forbidden")
    with patch("socket.socket.connect", deny), patch("socket.create_connection", deny):
        require({path: a3.sha(ROOT / path) for path in HISTORICAL_SHA} == HISTORICAL_SHA,
                "historical_a3_artifact_drift")
        require({path: a3.sha(ROOT / path) for path in CANDIDATE_SHA} == CANDIDATE_SHA,
                "a2_r1_candidate_drift")
        require(a3.immutable_hashes() == a3.HASHES, "a1_a2_authority_drift")
        historical_record = historical.validate()
        require(historical_record["A3_decision"] == "HOLD"
                and historical_record["A3_independently_accepted"] is False
                and historical_record["actual_gets"]["TPEX"] == 1,
                "historical_a3_disposition_drift")
        erratum = json.loads((ROOT / next(p for p in HISTORICAL_SHA if "ERRATUM" in p)).read_text(encoding="utf-8"))
        require(erratum["correct_http_get_attribution"] == {"TWSE": 1, "TPEX": 0, "TAIFEX": 0, "other": 0, "retry": 0}
                and erratum["owner_authority_consumed"] is True, "historical_http_dispatch_erratum_invalid")
        consumed = json.loads((ROOT / a3.CONSUMED).read_text(encoding="utf-8"))
        require(consumed["consumed"] is True and consumed["consumed_before_first_http_attempt"] is True,
                "old_owner_authority_not_consumed")
        require(CANONICAL_TO_TRANSPORT_MARKET == {"TWSE": "TWSE", "TPEX": "TPEx"}
                and transport_market_key("TWSE") == "TWSE" and transport_market_key("TPEX") == "TPEx",
                "canonical_transport_mapping_invalid")
        for alias in ("TPEx", "tpex", "TAIFEX", ""):
            try:
                transport_market_key(alias)
            except ValueError:
                pass
            else:
                raise ValueError("canonical_transport_alias_accepted")
        require(transport.URLS.keys() == {"TWSE", "TPEx"}
                and transport.MARKET_SSL_POLICY.keys() == {"TWSE", "TPEx"}
                and transport.MARKET_SSL_POLICY == {"TWSE": "compatibility", "TPEx": "strict"}
                and transport.MAX_BYTES == 4 * 1024 * 1024
                and transport.READ_CHUNK_BYTES == 64 * 1024
                and transport.TIMEOUT_SECONDS == 30
                and transport.RETRY_COUNT == 0, "reviewed_transport_policy_drift")
        validate_dispatch_seam()
        runner = (ROOT / "scripts/run_phase_i_i3_a3_bounded_live_acceptance.py").read_text(encoding="utf-8")
        require("actual_gets" not in runner and "acquisition_callback_attempts" in runner
                and "http_dispatch_count" in runner and "transport_market_key(canonical_market)" in runner,
                "current_runner_accounting_ambiguous")
        a3.production_containment()
        record = json.loads((ROOT / RECORD).read_text(encoding="utf-8"))
        require(record["schema_version"] == "phase_i_i3_a3_r1_transport_key_mapping_http_dispatch_accounting_closure.v1"
                and record["status"] == "OFFLINE_PASS_READY_FOR_SEPARATE_OWNER_REARM_DECISION"
                and record["owner_authority"] == OWNER
                and record["historical_a3_attempt_status"] == "HOLD"
                and record["historical_owner_authority_consumed"] is True
                and record["candidate_hashes_before"] == CANDIDATE_SHA
                and record["candidate_hashes_after"] == CANDIDATE_SHA
                and record["actual_market_gets_during_R1"] == {"TWSE": 0, "TPEx": 0, "TAIFEX": 0, "other": 0}
                and record["mcp_tool_count"] == 6
                and record["A3_rearm_authorized"] is False
                and record["production_activation_authorized"] is False
                and record["merge_authorized"] is False,
                "r1_record_invalid")
        print("I3-A3-R1 offline PASS; A3 Attempt 1 remains HOLD; market GETs=0; MCP=6")
        return record


if __name__ == "__main__":
    validate()

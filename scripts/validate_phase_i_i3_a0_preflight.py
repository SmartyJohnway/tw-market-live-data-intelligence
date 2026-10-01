"""Offline consistency/containment check; PASS here is not an A0 GO decision."""
from __future__ import annotations
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if not __debug__:
    raise RuntimeError("optimized_governance_validation_not_supported")
sys.path.insert(0, str(ROOT))
from scripts.run_phase_i_i3_a0_preflight import BASELINE, AUTHORITY, BRANCH, RECORD, ENDPOINTS, PROTECTED, MAX_BYTES, CORE


def validate(record=None):
    r = record if record is not None else json.loads((ROOT / RECORD).read_text(encoding="utf-8"))
    assert (r["owner_authority"], r["baseline_main"], r["branch"]) == (AUTHORITY, BASELINE, BRANCH)
    assert r["status"] == "HOLD" and r["final_decision"] == "HOLD / CONTRACT_REQUIRES_MORE_SOURCE_WORK"
    assert r["closure_failure"]["source_get_budget_consumed"] is True
    assert r["closure_failure"]["another_get_authorized"] is False
    assert r["retry_count"] == 0
    counts = r["actual_network_counts"]
    assert counts["other_market_data"] == 0 and sum(counts.values()) <= 2
    assert {t["canonical_target_id"] for t in r["security_master"]["targets"]} == {"TWSE:1101", "TPEX:5347"}
    for t in r["security_master"]["targets"]:
        assert (t["instrument_family"], t["instrument_type"], t["execution_eligibility"]) == ("company_share", "common_share", "allowed")
    for market in ("TWSE", "TPEX"):
        s = r["sources"][market]
        assert 0 <= counts[market] <= r["network_budget"][market] == 1
        assert s["get_count"] == counts[market] == 1
        assert s["endpoint"] == ENDPOINTS[market]
        assert s["http_status"] == 200 and s["redirect_outcome"] == "none"
        assert 0 < s["response_bytes"] <= MAX_BYTES
        assert re.fullmatch("[0-9a-f]{64}", s["response_sha256"])
        assert s["field_count"] == len(s["fields"]) and s["row_count"] > 0
        for check in r["arithmetic_invariants"]["whole_dataset"][market].values():
            assert check["status"] == "NOT_PERFORMED" and check["rows_checked"] == 0
            assert check["rows_failed"] is None and check["missing_field_rows"] is None
    # Do not mislabel an unrecognized discovery key as a source binding failure.
    assert r["sources"]["TPEX"]["binding_status"] == "NOT_EVALUATED"
    assert "binding_match_count" not in r["sources"]["TPEX"]
    assert r["sources"]["TPEX"]["selected_observation"] is None
    observation = r["sources"]["TWSE"]["selected_observation"]
    for group in CORE:
        values = observation[group]
        assert values["net_shares"] == values["buy_shares"] - values["sell_shares"]
    assert observation["institutional_total_net_shares"] == sum(observation[g]["net_shares"] for g in CORE)
    assert observation["trade_date"] == "2026-09-30" and observation["unit"] == "share"
    expected_groups = {"identity", "trade_date", *CORE, "institutional_total_net_shares", "foreign_dealer",
                       "foreign_and_mainland_including_foreign_dealer", "dealer_proprietary_and_hedging", "security_name"}
    assert {item["group"] for item in r["field_symmetry_matrix"]} == expected_groups
    assert all(item["classification"] in {"COMMON_CORE", "SOURCE_NATIVE_OPTIONAL", "NOT_EQUIVALENT"}
               and item["verification"] for item in r["field_symmetry_matrix"])
    assert r["cross_market_symmetry"]["trade_date_symmetry"] == "not_observed"
    assert r["publication_timing_findings"]["tpex"]["tpex_same_day_finality"] == "UNRESOLVED"
    assert r["raw_payload_persistence"] == r["raw_persistence_verification"]["result"] == "NONE"
    assert not r["raw_persistence_verification"]["raw_body_written"]
    assert not r["raw_persistence_verification"]["whole_market_rows_written"]
    assert not r["raw_persistence_verification"]["temporary_raw_files_created"]
    for key in ("a1_contract_freeze_authorized", "implementation_authorized", "production_activation_authorized",
                "merge_authorized", "i3_other_families_authorized"):
        assert r[key] is False
    for path in PROTECTED:
        current = (ROOT / path).read_bytes()
        baseline = subprocess.check_output(["git", "show", BASELINE + ":" + path], cwd=ROOT)
        assert current == baseline
        assert hashlib.sha256(current).hexdigest() == r["production_authority_sha256"][path]
    def deny(*args, **kwargs): raise AssertionError("A0 validator socket forbidden")
    with patch("socket.socket.connect", deny), patch("socket.create_connection", deny):
        from server.unified_mcp.tool_contracts import build_tool_specs
        from scripts.m8r_06_03_production_adapter import build_production_runtime_adapter_registry
        assert len(build_tool_specs()) == 6
        registry = build_production_runtime_adapter_registry()
        assert len(registry.routes_for_executor("phase_i_i1_market_state_executor")) == 2
        assert len(registry.routes_for_executor("phase_i_i2_index_futures_context_executor")) == 1
    def load(path): return json.loads((ROOT / path).read_text(encoding="utf-8"))
    catalog = load(PROTECTED[0])
    routing = load(PROTECTED[1])
    assert all(item["capability_id"] != "cash_institutional_flow_context" for item in catalog["data_need_capabilities"])
    assert all(item["capability_id"] != "cash_institutional_flow_context" for item in routing["routes"])
    for capability in ("market_state_context", "index_futures_context"):
        assert next(item for item in catalog["data_need_capabilities"] if item["capability_id"] == capability)["runtime_executable"]
    assert load(PROTECTED[2])["active_source_count"] == 3
    assert load(PROTECTED[3])["active_source_count"] == 1
    print("I3-A0 record/containment: PASS; A0 decision=HOLD, source/semantic GO NOT PROVEN; no additional network")


if __name__ == "__main__":
    validate()

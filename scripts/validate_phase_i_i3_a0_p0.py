"""Zero-network P0 closure validation. Integrity PASS can accompany gate HOLD."""
from __future__ import annotations
import ast
import hashlib
import json
import sys
from pathlib import Path
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import run_phase_i_i3_a0_preflight as p
from scripts.validate_phase_i_i3_a0_mapping import validate as validate_mapping
from scripts.validate_phase_i_i3_a0_preflight import validate as validate_historical

RECORD = "docs/governance/phase_i/PHASE_I_I3_A0_P0_OFFLINE_PROBE_HARNESS_CLOSURE_2026-10-01.json"
START_HEAD = "8a04fbd0a6749b5b52428bffafadd4ff2a84ecab"
START_TREE = "323c054b67935dd44f98c64634d48d237ed87a01"


def offline_proof():
    mapping = validate_mapping()
    body = (ROOT / "tests/fixtures/phase_i_i3_a0/twse_synthetic.json").read_bytes()
    twse = p.analyze_market("TWSE", body, mapping["markets"]["TWSE"])
    assert twse["status"] == "PASS" and twse["exact_matches"] == 1 and twse["row_count"] == 2
    assert all(c["rows_passed"] == 2 for c in twse["arithmetic"].values())
    tpex_body = (ROOT / "tests/fixtures/phase_i_i3_a0/tpex_synthetic_hypothesis_only.json").read_bytes()
    try:
        p.analyze_acquired_payloads(body, tpex_body, mapping)
    except ValueError as error:
        assert str(error) == "mapping_unresolved_dealer_total_sell"
    else:
        raise AssertionError("unresolved formal mapping incorrectly accepted")
    return {"TWSE": twse, "TPEX": {"status": "BLOCKED_UNRESOLVED_AGGREGATE_DEALER_SELL",
                                   "formal_full_path": "NOT_PROVEN",
                                   "test_only_engine_hypothesis_is_not_source_authority": True}}


def validate(record=None):
    if not __debug__:
        raise RuntimeError("optimized_governance_validation_not_supported")
    with patch("socket.socket.connect", p.deny_network), patch("socket.create_connection", p.deny_network):
        validate_historical()
        proof = offline_proof()
        source = (ROOT / "scripts/run_phase_i_i3_a0_preflight.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        forbidden = {"input", "stdin", "subprocess", "urllib", "requests"}
        assert not any(isinstance(n, ast.Name) and n.id in forbidden for n in ast.walk(tree))
        assert not any(isinstance(n, (ast.Import, ast.ImportFrom)) and
                       any(a.name.split(".")[0] in forbidden for a in n.names) for n in ast.walk(tree))
        transport_stub = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "fixed_get")
        assert all(isinstance(n, (ast.Expr, ast.Raise)) for n in transport_stub.body)
        assert any(isinstance(n, ast.Raise) for n in transport_stub.body)
        for invocation in (lambda: p.run(p.AUTHORITY),):
            try:
                invocation()
            except ValueError as error:
                assert str(error) == "fresh_a0_rearm_not_authorized"
            else:
                raise AssertionError("historical authority rearmed")
        r = record if record is not None else json.loads((ROOT / RECORD).read_text(encoding="utf-8"))
        assert r["schema_version"] == "phase_i_i3_a0_p0_offline_probe_harness_closure.v1"
        assert (r["owner_authority"], r["baseline_main"], r["starting_pr"], r["starting_head"], r["starting_tree"]) == (
            p.P0_AUTHORITY, p.BASELINE, 300, START_HEAD, START_TREE)
        h = r["historical_attempt_1"]
        assert h == {"status": "HOLD", "record_sha256": p.HISTORICAL_SHA,
                     "TWSE_get_consumed": 1, "TPEX_get_consumed": 1, "retry": 0, "immutable": True}
        assert r["mapping_authority"] == {"path": p.DEFAULT_MAPPING_AUTHORITY.relative_to(ROOT).as_posix(),
                                         "sha256": p.MAPPING_SHA, "mapping_status": "UNRESOLVED"}
        assert r["offline_fixture_proof"] == proof
        assert r["stdin_dependency"] == "absent" and r["arbitrary_local_mapping"] == "rejected"
        assert r["market_network_calls"] == 0 and r["production_authority_changed"] is False
        assert r["runtime"] == {"I1_active_sources": 3, "I1_routes": 2, "I2_active_sources": 1,
                                "I2_routes": 1, "I2_selected_executor": "phase_i_i2_index_futures_context_executor",
                                "I3_capability_present": False, "MCP": 6}
        assert r["final_decision"] == "HOLD"
        for key in ("fresh_a0_rearm_ready", "fresh_a0_rearm_authorized", "A1_authorized",
                    "implementation_authorized", "production_activation_authorized", "merge_authorized"):
            assert r[key] is False
        assert r["raw_payload_persistence"] == "NONE"
        assert hashlib.sha256((ROOT / p.RECORD).read_bytes()).hexdigest() == p.HISTORICAL_SHA
    print("P0 integrity/containment PASS; final P0=HOLD; fresh_a0_rearm_ready=false; market GETs=0")


if __name__ == "__main__":
    validate()

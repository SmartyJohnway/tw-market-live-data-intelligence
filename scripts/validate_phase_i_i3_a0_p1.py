"""Validate P1 adjudication tooling without source acquisition."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import run_phase_i_i3_a0_preflight as runner
from scripts.validate_phase_i_i3_a0_p0 import validate as validate_p0
from scripts.phase_i_i3_a4_compat import assert_candidate_is_dormant, assert_non_i3_authority_unchanged

RECORD = ROOT / "docs/governance/phase_i/PHASE_I_I3_A0_P1_TPEX_DEALER_SELL_ADJUDICATION_HARNESS_2026-10-01.json"
HISTORICAL = {
    "docs/governance/phase_i/PHASE_I_I3_A0_CASH_INSTITUTIONAL_FLOW_SOURCE_TIMING_SYMMETRY_PREFLIGHT_2026-10-01.json":
        "43ef038ffd33a455ae52eff18a8f08e52436164b6d27d6140090b368810df5e0",
    "docs/governance/phase_i/PHASE_I_I3_A0_CASH_INSTITUTIONAL_FLOW_PROBE_MAPPING_V1.json":
        "e3af3d8b5ce11fe88f0c32efa45400126fe1991ec0c0725fbc3f480e2888638c",
    "docs/governance/phase_i/PHASE_I_I3_A0_P0_OFFLINE_PROBE_HARNESS_CLOSURE_2026-10-01.json":
        "8d58c1eb22941099f28e72e884c4686ddab1a66de752dfd343892e959fca118a",
}


def _git_blob(path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{runner.BASELINE}:{path}"], cwd=ROOT)


def validate(record: dict | None = None) -> dict:
    if not __debug__:
        raise RuntimeError("optimized_governance_validation_not_supported")

    def deny(*args, **kwargs):
        raise AssertionError("P1 network access forbidden")

    with patch("socket.socket.connect", deny), patch("socket.create_connection", deny):
        # Replay exact prior-gate checks first; P1 cannot promote P0/HOLD.
        validate_p0()
        mapping = runner.load_mapping()
        authority = runner.load_adjudication_authority()
        assert mapping["mapping_status"] == "UNRESOLVED"
        assert authority["selection_status"] == "UNRESOLVED_UNTIL_FRESH_SOURCE"

        for rel, expected in HISTORICAL.items():
            assert hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == expected, rel
        for rel in runner.PROTECTED:
            if rel.endswith(".json") and rel in {
                runner.PROTECTED[0], runner.PROTECTED[1], runner.PROTECTED[6], runner.PROTECTED[7], runner.PROTECTED[8],
            }:
                assert_non_i3_authority_unchanged(rel)
            else:
                current = (ROOT / rel).read_bytes()
                assert current == _git_blob(rel), f"production_authority_changed:{rel}"

        scenarios = json.loads((ROOT / "tests/fixtures/phase_i_i3_a0/dealer_sell_adjudication_scenarios.json").read_text(encoding="utf-8"))
        expected = {
            "unique_candidate_a": ("RESOLVED", "Dealers-TotalSell"),
            "unique_candidate_b": ("RESOLVED", "Dealers -TotalSell"),
            "both_candidates_valid": ("AMBIGUOUS_ALIAS", None),
            "neither_candidate_valid": ("NO_MATCH", None),
            "missing_candidate_fields": ("MISSING_CANDIDATE_FIELD", None),
            "malformed_integer": ("NO_MATCH", None),
            "zero_rows": ("NO_MATCH", None),
            "institutional_total_mismatch": ("INSTITUTIONAL_TOTAL_MISMATCH", None),
        }
        for name, wanted in expected.items():
            outcome = runner.adjudicate_tpex_dealer_sell(scenarios[name], authority)
            assert (outcome["selection_status"], outcome["selected_candidate"]) == wanted, name
        partial = runner.adjudicate_tpex_dealer_sell(scenarios["one_candidate_row_mismatch"], authority)
        assert partial["selection_status"] == "RESOLVED"
        assert partial["selected_candidate"] == "Dealers -TotalSell"
        stats = partial["candidate_statistics"]["Dealers-TotalSell"]
        assert (stats["rows_checked"], stats["rows_passed"], stats["rows_failed"], stats["missing_rows"]) == (2, 1, 1, 0)

        value = record if record is not None else json.loads(RECORD.read_text(encoding="utf-8"))
        assert value["schema_version"] == "phase_i_i3_a0_p1_tpex_dealer_sell_adjudication_harness.v1"
        assert value["status"] == "OFFLINE_ADJUDICATION_HARNESS_READY"
        assert value["historical_gates"]["a0_attempt_1"]["status"] == "HOLD"
        assert value["historical_gates"]["p0"]["status"] == "HOLD"
        assert value["semantic_adjudication"]["exact_openapi_sell_key"] == "UNRESOLVED_UNTIL_FRESH_SOURCE"
        assert value["semantic_adjudication"]["selection_mode"] == "UNIQUE_WHOLE_DATASET_ARITHMETIC_MATCH"
        assert value["adjudication_authority"]["sha256"] == runner.ADJUDICATION_AUTHORITY_SHA
        assert value["offline_boundary"]["market_network_calls"] == 0
        assert value["offline_boundary"]["raw_payload_persistence"] == "NONE"
        assert value["runtime_containment"] == {
            "production_authority_changed": False, "I1_sources": 3, "I1_routes": 2,
            "I2_sources": 1, "I2_routes": 1,
            "I2_selected_executor": "phase_i_i2_index_futures_context_executor",
            "I3_capability_present": False, "MCP": 6,
        }
        assert_candidate_is_dormant(runner.PROTECTED[0], runner.PROTECTED[1])
        assert value["validation"] == {
            "focused_p1": {"passed": 14, "skipped": 0, "deselected": 0},
            "focused_a0_p0_p1": {"passed": 68, "skipped": 0, "deselected": 0},
            "default_ci": {"passed": 946, "skipped": 1, "deselected": 5},
            "full_current": {"passed": 1319, "skipped": 1, "deselected": 5},
            "compileall": "PASS", "historical_a0_validator": "PASS_HOLD_PRESERVED",
            "p0_validator": "PASS_INTEGRITY_GATE_HOLD", "p1_validator": "PASS_OFFLINE_ADJUDICATION_HARNESS",
            "I1_validators": "PASS", "I2_A1_A4_validators": "PASS", "Phase_H_validator": "PASS",
            "portable_catalog_sync": "PASS", "runtime_skill_guide_sync": "PASS_MCP_6",
            "production_authorities_vs_main": "BYTE_IDENTICAL", "normal_diff_check": "PASS",
            "crlf_aware_diff_check": "PASS",
        }
        decision = value["decision"]
        assert decision["p1"] == "OFFLINE_ADJUDICATION_HARNESS_READY"
        assert decision["a0_attempt_1"] == decision["p0"] == "HOLD"
        assert decision["fresh_attempt_2_ready"] is True
        for key in ("fresh_attempt_2_authorized", "A1_authorized", "implementation_authorized",
                    "production_activation_authorized", "merge_authorized", "I3_other_families_authorized",
                    "phase_j_authorized"):
            assert decision[key] is False, key

        # Attempt 1's authority remains permanently disarmed in the harness.
        try:
            runner.run(runner.AUTHORITY)
        except ValueError as error:
            assert str(error) == "fresh_a0_rearm_not_authorized"
        else:
            raise AssertionError("historical A0 authority unexpectedly rearmed")

    print("P1 offline adjudication PASS; Attempt 1 and P0 remain HOLD; market calls=0")
    return value


if __name__ == "__main__":
    validate()

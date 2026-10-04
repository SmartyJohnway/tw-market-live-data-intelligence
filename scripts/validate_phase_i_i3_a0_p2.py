"""Offline P2 provenance/TLS transport closure validator."""
from __future__ import annotations

import hashlib
import json
import ssl
import socket
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import phase_i_i3_a0_attempt_authority as authority
from scripts import phase_i_i3_a0_source_transport as transport
from scripts import validate_phase_i_i3_a0_attempt2 as attempt2

P2_RECORD = ROOT / "docs/governance/phase_i/PHASE_I_I3_A0_P2_ATTEMPT_2_PROVENANCE_AND_TWSE_TRANSPORT_COMPATIBILITY_CLOSURE_2026-10-02.json"
ERRATUM = ROOT / "docs/governance/phase_i/PHASE_I_I3_A0_ATTEMPT_2_PROVENANCE_ERRATUM_2026-10-02.json"
READINESS = ROOT / "docs/governance/phase_i/PHASE_I_I3_A0_ATTEMPT_3_READINESS_PLAN_2026-10-02.json"
EXPECTED = {
    "attempt_1_record_sha256": "43ef038ffd33a455ae52eff18a8f08e52436164b6d27d6140090b368810df5e0",
    "p0_mapping_sha256": "e3af3d8b5ce11fe88f0c32efa45400126fe1991ec0c0725fbc3f480e2888638c",
    "p0_record_sha256": "8d58c1eb22941099f28e72e884c4686ddab1a66de752dfd343892e959fca118a",
    "p1_authority_sha256": "666108fdd187f3ec753acc2a258e3ea7bd9415cc371346b5f32dc231ea665240",
    "p1_record_sha256": "541b62d45d248d28e114d04628aac379dbd2f5b6d66d6ad07ae8cd4ee661a70c",
}
STARTING_HEAD = "95ecd142500e6f1b4bc82ae9a799c209e6a8896b"
HISTORICAL_BLOBS = (
    "docs/governance/phase_i/PHASE_I_I3_A0_ATTEMPT_2_SOURCE_TIMING_SYMMETRY_REPROBE_2026-10-01.json",
    "docs/governance/phase_i/acceptance_runs/i3-a0-attempt2-authority-reservation.json",
    "docs/governance/phase_i/acceptance_runs/i3-a0-attempt2-authority-consumed.json",
)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate() -> dict:
    def deny(*args, **kwargs):
        raise AssertionError("P2 validator must remain offline")
    with patch("socket.socket.connect", deny), patch("socket.create_connection", deny):
        chain = authority.load_reviewed_authority_chain()
        for key, expected in EXPECTED.items():
            assert chain[key] == expected
        erratum = json.loads(ERRATUM.read_text(encoding="utf-8"))
        assert erratum["classification"] == "PROVENANCE_METADATA_DEFECT_ONLY"
        assert erratum["historical_recorded_value"] == EXPECTED["attempt_1_record_sha256"]
        assert erratum["correct_authority_value"] == EXPECTED["p0_record_sha256"]
        reservation = json.loads((ROOT / "docs/governance/phase_i/acceptance_runs/i3-a0-attempt2-authority-reservation.json").read_text(encoding="utf-8"))
        consumed = json.loads((ROOT / "docs/governance/phase_i/acceptance_runs/i3-a0-attempt2-authority-consumed.json").read_text(encoding="utf-8"))
        assert reservation["p0_record_sha256"] == consumed["p0_record_sha256"] == EXPECTED["attempt_1_record_sha256"]
        assert reservation["p0_record_sha256"] != EXPECTED["p0_record_sha256"]
        attempt2.validate_provenance(ROOT)
        record = json.loads(P2_RECORD.read_text(encoding="utf-8"))
        assert record["decision"] == "P2_PASS"
        chain_path = ROOT / "docs/governance/phase_i/PHASE_I_I3_A0_FUTURE_ATTEMPT_AUTHORITY_CHAIN_V1.json"
        assert record["future_authority_chain"]["path"] == chain_path.relative_to(ROOT).as_posix()
        assert record["future_authority_chain"]["sha256"] == _digest(chain_path)
        assert record["future_authority_chain"]["anchor_fields"] == list(EXPECTED)
        assert record["attempt_2"]["record_sha256_as_measured"] == _digest(ROOT / "docs/governance/phase_i/PHASE_I_I3_A0_ATTEMPT_2_SOURCE_TIMING_SYMMETRY_REPROBE_2026-10-01.json")
        assert record["attempt_2"]["previously_reported_record_sha256"] != record["attempt_2"]["record_sha256_as_measured"]
        assert record["attempt_2"]["record_bytes_match_starting_commit"] is True
        assert record["attempt_2"]["reservation_sha256"] == _digest(ROOT / "docs/governance/phase_i/acceptance_runs/i3-a0-attempt2-authority-reservation.json")
        assert record["attempt_2"]["consumed_latch_sha256"] == _digest(ROOT / "docs/governance/phase_i/acceptance_runs/i3-a0-attempt2-authority-consumed.json")
        assert record["attempt_3_ready"] is True and record["attempt_3_authorized"] is False
        assert record["market_network_calls"] == 0
        assert record["production_runtime_changed"] is False and record["MCP_tool_count"] == 6
        assert record["transport_finding"]["same_root_cause_for_attempt_2"] == "NOT_PROVEN"
        assert record["future_transport"]["TWSE_ssl_policy"] == "compatibility"
        assert record["future_transport"]["TPEx_ssl_policy"] == "strict"
        assert record["future_transport"]["unsafe_explicit"] == "forbidden"
        assert record["future_transport"]["silent_fallback"] is False
        assert record["future_transport"]["retry"] == 0
        plan = json.loads(READINESS.read_text(encoding="utf-8"))
        assert plan["attempt_3_authorized"] is False
        assert plan["reservation_created"] is False and plan["consumed_latch_created"] is False
        assert plan["outcome_record_created"] is False
        assert plan["markets"]["TWSE"] == {"ssl_policy": "compatibility", "max_gets": 1}
        assert plan["markets"]["TPEx"] == {"ssl_policy": "strict", "max_gets": 1}
        assert plan["retry"] == 0 and plan["silent_tls_fallback"] is False
        context = transport.build_ssl_context("compatibility")
        assert isinstance(context, ssl.SSLContext)
        assert context.verify_mode == ssl.CERT_REQUIRED and context.check_hostname
        if hasattr(ssl, "VERIFY_X509_STRICT"):
            assert context.verify_flags & ssl.VERIFY_X509_STRICT == 0
        immutable = {
            "docs/governance/phase_i/PHASE_I_I3_A0_CASH_INSTITUTIONAL_FLOW_SOURCE_TIMING_SYMMETRY_PREFLIGHT_2026-10-01.json": "43ef038ffd33a455ae52eff18a8f08e52436164b6d27d6140090b368810df5e0",
            "docs/governance/phase_i/PHASE_I_I3_A0_CASH_INSTITUTIONAL_FLOW_PROBE_MAPPING_V1.json": "e3af3d8b5ce11fe88f0c32efa45400126fe1991ec0c0725fbc3f480e2888638c",
            "docs/governance/phase_i/PHASE_I_I3_A0_P0_OFFLINE_PROBE_HARNESS_CLOSURE_2026-10-01.json": "8d58c1eb22941099f28e72e884c4686ddab1a66de752dfd343892e959fca118a",
            "docs/governance/phase_i/PHASE_I_I3_A0_TPEX_DEALER_SELL_ADJUDICATION_V1.json": "666108fdd187f3ec753acc2a258e3ea7bd9415cc371346b5f32dc231ea665240",
            "docs/governance/phase_i/PHASE_I_I3_A0_P1_TPEX_DEALER_SELL_ADJUDICATION_HARNESS_2026-10-01.json": "541b62d45d248d28e114d04628aac379dbd2f5b6d66d6ad07ae8cd4ee661a70c",
            "docs/governance/phase_i/PHASE_I_I3_A0_ATTEMPT_2_SOURCE_TIMING_SYMMETRY_REPROBE_2026-10-01.json": "21cafa9ec4bd351454a47de76d0eba3f562ebeeef0233731d5b256a1052a8d1c",
        }
        for rel, digest in immutable.items():
            assert _digest(ROOT / rel) == digest, rel
        record_attempt2 = HISTORICAL_BLOBS[0]
        measured_attempt2 = _digest(ROOT / record_attempt2)
        git_attempt2 = subprocess.check_output(["git", "show", f"{STARTING_HEAD}:{record_attempt2}"], cwd=ROOT)
        assert (ROOT / record_attempt2).read_bytes() == git_attempt2
        assert record["attempt_2"]["record_sha256_as_measured"] == measured_attempt2
        assert record["attempt_2"]["record_bytes_match_starting_commit"] is True
        for rel in HISTORICAL_BLOBS[1:]:
            prior = subprocess.check_output(["git", "show", f"{STARTING_HEAD}:{rel}"], cwd=ROOT)
            assert (ROOT / rel).read_bytes() == prior, rel
        attempt2.validate()
    print("I3-A0-P2 provenance/TLS policy closure: PASS; network=0; Attempt 3 unauthorized")
    return record


if __name__ == "__main__":
    validate()

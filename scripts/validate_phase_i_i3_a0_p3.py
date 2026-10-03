"""Offline P3 integrity, attribution, body-read and readiness gate."""
from __future__ import annotations

import hashlib
import json
import socket
import ssl
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import phase_i_i3_a0_attempt_authority as authority
from scripts import phase_i_i3_a0_source_transport as transport
from scripts import validate_phase_i_i3_a0_attempt3 as historical
from scripts.run_phase_i_i3_a0_preflight import PROTECTED

PREFIX = "docs/governance/phase_i/"
P3_REL = PREFIX + "PHASE_I_I3_A0_P3_ATTEMPT_3_EVIDENCE_ERRATUM_AND_BOUNDED_BODY_READ_CLOSURE_2026-10-03.json"
PLAN_REL = PREFIX + "PHASE_I_I3_A0_ATTEMPT_4_READINESS_PLAN_2026-10-03.json"
BASELINE = "dafa5999c63d34d55a4665c6534aa77477448d79"
OWNER = "USER_CHAT_2026-10-03_PHASE_I_I3_A0_P3_ATTEMPT3_EVIDENCE_ERRATUM_AND_BOUNDED_BODY_READ_CLOSURE"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate() -> dict:
    def deny(*args, **kwargs):
        raise AssertionError("P3 validator network forbidden")
    with patch("socket.socket.connect", deny), patch("socket.create_connection", deny):
        historical.validate_erratum(ROOT)
        assert sha(authority.AUTHORITY_PATH) == "bbe45e1ff6126f3751faf589343f31c28a0f8d2c552cea8472d58ab5c6f1e91c"
        # Replay the historical V2 authority, not current Attempt 4 eligibility.
        authority.load_reviewed_authority_chain(version="v2")
        record = json.loads((ROOT / P3_REL).read_text(encoding="utf-8"))
        assert record["owner_authority"] == OWNER
        assert record["baseline_main"] == BASELINE
        assert record["starting_head"] == "e9ef5c70d20f2f2914a22f00830721408e24d634"
        assert record["starting_tree"] == "717eb5d29a29a0f4190e00be30d1db74afc0a427"
        assert record["decision"] == "P3_PASS"
        assert record["market_network_calls"] == 0
        assert record["attempt_4_ready"] is True
        for field in ("attempt_4_authorized", "A1_authorized", "implementation_authorized", "production_activation_authorized", "merge_authorized"):
            assert record[field] is False
        assert record["attempt_3"]["status"] == "HOLD" and record["attempt_3"]["consumed"] is True
        assert record["twse_evidence"] == {"accepted": True, "reusable_for_composite_A0": True}
        assert record["tpex_evidence"] == {"complete_body": False, "semantics": "NOT_EVALUATED"}
        assert record["erratum"]["sha256"] == sha(ROOT / historical.ERRATUM_REL)
        assert record["future_authority_chain"]["version"] == "v2"
        assert record["future_authority_chain"]["sha256"] == sha(authority.AUTHORITY_V2_PATH)
        assert record["readiness_plan"]["sha256"] == sha(ROOT / PLAN_REL)
        assert transport.READ_CHUNK_BYTES == 65536 and transport.MAX_BYTES == 4194304
        assert transport.RETRY_COUNT == 0 and transport.TIMEOUT_SECONDS == 30
        assert transport.MARKET_SSL_POLICY == {"TWSE": "compatibility", "TPEx": "strict"}
        context = transport.build_ssl_context("compatibility")
        assert isinstance(context, ssl.SSLContext) and context.verify_mode == ssl.CERT_REQUIRED and context.check_hostname
        if hasattr(ssl, "VERIFY_X509_STRICT"):
            assert not context.verify_flags & ssl.VERIFY_X509_STRICT
        try:
            transport.policy_for_market("TWSE", "unsafe-explicit")
        except ValueError:
            pass
        else:
            raise AssertionError("unsafe policy accepted")
        plan = json.loads((ROOT / PLAN_REL).read_text(encoding="utf-8"))
        assert plan["status"] == "NON_EXECUTABLE_CONFIGURATION_ONLY"
        assert plan["attempt_4_authorized"] is False
        assert plan["markets"] == {"TWSE": {"max_gets": 0}, "TPEx": {"max_gets": 1, "ssl_policy": "strict"}}
        assert plan["retry"] == 0 and plan["redirect_policy"] == "reject"
        assert plan["TAIFEX_max_gets"] == plan["other_max_gets"] == 0
        twse = plan["twse_reuse"]
        old = json.loads((ROOT / historical.OUTCOME_REL).read_text(encoding="utf-8"))
        assert twse["response_sha256"] == old["source_telemetry"]["TWSE"]["response_sha256"]
        assert twse["response_sha256"] == "b292ec02ee89e3aa951337e0504662fee7ee2d7509628199e6752fa36860453e"
        assert twse["source_trade_date"] == "2026-09-30"
        assert twse["rows"] == 1341 and twse["fields"] == 19
        assert twse["exact_binding"] == 1 and twse["unit"] == "share"
        assert twse["whole_dataset_arithmetic"] == "PASS"
        assert plan["composite_closure"]["historical_hard_coded_batching_flags_are_fresh_proof"] is False
        # Historical P3 asserted no Attempt 4 latch at its own baseline. Later
        # V3-authorized Attempt 4 evidence must not invalidate that old fact.
        for rel in (PREFIX + "acceptance_runs/i3-a0-attempt4-authority-reservation.json",
                    PREFIX + "acceptance_runs/i3-a0-attempt4-authority-consumed.json"):
            historical_path = subprocess.run(["git", "cat-file", "-e", f"8be2cfe795b10591be564b441a17094df2884d1e:{rel}"],
                cwd=ROOT, capture_output=True)
            assert historical_path.returncode != 0, rel
            assert (ROOT / rel).is_file(), f"current_authorized_attempt4_artifact_missing:{rel}"
        for relative in PROTECTED:
            assert (ROOT / relative).read_bytes() == subprocess.check_output(["git", "show", BASELINE + ":" + relative], cwd=ROOT), relative
        from scripts.m8r_06_03_production_adapter import build_production_runtime_adapter_registry
        from server.unified_mcp.tool_contracts import build_tool_specs
        registry = build_production_runtime_adapter_registry()
        assert len(registry.routes_for_executor("phase_i_i1_market_state_executor")) == 2
        assert len(registry.routes_for_executor("phase_i_i2_index_futures_context_executor")) == 1
        assert len(build_tool_specs()) == record["MCP_tool_count"] == 6
        for rel, expected in (("docs/data_capabilities/phase_i_i1_source_authority.v1.json", 3),
                              ("docs/data_capabilities/phase_i_i2_source_authority.v1.json", 1)):
            value = json.loads((ROOT / rel).read_text(encoding="utf-8"))
            assert value["active_source_count"] == expected
        catalog = json.loads((ROOT / PROTECTED[0]).read_text(encoding="utf-8"))
        assert all(item["capability_id"] != "cash_institutional_flow_context" for item in catalog["data_need_capabilities"])
    print("P3 PASS: historical HOLD/readiness bytes unchanged; current Attempt 4 artifacts are separate; MCP=6")
    return record


if __name__ == "__main__":
    validate()

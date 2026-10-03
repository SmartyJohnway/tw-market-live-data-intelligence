"""Zero-network R1 real analyzer integration, immutable history and V3 gate."""
from __future__ import annotations
import hashlib
import json
import socket
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import phase_i_i3_a0_attempt_authority as authority
from scripts import phase_i_i3_a0_future_evidence as evidence
from scripts import run_phase_i_i3_a0_preflight as analyzer

PREFIX = "docs/governance/phase_i/"
RECORD = PREFIX + "PHASE_I_I3_A0_P3_R1_REAL_ANALYZER_FUTURE_EVIDENCE_INTEGRATION_CLOSURE_2026-10-03.json"
PLAN = PREFIX + "PHASE_I_I3_A0_ATTEMPT_4_READINESS_PLAN_V2_2026-10-03.json"
BASELINE = "dafa5999c63d34d55a4665c6534aa77477448d79"
START = "95b0453e2b7c6c93a99ecc6f59e6f743cf011520"
OWNER = "USER_CHAT_2026-10-03_PHASE_I_I3_A0_P3_R1_REAL_ANALYZER_FUTURE_EVIDENCE_INTEGRATION_CLOSURE"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def offline_interface_proof():
    fixtures = ROOT / "tests/fixtures/phase_i_i3_a0"
    twse = json.loads((fixtures / "twse_synthetic.json").read_text(encoding="utf-8"))
    tpex = json.loads((fixtures / "dealer_sell_adjudication_scenarios.json").read_text(encoding="utf-8"))["unique_candidate_a"]
    mapping = analyzer.load_mapping()
    result = analyzer.analyze_acquired_payloads(twse, tpex, mapping, analyzer.load_adjudication_authority())
    assert result["status"] == "PASS" and result["dealer_sell_adjudication"]["selection_status"] == "RESOLVED"
    assert result["dealer_sell_adjudication"]["selected_candidate"] == "Dealers-TotalSell"
    standalone = analyzer.analyze_market("TWSE", twse, mapping["markets"]["TWSE"])
    assert standalone == result["sources"]["TWSE"]
    composite = evidence.compose_analyzer_evidence(standalone, result["sources"]["TPEX"],
        result["dealer_sell_adjudication"], whole_market_observations={"TWSE": True, "TPEx": True},
        prior_evidence_refs=["synthetic-TWSE-summary", "synthetic-P1-proof"])
    for market, upstream in (("TWSE", "TWSE"), ("TPEx", "TPEX")):
        item = composite["sources"][market]
        actual = result["sources"][upstream]
        assert not {"unit", "observation", "whole_market_payload"} & set(actual)
        assert item["evaluation_status"] == "EVALUATED" and item["target_binding"] == 1
        assert item["unit_proof"] == "share" and item["whole_dataset_arithmetic"] == actual["arithmetic"]
        assert item["normalized_observation"] == {"market": upstream, **actual["selected_observation"]}
    assert composite["mixed_market_observation"] == "PROVEN"
    absent = evidence.source_findings_from_analyzer_result(None, complete_body_received=False, whole_market_payload_observed=False)
    assert absent["target_binding"] is None and absent["evaluation_status"] == "NOT_EVALUATED"
    zero = evidence.binding_findings_from_payload("TPEX", [r for r in tpex if r["SecuritiesCompanyCode"] != "5347"],
        complete_body_received=True, whole_market_payload_observed=True)
    target = next(r for r in tpex if r["SecuritiesCompanyCode"] == "5347")
    duplicate = evidence.binding_findings_from_payload("TPEX", tpex + [target], complete_body_received=True, whole_market_payload_observed=True)
    assert zero["target_binding"] == 0 and duplicate["target_binding"] == 2
    assert zero["normalized_observation"] is duplicate["normalized_observation"] is None
    return {"real_analyze_market": "PASS", "real_acquired_P1_path": "PASS", "canonical_source_adaptation": "PASS",
            "dealer_key": "Dealers-TotalSell", "bindings": {"TWSE": 1, "TPEX": 1}, "unit": "share",
            "no_body": "NOT_EVALUATED/null", "zero_match": "EVALUATED_BINDING_FAILED/0",
            "duplicate_match": "EVALUATED_BINDING_FAILED/2", "mixed_batching": "PROVEN", "raw_persistence": "NONE"}


def validate():
    def deny(*args, **kwargs):
        raise AssertionError("R1 validator external network forbidden")
    with patch("socket.socket.connect", deny), patch("socket.create_connection", deny):
        v2 = authority.load_reviewed_authority_chain(version="v2")
        v3 = authority.load_reviewed_authority_chain(version="v3", attempt_number=4)
        for version in ("v1", "v2"):
            try:
                authority.load_reviewed_authority_chain(version=version, attempt_number=4)
            except ValueError as error:
                assert str(error) == "attempt4_requires_explicit_v3"
            else:
                raise AssertionError("Attempt4 old authority accepted")
        immutable = set(authority.HASHED_PATHS.values()) | {x["path"] for x in v2["additional_anchors"].values()}
        immutable |= {authority.AUTHORITY_PATH.relative_to(ROOT).as_posix(), authority.AUTHORITY_V2_PATH.relative_to(ROOT).as_posix(),
            v2["p3_closure_reference"]["path"], PREFIX + "PHASE_I_I3_A0_ATTEMPT_4_READINESS_PLAN_2026-10-03.json",
            "scripts/phase_i_i3_a0_source_transport.py", "scripts/run_phase_i_i3_a0_preflight.py"}
        for rel in immutable:
            assert (ROOT / rel).read_bytes() == subprocess.check_output(["git", "show", START + ":" + rel], cwd=ROOT), rel
        for rel in analyzer.PROTECTED:
            assert (ROOT / rel).read_bytes() == subprocess.check_output(["git", "show", BASELINE + ":" + rel], cwd=ROOT), rel
        erratum = json.loads((ROOT / v3["r1_erratum"]["path"]).read_text(encoding="utf-8"))
        assert erratum["status"] == "ACCEPTED_INDEPENDENT_REVIEW_INTEGRATION_GAP"
        assert erratum["classification"] == "OFFLINE_INTERFACE_PROOF_GAP"
        assert erratum["attempt_4_readiness_acceptance_before_r1"] == "WITHHELD_PENDING_P3_R1"
        assert erratum["old_helper_assumptions"] == ["unit", "observation", "whole_market_payload"]
        assert all(value is False for value in erratum["impact"].values())
        record = json.loads((ROOT / RECORD).read_text(encoding="utf-8"))
        assert record["decision"] == "P3_R1_PASS" and record["owner_authority"] == OWNER
        assert record["baseline_main"] == BASELINE and record["starting_head"] == START
        assert record["starting_tree"] == "12788c66d36d1e1df557b582178b6850ac389e45"
        assert record["historical_p3"] == {"decision": "P3_PASS", "self_declared_attempt_4_ready": True, "bytes_unchanged": True}
        assert record["independent_review"]["readiness_accepted_before_r1"] is False
        assert record["market_network_calls"] == 0 and record["attempt_4_ready"] is True
        for field in ("attempt_4_authorized", "A1_authorized", "implementation_authorized", "production_activation_authorized", "merge_authorized"):
            assert record[field] is False
        proof = offline_interface_proof()
        assert record["offline_interface_proof"] == proof
        plan = json.loads((ROOT / PLAN).read_text(encoding="utf-8"))
        assert plan["supersedes_prior_readiness_plan"] is True and plan["prior_readiness_not_execution_authority"] is True
        assert plan["status"] == "NON_EXECUTABLE_CONFIGURATION_ONLY" and plan["authority_chain_version"] == "v3"
        assert plan["markets"] == {"TWSE": {"max_gets": 0}, "TPEx": {"max_gets": 1, "ssl_policy": "strict"}}
        assert plan["attempt_4_ready"] is True and plan["attempt_4_authorized"] is False
        assert plan["retry"] == 0 and plan["redirect_policy"] == "reject"
        old_plan = json.loads((ROOT / plan["prior_readiness_path"]).read_text(encoding="utf-8"))
        assert plan["twse_reuse"] == old_plan["twse_reuse"]
        assert record["readiness"]["sha256"] == sha(ROOT / PLAN)
        assert record["authority"]["v3_sha256"] == sha(authority.AUTHORITY_V3_PATH)
        # The R1 candidate proved there was no Attempt 4 reservation then.
        # A later separately authorized V3 attempt is valid current evidence.
        for rel in (PREFIX + "acceptance_runs/i3-a0-attempt4-authority-reservation.json",
                    PREFIX + "acceptance_runs/i3-a0-attempt4-authority-consumed.json"):
            historical_path = subprocess.run(["git", "cat-file", "-e", f"{START}:{rel}"],
                cwd=ROOT, capture_output=True)
            assert historical_path.returncode != 0, rel
            assert (ROOT / rel).is_file(), f"current_authorized_attempt4_artifact_missing:{rel}"
        from scripts.m8r_06_03_production_adapter import build_production_runtime_adapter_registry
        from server.unified_mcp.tool_contracts import build_tool_specs
        registry = build_production_runtime_adapter_registry()
        assert len(registry.routes_for_executor("phase_i_i1_market_state_executor")) == 2
        assert len(registry.routes_for_executor("phase_i_i2_index_futures_context_executor")) == 1
        assert len(build_tool_specs()) == 6
        assert json.loads((ROOT / "docs/data_capabilities/phase_i_i1_source_authority.v1.json").read_text(encoding="utf-8"))["active_source_count"] == 3
        assert json.loads((ROOT / "docs/data_capabilities/phase_i_i2_source_authority.v1.json").read_text(encoding="utf-8"))["active_source_count"] == 1
        catalog = json.loads((ROOT / analyzer.PROTECTED[0]).read_text(encoding="utf-8"))
        assert all(c["capability_id"] != "cash_institutional_flow_context" for c in catalog["data_need_capabilities"])
    print("P3-R1 PASS: real analyzer/composite interface; historical bytes immutable; current Attempt4 evidence is separate; MCP=6")
    return record


if __name__ == "__main__":
    validate()

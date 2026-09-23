from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from server.services.unified_local_service import describe_capabilities
from server.unified_mcp import ADAPTER_VERSION, LOCAL_SERVICE_CONTRACT_VERSION
from server.unified_mcp.tool_contracts import build_tool_specs


ROOT = Path(__file__).resolve().parents[2]
CLOSURE = ROOT / "docs/acceptance_runs/phase_g_pr_d_closure.json"
P0 = ROOT / "docs/acceptance_runs/phase_g_pr_d_p0_ledger.json"
P1 = ROOT / "docs/acceptance_runs/phase_g_pr_d_controlled_live.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_phase_g_final_acceptance_ledgers_are_complete_and_bound():
    closure = _load(CLOSURE)
    p0 = _load(P0)
    p1 = _load(P1)
    assert closure["status"] == p0["status"] == p1["status"] == "PASS"
    assert len(p0["cases"]) == closure["acceptance"]["p0"]["passed"] == 74
    assert closure["acceptance"]["p0"]["ledger_sha256"] == _sha256(P0)
    assert closure["acceptance"]["p1"]["ledger_sha256"] == _sha256(P1)
    assert closure["acceptance"]["p1"]["cases"] == {
        f"L{index:02d}": "PASS" for index in range(1, 9)
    }
    assert {case: value["status"] for case, value in p1["cases"].items()} == {
        f"L{index:02d}": "PASS" for index in range(1, 9)
    }
    assert closure["governed_commits"]["D4"] == "28de4ccd6e873f95458be39834e96247d05b53ad"
    assert closure["governed_commits"]["D5"]["status"] == "materialized_by_the_commit_containing_this_closure_ledger"
    assert closure["controlled_live_identity_authority"]["type"] == "acceptance-local qualified Security Master subset"
    assert closure["controlled_live_identity_authority"]["official_security_master_acquisition_bootstrap_proven"] is False


def test_phase_g_closure_remains_historical_while_current_authority_is_v3():
    closure = _load(CLOSURE)
    historical = closure["current_authority"]
    described = describe_capabilities()

    # Phase G closure is immutable evidence of the authority that existed when
    # that gate closed. H-ACT-V3 must not rewrite it.
    assert historical["local_service"] == LOCAL_SERVICE_CONTRACT_VERSION == "unified_market_evidence_local_service.v2"
    assert historical["mcp_adapter"] == ADAPTER_VERSION == "unified_market_evidence_mcp_adapter.v2"
    assert historical["preferred_request"] == "unified_market_evidence_request.v2"
    assert historical["accepted_requests"] == [
        "unified_market_evidence_request.v1",
        "unified_market_evidence_request.v2",
    ]
    assert historical["emitted_result"] == "unified_market_evidence_result.v2"

    # Current product authority advances independently through H-ACT-V3.
    assert described["preferred_request_schema_version"] == "unified_market_evidence_request.v3"
    assert described["accepted_request_schema_versions"] == [
        "unified_market_evidence_request.v1",
        "unified_market_evidence_request.v2",
        "unified_market_evidence_request.v3",
    ]
    assert described["emitted_result_schema_version"] == "unified_market_evidence_result.v3"
    assert [tool.name for tool in build_tool_specs()] == [
        "market_describe_capabilities",
        "market_validate_request",
        "market_preview_request",
        "market_read_result",
        "market_export_ai_handoff",
        "market_fetch_evidence",
    ]


def test_phase_g_closure_has_no_forbidden_runtime_expansion():
    closure = _load(CLOSURE)
    gates = closure["closure_gates"]
    for key in (
        "unauthorized_persistence",
        "scheduler",
        "polling",
        "background_refresh",
        "research_warehouse",
    ):
        assert gates[key] == "NONE"
    assert closure["network"] == {
        "controlled_live_only": True,
        "full_market_payload_persisted": False,
        "deterministic_tests_require_network": False,
    }
    combined = "\n".join(
        (ROOT / path).read_text(encoding="utf-8").casefold()
        for path in ("README.md", "README.zh-TW.md", "docs/agent_usage_guide.md")
    )
    for forbidden_claim in (
        "arbitrary historical disclosure lookup",
        "full historical fundamentals",
        "realtime disclosures are supported",
        "financial_summary is executable",
        "autonomous trading",
    ):
        assert forbidden_claim not in combined


def test_phase_g_v1_frozen_schemas_and_historical_golden_remain_intact():
    expected = {
        "unified_market_evidence_request.v1.schema.json": "b38c8c3adbeaf494bcf8aa489f7e3bd18cb31f91",
        "unified_market_evidence_result.v1.schema.json": "feaba1cfc9e7913bb262447a7c011e0ff0e33b52",
        "unified_market_evidence_audit_package.v1.schema.json": "38fc23480307e51fe9215ba55ce57dfba243bb5f",
    }
    for name, blob_id in expected.items():
        actual = subprocess.check_output(
            ["git", "rev-parse", f"HEAD:schemas/{name}"], cwd=ROOT, text=True
        ).strip()
        assert actual == blob_id
    golden = ROOT / "tests/fixtures/phase_g_pr_c/v1_mode_c_golden"
    for line in (golden / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", 1)
        assert _sha256(golden / relative) == digest

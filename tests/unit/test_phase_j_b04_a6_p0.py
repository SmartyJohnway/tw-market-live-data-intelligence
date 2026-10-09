from __future__ import annotations

from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

from scripts.phase_j_b04_a6_integrated_acceptance import (
    H2_EXECUTOR,
    H3_EXECUTOR,
    architecture_inventory,
    run_preflight,
)
from scripts.m8r_08g_identity_service import TaiwanMarketIdentityService


ROOT = Path(__file__).resolve().parents[2]


def _record(*, code: str = "2330", market: str = "TWSE", family: str = "company_share", kind: str = "common_share", eligibility: str = "allowed"):
    return {
        "listing_id": "TWSE:2330",
        "identity": {"security_code": code, "isin": "TW0002330008", "security_name_zh": "fixture-for-test-only"},
        "classification": {"market": market, "instrument_family": family, "instrument_type": kind},
        "execution_eligibility": {"status": eligibility, "reason_codes": [] if eligibility == "allowed" else ["fixture_block"]},
        "lifecycle": {"as_of": "2026-10-09", "events": []},
    }


def _runtime(record=None):
    service = TaiwanMarketIdentityService([record or _record()], release_id="test-release", manifest_hash="a" * 64)
    return SimpleNamespace(identity_service=service, manifest={"index_sha256": "b" * 64})


class _Unavailable(Exception):
    def __init__(self, reason):
        self.reason_code = reason


def test_clean_install_fails_closed_without_descriptor_or_execution():
    calls = {"H3": 0, "H2": 0, "bootstrap": 0}

    def loader():
        raise _Unavailable("NOT_INITIALIZED")

    result = run_preflight(loader)
    assert result["disposition"] == "J_B04_A6_P0_BLOCKED_SECURITY_MASTER_NOT_INITIALIZED"
    assert result["production_identity_verified"] is False
    assert result["identity_resolution"]["result"] == "not_attempted"
    assert result["execution_attempted"] is False
    assert calls == {"H3": 0, "H2": 0, "bootstrap": 0}


def test_active_qualified_exact_target_passes_identity_gate():
    result = run_preflight(lambda: _runtime())
    assert result["disposition"] == "J_B04_A6_P0_READY_FOR_EXACT_HEAD_INDEPENDENT_REVIEW"
    assert result["identity_resolution"]["resolution_status"] == "resolved"
    assert result["identity_resolution"]["resolution_reason"] == "exact_listing_id"
    assert result["identity_resolution"]["target_binding"] == {
        "canonical_target_id": "TWSE:2330", "market": "TWSE", "security_code": "2330",
        "isin": "TW0002330008", "instrument_family": "company_share", "instrument_type": "common_share",
        "execution_eligibility": "allowed",
    }
    assert result["production_identity_verified"] is True


def test_invalid_security_master_fails_closed():
    result = run_preflight(lambda: (_ for _ in ()).throw(_Unavailable("release_manifest_hash_mismatch")))
    assert result["disposition"] == "J_B04_A6_P0_BLOCKED_SECURITY_MASTER_INVALID"
    assert result["execution_attempted"] is False
    assert result["security_master_private_reason_code"] == "release_manifest_hash_mismatch"


def test_wrong_market_code_classification_or_eligibility_blocks():
    for record in (
        _record(code="2317"),
        _record(market="TPEX"),
        _record(family="etf"),
        _record(kind="preferred_share"),
        _record(eligibility="blocked"),
    ):
        result = run_preflight(lambda record=record: _runtime(record))
        assert result["disposition"] == "J_B04_A6_P0_BLOCKED_IDENTITY_RESOLUTION"
        assert result["production_identity_verified"] is False


def test_unresolved_or_ambiguous_identity_blocks():
    runtime = _runtime()

    class Ambiguous:
        release_id = "test-release"
        manifest_hash = "a" * 64

        def resolve(self, *_args, **_kwargs):
            return SimpleNamespace(status="ambiguous", selected=None, reason_codes=["multiple_candidates"])

    result = run_preflight(lambda: SimpleNamespace(identity_service=Ambiguous(), manifest={"index_sha256": "b" * 64}))
    assert result["disposition"] == "J_B04_A6_P0_BLOCKED_IDENTITY_RESOLUTION"
    assert result["identity_resolution"]["resolution_status"] == "ambiguous"
    assert runtime.identity_service.resolve("TWSE:2330", market_hint="TWSE").status == "resolved"


def test_integrated_inventory_order_limits_and_safety_boundary():
    inventory = architecture_inventory()
    assert inventory["execution_order"] == ["identity", "H3", "H2", "H4", "Result V3", "Audit V3", "handoff"]
    chain = inventory["integrated_chain"]
    assert [item["stage"] for item in chain][0] == "canonical_identity"
    assert H3_EXECUTOR in repr(inventory)
    assert H2_EXECUTOR in repr(inventory)
    assert inventory["activation_boundary"]["H2_runtime"] == "INACTIVE"
    assert inventory["activation_boundary"]["selected_executor_id"] is None
    assert inventory["future_bounded_live_contract"]["max_official_get_dispatches_per_session"] <= 10
    assert inventory["future_bounded_live_contract"]["designed_not_authorized"] is True
    assert inventory["audit_v3"]["schema_change_required"] is False
    assert "actual HTTP dispatch counts" in inventory["audit_v3"]["gap"]
    assert len(inventory["handoff_coverage_matrix"]) == 9
    assert inventory["no_trading_boundary"]


def test_mcp_surface_is_exactly_six():
    from server.unified_mcp.tool_contracts import build_tool_specs

    assert tuple(tool.name for tool in build_tool_specs()) == (
        "market_describe_capabilities", "market_validate_request", "market_preview_request",
        "market_read_result", "market_export_ai_handoff", "market_fetch_evidence",
    )


def test_existing_integrated_h4_partial_guard_projects_through_result_audit_and_handoff(tmp_path, monkeypatch):
    """Reuse the already-governed A3 end-to-end fixture; do not fork its path."""
    from tests.unit.test_phase_j_b04_a3_end_to_end_projection import (
        test_network_free_production_chain_projects_verified_h4_to_result_audit_and_handoff,
    )

    (tmp_path / "existing-a3-e2e").mkdir()
    test_network_free_production_chain_projects_verified_h4_to_result_audit_and_handoff(
        tmp_path / "existing-a3-e2e", monkeypatch, None,
    )


def test_actual_cloud_preflight_cli_reports_not_initialized_and_zero_network():
    completed = subprocess.run(
        [sys.executable, "scripts/phase_j_b04_a6_integrated_acceptance.py", "--preflight"],
        cwd=ROOT, text=True, capture_output=True, check=True,
    )
    import json

    result = json.loads(completed.stdout)
    assert result["disposition"] == "J_B04_A6_P0_BLOCKED_SECURITY_MASTER_NOT_INITIALIZED"
    assert result["network_counts"] == {
        "market_GET": 0, "market_HEAD": 0, "market_POST": 0, "Security_Master_live_acquisition": 0,
    }
    assert result["execution_attempted"] is False

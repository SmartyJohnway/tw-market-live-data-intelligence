"""Validate A5 preflight and canonical dormancy without contacting sources."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
STARTING_MAIN = "6daf6e2dcc6fd34e00e7e3831c25e98bb4d2399a"
RECORD = ROOT / "docs/governance/phase_j/PHASE_J_J_B04_A5_BOUNDED_LIVE_PREFLIGHT_2026-10-09.json"


def _strict_json(path: Path) -> dict[str, Any]:
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise AssertionError(f"duplicate_json_key:{key}")
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs)


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def validate_contract(record: dict[str, Any]) -> dict[str, Any]:
    assert record["gate"] == "J-B04-A5"
    assert record["starting_main"] == STARTING_MAIN
    assert record["identity_resolution"]["target"] == "TWSE:2330"
    assert record["canonical_identity_authority"] == "installation_local_security_master_release"
    assert record["identity_resolution"]["authority"] == "installation-local Taiwan Market Identity Service"
    assert "m8r_06_mode_a_security_master_pointer.json" not in record["identity_resolution"]["authority"]
    assert record["legacy_candidate_fallback"] is False
    assert record["identity_resolution"]["legacy_candidate_fallback"] is False
    assert record["identity_resolution"]["fixture_identity_fallback"] is False
    assert record["identity_resolution"]["company_name_fallback"] is False
    assert record["identity_resolution"]["live_security_master_bootstrap_performed"] is False
    assert record["live_security_master_bootstrap_performed"] is False
    assert record["TW_MARKET_SECURITY_MASTER_ROOT_selected"] is record["identity_resolution"]["TW_MARKET_SECURITY_MASTER_ROOT_selected"]
    assert record["source_call_plan"] == {
        "endpoint": "https://openapi.twse.com.tw/v1/exchangeReport/TWT48U_ALL", "method": "GET",
        "logical_get_maximum": 1, "http_dispatch_maximum": 1, "retry": 0,
        "redirect_policy": "reject", "timeout_seconds_maximum": 15,
        "response_ceiling_bytes": 4 * 1024 * 1024, "target": "TWSE:2330", "H3_live_GETs": 0,
        "TPEx_GETs": 0, "TWT49U_GETs": 0, "browser_fallback": "prohibited", "raw_payload_persistence": "NONE"}
    overlay = record["authority_overlay"]
    assert (overlay["source"], overlay["source_contract"], overlay["executor"], overlay["production_activation"]) == (
        "H2-TWSE-EXRIGHT-PRE-OPENAPI", "TWT48U_ALL", "phase_h_h2_twse_exright_pre_executor", "NOT_AUTHORIZED")
    assert overlay["single_use"] is True and overlay["owner_live_authorization"] == "NOT PRESENT"
    assert record["preflight_status"] != "J_B04_A5_PREFLIGHT_BLOCKED_CANONICAL_SECURITY_MASTER_NOT_INITIALIZED" or record["live_authorization"] == "NOT REQUESTED; P0 blocked"
    identity = record["identity_resolution"]
    if record["preflight_status"] == "J_B04_A5_P0_R1_READY_FOR_INDEPENDENT_REVIEW":
        assert record["security_master_status"] == "ACTIVE"
        assert identity["result"] == "resolved"
        assert identity["resolution_status"] == "resolved"
        assert identity["resolution_reason"] == "exact_listing_id"
        assert identity["security_master_release_id"]
        assert len(identity["security_master_manifest_hash"]) == 64
        assert len(identity["security_master_release_index_sha256"]) == 64
        binding = identity["target_binding"]
        assert (binding["canonical_target_id"], binding["market"], binding["security_code"],
                binding["instrument_family"], binding["instrument_type"], binding["execution_eligibility"]) == (
                    "TWSE:2330", "TWSE", "2330", "company_share", "common_share", "allowed")
    elif record["preflight_status"] == "J_B04_A5_PREFLIGHT_BLOCKED_CANONICAL_SECURITY_MASTER_NOT_INITIALIZED":
        assert record["security_master_status"] == "NOT_INITIALIZED"
        assert identity["result"] == "not_resolved" and identity["reason_code"] == "NOT_INITIALIZED"
        assert identity["security_master_release_id"] is None
        assert identity["security_master_manifest_hash"] is None
    elif record["preflight_status"] == "J_B04_A5_PREFLIGHT_BLOCKED_CANONICAL_SECURITY_MASTER_INVALID":
        assert record["security_master_status"] == "INVALID"
        assert identity["result"] == "not_resolved" and identity["security_master_release_id"] is None
    elif record["preflight_status"] == "J_B04_A5_PREFLIGHT_BLOCKED_TARGET_IDENTITY_SCOPE_INVALID":
        assert record["security_master_status"] == "TARGET_SCOPE_INVALID"
        assert identity["result"] == "not_resolved" and identity["security_master_release_id"] is None
    else:
        raise AssertionError("unknown_a5_p0_disposition")
    state = record["canonical_state"]
    assert state == {"H2_source_activation_state": "eligible", "H2_source_runtime_executable": False,
        "corporate_action_context_routing": "plan_only", "candidate_executor_ids": ["phase_h_h2_twse_exright_pre_executor"],
        "selected_executor_id": None, "H2_runtime": "INACTIVE", "H3_TWSE": "ACTIVE",
        "H3_TPEX": "BLOCKED / NON-EXECUTABLE", "J-B04": "BLOCKING", "Phase J": "NOT_STARTED", "MCP": 6}
    assert record["network_calls_so_far"] == {"market_GET": 0, "market_HEAD": 0, "market_POST": 0}
    return {"status": "BLOCKED", "reason": record["preflight_status"]}


def validate_repository() -> dict[str, Any]:
    record = _strict_json(RECORD)
    status = validate_contract(record)
    from scripts.phase_j_b04_a5_bounded_live_acceptance import run_p0_preflight
    current = run_p0_preflight()
    assert current["preflight_status"] == record["preflight_status"]
    assert current["canonical_identity_authority"] == record["canonical_identity_authority"]
    assert current["TW_MARKET_SECURITY_MASTER_ROOT_selected"] == record["TW_MARKET_SECURITY_MASTER_ROOT_selected"]
    assert current["security_master_status"] == record["security_master_status"]
    if record["security_master_status"] == "ACTIVE":
        assert current["identity_resolution"]["security_master_release_id"] == record["identity_resolution"]["security_master_release_id"]
        assert current["identity_resolution"]["target_binding"] == record["identity_resolution"]["target_binding"]
    descriptors = _strict_json(ROOT / "config/phase_h_h2_dormant_source_descriptors.json")
    source = next(item for item in descriptors["sources"] if item["source_id"] == "H2-TWSE-EXRIGHT-PRE-OPENAPI")
    assert source["activation_state"] == "eligible" and source["runtime_executable"] is False
    routing = _strict_json(ROOT / "docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json")
    route = next(item for item in routing["routes"] if item["capability_id"] == "corporate_action_context")
    assert route["routing_status"] == "plan_only" and route["runtime_executable"] is False
    assert route["candidate_executor_ids"] == ["phase_h_h2_twse_exright_pre_executor"]
    assert route["selected_executor_id"] is None
    catalog = _strict_json(ROOT / "docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json")
    capability = next(item for item in catalog["data_need_capabilities"] if item["capability_id"] == "corporate_action_context")
    assert capability["runtime_executable"] is False
    from server.unified_mcp.tool_contracts import build_tool_contract_snapshot
    assert len(build_tool_contract_snapshot().tools) == 6
    assert _git("rev-parse", "origin/main") == STARTING_MAIN
    changed = set(_git("diff", "--name-only", STARTING_MAIN, "HEAD").splitlines())
    modified = set(_git("diff", "--name-only").splitlines()) | set(_git("diff", "--cached", "--name-only").splitlines())
    untracked = set(_git("ls-files", "--others", "--exclude-standard").splitlines())
    allowed = {"scripts/phase_j_b04_a5_bounded_live_acceptance.py", "scripts/validate_phase_j_b04_a5_bounded_live_acceptance.py",
        "tests/unit/test_phase_j_b04_a5_runner.py", "docs/governance/phase_j/PHASE_J_J_B04_A5_BOUNDED_LIVE_PREFLIGHT_2026-10-09.json",
        "docs/governance/phase_j/PHASE_J_J_B04_A5_BOUNDED_LIVE_PREFLIGHT_2026-10-09.md"}
    assert not (changed | modified | untracked) - allowed
    for frozen in ("server/services/phase_h_discontinuity_safety.py", "schemas/corporate_action_context_evidence.v1.schema.json",
        "schemas/recent_performance_evidence.v1.schema.json", "schemas/discontinuity_safety_evidence.v1.schema.json",
        "schemas/unified_market_evidence_result.v3.schema.json", "schemas/unified_market_evidence_audit_package.v3.schema.json"):
        assert _git("diff", "--quiet", STARTING_MAIN, "HEAD", "--", frozen) == ""
    runs = ROOT / "docs/governance/phase_j/acceptance_runs"
    if runs.exists():
        assert not any(path.is_file() for path in runs.rglob("*")), "unexpected A5 run artifact in P0"
    for path in ROOT.rglob("*.pyc"):
        assert path.parent.name != "acceptance_runs", "raw payload cache not permitted in acceptance run"
    return status | {"canonical_h2_runtime": "INACTIVE", "selected_executor_id": None, "mcp_tool_count": 6,
        "market_GET_HEAD_POST": "0/0/0", "raw_body_absence_verified": True}


if __name__ == "__main__":
    print(json.dumps(validate_repository(), indent=2, sort_keys=True))

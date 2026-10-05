"""Fail-closed, zero-network A4 technical activation/rollback validator."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.phase_i_i2_a4_proof import (
    AUTHORITY, BASELINE, CATALOG, ROUTING, SOURCE, EXECUTOR, current_json,
    historical_dormant_authority, production_preview, rollback_authority,
    run_production_offline_proof, verify_a3_hashes, verify_candidate_authority,
)

LEDGER = "docs/governance/phase_i/PHASE_I_I2_A4_PRODUCTION_ROUTE_ACTIVATION_CANDIDATE_2026-10-01.json"


def validate(*, require_record=True):
    def deny(*args, **kwargs):
        raise AssertionError("external market network forbidden in A4 validator")
    with patch("socket.socket.connect", deny), patch("socket.create_connection", deny):
        verify_candidate_authority()
        import ast
        for name in ("phase_i_i2_production_candidate.py", "phase_i_i2_production_transport.py"):
            tree = ast.parse((ROOT / "server/services" / name).read_text(encoding="utf-8"))
            assert not any(isinstance(node, ast.ImportFrom) and "acceptance" in (node.module or "")
                           for node in ast.walk(tree))
        from server.services.phase_i_i2_production_transport import MAX_READ_BYTES, TIMEOUT_SECONDS
        assert (MAX_READ_BYTES, TIMEOUT_SECONDS) == (2097153, 30)
        preserved = verify_a3_hashes()
        a1 = ROOT / "docs/governance/phase_i/PHASE_I_I2_TX_REGULAR_SESSION_SOURCE_EVIDENCE_CONTRACT_2026-09-30_FROZEN.json"
        assert hashlib.sha256(a1.read_bytes()).hexdigest() == "6d535e34defb1e82947f64ceec6df5e1859888fb3550e36e6ded1b6a7573d4fb"
        rolled, registry = rollback_authority()
        with historical_dormant_authority():
            _, _, _, preview = production_preview()
            plan = preview["orchestration_plan"]
            assert plan["accounting"]["network_request_estimate"] == 0
            assert all(x["operation_status"] == "plan_only_not_executable" and x["executor_id"] is None for x in plan["operations"])
        from scripts.run_phase_i_i2_a3_bounded_live_acceptance import deterministic_fixture_payload
        with tempfile.TemporaryDirectory(prefix="i2-a4-proof-") as temp:
            proof = run_production_offline_proof(Path(temp) / "production", deterministic_fixture_payload())
        assert proof["fake_acquisitions"] == 1 and proof["external_market_calls"] == 0
        assert all(x["status"] == "succeeded" for x in proof["execution"]["dispatch_outcomes"])
    if require_record:
        ledger = current_json(LEDGER)
        assert (ledger["schema_version"], ledger["status"], ledger["owner_authorization_reference"], ledger["baseline_main"]) == (
            "phase_i_i2_production_route_activation_candidate.v1", "TECHNICAL_ACTIVATION_CANDIDATE_READY_FOR_OWNER_REVIEW", AUTHORITY, BASELINE)
        assert ledger["final_owner_activation_acceptance"] == "PENDING" and ledger["merge_authorized"] is False
        assert ledger["market_network_calls"] == 0 and ledger["i3_started"] is False and ledger["phase_j_started"] is False
        candidate = ledger["activation_candidate"]
        assert (candidate["capability_id"], candidate["executor_id"], candidate["supported_markets"], candidate["instrument_families"], candidate["instrument_types"], candidate["evidence_contract"], candidate["normal_production_routes"], candidate["active_i2_sources"], candidate["batching_scope"], candidate["approval_required"], candidate["maximum_unique_taifex_gets"], candidate["retry_count"], candidate["timeout_seconds"], candidate["maximum_response_bytes"], candidate["raw_payload_persistence"], candidate["optional_explicit_loading_only"]) == (
            "index_futures_context", EXECUTOR, ["TWSE"], ["company_share"], ["common_share"], "index_futures_context_evidence.v1", 1, 1, "same_source", True, 1, 0, 30, 2097152, "forbidden", True)
        import subprocess
        reviewed = ledger["implementation_candidate"]
        assert subprocess.check_output(["git", "rev-parse", reviewed["head"] + "^{tree}"], cwd=ROOT, text=True).strip() == reviewed["tree"]
        assert subprocess.run(["git", "merge-base", "--is-ancestor", reviewed["head"], "HEAD"], cwd=ROOT, check=False).returncode == 0
        rollback = ledger["rollback_rehearsal"]
        assert (rollback["gate_id"], rollback["status"], rollback["method"], rollback["rollback_target_commit"]) == (
            "I2-ROLL-001", "PASS", "deterministic in-memory authority rollback", BASELINE)
        assert rollback["expected_after_state"] == {"support_status": "contract_supported", "runtime_executable": False,
            "phase_i_activation_state": "implementation_candidate_inactive", "routing_status": "plan_only", "selected_executor_id": None,
            "active_i2_sources": 0, "normal_production_i2_routes": 0, "source_activation_state": "inactive", "estimated_i2_network_requests": 0,
            "i1_active_sources": 3, "i1_production_routes": 2, "mcp_tool_count": 6}
        assert ledger["preserved_a3_hashes"] == preserved
        assert ledger["normal_production_offline_e2e"]["status"] == "PASS"
        assert ledger["normal_production_offline_e2e"]["result_v3_schema"] == "PASS"
        assert ledger["normal_production_offline_e2e"]["audit_v3_schema"] == "PASS"
        assert ledger["normal_production_offline_e2e"]["result_replay"] == "PASS"
        assert ledger["normal_production_offline_e2e"]["audit_replay"] == "PASS"
        for key, path in (("catalog", CATALOG), ("routing", ROUTING), ("source", SOURCE)):
            # The I2 ledger pins its historical candidate snapshot. Current
            # Catalog/Route may now carry the separately authorized dormant I3
            # candidate, so verify provenance against the pinned Git commit and
            # verify live I2 semantics independently above.
            pinned = subprocess.check_output(["git", "show", f"{reviewed['head']}:{path}"], cwd=ROOT)
            assert ledger["candidate_authority_sha256"][key] == hashlib.sha256(pinned).hexdigest()
    print("Phase I I2-A4 technical activation: PASS (normal-production offline E2E; exact dormant rollback; market network=0; final Owner acceptance pending)")
    return proof


if __name__ == "__main__":
    validate()

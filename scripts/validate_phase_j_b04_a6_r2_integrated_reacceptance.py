#!/usr/bin/env python3
"""Network-free exact-evidence validator for the J-B04-A6-R2 re-acceptance."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SESSION_ROOT = Path(os.environ.get("A6_SESSION_ROOT", "/tmp/j-b04-a6-r2"))
RECORD = ROOT / "docs/governance/phase_j/PHASE_J_J_B04_A6_R2_TRANSPORT_LEDGER_VALIDATOR_REPAIR_AND_LIVE_REACCEPTANCE_2026-10-10.json"
OLD_A6 = ROOT / "docs/governance/phase_j/PHASE_J_J_B04_A6_INTEGRATED_MARKET_RESEARCH_INTERPRETATION_LIVE_ACCEPTANCE_2026-10-10.json"
OLD_A6_MD = OLD_A6.with_suffix(".md")
R1 = ROOT / "docs/governance/phase_j/PHASE_J_J_B04_A6_R1_H3_STOCK_DAY_CLOSE_NUMERIC_CONTRACT_REPAIR_2026-10-10.json"
R1_MD = R1.with_suffix(".md")


def strict_text(text: str):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"duplicate_json_key:{key}")
            result[key] = value
        return result
    return json.loads(text, object_pairs_hook=pairs)


def strict(path: Path):
    return strict_text(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate() -> dict:
    sys.path.insert(0, str(ROOT))
    from scripts.validate_phase_j_b04_a6_integrated_acceptance import validate_transport_events

    record = strict(RECORD)
    authorization = strict(SESSION_ROOT / "owner-authorization.json")
    session = strict(SESSION_ROOT / "session.json")
    output_path = SESSION_ROOT / "acceptance-result.json"
    output = strict(output_path)
    ledger_path = SESSION_ROOT / "transport-ledger.jsonl"
    ledger = [strict_text(line) for line in ledger_path.read_text(encoding="utf-8").splitlines()]

    assert record["terminal_disposition"] == "J_B04_A6_R2_INTEGRATED_LIVE_REACCEPTANCE_PASS"
    assert record["authority"]["starting_head"] == "8a56fcd3204fa852a7444363485bfc8af264e74c"
    assert record["authority"]["starting_tree"] == "c3e245b8a31a600e45c3552cd90a778baff6288e"
    assert record["authority"]["owner_authorization_sha256"] == "a78b43ae8d251c96604820ac0e3f985eb5b92ea23d9020880ea0425cb8369252"
    assert record["authority"]["implementation_commit"] == "0f610dca09c34e101d8d7eb70755b0c0e0a7525d"
    assert hashlib.sha256(authorization["statement"].encode("utf-8")).hexdigest() == record["authority"]["owner_authorization_sha256"]
    assert record["stage_2"]["attempt_count"] == session["attempt_count"] == 1
    assert record["stage_2"]["network_frozen"] is True and session["network_enabled"] is False
    assert record["network"]["security_master_acquisition"] == 0
    assert record["network"]["trading_order_broker_recommendation"] == 0
    assert record["network"]["stage_1_market_source_get_head_post"] == {"GET": 0, "HEAD": 0, "POST": 0}
    assert record["network"]["stage_2_market_source_get_head_post"] == {"GET": 3, "HEAD": 0, "POST": 0}
    assert session["owner_authorization_sha256"] == record["authority"]["owner_authorization_sha256"]
    assert session["active_release_id"] == "security-master-20261010T112837Z"
    assert session["active_manifest_sha256"] == "e23d5a60053aec9733764adc49908b3a238d2108cd70ac6e3965d99a1e2a26bc"
    assert session["active_h2_executor"] == "phase_h_h2_twse_exright_pre_executor"
    assert session["active_h3_executor"] == "phase_h_h3_twse_recent_performance_executor"
    assert session["mcp_tool_count"] == 6
    validate_transport_events(ledger, expected_dispatches=3)
    assert session["actual_dispatches"] == 3
    assert session["attempt_h3"] == {"1": 2} and session["attempt_h2"] == {"1": 1}
    assert sha(output_path) == session["terminal_output_sha256"]
    assert sha(ledger_path) == record["stage_2"]["transport"]["ledger_sha256"]
    assert sha(output_path) == record["local_evidence"]["acceptance_result"]["sha256"]

    fetch = output["fetch"]
    result = fetch["canonical_result"]
    audit = output["audit"]
    from jsonschema import Draft202012Validator
    result_schema = strict(ROOT / "schemas/unified_market_evidence_result.v3.schema.json")
    audit_schema = strict(ROOT / "schemas/unified_market_evidence_audit_package.v3.schema.json")
    assert not list(Draft202012Validator(result_schema).iter_errors(result))
    assert not list(Draft202012Validator(audit_schema).iter_errors(audit))
    assert result["result_hash"] == record["stage_2"]["result_v3"]["result_hash"]
    assert audit["audit_package_hash"] == record["stage_2"]["audit_v3"]["package_hash"]
    assert audit["integrity_verification"]["all_artifact_hashes_verified"] is True
    assert audit["integrity_verification"]["receipt_hash_verified"] is True
    assert output["fetch"]["control_package_id"] == record["stage_2"]["audit_v3"]["control_package_id"]
    assert audit["authorization_identity"]["authorization_id"] == record["stage_2"]["audit_v3"]["authorization_id"]
    assert audit["claim_identity"]["claim_id"] == record["stage_2"]["audit_v3"]["claim_id"]
    assert audit["receipt_identity"]["execution_receipt_id"] == record["stage_2"]["audit_v3"]["receipt_id"]
    assert [x["operation_id"] for x in audit["operation_lineage"]] == record["stage_2"]["audit_v3"]["operation_ids"]

    evidence = result["targets"][0]["evidence"]
    identity = result["targets"][0]["canonical_identity"]
    assert identity["canonical_target_id"] == "TWSE:2330"
    assert identity["market"] == "TWSE" and identity["security_code"] == "2330"
    assert identity["instrument_family"] == "company_share" and identity["instrument_type"] == "common_share"
    h3, h2, h4 = evidence["recent_performance"], evidence["corporate_action_context"], evidence["discontinuity_safety"]
    assert h3["coverage_status"] == "complete" and h3["valid_observation_count"] == 20
    assert h2["coverage"]["retrieval_succeeded"] is True
    assert h2["coverage"]["source_contract_validated"] is True
    assert h2["coverage"]["exact_target_search_succeeded"] is True
    assert h2["events"] == []
    assert h4["state"] == "coverage_incomplete"
    assert h4["ordinary_return_interpretation"] == "blocked"
    assert h4["interpretation_guard"] == "CORPORATE_ACTION_COVERAGE_INCOMPLETE"

    assert fetch["execution_outcome"] == "succeeded"
    assert output["package"]["result_status"] == "full_success"
    assert output["handoff"]["execution_outcome"] == "succeeded"
    assert output["workbench_package"]["result_status"] == "full_success"
    assert "CORPORATE_ACTION_COVERAGE_INCOMPLETE" in fetch["ai_ready_markdown"]
    assert fetch["additional_market_network_executed"] is False
    assert output["handoff"]["additional_market_network_executed"] is False
    assert output["package"]["external_market_network_executed"] is False
    assert output["workbench_package"]["external_market_network_executed"] is False

    for item in record["local_evidence"]["artifacts"].values():
        path = ROOT / item["path"]
        assert sha(path) == item["sha256"], f"artifact_hash_mismatch:{item['path']}"
    assert sha(SESSION_ROOT / "preflight.json") == record["stage_2"]["preflight"]["sha256"]

    immutable = {
        OLD_A6: "1e3382bedc876fa0578ff0716c1e42a0d2a11209d2eef26e5f5d13e513571aba",
        OLD_A6_MD: "f9b0ded99236246fc00ab45183a7c2d71a3d08f576a97aac4fad5bc29b571d5f",
        R1: "bee0953ee6a18bce65ff12f3e23d2b86e75c242f86dab3ee97717277e3fc87e0",
        R1_MD: "af769f61de18f8280e535a1273e5b5dcf109b03758eda8498fcc7941f300994f",
    }
    assert all(sha(path) == expected for path, expected in immutable.items())

    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    implementation = record["authority"]["implementation_commit"]
    if head != implementation:
        parents = subprocess.check_output(["git", "rev-list", "--parents", "-n", "1", head], cwd=ROOT, text=True).split()
        subject = subprocess.check_output(["git", "show", "-s", "--format=%s", head], cwd=ROOT, text=True).strip()
        changed = set(subprocess.check_output(["git", "diff-tree", "--no-commit-id", "--name-only", "-r", head], cwd=ROOT, text=True).splitlines())
        expected_evidence = {
            "docs/governance/phase_j/PHASE_J_J_B04_A6_R2_TRANSPORT_LEDGER_VALIDATOR_REPAIR_AND_LIVE_REACCEPTANCE_2026-10-10.json",
            "docs/governance/phase_j/PHASE_J_J_B04_A6_R2_TRANSPORT_LEDGER_VALIDATOR_REPAIR_AND_LIVE_REACCEPTANCE_2026-10-10.md",
            "scripts/validate_phase_j_b04_a6_r2_integrated_reacceptance.py",
        }
        assert parents == [head, implementation]
        assert subject == "evidence(a6): record R2 integrated live re-acceptance"
        assert changed == expected_evidence
    status = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT, text=True)
    if head == implementation:
        staged_paths = {line[3:] for line in status.splitlines() if line[:2] == "A "}
        assert staged_paths == {
            "docs/governance/phase_j/PHASE_J_J_B04_A6_R2_TRANSPORT_LEDGER_VALIDATOR_REPAIR_AND_LIVE_REACCEPTANCE_2026-10-10.json",
            "docs/governance/phase_j/PHASE_J_J_B04_A6_R2_TRANSPORT_LEDGER_VALIDATOR_REPAIR_AND_LIVE_REACCEPTANCE_2026-10-10.md",
            "scripts/validate_phase_j_b04_a6_r2_integrated_reacceptance.py",
        }
    else:
        assert status == ""
    print("J-B04-A6-R2 terminal evidence validation: PASS (network-free)")
    return {"status": "PASS", "attempts": 1, "dispatches": 3,
            "reservations": 3, "completions": 3, "network_after_session": False}


if __name__ == "__main__":
    try:
        print(json.dumps(validate(), sort_keys=True, indent=2))
    except Exception as exc:
        print(f"J-B04-A6-R2 terminal evidence validation: FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)

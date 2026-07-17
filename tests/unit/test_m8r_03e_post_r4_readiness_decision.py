import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DECISION_PATH = ROOT / "docs/acceptance_runs/M8R_03E_POST_R4_PHASE_C_READINESS_DECISION.json"
CONTRACT_PATH = ROOT / "docs/ai/m8_ai_capability_contract.json"

def load_json(p):
    return json.loads(p.read_text(encoding="utf-8"))

def test_sha_semantics():
    dec = load_json(DECISION_PATH)
    assert dec["baseline_main_sha"] == "9861a90424f3589e12491b876d14e2c37db51f70"
    assert dec["tested_parent_sha"] == "0cd81632be83b3f7969da043c7f1510eeeddda00"
    assert dec["tested_tree_sha"] is None
    assert dec["tested_worktree_digest"] is None
    assert dec["binding_status"] == "unsealed_precommit_evidence"

    eb = dec["evidence_binding"]
    assert eb["status"] == "unsealed_precommit_evidence"
    assert eb["baseline_main_sha"] == "9861a90424f3589e12491b876d14e2c37db51f70"
    assert eb["tested_parent_sha"] == "0cd81632be83b3f7969da043c7f1510eeeddda00"
    assert eb["tested_tree_sha"] is None
    assert eb["tested_commit_sha"] is None

def test_assignment_coverage():
    dec = load_json(DECISION_PATH)
    failing_nodes = dec["full_non_network_exact_result"]["failing_node_ids"]
    assert len(failing_nodes) == 48

    groups = dec["full_non_network_failure_classification"]
    assigned_nodes = []
    for cat, nodes in groups.items():
        if cat in ["test_harness_side_effect", "new_regression", "r5a_10_target_dependency", "unknown_unclassified", "known_historical_failure", "environment_or_dependency", "windows_path_semantics", "artifact_or_fixture_drift", "stale_governance_expectation"]:
            assigned_nodes.extend(nodes)

    assert len(assigned_nodes) == 48
    assert len(set(assigned_nodes)) == 48
    assert set(assigned_nodes) == set(failing_nodes)

def test_assignment_versus_confirmation():
    dec = load_json(DECISION_PATH)
    assert dec["full_non_network_failure_assignment_status"] == "complete"
    assert dec["full_non_network_root_cause_confirmation_status"] == "partial"
    assert dec["full_non_network_regression_determination_status"] == "not_demonstrated_on_equivalent_cross_platform_baseline"
    assert dec["new_regression"] is None
    assert dec["new_regression_count"] is None
    assert dec["new_regression_status"] == "not_demonstrated_due_to_platform_specific_failure_expansion"

    pac = dec["provisional_assignment_counts"]
    assert pac["total"] == 48
    assert "new_regression_assignment_count_note" in pac

def test_root_cause_group_references():
    dec = load_json(DECISION_PATH)
    groups = dec["root_cause_groups"]
    assert "WINDOWS-PYTHONPATH-01" in groups
    assert "WINDOWS-PATH-SEMANTICS-01" in groups
    assert "CRLF-HASH-DRIFT-01" in groups
    assert "STALE-GOVERNANCE-01" in groups

    for item in dec["full_non_network_failures_auditable"]:
        ref = item.get("root_cause_group_id")
        assert ref in groups, f"Node {item['node_id']} references non-existent group {ref}"

def test_network_summary():
    dec = load_json(DECISION_PATH)
    pre = dec["controlled_network_preflight"]
    assert pre["overall_status"] == "partial_market_value_verification"
    assert pre["source_status_counts"]["actual_market_values_verified"] == 4
    assert pre["source_status_counts"]["contract_record_and_timestamp_verified"] == 1
    assert pre["source_status_counts"]["failed"] == 0

    taifex_mis = pre["sources"]["TAIFEX_MIS"]
    assert taifex_mis["status"] == "contract_record_and_timestamp_verified"
    assert taifex_mis.get("sample_market_values") is None
    assert taifex_mis["price_retrieval_status"] == "actual_quote_value_unavailable_after_session"

def test_successor_and_phase_c_gates():
    dec = load_json(DECISION_PATH)
    assert dec["recommended_next_task"] == "M8R-03E-R5A-PHASE-C-ENABLING-CROSS-LAYER-FIXTURE-INFRASTRUCTURE"
    assert dec["parallel_authorized_workstream"] == "M8R-03E-R5B-WINDOWS-FILESYSTEM-FAIL-CLOSED-CORRECTION"

    contract = load_json(CONTRACT_PATH)
    pd = contract["phase_dependencies"]
    assert pd["Phase C"] == "implementation_ready_activation_blocked"
    assert pd["Phase C implementation"] == "ready_after_post_R4_readiness_decision"
    assert pd["Phase C activation"] == "blocked_pending_R5A_10_target_fixture_and_windows_path_validation_correction"

def test_protocol_passed_metrics():
    protocol_path = ROOT / "docs/protocol/M8R_03E_POST_R4_PHASE_C_READINESS_AND_R5_SEQUENCING_DECISION.md"
    text = protocol_path.read_text(encoding="utf-8")
    assert "Passed**: 1,665" in text

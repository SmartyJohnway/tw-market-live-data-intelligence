import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NEXT = "M8R-03E-F1-AI-CAPABILITY-GUIDE-AND-AGENT-SKILL-CONTRACT"

def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def test_registry_post_m8c_realignment_semantics():
    reg = load("docs/data_capabilities/m8_source_capability_registry.json")
    assert reg["implemented_through_track"] == "M8R-03E"
    assert reg["recommended_next_task"] == NEXT
    assert reg["registry_successor"] == NEXT
    assert reg["original_m8r04_disposition"] == "superseded_and_split"
    assert reg["active_architectural_model"] == "governed_market_evidence_platform"
    assert reg["ai_behavior_hardcoding"] == "deprecated_direction"
    assert reg["agent_skill_contract"] == "required_successor_capability"
    assert reg["unified_tool_api"] == "required_successor_capability"
    assert reg["m8_active_consolidated_status"]["m8r_03e_status"] == "GO_WITH_CAVEATS"
    assert reg["recommended_next_task"] != "M8R-03D-WATCHLIST-EVIDENCE-SOURCE-INTEGRATION-AND-CONTROLLED-EXECUTION"

def test_health_status_and_debt_register_shapes():
    status = load("docs/data_capabilities/m8_repository_health_status.json")
    required = {"schema_version","task_id","baseline_sha","generated_at_utc","audit_scope","roadmap_alignment_status","implemented_through_track","original_m8r04_disposition","architecture_model","ai_behavior_policy_decoupling_status","correctness_status","security_status","performance_status","testing_status","documentation_status","p0_count","p1_count","p2_count","p3_count","blocking_findings","direct_corrections","recommended_next_task","recommended_next_task_reason","validation_commands","validation_results"}
    assert required <= set(status)
    assert status["implemented_through_track"] == "M8R-03E"
    assert status["recommended_next_task"] == NEXT
    debt = load("docs/quality/m8_technical_debt_register.json")
    entry_required = {"debt_id","category","severity","status","affected_paths","finding","evidence","risk","recommended_action","blocking_phase","target_remediation_task"}
    assert debt["entries"]
    for entry in debt["entries"]:
        assert entry_required <= set(entry)
        assert entry["severity"] in {"P0","P1","P2","P3"}
        assert entry["status"] in {"open","corrected_in_r1","accepted","deferred","requires_operator_decision"}

def test_roadmap_phase_ids_unique_and_complete():
    text = (ROOT / "docs/roadmap/M8_POST_M8C_REVISED_ROADMAP.md").read_text(encoding="utf-8")
    phases = re.findall(r"^## Phase ([A-O]) ", text, flags=re.MULTILINE)
    assert phases == list("ABCDEFGHIJKLMNO")
    assert len(phases) == len(set(phases))

def test_ai_behavior_policy_inventory_dispositions_valid():
    inv = load("docs/quality/m8_ai_behavior_policy_inventory.json")
    valid = set(inv["dispositions"])
    assert inv["items"]
    for item in inv["items"]:
        assert item["recommended_disposition"] in valid
        assert item["breaking_change_risk"] in {"low", "medium", "high"}
    assert "prohibited_inferences" in inv["migration_plan"]["compatibility_sensitive_fields"]

def test_historical_artifacts_remain_discoverable():
    for path in [
        "docs/protocol/M8R_03B_AI_CONVERSATION_INPUT_OUTPUT_DESIGN_REVIEW.md",
        "docs/protocol/M8R_03D_WATCHLIST_EVIDENCE_SOURCE_INTEGRATION_AND_CONTROLLED_EXECUTION.md",
        "docs/protocol/M8R_03E_WATCHLIST_AI_CONTEXT_PACKAGE_AND_CONVERSATION_HANDOFF.md",
    ]:
        assert (ROOT / path).exists()

def test_active_registry_has_no_authoritative_ai_behavior_policy_flags():
    reg = load("docs/data_capabilities/m8_source_capability_registry.json")
    forbidden = {"recommendation_allowed", "trading_signal_allowed", "no_recommendation", "no_trading_advice", "no_trading_signal"}
    active_objects = [reg, reg["m8_active_consolidated_status"], reg["planning_state"], *reg["sources"]]
    for obj in active_objects:
        assert forbidden.isdisjoint(obj)
    assert forbidden.isdisjoint(reg.get("global_ai_interpretation_policy", {}))
    deprecated = reg.get("deprecated_ai_behavior_policy_fields", {})
    assert deprecated


def test_p1_blocking_and_successor_semantics_are_consistent():
    status = load("docs/data_capabilities/m8_repository_health_status.json")
    debt = load("docs/quality/m8_technical_debt_register.json")
    p1 = [entry for entry in debt["entries"] if entry["severity"] == "P1"]
    assert status["p1_count"] == len(p1)
    assert status["recommended_next_task"] == NEXT
    assert all(entry.get("blocking_phase") != "Phase B" for entry in p1)
    phase_c_blockers = [entry for entry in p1 if entry.get("blocking_phase") == "Phase C"]
    assert phase_c_blockers
    assert all("blocking_condition" in entry for entry in phase_c_blockers)


def test_finding_counts_match_debt_register_and_blocking_findings_agree():
    status = load("docs/data_capabilities/m8_repository_health_status.json")
    debt = load("docs/quality/m8_technical_debt_register.json")
    counts = {severity: sum(1 for entry in debt["entries"] if entry["severity"] == severity) for severity in ["P0", "P1", "P2", "P3"]}
    assert status["p0_count"] == counts["P0"]
    assert status["p1_count"] == counts["P1"]
    assert status["p2_count"] == counts["P2"]
    assert status["p3_count"] == counts["P3"]
    declared_blockers = [entry["debt_id"] for entry in debt["entries"] if entry["severity"] == "P0" or entry.get("blocking_phase") == "Phase B"]
    assert status["blocking_findings"] == declared_blockers


def test_ai_policy_inventory_covers_active_m8r03e_compatibility_fields():
    inv = load("docs/quality/m8_ai_behavior_policy_inventory.json")
    fields = set(inv["coverage_assertions"]["compatibility_sensitive_active_m8r03e_fields"])
    assert {"conversation_scope.disallowed_topics", "targets[].allowed_interpretations", "targets[].prohibited_inferences", "prohibitions"} <= fields
    joined = "\n".join(item["path"] + " " + item["symbol_or_json_path"] + " " + item["current_purpose"] for item in inv["items"])
    for token in ["disallowed_topics", "allowed_interpretations", "prohibited_inferences", "prohibitions"]:
        assert token in joined
    ids = [item["item_id"] for item in inv["items"]]
    assert len(ids) == len(set(ids))


def test_performance_baseline_contains_required_scenarios():
    perf = load("docs/quality/m8_performance_baseline.json")
    scenarios = {s["scenario_id"]: s for s in perf["scenarios"]}
    required = {"1_target_snapshot", "10_target_snapshot", "50_target_snapshot", "100_target_snapshot", "high_citation_pressure", "high_missing_evidence_pressure", "snapshot", "performance", "partial_failure"}
    assert required <= set(scenarios)
    for scenario in scenarios.values():
        assert scenario["build_time_ms"] >= 0
        assert scenario["validation_time_ms"] >= 0
        assert scenario["serialized_bytes"] > 0
        assert "growth_ratio_vs_one_target" in scenario
    assert perf["summary"]["all_valid"] is True
    assert perf["measurement_environment"]["network"] is False


def test_full_non_network_status_records_exact_known_failures():
    status = load("docs/data_capabilities/m8_repository_health_status.json")
    evidence = status["full_non_network_evidence"]
    expected = [
        "tests/unit/test_m5d_frontend_publication_preflight.py::test_m5d_request_is_request_only",
        "tests/unit/test_m5d_publication_candidate.py::test_candidate_validates",
        "tests/unit/test_m5d_publication_candidate.py::test_frontend_public_baseline_recomputed_matches_current",
        "tests/unit/test_m5d_publication_candidate.py::test_destination_already_exists_simulation",
        "tests/unit/test_m5d_publication_candidate.py::test_rollback_no_existing_destination_deletes_new_file",
        "tests/unit/test_m5d_publication_candidate.py::test_shallow_checkout_missing_pr57_commit_does_not_block",
        "tests/unit/test_m5e_controlled_frontend_publication.py::test_reproducibility_materialize_candidate",
    ]
    assert evidence["failing_node_ids"] == expected
    assert evidence["baseline_reproduced"] is True
    assert evidence["failure_set_changed_by_pr_149"] is False
    assert evidence["new_m8_m8r_failure_count"] == 0

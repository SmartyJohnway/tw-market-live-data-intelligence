import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IMPLEMENTED_THROUGH_TRACK = "M8R-03E-R3-ARCHITECTURE-AND-CODE-HEALTH-CLEANUP"
RECOMMENDED_NEXT_TASK = "M8R-03E-R5A-PHASE-C-ENABLING-CROSS-LAYER-FIXTURE-INFRASTRUCTURE"

def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def test_registry_post_m8c_realignment_semantics():
    reg = load("docs/data_capabilities/m8_source_capability_registry.json")
    assert reg["implemented_through_track"] == IMPLEMENTED_THROUGH_TRACK
    assert reg["recommended_next_task"] == RECOMMENDED_NEXT_TASK
    assert reg["registry_successor"] == RECOMMENDED_NEXT_TASK
    assert reg["original_m8r04_disposition"] == "superseded_and_split"
    assert reg["active_architectural_model"] == "governed_market_evidence_platform"
    assert reg["ai_behavior_hardcoding"] == "deprecated_direction"
    assert reg["agent_skill_contract"] == "implemented"
    assert reg["unified_tool_api"] == "required_successor_capability"
    assert reg["m8_active_consolidated_status"]["m8r_03e_status"] == "GO_WITH_CAVEATS"
    assert reg["recommended_next_task"] != "M8R-03D-WATCHLIST-EVIDENCE-SOURCE-INTEGRATION-AND-CONTROLLED-EXECUTION"

def test_health_status_and_debt_register_shapes():
    status = load("docs/data_capabilities/m8_repository_health_status.json")
    required = {"schema_version","task_id","baseline_sha","generated_at_utc","audit_scope","roadmap_alignment_status","implemented_through_track","original_m8r04_disposition","architecture_model","ai_behavior_policy_decoupling_status","correctness_status","security_status","performance_status","testing_status","documentation_status","p0_count","p1_count","p2_count","p3_count","blocking_findings","direct_corrections","recommended_next_task","recommended_next_task_reason","validation_commands","validation_results"}
    assert required <= set(status)
    assert status["implemented_through_track"] == IMPLEMENTED_THROUGH_TRACK
    assert status["recommended_next_task"] == RECOMMENDED_NEXT_TASK
    final = load("docs/acceptance_runs/M8R_03E_R2_FINAL_VALIDATION.json")
    assert final["r2_f0_disposition"] == "GO_WITH_CAVEATS"
    assert final["r2_disposition"] == "GO_WITH_CAVEATS"
    assert final["combined_pr_disposition"] == "APPROVE_WITH_CAVEATS"
    assert final["recommended_next_task"] == "M8R-03E-R3-ARCHITECTURE-AND-CODE-HEALTH-CLEANUP"
    debt = load("docs/quality/m8_technical_debt_register.json")
    entry_required = {"debt_id","category","severity","status","affected_paths","finding","evidence","risk","recommended_action","blocking_phase","target_remediation_task"}
    assert debt["entries"]
    for entry in debt["entries"]:
        assert entry_required <= set(entry)
        assert entry["severity"] in {"P0","P1","P2","P3"}
        assert entry["status"] in {"open","corrected_in_r1","accepted","deferred","requires_operator_decision","partially_resolved_with_platform_limitations","partially_resolved","corrected_in_r3","resolved_in_r4","partially_resolved_in_r4"}

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
    assert status["recommended_next_task"] == RECOMMENDED_NEXT_TASK
    assert all(entry.get("blocking_phase") != "Phase B" for entry in p1)
    phase_c_blockers = [entry for entry in p1 if entry.get("blocking_phase") == "Phase C" and entry.get("status") not in {"corrected_in_r3", "resolved"}]
    assert not phase_c_blockers


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
    assert evidence["failure_set_changed"] is False
    assert evidence["current_head_failure_set_matches_baseline"] is True
    assert "failure_set_changed_by_pr_149" not in evidence
    assert evidence["new_m8_m8r_failure_count"] == 0


def test_performance_baseline_runner_exists_and_declared():
    runner = ROOT / "scripts/run_m8r_03e_performance_baseline.py"
    assert runner.exists()
    baseline = load("docs/quality/m8_performance_baseline.json")
    assert baseline["generator_script"] == "scripts/run_m8r_03e_performance_baseline.py"
    assert baseline["generator_version"] == "m8r_03e_performance_baseline_runner.v1"
    assert baseline["network_execution_used"] is False


def test_performance_baseline_runner_exercises_actual_m8r03e_functions():
    runner_text = (ROOT / "scripts/run_m8r_03e_performance_baseline.py").read_text(encoding="utf-8")
    for token in [
        "build_watchlist_ai_context_package",
        "validate_watchlist_ai_context_package",
        "build_watchlist_conversation_handoff",
        "build_context_manifest",
    ]:
        assert token in runner_text
    baseline = load("docs/quality/m8_performance_baseline.json")
    for scenario in baseline["scenarios"]:
        exercised = set(scenario["actual_functions_exercised"])
        assert "build_watchlist_ai_context_package" in exercised
        assert "validate_watchlist_ai_context_package" in exercised
        assert "build_watchlist_conversation_handoff" in exercised
        assert "build_context_manifest" in exercised


def test_performance_baseline_verify_mode_succeeds():
    import subprocess
    import sys
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_m8r_03e_performance_baseline.py",
            "--verify-existing",
            "docs/quality/m8_performance_baseline.json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert '"status": "pass"' in result.stdout


def test_hundred_target_workload_mode_is_explicit_and_real_pipeline():
    baseline = load("docs/quality/m8_performance_baseline.json")
    scenarios = {scenario["scenario_id"]: scenario for scenario in baseline["scenarios"]}
    hundred = scenarios["100_target_snapshot"]
    assert hundred["target_count"] == 100
    assert hundred["workload_mode"] == "aggregate_valid_packages_100_targets_schema_safe"
    assert hundred["scenario_construction_method"].startswith("repeat checked-in M8R-03E fixture")
    assert hundred["valid"] is True


def test_performance_runner_peak_memory_optional(monkeypatch):
    import scripts.run_m8r_03e_performance_baseline as runner
    monkeypatch.setattr(runner, "_resource", None)
    memory = runner._peak_memory()
    assert memory == {"status": "unavailable_on_platform", "value_kb": None, "source": None}


def test_performance_runner_generates_without_resource(monkeypatch):
    import scripts.run_m8r_03e_performance_baseline as runner
    monkeypatch.setattr(runner, "_resource", None)
    baseline = runner.build_baseline()
    assert baseline["measurement_environment"]["peak_memory"]["status"] == "unavailable_on_platform"
    assert baseline["summary"]["peak_memory"]["value_kb"] is None
    assert baseline["network_execution_used"] is False
    assert set(baseline["required_scenarios"]) == {s["scenario_id"] for s in baseline["scenarios"]}
    assert all(s["valid"] for s in baseline["scenarios"])


def test_performance_runner_verify_ignores_platform_memory_values(tmp_path):
    import scripts.run_m8r_03e_performance_baseline as runner
    baseline = load("docs/quality/m8_performance_baseline.json")
    baseline["measurement_environment"]["peak_memory"] = {
        "status": "unavailable_on_platform",
        "value_kb": None,
        "source": None,
    }
    baseline["summary"]["peak_memory"] = {
        "status": "unavailable_on_platform",
        "value_kb": None,
        "source": None,
    }
    path = tmp_path / "baseline.json"
    path.write_text(json.dumps(baseline, sort_keys=True), encoding="utf-8")
    ok, issues = runner.verify_existing(path)
    assert ok, issues

from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
R2 = "M8R-03E-R2-CRITICAL-CORRECTNESS-AND-SECURITY-REMEDIATION"
R3 = "M8R-03E-R3-ARCHITECTURE-AND-CODE-HEALTH-CLEANUP"


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_active_r2_r3_status_surfaces_are_consistent():
    health = load("docs/data_capabilities/m8_repository_health_status.json")
    registry = load("docs/data_capabilities/m8_source_capability_registry.json")
    final = load("docs/acceptance_runs/M8R_03E_R2_FINAL_VALIDATION.json")
    roadmap = (ROOT / "docs/roadmap/M8_POST_M8C_REVISED_ROADMAP.md").read_text(encoding="utf-8")

    assert health["implemented_through_track"] == R2
    assert health["recommended_next_task"] == R3
    assert health["registry_successor"] == R3
    assert health["phase_c_status"] == "blocked_pending_M8R-03E-R3-critical-subset"
    assert health["phase_c_gate_status"] == "blocked_pending_R3_critical_subset"

    for active_surface in (registry, registry["m8_active_consolidated_status"], registry["planning_state"]):
        assert active_surface["implemented_through_track"] == R2
        assert active_surface["next_task"] == R3
        assert active_surface["recommended_next_task"] == R3
        assert active_surface["registry_successor"] == R3
    assert registry["phase_c_status"] == "blocked_pending_M8R-03E-R3-critical-subset"
    assert registry["phase_c_gate_status"] == "blocked_pending_R3_critical_subset"

    assert final["r2_f0_disposition"] == "GO_WITH_CAVEATS"
    assert final["r2_disposition"] == "GO_WITH_CAVEATS"
    assert final["combined_pr_disposition"] == "APPROVE_WITH_CAVEATS"
    assert final["recommended_next_task"] == R3
    assert final["phase_c_gate_status"] == "blocked_pending_R3_critical_subset"
    assert R2 in roadmap and R3 in roadmap
    assert "blocked_pending_R3_critical_subset" in roadmap


def test_health_status_and_debt_register_shapes():
    status = load("docs/data_capabilities/m8_repository_health_status.json")
    required = {"schema_version","task_id","baseline_sha","generated_at_utc","audit_scope","roadmap_alignment_status","implemented_through_track","original_m8r04_disposition","architecture_model","ai_behavior_policy_decoupling_status","correctness_status","security_status","performance_status","testing_status","documentation_status","p0_count","p1_count","p2_count","p3_count","blocking_findings","direct_corrections","recommended_next_task","recommended_next_task_reason","validation_commands","validation_results"}
    assert required <= set(status)
    assert status["implemented_through_track"] == R2
    assert status["recommended_next_task"] == R3
    debt = load("docs/quality/m8_technical_debt_register.json")
    entry_required = {"debt_id","category","severity","status","affected_paths","finding","evidence","risk","recommended_action","blocking_phase","target_remediation_task"}
    assert debt["entries"]
    assert all(entry_required <= set(entry) for entry in debt["entries"])


def test_original_m8r04_is_superseded_not_silently_deleted():
    reg = load("docs/data_capabilities/m8_source_capability_registry.json")
    assert reg["original_m8r04_disposition"] == "superseded_and_split"
    deprecated = reg["recommended_successor_after_m8r_03e"]
    assert deprecated["status"] == "historical_superseded"


def test_p1_blocking_and_successor_semantics_are_consistent():
    status = load("docs/data_capabilities/m8_repository_health_status.json")
    debt = load("docs/quality/m8_technical_debt_register.json")
    p1 = [entry for entry in debt["entries"] if entry["severity"] == "P1"]
    assert status["p1_count"] == len(p1)
    assert status["recommended_next_task"] == R3
    assert all(entry.get("blocking_phase") != "Phase B" for entry in p1)
    phase_c_blockers = [entry for entry in p1 if entry.get("blocking_phase") == "Phase C"]
    assert phase_c_blockers

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

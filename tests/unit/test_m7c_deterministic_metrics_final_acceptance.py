import json
from pathlib import Path


def test_m7c_final_acceptance_doc_contains_required_closure_terms():
    text = Path("docs/protocol/M7C_DETERMINISTIC_METRICS_FINAL_ACCEPTANCE.md").read_text(encoding="utf-8")
    required = [
        "Status:\n- pass_with_caveats", "M7C-00", "M7C-01", "M7C-02", "M7C-03", "M7C-04",
        "M7B completed as pass_with_caveats", "raw_rich_facts_exposed=false", "raw_full_ladder_exposed=false",
        "metrics_are_signals=false", "not trading signal", "not recommendation", "M7D-BOUNDED-WATCHLIST-CROSS-CONTEXT",
    ]
    for item in required:
        assert item in text


def test_m7c_inventory_final_closure_metadata():
    inv = json.loads(Path("docs/data_capabilities/twse_mis_rich_field_inventory.json").read_text(encoding="utf-8"))
    m7c = inv["rich_observation_contract"]["m7c_deterministic_metrics"]
    assert m7c["completed_tasks"] == ["M7C-00", "M7C-01", "M7C-02", "M7C-03", "M7C-04"]
    assert m7c["controlled_exposure_enabled"] is True
    assert m7c["runtime_exposure_enabled"] is True
    assert m7c["runtime_populated"] is True
    assert m7c["runtime_behavior_changed"] is True
    assert m7c["conversation_context_changed"] is True
    assert m7c["fastapi_changed"] == "shared_conversation_context_only"
    assert m7c["mcp_changed"] == "shared_conversation_context_only"
    assert m7c["frontend_changed"] is False
    assert m7c["source_health_changed"] is False
    assert m7c["latest_observation_changed"] is False
    assert m7c["safe_for_ai_context"] is True
    assert m7c["builder_output_safe_for_ai_context"] is False
    assert m7c["metrics_are_signals"] is False
    assert m7c["raw_rich_facts_exposed"] is False
    assert m7c["raw_full_ladder_exposed"] is False
    assert m7c["final_acceptance_status"] == "pass_with_caveats"
    assert m7c["next_task"] == "M7D-BOUNDED-WATCHLIST-CROSS-CONTEXT"

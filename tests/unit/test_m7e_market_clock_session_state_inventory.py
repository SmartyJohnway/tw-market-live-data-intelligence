import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_m7e_inventory_entry_policy_schema_and_builder_only():
    inv = json.loads((ROOT / "docs/data_capabilities/twse_mis_rich_field_inventory.json").read_text(encoding="utf-8"))
    m7e = inv["rich_observation_contract"]["m7e_market_clock_session_state"]
    assert m7e["status"] == "policy_schema_and_pure_builder_defined"
    assert m7e["completed_tasks"] == ["M7E-00", "M7E-01"]
    assert m7e["schema_version"] == "m7e_market_clock_session_state.v1"
    assert m7e["runtime_populated"] is False
    assert m7e["runtime_behavior_changed"] is False
    assert m7e["conversation_context_changed"] is False
    assert m7e["fastapi_changed"] is False
    assert m7e["mcp_changed"] is False
    assert m7e["frontend_changed"] is False
    assert m7e["safe_for_ai_context"] is False
    assert m7e["builder_output_safe_for_ai_context"] is False
    assert m7e["controlled_promotion_available"] is False
    assert m7e["market_clock_builder_available"] is True
    assert m7e["holiday_schedule_network_fetch_added"] is False
    assert m7e["holiday_schedule_runtime_fetch_added"] is False
    assert m7e["next_task"] == "M7E-02-M7E-03-CONTROLLED-PROMOTION-AND-SHARED-CONTEXT-INTEGRATION"

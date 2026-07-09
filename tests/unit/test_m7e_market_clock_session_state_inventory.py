import json
from pathlib import Path


def test_m7e_inventory_final_acceptance_closure():
    inv = json.loads(Path("docs/data_capabilities/twse_mis_rich_field_inventory.json").read_text(encoding="utf-8"))
    m7e = inv["rich_observation_contract"]["m7e_market_clock_session_state"]
    assert m7e["completed_tasks"] == ["M7E-00", "M7E-01", "M7E-02", "M7E-03", "M7E-04"]
    assert m7e["safe_for_ai_context"] is True
    assert m7e["builder_output_safe_for_ai_context"] is False
    assert m7e["controlled_promotion_available"] is True
    assert m7e["shared_context_integration_available"] is True
    assert m7e["conversation_context_changed"] is True
    assert m7e["holiday_schedule_network_fetch_added"] is False
    assert m7e["holiday_schedule_runtime_fetch_added"] is False
    assert m7e["final_acceptance_status"] == "pass_with_caveats"
    assert m7e["status"] == "final_acceptance_pass_with_caveats"
    assert m7e["final_acceptance_doc"] == "docs/protocol/M7E_MARKET_CLOCK_SESSION_STATE_FINAL_ACCEPTANCE.md"
    assert m7e["next_task"] == "M7F-FRONTEND-OPERATOR-PRESENTATION-AND-CONTEXT-WORKBENCH"

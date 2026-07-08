import json
from pathlib import Path


def test_m7e_preflight_artifacts_exist_and_point_to_m7e():
    audit = Path("docs/reviews/M7E_PREFLIGHT_REPO_HEALTH_AUDIT.md")
    triage = Path("docs/reviews/JULES_SUGGESTIONS_TRIAGE_20260708.md")
    backlog = Path("docs/reviews/M7E_PREFLIGHT_REMEDIATION_BACKLOG.json")
    assert audit.exists()
    assert triage.exists()
    data = json.loads(backlog.read_text(encoding="utf-8"))
    assert data["schema_version"] == "m7e_preflight_remediation_backlog.v1"
    assert data["next_task"] == "M7E-MARKET-CLOCK-AND-SESSION-STATE"
    assert data["jules_suggestions_total"] == 39
    assert data["m7e_readiness"]["ready_for_m7e"] is True


def test_m7b_m7c_m7d_final_docs_and_inventory_guardrails_remain_intact():
    for path in [
        "docs/protocol/M7B_AI_SAFE_MARKET_CONTEXT_FINAL_ACCEPTANCE.md",
        "docs/protocol/M7C_DETERMINISTIC_METRICS_FINAL_ACCEPTANCE.md",
        "docs/protocol/M7D_BOUNDED_WATCHLIST_CROSS_CONTEXT_FINAL_ACCEPTANCE.md",
    ]:
        text = Path(path).read_text(encoding="utf-8")
        assert "pass_with_caveats" in text

    inv = json.loads(Path("docs/data_capabilities/twse_mis_rich_field_inventory.json").read_text(encoding="utf-8"))
    roc = inv["rich_observation_contract"]
    m7c = roc["m7c_deterministic_metrics"]
    m7d = roc["m7d_bounded_watchlist_cross_context"]

    assert m7c["safe_for_ai_context"] is True
    assert m7c["builder_output_safe_for_ai_context"] is False
    assert m7c["raw_rich_facts_exposed"] is False
    assert m7c["raw_full_ladder_exposed"] is False

    assert m7d["completed_tasks"] == ["M7D-00", "M7D-01", "M7D-02", "M7D-03", "M7D-04"]
    assert m7d["final_acceptance_status"] == "pass_with_caveats"
    assert m7d["next_task"] == "M7E-MARKET-CLOCK-AND-SESSION-STATE"
    assert m7d["safe_for_ai_context"] is True
    assert m7d["builder_output_safe_for_ai_context"] is False
    assert m7d["bounded_watchlist_only"] is True
    assert m7d["not_full_market_breadth"] is True
    assert m7d["raw_rich_facts_exposed"] is False
    assert m7d["raw_full_ladder_exposed"] is False

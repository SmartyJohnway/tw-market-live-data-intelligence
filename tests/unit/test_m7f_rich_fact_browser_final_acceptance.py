import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/protocol/M7F_RICH_FACT_BROWSER_OPERATOR_WORKBENCH_FINAL_ACCEPTANCE.md"
INV = ROOT / "docs/data_capabilities/twse_mis_rich_field_inventory.json"
PROFILE = ROOT / "config/test_execution_profiles.json"
FRONTEND = ROOT / "frontend/public/index.html"


def _entry():
    data = json.loads(INV.read_text(encoding="utf-8"))
    return data["rich_observation_contract"]["m7f_rich_fact_browser_operator_workbench"]


def test_final_acceptance_doc_records_m7f_closure():
    text = DOC.read_text(encoding="utf-8")
    for needle in [
        "final_acceptance_pass_with_caveats",
        "pass_with_caveats",
        "Rich fact browser is present",
        "not summary-only",
        "AI discussion handoff preview is present",
        "Safe Markdown handoff preview is present",
        "Safe JSON projection preview is present",
        "No real artifact loading",
        "No AI/model call",
        "No raw payload exposure",
        "M7G-LOCAL-SAFE-CONTEXT-ARTIFACT-LOAD-AND-OPERATOR-REFRESH-WORKFLOW",
    ]:
        assert needle in text


def test_final_inventory_status_is_strict_not_rollout_compatible_only():
    entry = _entry()
    assert entry["status"] == "final_acceptance_pass_with_caveats"
    assert entry["final_acceptance_status"] == "pass_with_caveats"
    assert entry["completed_tasks"] == ["M7F-00", "M7F-01", "M7F-02", "M7F-03", "M7F-04", "M7F-05", "M7F-06", "M7F-07", "M7F-08"]
    for key in [
        "frontend_security_regression_completed",
        "semantic_regression_completed",
        "final_acceptance_completed",
        "rich_fact_browser_final_accepted",
        "operator_workbench_final_accepted",
        "ai_discussion_handoff_final_accepted",
        "canonical_raw_payload_guardrail_keys_preserved",
    ]:
        assert entry[key] is True
    assert entry["browser_e2e_screenshot_captured"] is False
    assert entry["next_task"] == "M7G-LOCAL-SAFE-CONTEXT-ARTIFACT-LOAD-AND-OPERATOR-REFRESH-WORKFLOW"


def test_inventory_preserves_runtime_raw_and_trading_boundaries():
    entry = _entry()
    for key in [
        "runtime_behavior_changed", "fastapi_changed", "mcp_changed", "live_probe_added",
        "runtime_network_fetch_added", "hidden_fetch_added", "auto_refresh_added",
        "manual_refresh_added", "real_artifact_loading_added", "ai_model_call_added",
        "automatic_clipboard_write_added", "frontend_side_trading_day_inference_added",
        "raw_payload_exposure_allowed", "raw_forbidden_values_rendered",
        "raw_forbidden_fields_selectable", "raw_forbidden_values_copied",
        "trading_advice_allowed",
    ]:
        assert entry[key] is False


def test_official_enum_alignment_preserved():
    text = FRONTEND.read_text(encoding="utf-8")
    for drift in ["group: 'provenance'", "group: 'observed_value'", "group: 'order_context'", "group: 'calendar'", "exposure: 'display'", "confidence: 'forbidden'"]:
        assert drift not in text
    for value in [
        "source", "price_quote", "price_change", "volume_trading", "rich_observation",
        "market_clock_currentness", "trading_calendar_authority", "caveats_governance",
        "raw_forbidden", "operator_display_allowed", "caveated_display_allowed",
    ]:
        assert value in text


def test_default_ci_includes_final_acceptance_tests():
    data = json.loads(PROFILE.read_text(encoding="utf-8"))
    paths = data["profiles"]["default-ci"]["pytest_paths"]
    assert "tests/unit/test_m7f_frontend_security_semantic_regression.py" in paths
    assert "tests/unit/test_m7f_rich_fact_browser_final_acceptance.py" in paths

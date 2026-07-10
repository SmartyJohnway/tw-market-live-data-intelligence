import json
from pathlib import Path
from scripts.m7g_controlled_refresh_executor import (
    EXECUTION_SUPPORTED_SOURCE_FAMILIES,
    DECLARED_BUT_NOT_YET_EXECUTABLE_SOURCE_FAMILIES,
    DECLARED_SOURCE_FAMILIES,
)

FINAL_DOC = Path("docs/protocol/M7G_LOCAL_SAFE_CONTEXT_ARTIFACT_LOAD_FINAL_ACCEPTANCE.md")
INVENTORY = Path("docs/data_capabilities/twse_mis_rich_field_inventory.json")

def test_m7g_final_acceptance_doc_exists_and_contains_semantics():
    assert FINAL_DOC.exists()
    text = FINAL_DOC.read_text(encoding="utf-8")

    required_phrases = [
        "final_acceptance_pass_with_caveats",
        "PR #117",
        "PR #118",
        "manual UI acceptance",
        "bounded live smoke",
        "2330",
        "8069",
        "tse_2330.tw",
        "otc_8069.tw",
        "TPEX_MIS",
        "rotc_",
        "not introduced",
        "Mode A/B/C",
        "Level 1/2",
        "unchanged",
        "no raw payload exposure",
        "no trading advice"
    ]

    for phrase in required_phrases:
        assert phrase.lower() in text.lower()

def test_m7g_inventory_final_acceptance_properties():
    assert INVENTORY.exists()
    data = json.loads(INVENTORY.read_text(encoding="utf-8"))

    m7g = data["rich_observation_contract"]["m7g_local_safe_context_artifact_load"]

    assert m7g["status"] == "final_acceptance_pass_with_caveats"
    assert m7g["final_acceptance_status"] == "pass_with_caveats"
    assert m7g["final_acceptance_doc"] == FINAL_DOC.as_posix()

    # Check completed tasks
    for i in range(12):
        task_id = f"M7G-{i:02d}"
        assert task_id in m7g["completed_tasks"]

    assert m7g["manual_ui_acceptance_completed"] is True
    assert m7g["manual_ui_acceptance_result"] == "pass"
    assert m7g["bounded_live_smoke_completed"] is True
    assert m7g["bounded_live_smoke_result"] == "pass_with_caveats"

    # Final accepted validation flags
    assert m7g["m7g_final_accepted"] is True
    assert m7g["controlled_refresh_gate_final_accepted"] is True
    assert m7g["safe_artifact_load_gate_final_accepted"] is True
    assert m7g["ai_handoff_from_loaded_artifact_final_accepted"] is True
    assert m7g["source_route_semantics_final_accepted"] is True

    # Route checks
    assert m7g["tpex_mis_introduced"] is False
    assert m7g["rotc_route_introduced"] is False
    assert m7g["emerging_stock_live_supported"] is False

    # Gates and updates
    assert m7g["execute_auto_loads_artifact"] is False
    assert m7g["load_refreshed_safe_artifact_required"] is True
    assert m7g["rich_fact_browser_updates_only_after_load"] is True
    assert m7g["ai_handoff_updates_only_after_load"] is True

    # Mode/Level boundaries
    assert m7g["mode_abc_unchanged"] is True
    assert m7g["level_1_2_unchanged"] is True
    assert m7g["mode_d_added"] is False
    assert m7g["level_3_added"] is False
    assert m7g["m5f_mutated"] is False
    assert m7g["level1_mutated"] is False

    # No automation / Forbidden content
    assert m7g["auto_refresh_added"] is False
    assert m7g["scheduler_added"] is False
    assert m7g["polling_added"] is False
    assert m7g["hidden_fetch_added"] is False
    assert m7g["startup_fetch_added"] is False
    assert m7g["ai_model_call_added"] is False
    assert m7g["db_write_added"] is False
    assert m7g["raw_payload_returned_in_execution_result"] is False
    assert m7g["raw_payload_returned_in_safe_artifact"] is False
    assert m7g["trading_advice_allowed"] is False
    assert m7g["trading_signal_allowed"] is False
    assert m7g["recommendation_allowed"] is False

def test_m7g_source_taxonomy_unchanged():
    assert list(EXECUTION_SUPPORTED_SOURCE_FAMILIES) == ["TWSE_MIS"]
    assert "TPEX_MIS" not in DECLARED_SOURCE_FAMILIES

    # Declared but not yet executable families
    expected_non_executable = {"TAIFEX_MIS", "TWSE_OPENAPI", "TPEX_OPENAPI", "TAIFEX_OPENAPI"}
    assert DECLARED_BUT_NOT_YET_EXECUTABLE_SOURCE_FAMILIES == expected_non_executable

def test_windows_path_fix_remains_green():
    # Import and run the target m7e compatibility test
    from tests.unit.test_m7e_market_clock_session_state_final_acceptance import test_inventory_final_closure
    # Ensure it executes without throwing AssertionError (this validates path separator fix)
    test_inventory_final_closure()

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/protocol/M7A_TWSE_MIS_RICH_FACTS_FINAL_ACCEPTANCE.md"
INVENTORY = ROOT / "docs/data_capabilities/twse_mis_rich_field_inventory.json"


def _doc_text():
    return DOC.read_text(encoding="utf-8")


def _inventory():
    return json.loads(INVENTORY.read_text(encoding="utf-8"))


def test_final_acceptance_doc_exists_and_status_is_pass_with_caveats():
    text = _doc_text()
    assert text.startswith("# M7A TWSE MIS rich facts final acceptance")
    assert "Status:\n- pass_with_caveats" in text


def test_final_acceptance_doc_mentions_all_completed_m7a_stages():
    text = _doc_text()
    for stage in ["M7A-00", "M7A-01", "M7A-01B", "M7A-01D", "M7A-02", "M7A-02A", "M7A-03", "M7A-04", "M7A-05", "M7A-06"]:
        assert stage in text


def test_final_acceptance_doc_retains_required_caveats():
    text = _doc_text().lower()
    assert "no official public twse mis api field dictionary found" in text
    assert "no official api field dictionary" in text
    assert "no realtime sla" in text
    assert "unit_verified=false" in text
    assert "not support/resistance" in text
    assert "not true liquidity" in text
    assert "not full order book" in text
    assert "order-book truth" in text
    assert "safe_for_ai_context=false" in text


def test_inventory_final_acceptance_metadata_flags():
    acceptance = _inventory()["rich_observation_contract"]["m7a_final_acceptance"]
    assert acceptance["status"] == "pass_with_caveats"
    assert acceptance["completed"] is True
    for flag in [
        "downstream_compatibility_checked",
        "fastapi_checked",
        "mcp_checked",
        "frontend_watchlist_checked",
        "conversation_context_checked",
        "source_health_checked",
        "non_twse_mis_checked",
    ]:
        assert acceptance[flag] is True
    assert acceptance["ai_exposure_safe_for_context"] is False
    assert acceptance["official_api_field_dictionary_available"] is False
    assert acceptance["unit_verified_for_runtime_normalization"] is False
    assert acceptance["realtime_sla_verified"] is False
    assert acceptance["live_probe_executed_in_m7a_05_06"] is False
    assert acceptance["new_probe_output_committed_in_m7a_05_06"] is False
    assert acceptance["recommended_next_track"] == "M7B-AI-SAFE-MARKET-CONTEXT-PROJECTION-DESIGN"


def test_new_m7a_docs_and_metadata_do_not_introduce_uncaveated_signal_language():
    corpus = {
        str(DOC.relative_to(ROOT)): _doc_text(),
        str(INVENTORY.relative_to(ROOT)): INVENTORY.read_text(encoding="utf-8"),
    }
    forbidden_patterns = [
        r"support level",
        r"resistance level",
        r"liquidity signal",
        r"buy opportunity",
        r"sell pressure",
        r"main force accumulation",
    ]
    for name, text in corpus.items():
        lowered = text.lower()
        for pattern in forbidden_patterns:
            assert not re.search(pattern, lowered), f"{pattern} found in {name}"

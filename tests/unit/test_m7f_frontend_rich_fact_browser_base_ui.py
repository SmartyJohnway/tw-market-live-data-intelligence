import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend/public/index.html"
DOC = ROOT / "docs/protocol/M7F_FRONTEND_RICH_FACT_BROWSER_BASE_UI.md"
INV = ROOT / "docs/data_capabilities/twse_mis_rich_field_inventory.json"
PROFILE = ROOT / "config/test_execution_profiles.json"


def test_m7f02_doc_exists_and_records_policy():
    assert DOC.exists()
    text = DOC.read_text(encoding="utf-8")
    for phrase in [
        "base_ui_defined",
        "read-only frontend rich fact browser",
        "not summary-only",
        "no raw payload exposure",
        "no trading advice",
        "DOM API / textContent",
        "No unsafe innerHTML",
        "M7F-03-04-FIELD-BADGES-CURRENTNESS-AND-CALENDAR-INTEGRATION",
    ]:
        assert phrase in text


def test_frontend_contains_required_m7f02_sections():
    text = FRONTEND.read_text(encoding="utf-8")
    for phrase in [
        "Rich Fact Browser",
        "Operator status",
        "Observed Rich Facts",
        "View governed rich fields",
        "Governance",
        "Raw forbidden fields omitted",
        "Static sample",
        "Not live data",
        "Not trading advice",
    ]:
        assert phrase in text


def test_m7f02_frontend_uses_safe_dom_rendering():
    text = FRONTEND.read_text(encoding="utf-8")
    m7f = text[text.index("const M7F_DISPLAY_CATALOG") : text.index("function renderMatrixLoadError")]
    forbidden = ["innerHTML", "insertAdjacentHTML", "document.write", "eval(", "new Function"]
    for token in forbidden:
        assert token not in m7f
    assert "textContent" in text
    assert "document.createElement" in m7f


def test_m7f02_frontend_catalog_uses_official_enum_values():
    text = FRONTEND.read_text(encoding="utf-8")
    m7f_catalog = text[text.index("const M7F_DISPLAY_CATALOG") : text.index("const M7F_DEMO_RICH_CONTEXT")]
    for drift_enum in [
        "group: 'provenance'",
        "group: 'observed_value'",
        "group: 'order_context'",
        "group: 'calendar'",
        "exposure: 'display'",
        "confidence: 'forbidden'",
    ]:
        assert drift_enum not in m7f_catalog

    for key in [
        "raw_payload",
        "twse_mis_rich_facts",
        "full_ladder",
        "bid_prices",
        "ask_prices",
        "source_investigation_notes",
    ]:
        pattern = rf"{key}: \{{[^}}]*group: 'raw_forbidden'[^}}]*confidence: 'raw_forbidden'[^}}]*exposure: 'raw_forbidden'"
        assert re.search(pattern, m7f_catalog, flags=re.DOTALL), key


def test_raw_forbidden_keys_are_classified_but_not_present_in_demo_observations():
    text = FRONTEND.read_text(encoding="utf-8")
    for key in [
        "raw_payload",
        "twse_mis_rich_facts",
        "full_ladder",
        "bid_prices",
        "ask_prices",
        "source_investigation_notes",
    ]:
        pattern = rf"{key}: \{{[^}}]*display_allowed: false[^}}]*raw_forbidden: true"
        assert re.search(pattern, text, flags=re.DOTALL), key

    observations = text[text.index("observations: [") : text.index("function getM7FDisplayableFields")]
    for key in ["raw_payload", "twse_mis_rich_facts", "full_ladder", "bid_prices", "ask_prices", "source_investigation_notes"]:
        assert key not in observations


def test_m7f02_section_avoids_positive_trading_language():
    text = FRONTEND.read_text(encoding="utf-8")
    section = text[text.index('id="m7f-rich-fact-browser"') : text.index("<h2>Local API Tools</h2>")]
    script = text[text.index("const M7F_DISPLAY_CATALOG") : text.index("function renderMatrixLoadError")]
    m7f_text = section + script
    normalized = re.sub(r"not trading signal[s]?", "", m7f_text, flags=re.IGNORECASE)
    normalized = re.sub(r"Badges are not trading signal[s]?", "", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"Not trading advice", "", normalized)
    normalized = re.sub(r"No recommendation", "", normalized)
    normalized = re.sub(r"Badges are not recommendation[s]?", "", normalized, flags=re.IGNORECASE)
    disallowed = [
        "Buy", "Sell", "Hold", "Signal", "Target price", "Support", "Resistance",
        "Capital flow", "Sector rotation", "Top movers", "Strongest", "Weakest", "Ranking",
    ]
    for phrase in disallowed:
        assert phrase not in normalized


def test_m7f02_displays_multiple_rich_fields_not_summary_only():
    text = FRONTEND.read_text(encoding="utf-8")
    for field in [
        "price_like_value",
        "change_percent",
        "volume_candidate",
        "best_bid_candidate",
        "best_ask_candidate",
        "session_state",
        "freshness_state",
        "currentness_label",
        "calendar_confidence",
        "trading_day_status",
        "not_trading_signal",
        "not_recommendation",
    ]:
        assert field in text


def test_m7f02_inventory_status():
    inv = json.loads(INV.read_text(encoding="utf-8"))
    entry = inv["rich_observation_contract"]["m7f_rich_fact_browser_operator_workbench"]
    assert entry["status"] in {"base_ui_defined", "field_badges_currentness_calendar_integrated"}
    assert entry["completed_tasks"] in (["M7F-00", "M7F-01", "M7F-02"], ["M7F-00", "M7F-01", "M7F-02", "M7F-03", "M7F-04"])
    for key in ["frontend_changed"]:
        assert entry[key] is True
    for key in [
        "runtime_behavior_changed",
        "fastapi_changed",
        "mcp_changed",
        "live_probe_added",
        "runtime_network_fetch_added",
        "hidden_fetch_added",
        "raw_payload_exposure_allowed",
        "unsafe_inner_html_allowed",
        "raw_forbidden_values_rendered",
    ]:
        assert entry[key] is False
    assert entry["next_task"] in {"M7F-03-04-FIELD-BADGES-CURRENTNESS-AND-CALENDAR-INTEGRATION", "M7F-05-06-AI-DISCUSSION-HANDOFF-RICH-FACT-SELECTION-SEARCH-AND-FILTERS"}


def test_m7f02_default_ci_inclusion():
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    assert "tests/unit/test_m7f_frontend_rich_fact_browser_base_ui.py" in profile["profiles"]["default-ci"]["pytest_paths"]

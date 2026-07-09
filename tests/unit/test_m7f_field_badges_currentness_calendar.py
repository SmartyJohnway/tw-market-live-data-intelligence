import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend/public/index.html"
DOC = ROOT / "docs/protocol/M7F_FIELD_BADGES_CURRENTNESS_CALENDAR_INTEGRATION.md"
INV = ROOT / "docs/data_capabilities/twse_mis_rich_field_inventory.json"
PROFILE = ROOT / "config/test_execution_profiles.json"


def _frontend_text():
    return FRONTEND.read_text(encoding="utf-8")


def _m7f_js(text):
    return text[text.index("const M7F_DISPLAY_CATALOG") : text.index("function renderMatrixLoadError")]


def test_doc_exists_and_records_m7f0304_policy():
    assert DOC.exists()
    text = DOC.read_text(encoding="utf-8")
    for phrase in [
        "field_badges_currentness_calendar_integrated",
        "field-level confidence",
        "exposure",
        "caveat badges",
        "currentness",
        "trading-calendar authority",
        "Badges are not trading signals",
        "Badges are not recommendations",
        "No hidden fetch",
        "No FastAPI/MCP changes",
        "No frontend-side trading-day inference",
        "M7F-05-06-AI-DISCUSSION-HANDOFF-RICH-FACT-SELECTION-SEARCH-AND-FILTERS",
    ]:
        assert phrase in text


def test_frontend_contains_badge_ui_text_and_classes():
    text = _frontend_text()
    for phrase in [
        "Badge legend",
        "Confidence badges",
        "Exposure class",
        "Currentness",
        "Calendar authority",
        "No realtime SLA",
        "Badges are not trading signals",
        "Badges are not recommendations",
        "m7f-badge",
        "m7f-badge-confidence",
        "m7f-badge-exposure",
        "m7f-badge-currentness",
        "m7f-badge-calendar",
        "m7f-badge-caveat",
    ]:
        assert phrase in text


def test_frontend_currentness_labels_are_recognized():
    text = _frontend_text()
    for label in ["live_candidate", "recent_but_unverified", "reference_only", "not_current", "degraded_unknown"]:
        assert label in text


def test_frontend_calendar_authority_labels_are_recognized():
    text = _frontend_text()
    for label in [
        "controlled_twse_holiday_schedule_artifact",
        "weekday_heuristic_only",
        "artifact_missing_date",
        "trading_day",
        "non_trading_day",
        "unknown",
        "not_full_exchange_calendar_engine",
        "no_realtime_sla",
        "not_trading_advice",
    ]:
        assert label in text


def test_m7f_js_has_no_frontend_side_trading_day_inference():
    js = _m7f_js(_frontend_text())
    scrubbed = js.replace("weekday_heuristic_only", "")
    for pattern in ["getDay(", "dayOfWeek", "isWeekend", "isTradingDay ="]:
        assert pattern not in scrubbed
    assert not re.search(r"\bweekday\b", scrubbed, flags=re.IGNORECASE)


def test_m7f_js_uses_safe_dom_rendering_only():
    js = _m7f_js(_frontend_text())
    for token in ["innerHTML", "insertAdjacentHTML", "document.write", "eval(", "new Function"]:
        assert token not in js
    assert "document.createElement" in js
    assert "textContent" in js


def test_m7f_section_has_no_positive_trading_semantics():
    text = _frontend_text()
    section = text[text.index('id="m7f-rich-fact-browser"') : text.index("<h2>Local API Tools</h2>")]
    js = _m7f_js(text)
    normalized = section + js
    allowed = [
        r"not trading signal[s]?",
        r"Badges are not trading signal[s]?",
        r"Not trading advice",
        r"not_trading_advice",
        r"not_trading_signal",
        r"not recommendation[s]?",
        r"Badges are not recommendation[s]?",
        r"No recommendation",
    ]
    for phrase in allowed:
        normalized = re.sub(phrase, "", normalized, flags=re.IGNORECASE)
    for phrase in [
        "Buy", "Sell", "Hold", "Target price", "Support", "Resistance", "Capital flow",
        "Sector rotation", "Top movers", "Strongest", "Weakest", "Ranking", "bullish", "bearish",
    ]:
        assert phrase not in normalized


def test_m7f_in_page_catalog_enum_alignment_is_preserved():
    text = _frontend_text()
    catalog = text[text.index("const M7F_DISPLAY_CATALOG") : text.index("const M7F_DEMO_RICH_CONTEXT")]
    for drift_enum in [
        "group: 'provenance'",
        "group: 'observed_value'",
        "group: 'order_context'",
        "group: 'calendar'",
        "exposure: 'display'",
        "confidence: 'forbidden'",
    ]:
        assert drift_enum not in catalog
    for value in [
        "operator_display_allowed",
        "caveated_display_allowed",
        "raw_forbidden",
        "market_clock_currentness",
        "trading_calendar_authority",
        "caveats_governance",
    ]:
        assert value in catalog


def test_raw_forbidden_keys_not_rendered_inside_demo_observations():
    text = _frontend_text()
    observations = text[text.index("observations: [") : text.index("function getM7FDisplayableFields")]
    for key in [
        "raw_payload",
        "twse_mis_rich_facts",
        "raw_unknown_facts",
        "full_ladder",
        "bid_prices",
        "ask_prices",
        "source_investigation_notes",
    ]:
        assert key not in observations


def test_inventory_status_for_m7f0304():
    entry = json.loads(INV.read_text(encoding="utf-8"))["rich_observation_contract"]["m7f_rich_fact_browser_operator_workbench"]
    expected_true = [
        "field_confidence_badges_added", "field_exposure_badges_added", "field_caveat_badges_added",
        "currentness_panel_added", "calendar_authority_panel_added", "badge_legend_added",
        "frontend_changed", "badges_are_not_trading_signals", "badges_are_not_recommendations",
    ]
    expected_false = [
        "runtime_behavior_changed", "fastapi_changed", "mcp_changed", "live_probe_added",
        "runtime_network_fetch_added", "hidden_fetch_added", "auto_refresh_added",
        "frontend_side_trading_day_inference_added", "raw_payload_exposure_allowed",
        "raw_forbidden_values_rendered", "trading_advice_allowed",
    ]
    assert entry["status"] == "field_badges_currentness_calendar_integrated"
    assert entry["completed_tasks"] == ["M7F-00", "M7F-01", "M7F-02", "M7F-03", "M7F-04"]
    for key in expected_true:
        assert entry[key] is True
    for key in expected_false:
        assert entry[key] is False
    assert entry["next_task"] == "M7F-05-06-AI-DISCUSSION-HANDOFF-RICH-FACT-SELECTION-SEARCH-AND-FILTERS"


def test_default_ci_includes_m7f0304_test():
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    assert "tests/unit/test_m7f_field_badges_currentness_calendar.py" in profile["profiles"]["default-ci"]["pytest_paths"]

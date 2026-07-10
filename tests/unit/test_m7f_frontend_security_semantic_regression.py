from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend/public/index.html"
DOC = ROOT / "docs/protocol/M7F_FRONTEND_SECURITY_SEMANTIC_REGRESSION.md"

RAW_FORBIDDEN_KEYS = [
    "raw_payload",
    "twse_mis_rich_facts",
    "raw_unknown_facts",
    "full_ladder",
    "bid_prices",
    "ask_prices",
    "source_investigation_notes",
]


def _frontend() -> str:
    return FRONTEND.read_text(encoding="utf-8")


def _m7f_js_slice() -> str:
    text = _frontend()
    start = text.index("const M7F_DISPLAY_CATALOG")
    end = text.index("async function executeM7GControlledRefreshOnce", start)
    return text[start:end]


def test_security_semantic_regression_doc_records_final_gate():
    text = DOC.read_text(encoding="utf-8")
    for needle in [
        "frontend_security_semantic_regression_pass_with_caveats",
        "No unsafe innerHTML",
        "No hidden fetch",
        "No auto refresh",
        "No backend/API/MCP hook",
        "Clipboard write only occurs through explicit operator click",
        "raw_payload values are not rendered",
        "No trading advice",
        "No frontend-side trading-day inference",
        "pass_with_caveats",
    ]:
        assert needle in text


def test_m7f_js_slice_has_no_hidden_network_or_unsafe_dom_execution():
    js = _m7f_js_slice()
    forbidden = [
        "innerHTML",
        "insertAdjacentHTML",
        "document.write",
        "eval(",
        "new Function",
        "fetch(",
        "XMLHttpRequest",
        "WebSocket",
        "EventSource",
        "setInterval",
        "setTimeout",
        "/api/",
        "mcp",
        "uvicorn",
        "localhost",
        "127.0.0.1",
    ]
    for token in forbidden:
        assert token not in js


def test_clipboard_writes_are_explicit_copy_click_only():
    text = _frontend()
    assert "navigator.clipboard.writeText" in text
    assert "addEventListener('click'" in text
    assert "Copy Safe Markdown" in text
    assert "Copy Safe JSON" in text
    write_index = text.index("navigator.clipboard.writeText")
    function_start = text.rfind("function copyM7FPreviewText", 0, write_index)
    function_end = text.index("function renderM7FHandoffPanel", function_start)
    assert function_start != -1
    assert function_start < write_index < function_end


def test_raw_forbidden_values_are_not_in_demo_observations_or_copied():
    js = _m7f_js_slice()
    demo_start = js.index("observations: [")
    demo_end = js.index("M7F_DEFAULT_HANDOFF_FIELDS", demo_start)
    demo = js[demo_start:demo_end]
    for key in RAW_FORBIDDEN_KEYS:
        assert f"{key}:" not in demo
    assert "display_allowed === true && meta.ai_handoff_allowed === true && meta.raw_forbidden === false" in js
    assert "JSON.stringify(context" not in js
    assert "JSON.stringify(projection" in js


def test_canonical_raw_exposure_guardrail_keys_are_preserved_in_handoff():
    js = _m7f_js_slice()
    for key in ["raw_payload_exposed", "raw_rich_facts_exposed", "raw_full_ladder_exposed"]:
        assert key in js
        assert f"{key}: false" in js or f"{key}: context.governance.{key}" in js
    projection_start = js.index("governance_guardrails:")
    projection = js[projection_start: js.index("raw_forbidden_omission_notice", projection_start)]
    assert "raw_payload_exposed" in projection
    assert "raw_rich_facts_exposed" in projection
    assert "raw_full_ladder_exposed" in projection


def test_no_positive_trading_semantics_or_frontend_trading_day_inference():
    js = _m7f_js_slice()
    for token in [
        "Buy", "Sell", "Hold", "Target price", "Support", "Resistance",
        "Capital flow", "Sector rotation", "Top movers", "Strongest",
        "Weakest", "Ranking", "bullish", "bearish", "entry", "exit",
        "stop loss", "take profit",
    ]:
        assert token not in js
    for token in ["getDay(", "dayOfWeek", "isWeekend", "isTradingDay ="]:
        assert token not in js


def test_required_m7f_ui_capabilities_remain_present():
    text = _frontend()
    for needle in [
        "Rich Fact Browser / Operator Workbench",
        "Operator status",
        "Observed Rich Facts",
        "View governed rich fields",
        "Badge legend",
        "Currentness",
        "Calendar authority",
        "Search, filters",
        "Symbol/name search",
        "Field group filter",
        "Confidence filter",
        "Exposure filter",
        "Currentness filter",
        "Show caveated fields",
        "AI Discussion Handoff Preview",
        "Safe Markdown handoff preview",
        "Safe JSON projection preview",
        "Copy Safe Markdown",
        "Copy Safe JSON",
        "Raw forbidden fields omitted",
    ]:
        assert needle in text

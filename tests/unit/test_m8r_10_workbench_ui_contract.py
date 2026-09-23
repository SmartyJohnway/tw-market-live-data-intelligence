from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HTML = ROOT / "frontend" / "unified-workbench" / "UnifiedMarketEvidenceWorkbench.html"
SCRIPT = ROOT / "frontend" / "unified-workbench" / "watchlist-workbench.js"


def test_watchlist_workbench_is_canonical_and_complete():
    html = HTML.read_text(encoding="utf-8")
    for required in (
        "Persistent Watchlist &amp; Request Builder",
        "btn-watchlist-create",
        "btn-watchlist-rename",
        "btn-watchlist-default",
        "btn-watchlist-delete",
        "btn-watchlist-restore",
        "btn-watchlist-history",
        "watchlist-import",
        "btn-compose-request",
        "btn-confirm-mutation",
        "watchlist-workbench.js",
    ):
        assert required in html


def test_watchlist_ui_has_no_browser_authority_or_unsafe_rendering():
    script = SCRIPT.read_text(encoding="utf-8")
    assert "localStorage" not in script
    assert "sessionStorage" not in script
    assert "setInterval" not in script
    assert ".innerHTML" not in script
    assert "textContent" in script
    assert "market_fetch_evidence" not in script
    assert "confirmMutation" in script and "composeRequest" in script


def test_three_confirmations_remain_separate_in_ui_sources():
    html = HTML.read_text(encoding="utf-8")
    assert 'id="btn-confirm-mutation"' in html
    assert 'id="btn-authorize"' in html
    assert 'id="confirm-network-execution"' in html
    assert 'id="btn-execute-once"' in html


def test_phase_g_builder_and_result_wording_are_truthful():
    builder = SCRIPT.read_text(encoding="utf-8")
    result_script = (
        ROOT / "frontend" / "unified-workbench" / "unified-workbench.js"
    ).read_text(encoding="utf-8")
    assert "watchlist_evidence_selection_request.v3" in builder
    assert "no matching disclosure in the latest completed official daily batch" in result_script
    assert "this is not a claim of no historical disclosures" in result_script
    assert "value is unavailable, not zero" in result_script
    assert "research_status" in result_script

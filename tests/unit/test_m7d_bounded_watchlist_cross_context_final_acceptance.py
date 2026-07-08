from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/protocol/M7D_BOUNDED_WATCHLIST_CROSS_CONTEXT_FINAL_ACCEPTANCE.md"
POLICY = ROOT / "docs/protocol/M7D_BOUNDED_WATCHLIST_CROSS_CONTEXT_POLICY.md"


def test_final_acceptance_doc_added_with_required_closure_language():
    text = DOC.read_text(encoding="utf-8")
    for token in ["pass_with_caveats", "M7D-04 controlled integration", "safe_for_ai_context=true only after controlled promotion", "bounded_watchlist_only=true", "not_full_market_breadth=true", "cross_context_is_signal=false", "no live probe in M7D", "no raw rich facts exposed", "no full ladder arrays exposed", "M7E-MARKET-CLOCK-AND-SESSION-STATE"]:
        assert token in text


def test_policy_doc_has_final_status_section():
    text = POLICY.read_text(encoding="utf-8")
    assert "M7D-02/M7D-03/M7D-04 final status" in text
    assert "M7D is complete as pass_with_caveats" in text
    assert "The next track is M7E-MARKET-CLOCK-AND-SESSION-STATE" in text

import re

from scripts.m5k_common import build_conversation_context, conversation_context_markdown
from tests.unit.test_m7e_market_clock_session_state_context_integration import _watchlist


def test_markdown_market_clock_section_and_safe_language():
    context = build_conversation_context(_watchlist(), {"generated_at_utc": "2026-01-05T05:44:00+00:00", "observations": []}, now_utc="2026-01-05T05:45:00+00:00")
    md = conversation_context_markdown(context)
    assert "## Market Clock / Currentness" in md
    assert "Session state:" in md
    assert "Currentness label:" in md
    assert "AI currentness summary:" in md
    assert "do not describe it as current intraday movement" in md
    for phrase in ["currently rising", "currently falling", "market is now moving", "buy signal", "sell signal", "recommendation", "target price", "support", "resistance", "capital flow", "sector rotation", "full-market breadth"]:
        assert not re.search(rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])", md)

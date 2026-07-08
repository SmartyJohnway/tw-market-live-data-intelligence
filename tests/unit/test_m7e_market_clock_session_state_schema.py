from scripts.market_clock_session_state import build_empty_market_clock_session_state


def test_empty_market_clock_session_state_schema_flags():
    ctx = build_empty_market_clock_session_state()
    assert ctx["schema_version"] == "m7e_market_clock_session_state.v1"
    assert ctx["context_status"] == "schema_defined_not_computed"
    assert ctx["runtime_populated"] is False
    assert ctx["safe_for_ai_context"] is False
    assert ctx["builder_output_safe_for_ai_context"] is False
    assert ctx["not_trading_signal"] is True
    assert ctx["not_recommendation"] is True
    assert ctx["not_capital_flow"] is True
    for key in ["session_state", "calendar_policy", "freshness_state", "allowed_language", "blocked_language", "quality_gates"]:
        assert key in ctx


def test_schema_safety_language_lists_are_guardrail_examples_only():
    ctx = build_empty_market_clock_session_state()
    blocked = set(ctx["blocked_language"])
    for phrase in ["buy signal", "sell signal", "recommendation", "support", "resistance", "capital flow", "full-market breadth"]:
        assert phrase in blocked
        assert phrase not in ctx["allowed_language"]
    assert ctx["quality_gates"]["raw_rich_facts_exposed"] is False
    assert ctx["quality_gates"]["raw_full_ladder_exposed"] is False

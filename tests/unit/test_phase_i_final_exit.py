from scripts.validate_phase_i_final_exit import validate


def test_phase_i_exit_review_matches_active_runtime_and_closure():
    result = validate()
    assert result["status"] == "PASS"
    assert result["phase_i_exit"] == "PHASE_I_OWNER_ACCEPTANCE_CANDIDATE_EXIT_PASS"
    assert result["i1_sources_routes"] == "3/2"
    assert result["i2_sources_routes"] == "1/1"
    assert (result["i3_sources"], result["i3_logical_routes"], result["i3_runtime_market_routes"]) == (2, 1, 2)
    assert result["mcp_tool_count"] == 6
    assert result["market_gets"] == 0

from scripts.phase_j_real_agent_attempt2_proxy import (
    ALLOWED_SEQUENCE,
    CONTROL_PACKAGE_ID,
    tool_call_is_authorized,
)


def test_witness_proxy_allows_only_one_read_then_one_handoff():
    calls = []
    assert tool_call_is_authorized(
        "market_read_result", {"control_package_id": CONTROL_PACKAGE_ID}, calls
    )
    calls.append(ALLOWED_SEQUENCE[0])
    assert tool_call_is_authorized(
        "market_export_ai_handoff", {"control_package_id": CONTROL_PACKAGE_ID}, calls
    )


def test_witness_proxy_rejects_unapproved_tool_duplicate_or_wrong_package():
    args = {"control_package_id": CONTROL_PACKAGE_ID}
    assert not tool_call_is_authorized("market_fetch_evidence", args, [])
    assert not tool_call_is_authorized("market_export_ai_handoff", args, [])
    assert not tool_call_is_authorized("market_read_result", args, [ALLOWED_SEQUENCE[0]])
    assert not tool_call_is_authorized("market_read_result", {"control_package_id": "other"}, [])

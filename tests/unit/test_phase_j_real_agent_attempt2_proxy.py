from scripts.phase_j_real_agent_attempt2_proxy import (
    ALLOWED_SEQUENCE,
    CONTROL_PACKAGE_ID_PATTERN,
    tool_call_is_authorized,
)

FRESH_ID = "umea-v1-1234567890abcdef1234"
HISTORICAL_ID = "umea-v1-559d58856cff60f2f2e0"


def test_witness_proxy_allows_explicit_package_one_read_then_one_handoff():
    calls = []
    assert tool_call_is_authorized(
        "market_read_result", {"control_package_id": FRESH_ID}, calls, FRESH_ID
    )
    calls.append(ALLOWED_SEQUENCE[0])
    assert tool_call_is_authorized(
        "market_export_ai_handoff", {"control_package_id": FRESH_ID}, calls, FRESH_ID
    )


def test_witness_proxy_rejects_unapproved_tool_duplicate_wrong_package_and_extra_calls():
    args = {"control_package_id": FRESH_ID}
    assert not tool_call_is_authorized("market_fetch_evidence", args, [], FRESH_ID)
    assert not tool_call_is_authorized("market_export_ai_handoff", args, [], FRESH_ID)
    assert not tool_call_is_authorized("market_read_result", args, [ALLOWED_SEQUENCE[0]], FRESH_ID)
    assert not tool_call_is_authorized("market_read_result", {"control_package_id": "other"}, [], FRESH_ID)
    assert not tool_call_is_authorized("market_read_result", {"control_package_id": HISTORICAL_ID}, [], FRESH_ID)
    assert not tool_call_is_authorized("market_read_result", args, [], "not-a-package")
    assert not tool_call_is_authorized("market_read_result", args, list(ALLOWED_SEQUENCE), FRESH_ID)


def test_proxy_requires_explicit_package_identity_and_has_no_historical_default():
    assert CONTROL_PACKAGE_ID_PATTERN.fullmatch(FRESH_ID)
    assert CONTROL_PACKAGE_ID_PATTERN.fullmatch(HISTORICAL_ID)
    assert "CONTROL_PACKAGE_ID =" not in open(
        "scripts/phase_j_real_agent_attempt2_proxy.py", encoding="utf-8"
    ).read()

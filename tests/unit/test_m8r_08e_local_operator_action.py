import pytest

from server.services import unified_local_operator_action as action
from server.services.unified_local_operator_action import LocalOperatorActionError


def _request(mode="execute"):
    return {
        "schema_version": "unified_market_evidence_request.v1", "request_id": "m8r08e-action",
        "execution_mode": mode, "targets": [{"input": "2330", "market_hint": "TWSE"}],
        "data_needs": [{"type": "current_observation", "priority": "required"}],
    }


def test_preview_is_rejected_before_ticket_or_network(monkeypatch):
    monkeypatch.setattr(action, "build_local_operator_execution_ticket", lambda *_: pytest.fail("ticket"))
    monkeypatch.setattr(action, "execute_local_operator_ticket", lambda *_args, **_kwargs: pytest.fail("network"))
    with pytest.raises(LocalOperatorActionError, match="market_fetch_requires_execute_mode"):
        action.fetch_market_evidence({"request": _request("preview")})


def test_execute_composes_existing_ticket_execution_and_mode_c(monkeypatch):
    calls = []
    monkeypatch.setattr(action, "build_local_operator_execution_ticket", lambda request: calls.append(("ticket", request)) or {
        "control_package_id": "umea-v1-0123456789abcdef0123", "authorization_id": "umea-v1-0123456789abcdef0123",
        "authorization_hash": "a" * 64, "network_required": True,
    })
    monkeypatch.setattr(action, "execute_local_operator_ticket", lambda control, *, network_required: calls.append(("execute", control, network_required)) or {
        "aggregation_status": "succeeded", "external_market_network_attempted": True,
        "external_market_network_executed": True,
    })
    monkeypatch.setattr(action, "build_mode_c_ai_handoff", lambda control: calls.append(("mode_c", control)) or {
        "canonical_result": {"result_hash": "r"}, "ai_ready_markdown": "# governed",
        "result_hash": "r", "audit_reference": "audit/x.json", "additional_market_network_executed": False,
    })
    result = action.fetch_market_evidence({"request": _request()})
    assert calls == [
        ("ticket", _request()), ("execute", "umea-v1-0123456789abcdef0123", True),
        ("mode_c", "umea-v1-0123456789abcdef0123"),
    ]
    assert result["market_network_executed"] is True
    assert result["additional_market_network_executed"] is False
    assert result["canonical_result"]["result_hash"] == "r"


def test_action_envelope_rejects_privileged_fields_without_ticket():
    with pytest.raises(LocalOperatorActionError, match="invalid_api_envelope"):
        action.fetch_market_evidence({"request": _request(), "confirm_execution": True})

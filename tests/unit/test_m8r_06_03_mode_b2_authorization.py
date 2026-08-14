from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from server.services import unified_mode_b2


def _rebuilt():
    plan = json.loads(open("tests/fixtures/m8r_05b_01/golden/single_executable_plan.json", encoding="utf-8").read())
    return {
        "preview": {"status": "ready_for_confirmation", "internal_execution_reference": {"preview_id": "umepreview-v1-test"}},
        "orchestration_plan": plan,
    }


def _payload():
    rebuilt = _rebuilt()
    return {
        "request": {"schema_version": "unified_market_evidence_request.v1", "request_id": "b2-test"},
        "expected_preview_id": rebuilt["preview"]["internal_execution_reference"]["preview_id"],
        "expected_plan_id": rebuilt["orchestration_plan"]["plan_id"],
        "expected_plan_hash": rebuilt["orchestration_plan"]["plan_hash"],
        "confirm_authorization": True,
        "approval_scope_mode": "whole_plan_executable_scope",
        "decision_reason": "offline test",
        "owner_review_reference": "unit-test",
    }


def test_authorization_rebuilds_and_persists_server_owned_control_package(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(unified_mode_b2, "CONTROL_ROOT", tmp_path)
    monkeypatch.setattr(unified_mode_b2, "build_mode_b1_preview", lambda request: calls.append(request) or _rebuilt())

    result = unified_mode_b2.build_mode_b2_authorization(_payload())
    assert calls
    assert result["authorization_created"] is True
    assert result["network_executed"] is False
    assert "governed_output_root" not in result
    assert (tmp_path / result["authorization_id"] / "control" / "manifest.json").is_file()


def test_stale_or_privileged_browser_fields_fail_closed_without_rebuild(monkeypatch):
    called = False
    def rebuild(_request):
        nonlocal called
        called = True
        return _rebuilt()
    monkeypatch.setattr(unified_mode_b2, "build_mode_b1_preview", rebuild)
    payload = _payload() | {"command": "whoami"}
    with pytest.raises(unified_mode_b2.ModeB2Error, match="privileged_field_forbidden"):
        unified_mode_b2.build_mode_b2_authorization(payload)
    assert called is False

    payload = _payload() | {"expected_plan_hash": "0" * 64}
    with pytest.raises(unified_mode_b2.ModeB2Error, match="mode_b2_preview_stale"):
        unified_mode_b2.build_mode_b2_authorization(payload)


@pytest.mark.parametrize(
    "payload",
    [
        _payload() | {"approved_operation_ids": ["unexpected"]},
        _payload() | {"approval_scope_mode": "selected_operations", "approved_operation_ids": []},
        _payload() | {"approval_scope_mode": "selected_operations", "approved_operation_ids": ["umeop-op-v1-37e7ffc42102745298c7"], "approved_batch_group_ids": ["unexpected"]},
        _payload() | {"approval_scope_mode": "selected_batches", "approved_operation_ids": ["unexpected"], "approved_batch_group_ids": ["umeop-batch-v1-e2e0b2ff88ba782d586b"], "approved_batch_membership": {"umeop-batch-v1-e2e0b2ff88ba782d586b": ["umeop-op-v1-37e7ffc42102745298c7"]}},
    ],
)
def test_scope_mode_rejects_mixed_browser_selection_inputs(payload, monkeypatch):
    monkeypatch.setattr(unified_mode_b2, "build_mode_b1_preview", lambda _request: _rebuilt())
    with pytest.raises(unified_mode_b2.ModeB2Error, match="approval_scope_input_conflict"):
        unified_mode_b2.build_mode_b2_authorization(payload)


def test_finalized_control_package_is_write_once(tmp_path, monkeypatch):
    monkeypatch.setattr(unified_mode_b2, "CONTROL_ROOT", tmp_path)
    monkeypatch.setattr(unified_mode_b2, "build_mode_b1_preview", lambda _request: _rebuilt())
    monkeypatch.setattr(unified_mode_b2, "_utc_now", lambda: datetime(2026, 8, 11, tzinfo=timezone.utc))
    payload = _payload()
    unified_mode_b2.build_mode_b2_authorization(payload)
    with pytest.raises(unified_mode_b2.ModeB2Error, match="control_package_already_finalized"):
        unified_mode_b2.build_mode_b2_authorization(payload)


def test_mode_b1_planning_dependency_is_bounded_at_b2_service(monkeypatch):
    from server.services.unified_mode_b1 import ModeB1PlanningUnavailable

    def unavailable(_request):
        raise ModeB1PlanningUnavailable("P:\\secret\\authority.json")

    monkeypatch.setattr(unified_mode_b2, "build_mode_b1_preview", unavailable)
    with pytest.raises(unified_mode_b2.ModeB2Error, match="mode_b1_planning_dependency_unavailable"):
        unified_mode_b2.build_mode_b2_authorization(_payload())


def test_local_operator_ticket_uses_truthful_non_workbench_provenance(tmp_path, monkeypatch):
    monkeypatch.setattr(unified_mode_b2, "CONTROL_ROOT", tmp_path)
    monkeypatch.setattr(unified_mode_b2, "build_mode_b1_preview", lambda _request: _rebuilt())
    request = _payload()["request"] | {"execution_mode": "execute"}
    result = unified_mode_b2.build_local_operator_execution_ticket(request)
    authorization = json.loads((tmp_path / result["authorization_id"] / "control" / "authorization.json").read_text(encoding="utf-8"))
    assert authorization["owner_identity_reference"] == "local_operator_mcp"
    assert authorization["owner_review_reference"] == "local_operator_mcp_action"
    assert authorization["single_use"] is True
    assert authorization["maximum_use_count"] == 1


def test_local_operator_preview_mode_creates_no_ticket(monkeypatch):
    monkeypatch.setattr(unified_mode_b2, "build_mode_b1_preview", lambda _request: _rebuilt())
    with pytest.raises(unified_mode_b2.ModeB2Error, match="market_fetch_requires_execute_mode"):
        unified_mode_b2.build_local_operator_execution_ticket(_payload()["request"] | {"execution_mode": "preview"})

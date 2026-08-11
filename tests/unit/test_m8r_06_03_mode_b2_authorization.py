from __future__ import annotations

import json

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

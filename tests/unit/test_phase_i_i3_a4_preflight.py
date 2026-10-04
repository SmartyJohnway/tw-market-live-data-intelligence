"""I3-A4 production activation preflight tests. All external sockets are denied."""
import json
import socket

import pytest

from scripts import validate_phase_i_i3_a4_preflight as preflight


@pytest.fixture(autouse=True)
def deny_network(monkeypatch):
    def deny(*args, **kwargs):
        raise AssertionError("i3_a4_preflight_external_network_forbidden")
    monkeypatch.setattr(socket.socket, "connect", deny)
    monkeypatch.setattr(socket, "create_connection", deny)


def test_preflight_validator_accepts_current_nonproduction_state():
    record = preflight.validate()
    assert record["status"] == "PREFLIGHT_PASS_WITH_EXPLICIT_DESIGN_BLOCKERS"
    assert record["preflight_market_gets"] == {"TPEX": 0, "TWSE": 0, "TAIFEX": 0, "other": 0}


def test_recommended_topology_preserves_dual_market_bounded_semantics():
    record = json.loads((preflight.ROOT / preflight.PREFLIGHT).read_text(encoding="utf-8"))
    topology = record["recommended_topology"]
    assert topology["capability_id"] == preflight.CAPABILITY
    assert topology["executor_id"] == preflight.EXECUTOR
    assert topology["supported_markets"] == ["TWSE", "TPEX"]
    assert topology["metadata_registrations"] == 2
    assert topology["active_source_count_if_later_activated"] == 2
    assert topology["batching_scope"] == "same_market"
    assert topology["same_market_max_acquisitions"] == 1
    assert topology["maximum_unique_market_acquisitions"] == 2
    assert topology["production_retry_count"] == 0
    assert topology["raw_payload_persistence"] == "FORBIDDEN"
def test_preflight_does_not_smuggle_a3_retry_policy_into_production():
    record = json.loads((preflight.ROOT / preflight.PREFLIGHT).read_text(encoding="utf-8"))
    assert record["recommended_topology"]["production_retry_count"] == 0
    assert record["a3_retry_policy_disposition"] == (
        "ACCEPTANCE_RUN_ONLY_NOT_PRODUCTION_AUTHORITY"
    )


def test_twse_date_binding_is_an_explicit_activation_blocker():
    record = json.loads((preflight.ROOT / preflight.PREFLIGHT).read_text(encoding="utf-8"))
    gap = record["design_gaps"]["twse_source_date_binding"]
    assert gap["frozen_contract_requires_explicit_date"] is True
    assert gap["automatic_previous_trading_day_fallback_allowed"] is False
    assert gap["calendar_today_implies_current_allowed"] is False
    assert gap["current_public_request_carries_source_date"] is False
    assert gap["decision_required_before_activation"] is True


def test_public_v3_gap_is_inventory_only_not_implementation():
    record = json.loads((preflight.ROOT / preflight.PREFLIGHT).read_text(encoding="utf-8"))
    gap = record["design_gaps"]["public_v3"]
    assert gap["request_v3_supported"] is False
    assert gap["result_v3_typed_projection_supported"] is False
    assert gap["audit_v3_typed_reference_supported"] is False
    assert gap["implementation_authorized_in_this_preflight"] is False


def test_rollback_target_is_exact_post_a3_merge_main():
    record = json.loads((preflight.ROOT / preflight.PREFLIGHT).read_text(encoding="utf-8"))
    rollback = record["rollback_contract"]
    assert rollback["rollback_target_commit"] == preflight.BASELINE
    assert rollback["rollback_target_tree"] == preflight.BASELINE_TREE
    assert rollback["expected_i3_after_rollback"] == {
        "active_sources": 0,
        "production_routes": 0,
        "executor_reachable": False,
        "public_v3_supported": False,
    }

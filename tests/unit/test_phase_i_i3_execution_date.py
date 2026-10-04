"""Governed I3 TWSE runtime date binding stays explicit, pure, and immutable."""
from datetime import date, datetime, timedelta

import pytest

from scripts.phase_i_i3_execution_date import bind_i3_source_trade_date, resolve_and_bind_i3_twse_plan, resolve_i3_twse_source_trade_date
from scripts.m8r_05b_03.registry import ExecutorMetadata
from scripts.m8r_05b_03.request_projection import build_execution_request_projection


def _calendar(start="2025-10-04", days=367, holidays=()):
    first = date.fromisoformat(start)
    return {"schema_version": "twse_trading_calendar.v1", "market": "TWSE",
            "source": {"source_url": "https://openapi.twse.com.tw/v1/holidaySchedule/holidaySchedule", "runtime_fetch": False},
            "dates": [{"date": (first + timedelta(days=i)).isoformat(),
                       "is_trading_day": (first + timedelta(days=i)).weekday() < 5 and (first + timedelta(days=i)).isoformat() not in holidays,
                       "is_weekend": (first + timedelta(days=i)).weekday() >= 5,
                       "reason": "scheduled holiday" if (first + timedelta(days=i)).isoformat() in holidays else "calendar"}
                      for i in range(days)]}


def _resolve(evaluation, cal=None, closure_complete=True):
    evaluation_day = date.fromisoformat(evaluation[:10])
    return resolve_i3_twse_source_trade_date(
        evaluation_time=evaluation, official_calendar=cal or _calendar(start=(evaluation_day - timedelta(days=366)).isoformat()),
        closure_events=[], calendar_authority_ref="official-calendar:test-v1",
        closure_authority_ref="closure-feed:test-v1", closure_authority_complete=closure_complete,
    )


def test_weekend_and_post_close_resolve_last_trading_session():
    result = _resolve("2026-10-04T21:00:00+08:00")
    assert result["resolved_source_trade_date"] == "2026-10-02"


def test_scheduled_holiday_is_skipped_by_supplied_official_calendar():
    cal = _calendar(start="2025-10-04", holidays={"2026-10-05"})
    result = _resolve("2026-10-05T21:00:00+08:00", cal)
    assert result["resolved_source_trade_date"] == "2026-10-02"


def test_incomplete_calendar_or_closure_authority_fails_closed():
    with pytest.raises(ValueError, match="coverage_incomplete"):
        _resolve("2026-10-04T21:00:00+08:00", _calendar(start="2026-01-01", days=30))
    with pytest.raises(ValueError, match="closure_coverage_unresolved"):
        _resolve("2026-10-04T21:00:00+08:00", closure_complete=False)


def test_date_is_bound_before_authorization_and_changes_plan_identity():
    base = {
        "schema_version": "unified_market_evidence_orchestration_plan.v1",
        "input_bindings": {"routing_matrix_version": "v3", "routing_matrix_hash": "a" * 64,
                           "handoff_contract_version": "h1", "handoff_contract_hash": "b" * 64},
        "plan_status": "plan_ready", "operations": [{"capability_id": "cash_institutional_flow_context", "market": "TWSE"}],
        "batch_groups": [], "accounting": {}, "blocked_operations": [], "omitted_optional_capabilities": [],
        "package_approval_requirements": {},
    }
    a = _resolve("2026-10-04T21:00:00+08:00")
    b = dict(a, resolved_source_trade_date="2026-10-01")
    bound_a = bind_i3_source_trade_date(base, a)
    bound_b = bind_i3_source_trade_date(base, b)
    assert bound_a["resolved_source_trade_date"] == "2026-10-02"
    assert bound_a["plan_hash"] != bound_b["plan_hash"]
    assert "resolved_source_trade_date" not in base


def test_unzoned_evaluation_time_is_rejected():
    with pytest.raises(ValueError, match="timezone_required"):
        _resolve("2026-10-04T21:00:00")


def test_execution_request_v3_carries_date_and_hashes_it():
    executor = ExecutorMetadata("phase_i_i3_cash_institutional_flow_context_executor",
        "cash_institutional_flow_context", "TWSE", ("equity",),
        "cash_institutional_flow_context_evidence.v2", True, True, 30, 50, "no_raw_payload_retention")
    operation = {"operation_id": "umeop-op-v1-" + "1" * 20,
                 "batch_group_id": "umeop-batch-v1-" + "2" * 20,
                 "canonical_target_ids": ["TWSE:1101"], "security_types": ["equity"], "parameters": {}}
    binding = {"capability_id": "cash_institutional_flow_context", "market": "TWSE",
               "executor_id": executor.executor_id}
    identity_args = {"authorization": {"authorization_id": "umea-v1-" + "3" * 20, "authorization_hash": "a" * 64},
                     "consumption_binding": {"consumption_binding_id": "umeacb-v1-" + "4" * 20,
                                              "consumption_binding_hash": "b" * 64},
                     "operation": operation, "binding": binding, "executor": executor, "network_authorized": True}
    date_a = _resolve("2026-10-04T21:00:00+08:00")
    date_b = dict(date_a, resolved_source_trade_date="2026-10-01")
    plan_base = {"schema_version": "unified_market_evidence_orchestration_plan.v1",
        "input_bindings": {"routing_matrix_version": "v3", "routing_matrix_hash": "a" * 64,
                           "handoff_contract_version": "h1", "handoff_contract_hash": "b" * 64},
        "plan_status": "plan_ready", "operations": [{"capability_id": "cash_institutional_flow_context", "market": "TWSE"}],
        "batch_groups": [], "accounting": {}, "blocked_operations": [], "omitted_optional_capabilities": [],
        "package_approval_requirements": {}}
    plan_a = bind_i3_source_trade_date(plan_base, date_a)
    plan_b = bind_i3_source_trade_date(plan_base, date_b)
    request_a, _ = build_execution_request_projection(plan=plan_a, **identity_args)
    request_b, _ = build_execution_request_projection(plan=plan_b, **identity_args)
    assert request_a["schema_version"] == "unified_market_evidence_execution_request.v3"
    assert request_a["parameters"] == {"resolved_source_trade_date": "2026-10-02"}
    assert request_a["execution_request_hash"] != request_b["execution_request_hash"]


def test_unified_v3_preview_accepts_i3_and_binds_date_without_authorizing_execution():
    from scripts.m8r_06_02_mode_b1_preview import build_mode_b1_preview_package, load_planning_authorities
    from server.services.unified_mode_a import validate_mode_a_request

    class PreviewSecurityMaster:
        pointer = {"index_path": "sealed/index.json", "manifest_path": "sealed/manifest.json",
                   "compact_index_sha256": "a" * 64, "compact_manifest_sha256": "b" * 64}

    request = {"schema_version": "unified_market_evidence_request.v3", "request_id": "i3-a4-preview",
               "execution_mode": "preview", "targets": [{"input": "2330", "market_hint": "TWSE"}],
               "data_needs": [{"type": "cash_institutional_flow_context", "priority": "required"}]}
    validation = validate_mode_a_request(request, allow_fixture_snapshot=True)
    package = build_mode_b1_preview_package(
        request, validation, PreviewSecurityMaster(), planning_timestamp="2026-10-04T12:00:00Z",
        authorities=load_planning_authorities(request["schema_version"]),
    )
    plan = package["orchestration_plan"]
    assert plan["plan_status"] == "plan_only_not_executable"
    assert plan["operations"][0]["network_required"] is False
    assert package["network_executed"] is False and package["authorization_created"] is False
    assert package["authorization_consumed"] is False and package["execution_performed"] is False
    bound = resolve_and_bind_i3_twse_plan(
        plan, evaluation_time="2026-10-04T21:00:00+08:00",
        official_calendar=_calendar(start=(date(2026, 10, 4) - timedelta(days=366)).isoformat()), closure_events=[],
        calendar_authority_ref="calendar-v1", closure_authority_ref="closures-v1",
        closure_authority_complete=True,
    )
    assert bound["resolved_source_trade_date"] == "2026-10-02"
    assert bound["plan_hash"] != plan["plan_hash"]
    assert bound["operations"][0]["executor_invocation_eligible"] is False

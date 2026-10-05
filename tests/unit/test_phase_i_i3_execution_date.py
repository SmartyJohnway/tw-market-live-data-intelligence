"""Governed I3 TWSE runtime date binding stays explicit, pure, and immutable."""
from datetime import date, datetime, timedelta

import pytest

from scripts.phase_i_i3_execution_date import bind_i3_source_trade_date, resolve_and_bind_i3_twse_plan, resolve_i3_twse_source_trade_date
from scripts.m8r_05b_03.registry import ExecutorMetadata
from scripts.m8r_05b_03.request_projection import build_execution_request_projection


def _calendar(start="2026-01-01", days=None, holidays=(), omit=()):
    first = date.fromisoformat(start)
    year = first.year
    first = date(year, 1, 1)
    days = days if days is not None else (date(year + 1, 1, 1) - first).days
    return {"schema_version": "twse_trading_calendar.v1", "market": "TWSE", "year": year,
            "source": {"source_url": "https://openapi.twse.com.tw/v1/holidaySchedule/holidaySchedule", "runtime_fetch": False},
            "dates": [{"date": (first + timedelta(days=i)).isoformat(),
                       "is_trading_day": (first + timedelta(days=i)).weekday() < 5 and (first + timedelta(days=i)).isoformat() not in holidays,
                       "is_weekend": (first + timedelta(days=i)).weekday() >= 5,
                       "reason": "scheduled holiday" if (first + timedelta(days=i)).isoformat() in holidays else "calendar"}
                      for i in range(days) if (first + timedelta(days=i)).isoformat() not in omit]}


def _resolve(evaluation, cal=None, closure_complete=True):
    evaluation_day = date.fromisoformat(evaluation[:10])
    calendar = cal or _calendar(start=evaluation_day.isoformat())
    if evaluation_day.month == 1 and evaluation_day.day <= 2 and evaluation_day.year > 1900 and cal is None:
        calendar = [_calendar(start=f"{evaluation_day.year - 1}-01-01"), _calendar(start=f"{evaluation_day.year}-01-01")]
    return resolve_i3_twse_source_trade_date(
        evaluation_time=evaluation, official_calendar=calendar,
        closure_events=[], calendar_authority_ref="official-calendar:test-v1",
        closure_authority_ref="closure-feed:test-v1", closure_authority_complete=closure_complete,
    )


def test_weekend_and_post_close_resolve_last_trading_session():
    result = _resolve("2026-10-04T21:00:00+08:00")
    assert result["resolved_source_trade_date"] == "2026-10-02"


def test_scheduled_holiday_is_skipped_by_supplied_official_calendar():
    cal = _calendar(start="2026-01-01", holidays={"2026-10-05"})
    result = _resolve("2026-10-05T21:00:00+08:00", cal)
    assert result["resolved_source_trade_date"] == "2026-10-02"


def test_incomplete_calendar_or_closure_authority_fails_closed():
    with pytest.raises(ValueError, match="coverage_incomplete"):
        _resolve("2026-10-04T21:00:00+08:00", _calendar(start="2026-01-01", days=30))
    with pytest.raises(ValueError, match="closure_coverage_unresolved"):
        _resolve("2026-10-04T21:00:00+08:00", closure_complete=False)


def test_canonical_annual_calendar_artifacts_resolve_across_new_year():
    # Jan 1 and Jan 2 are scheduled non-trading days; resolution traverses
    # into the prior annual artifact and stops at Dec 31.
    prior = _calendar("2025-01-01", holidays={"2025-12-31"})
    current = _calendar("2026-01-01", holidays={"2026-01-01", "2026-01-02"})
    prior["dates"][-1]["is_trading_day"] = True
    for evaluation in ("2026-01-01T21:00:00+08:00", "2026-01-02T21:00:00+08:00"):
        result = resolve_i3_twse_source_trade_date(evaluation_time=evaluation,
            official_calendar=[prior, current], closure_events=[], calendar_authority_ref="annual:2025-2026",
            closure_authority_ref="closure:v1", closure_authority_complete=True)
        assert result["resolved_source_trade_date"] == "2025-12-31"


def test_first_trading_day_after_new_year_resolves_itself_after_cutoff():
    cal = [_calendar("2025-01-01"), _calendar("2026-01-01", holidays={"2026-01-01"})]
    result = resolve_i3_twse_source_trade_date(evaluation_time="2026-01-02T20:01:00+08:00",
        official_calendar=cal, closure_events=[], calendar_authority_ref="annual:pair",
        closure_authority_ref="closure:v1", closure_authority_complete=True)
    assert result["resolved_source_trade_date"] == "2026-01-02"


def test_weekend_and_scheduled_holiday_cross_year_and_december_31():
    prior = _calendar("2025-01-01")
    current = _calendar("2026-01-01", holidays={"2026-01-01", "2026-01-02"})
    prior["dates"][-1]["is_trading_day"] = True
    for evaluation in ("2026-01-03T21:00:00+08:00", "2026-01-01T21:00:00+08:00"):
        result = resolve_i3_twse_source_trade_date(evaluation_time=evaluation,
            official_calendar=[prior, current], closure_events=[], calendar_authority_ref="annual:pair",
            closure_authority_ref="closure:v1", closure_authority_complete=True)
        assert result["resolved_source_trade_date"] == "2025-12-31"
    dec31 = resolve_i3_twse_source_trade_date(evaluation_time="2025-12-31T21:00:00+08:00",
        official_calendar=prior, closure_events=[], calendar_authority_ref="annual:2025",
        closure_authority_ref="closure:v1", closure_authority_complete=True)
    assert dec31["resolved_source_trade_date"] == "2025-12-31"


def test_missing_inspected_prior_year_day_fails_but_irrelevant_gap_does_not():
    prior = _calendar("2025-01-01", omit={"2025-12-31"})
    current = _calendar("2026-01-01", holidays={"2026-01-01"})
    with pytest.raises(ValueError, match="coverage_incomplete"):
        resolve_i3_twse_source_trade_date(evaluation_time="2026-01-01T21:00:00+08:00",
            official_calendar=[prior, current], closure_events=[], calendar_authority_ref="annual:pair",
            closure_authority_ref="closure:v1", closure_authority_complete=True)
    prior = _calendar("2025-01-01", omit={"2025-07-01"})
    current = _calendar("2026-01-01")
    result = resolve_i3_twse_source_trade_date(evaluation_time="2026-01-05T21:00:00+08:00",
        official_calendar=[prior, current], closure_events=[], calendar_authority_ref="annual:pair",
        closure_authority_ref="closure:v1", closure_authority_complete=True)
    assert result["resolved_source_trade_date"] == "2026-01-05"


@pytest.mark.parametrize("mutation,code", [
    ("duplicate", "duplicate_or_invalid_dates"),
    ("wrong_year", "year_membership_invalid"),
    ("invalid_status", "status_invalid"),
    ("invalid_authority", "authority_invalid"),
])
def test_annual_calendar_artifact_validation_fails_closed(mutation, code):
    cal = _calendar("2026-01-01")
    if mutation == "duplicate":
        cal["dates"].append(dict(cal["dates"][0]))
    elif mutation == "wrong_year":
        cal["dates"][0]["date"] = "2025-12-31"
    elif mutation == "invalid_status":
        cal["dates"][0]["is_trading_day"] = 1
    else:
        cal["source"]["runtime_fetch"] = True
    with pytest.raises(ValueError, match=code):
        resolve_i3_twse_source_trade_date(evaluation_time="2026-01-01T21:00:00+08:00",
            official_calendar=cal, closure_events=[], calendar_authority_ref="annual:2026",
            closure_authority_ref="closure:v1", closure_authority_complete=True)


def test_conflicting_duplicate_date_across_annual_inputs_fails_closed():
    first = _calendar("2026-01-01")
    second = _calendar("2026-01-01")
    second["dates"][0]["is_trading_day"] = not first["dates"][0]["is_trading_day"]
    with pytest.raises(ValueError, match="conflicting_duplicate_date"):
        resolve_i3_twse_source_trade_date(evaluation_time="2026-01-01T21:00:00+08:00",
            official_calendar=[first, second], closure_events=[], calendar_authority_ref="annual:dupe",
            closure_authority_ref="closure:v1", closure_authority_complete=True)


def test_canonical_annual_calendar_builder_artifact_is_directly_usable():
    from scripts.twse_trading_calendar import build_twse_trading_calendar_from_holiday_schedule
    annual = build_twse_trading_calendar_from_holiday_schedule(
        year=2026, holiday_schedule_records=[], generated_at_utc="2026-01-01T00:00:00Z")
    resolved = resolve_i3_twse_source_trade_date(evaluation_time="2026-10-04T21:00:00+08:00",
        official_calendar=annual, closure_events=[], calendar_authority_ref="canonical:2026",
        closure_authority_ref="closure:v1", closure_authority_complete=True)
    assert resolved["resolved_source_trade_date"] == "2026-10-02"


def test_dormant_candidate_pipeline_binds_date_before_authorization_and_request(monkeypatch):
    from scripts.phase_i_i3_dormant_orchestration import (
        build_dormant_i3_candidate_preview, prepare_dormant_i3_execution,
    )
    from scripts.twse_trading_calendar import build_twse_trading_calendar_from_holiday_schedule
    from server.services.unified_mode_a import validate_mode_a_request

    class PreviewSecurityMaster:
        pointer = {"index_path": "sealed/index.json", "manifest_path": "sealed/manifest.json",
                   "compact_index_sha256": "a" * 64, "compact_manifest_sha256": "b" * 64}

    request = {"schema_version": "unified_market_evidence_request.v3", "request_id": "i3-r1-preauth",
               "execution_mode": "preview", "targets": [{"input": "2330", "market_hint": "TWSE"}],
               "data_needs": [{"type": "cash_institutional_flow_context", "priority": "required"}]}
    validation = validate_mode_a_request(request, allow_fixture_snapshot=True)
    package = build_dormant_i3_candidate_preview(request, validation, PreviewSecurityMaster(),
        planning_timestamp="2026-10-05T12:00:00Z")
    calendar = build_twse_trading_calendar_from_holiday_schedule(year=2026,
        holiday_schedule_records=[], generated_at_utc="2026-01-01T00:00:00Z")
    common = {"official_calendar": calendar, "closure_events": [], "calendar_authority_ref": "calendar:2026",
              "closure_authority_ref": "closures:2026", "closure_authority_complete": True,
              "owner_identity_reference": "offline-test-owner", "owner_review_reference": "offline-test"}
    before_close = prepare_dormant_i3_execution(package, evaluation_time="2026-10-05T19:00:00+08:00", **common)
    after_close = prepare_dormant_i3_execution(package, evaluation_time="2026-10-05T21:00:00+08:00", **common)
    assert before_close["plan"]["resolved_source_trade_date"] == "2026-10-02"
    assert after_close["plan"]["resolved_source_trade_date"] == "2026-10-05"
    assert before_close["plan"]["plan_hash"] != after_close["plan"]["plan_hash"]
    assert before_close["authorization"]["authorization_hash"] != after_close["authorization"]["authorization_hash"]
    req_a, req_b = before_close["execution_requests"][0], after_close["execution_requests"][0]
    assert req_a["parameters"] == {"resolved_source_trade_date": "2026-10-02"}
    assert req_b["parameters"] == {"resolved_source_trade_date": "2026-10-05"}
    assert req_a["execution_request_hash"] != req_b["execution_request_hash"]
    assert req_a["execution_request_id"] != req_b["execution_request_id"]
    assert before_close["network_dispatched"] is after_close["network_dispatched"] is False


def test_dormant_candidate_date_failure_prevents_authorization_and_request(monkeypatch):
    from scripts.phase_i_i3_dormant_orchestration import (
        build_dormant_i3_candidate_preview, prepare_dormant_i3_execution,
    )
    from server.services.unified_mode_a import validate_mode_a_request
    import scripts.phase_i_i3_dormant_orchestration as orchestration

    class PreviewSecurityMaster:
        pointer = {"index_path": "sealed/index.json", "manifest_path": "sealed/manifest.json",
                   "compact_index_sha256": "a" * 64, "compact_manifest_sha256": "b" * 64}
    request = {"schema_version": "unified_market_evidence_request.v3", "request_id": "i3-r1-fail-closed",
               "execution_mode": "preview", "targets": [{"input": "2330", "market_hint": "TWSE"}],
               "data_needs": [{"type": "cash_institutional_flow_context", "priority": "required"}]}
    package = build_dormant_i3_candidate_preview(request, validate_mode_a_request(request, allow_fixture_snapshot=True),
        PreviewSecurityMaster(), planning_timestamp="2026-10-05T12:00:00Z")
    calls = []
    monkeypatch.setattr(orchestration, "build_execution_authorization", lambda *_a, **_k: calls.append("authorization"))
    with pytest.raises(ValueError, match="date_authority|required|coverage_incomplete"):
        prepare_dormant_i3_execution(package, evaluation_time="2026-10-05T21:00:00+08:00",
            official_calendar=None, closure_events=None, calendar_authority_ref=None,
            closure_authority_ref=None, closure_authority_complete=False,
            owner_identity_reference="test", owner_review_reference="test")
    assert calls == []


def test_dormant_tpex_only_candidate_skips_twse_date_authority(monkeypatch):
    from scripts.phase_i_i3_dormant_orchestration import (
        build_dormant_i3_candidate_preview, prepare_dormant_i3_execution,
    )
    from server.services.unified_mode_a import validate_mode_a_request
    import scripts.phase_i_i3_dormant_orchestration as orchestration

    class PreviewSecurityMaster:
        pointer = {"index_path": "sealed/index.json", "manifest_path": "sealed/manifest.json",
                   "compact_index_sha256": "a" * 64, "compact_manifest_sha256": "b" * 64}
    request = {"schema_version": "unified_market_evidence_request.v3", "request_id": "i3-r1-tpex-only",
               "execution_mode": "preview", "targets": [{"input": "6488", "market_hint": "TPEX"}],
               "data_needs": [{"type": "cash_institutional_flow_context", "priority": "required"}]}
    package = build_dormant_i3_candidate_preview(request, validate_mode_a_request(request, allow_fixture_snapshot=True),
        PreviewSecurityMaster(), planning_timestamp="2026-10-05T12:00:00Z")
    monkeypatch.setattr(orchestration, "resolve_and_bind_i3_twse_plan",
                        lambda *_a, **_k: pytest.fail("TPEX-only request must not resolve a TWSE date"))
    prepared = prepare_dormant_i3_execution(package, evaluation_time="2026-10-05T12:00:00+08:00",
        official_calendar=None, closure_events=None, calendar_authority_ref=None,
        closure_authority_ref=None, closure_authority_complete=False,
        owner_identity_reference="offline-test", owner_review_reference="offline-test")
    assert prepared["execution_requests"][0]["market"] == "TPEX"
    assert prepared["execution_requests"][0]["parameters"] == {}


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
        official_calendar=[_calendar("2025-01-01"), _calendar("2026-01-01")], closure_events=[],
        calendar_authority_ref="calendar-v1", closure_authority_ref="closures-v1",
        closure_authority_complete=True,
    )
    assert bound["resolved_source_trade_date"] == "2026-10-02"
    assert bound["plan_hash"] != plan["plan_hash"]
    assert bound["operations"][0]["executor_invocation_eligible"] is False

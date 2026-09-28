from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

import scripts.m8r_06_03_production_adapter as production
from scripts.m8r_05b_03.dispatch import (
    DispatchRuntimeContext,
    dispatch_prepared,
    prepare_dispatch,
)
from scripts.m8r_05b_03.registry import ExecutorMetadataRegistry
from server.services.phase_h_h3_twse_stock_day_adapter import (
    SOURCE_CONTRACT_ID,
    SOURCE_FAMILY,
    TWSEStockDayResult,
)


ROOT = Path(__file__).resolve().parents[2]
TARGET = "TWSE:1423"
EXECUTOR = "phase_h_h3_twse_recent_performance_executor"
FIXED_TIMESTAMP = datetime(2025, 3, 10, 8, 0, tzinfo=timezone.utc)


class FixedDateTime(datetime):
    clock_reads = 0

    @classmethod
    def now(cls, tz=None):
        cls.clock_reads += 1
        return FIXED_TIMESTAMP.astimezone(tz or timezone.utc)


def _request(lookback: int = 1) -> dict:
    operation_id = "umeop-op-v1-" + "a" * 20
    return {
        "schema_version": "unified_market_evidence_execution_request.v2",
        "execution_request_id": "umereq-v2-" + "b" * 20,
        "execution_request_hash": "b" * 64,
        "operation_id": operation_id,
        "batch_group_id": "umeop-batch-v1-" + "c" * 20,
        "plan_id": "plan-h3-fixture",
        "plan_hash": "d" * 64,
        "authorization_id": "umea-v1-" + "e" * 20,
        "authorization_hash": "e" * 64,
        "consumption_binding_id": "umeacb-v1-" + "f" * 20,
        "consumption_binding_hash": "f" * 64,
        "market": "TWSE",
        "approved_security_identifiers": [TARGET],
        "approved_security_types": ["equity"],
        "capability_id": "recent_performance",
        "executor_id": EXECUTOR,
        "requested_fields": [],
        "currentness_requirement": None,
        "maximum_records": 1,
        "timeout_seconds": 15,
        "network_authorized": True,
        "relative_contained_output_path": f"operations/{operation_id}.execution-request.json",
        "parameters": {"lookback_trading_days": lookback},
    }


def _observation(day: str, stamp: str, *, close: float | None = None) -> dict:
    return {
        "canonical_target_id": TARGET,
        "market": "TWSE",
        "security_code": "1423",
        "trade_date": day,
        "close": close if close is not None else float(day[-2:]) + 30.0,
        "volume": 1000 + int(day[-2:]),
        "source_family": SOURCE_FAMILY,
        "source_contract_id": SOURCE_CONTRACT_ID,
        "retrieved_at": stamp,
        "citation_ids": [f"synthetic:{day}"],
    }


def _source_result(month: str, stamp: str, observations: list[dict]) -> TWSEStockDayResult:
    return TWSEStockDayResult(
        status="available" if observations else "no_evidence_in_covered_scope",
        requested_month=month,
        requested_url=f"https://www.twse.com.tw/exchangeReport/STOCK_DAY?month={month}",
        effective_url=f"https://www.twse.com.tw/exchangeReport/STOCK_DAY?month={month}",
        http_status=200,
        content_type="text/html;charset=utf-8",
        retrieved_at=stamp,
        response_byte_count=100,
        response_sha256=(month.replace("-", "") + "0" * 58)[:64],
        observations=tuple(observations),
    )


def _dispatch(request: dict, tmp_path: Path) -> dict:
    metadata = production.load_production_executor_metadata()
    registry = production.build_production_runtime_adapter_registry()
    binding = {
        "operation_id": request["operation_id"],
        "executor_id": EXECUTOR,
        "capability_id": "recent_performance",
        "market": "TWSE",
        "security_types": ["equity"],
        "expected_evidence_contract": "recent_performance_evidence.v1",
    }
    preflight = {
        "approved_operation_order": [request["operation_id"]],
        "bounded_execution_requests": [request],
        "resolved_operation_bindings": {request["operation_id"]: binding},
        "resolved_batch_bindings": {},
    }
    prepared = prepare_dispatch(
        preflight,
        ExecutorMetadataRegistry.from_json(metadata),
        registry,
        mode="execute-approved",
    )
    return dispatch_prepared(
        prepared,
        governed_output_root=str(tmp_path),
        mode="execute-approved",
    )[0]


@pytest.fixture
def fake_month_source(monkeypatch):
    FixedDateTime.clock_reads = 0
    monkeypatch.setattr(production, "datetime", FixedDateTime)
    calls: list[tuple[str, str, float, int, str]] = []

    def fetch(**kwargs):
        month = kwargs["requested_month"]
        stamp = kwargs["retrieved_at"]
        calls.append((month, kwargs["ssl_policy"], kwargs["timeout_seconds"], kwargs["max_response_bytes"], stamp))
        if month == "2025-03":
            rows = [_observation("2025-03-07", stamp), _observation("2025-03-10", stamp), _observation("2025-03-12", stamp)]
        elif month == "2025-02":
            rows = []
            for day in range(1, 29):
                value = date(2025, 2, day)
                if value.weekday() < 5:
                    rows.append(_observation(value.isoformat(), stamp))
        elif month == "2025-01":
            rows = [_observation("2025-01-31", stamp)]
        else:
            rows = []
        return _source_result(month, stamp, rows)

    monkeypatch.setattr(production, "fetch_twse_stock_day_month", fetch)
    return calls


def test_h3_registry_is_exact_twse_single_target_route():
    metadata = production.load_production_executor_metadata()
    registry = production.build_production_runtime_adapter_registry()
    route = registry.get_route(EXECUTOR, "recent_performance", "TWSE")
    assert route is not None
    assert route.fake_adapter is False
    assert route.network_required is True
    assert route.batch_adapter is None
    assert route.expected_evidence_contract == "recent_performance_evidence.v1"
    assert not any(item["market"] == "TPEX" and item["capability_id"] == "recent_performance" for item in metadata["executors"])
    inventory = json.loads((ROOT / "docs/data_capabilities/m8r_05b_existing_orchestrator_disposition.json").read_text(encoding="utf-8"))
    disposition = next(item for item in inventory["surfaces"] if item["surface_id"] == EXECUTOR)
    assert disposition["reusable_for_05b"] is True
    assert disposition["disposition"] == "adapter_required"
    assert disposition["supported_markets"] == ["TWSE"]
    assert disposition["supported_capabilities"] == ["recent_performance"]


@pytest.mark.parametrize("bad", [0, 21, True, False, 5.0, "5", {}, {"lookback_trading_days": 5, "extra": 1}])
def test_h3_rejects_invalid_or_non_v2_parameters_before_source_call(tmp_path, monkeypatch, bad):
    from scripts.m8r_05b_03.errors import OrchestrationError

    calls = []
    monkeypatch.setattr(production, "fetch_twse_stock_day_month", lambda **kwargs: calls.append(kwargs))
    request = _request()
    request["parameters"] = bad if isinstance(bad, dict) else {"lookback_trading_days": bad}
    with pytest.raises(OrchestrationError, match="execution_request_parameters_invalid"):
        production.production_operation_adapter(request, DispatchRuntimeContext(str(tmp_path), "execute-approved"))
    assert calls == []


def test_h3_exact_target_and_authorized_execution_are_required_before_network(tmp_path, monkeypatch):
    from scripts.m8r_05b_03.errors import OrchestrationError

    calls = []
    monkeypatch.setattr(production, "fetch_twse_stock_day_month", lambda **kwargs: calls.append(kwargs))
    request = _request()
    request["approved_security_identifiers"] = ["TWSE:1423", "TWSE:2330"]
    with pytest.raises(OrchestrationError, match="approved_target_count_invalid"):
        production.production_operation_adapter(request, DispatchRuntimeContext(str(tmp_path), "execute-approved"))
    request = _request()
    request["market"] = "TPEX"
    request["approved_security_identifiers"] = ["TPEX:6488"]
    with pytest.raises(OrchestrationError, match="unsupported_production_route"):
        production.production_operation_adapter(request, DispatchRuntimeContext(str(tmp_path), "execute-approved"))
    request = _request()
    request["network_authorized"] = False
    with pytest.raises(OrchestrationError, match="network_required_not_authorized"):
        production.production_operation_adapter(request, DispatchRuntimeContext(str(tmp_path), "execute-approved"))
    assert calls == []


def test_h3_request_v2_dispatch_reuses_governed_end_month_and_preserves_evidence_lineage(
    tmp_path, fake_month_source
):
    request = _request(lookback=1)
    outcome = _dispatch(request, tmp_path)
    assert outcome["schema_version"] == "unified_market_evidence_operation_result.v2"
    assert outcome["execution_request_id"] == request["execution_request_id"]
    assert outcome["execution_request_hash"] == request["execution_request_hash"]
    assert outcome["status"] == "succeeded"
    assert fake_month_source == [("2025-03", "compatibility", 15, 2 * 1024 * 1024, "2025-03-10T08:00:00Z")]
    assert FixedDateTime.clock_reads == 1

    primary = next(item for item in outcome["evidence_artifacts"] if item["artifact_role"] == "primary_evidence")
    sidecar = next(item for item in outcome["evidence_artifacts"] if item["artifact_role"] == "supporting_governance")
    evidence = json.loads((tmp_path / primary["relative_path"]).read_text(encoding="utf-8"))
    governance = json.loads((tmp_path / sidecar["relative_path"]).read_text(encoding="utf-8"))
    assert evidence["coverage_status"] == "complete"
    assert evidence["requested_observations"] == 1
    assert evidence["valid_observation_count"] == 1
    assert evidence["governed_end_observation"]["trade_date"] == "2025-03-10"
    assert [row["trade_date"] for row in evidence["observations"]] == ["2025-03-07"]
    assert evidence["baselines"][0]["required_distinct_close_count"] == 2
    assert evidence["baselines"][0]["actual_distinct_close_count"] == 2
    assert evidence["baselines"][0]["return_basis"] == "raw_unadjusted_close_to_close"
    assert evidence["recent_close_range"]["range_basis"] == "completed_session_closing_price"
    assert evidence["volume_context"] == {
        "current_volume_basis": "completed_session",
        "historical_average_basis": "completed_official_sessions",
        "comparison_alignment": "unavailable",
        "historical_average_volume": None,
    }
    assert governance["attempts"][0]["activation_state"] == "active"
    assert governance["attempts"][0]["license_authority"] is None
    assert governance["attempts"][0]["coverage_result"] == "complete"
    assert governance["attempts"][0]["citation_ids"] == evidence["citation_ids"]
    assert "36.65" not in json.dumps(evidence)


def test_h3_twenty_day_dispatch_uses_minimal_months_and_n_plus_one(tmp_path, fake_month_source):
    request = _request(lookback=20)
    outcome = _dispatch(request, tmp_path)
    assert outcome["status"] == "succeeded"
    assert [call[0] for call in fake_month_source] == ["2025-03", "2025-02"]
    assert len({call[0] for call in fake_month_source}) == 2
    assert FixedDateTime.clock_reads == 1
    primary = next(item for item in outcome["evidence_artifacts"] if item["artifact_role"] == "primary_evidence")
    evidence = json.loads((tmp_path / primary["relative_path"]).read_text(encoding="utf-8"))
    assert evidence["coverage_status"] == "complete"
    assert evidence["requested_observations"] == 20
    assert evidence["valid_observation_count"] == 20
    assert evidence["missing_observation_count"] == 0
    assert evidence["baselines"][0]["required_distinct_close_count"] == 21
    assert evidence["baselines"][0]["actual_distinct_close_count"] == 21
    assert evidence["baselines"][0]["end_observation_date"] == "2025-03-10"
    assert all(row["trade_date"] < "2025-03-10" for row in evidence["observations"])
    assert evidence["governed_end_observation"]["trade_date"] == "2025-03-10"


def test_h3_current_date_live_telemetry_writes_without_escaping_adapter(tmp_path, monkeypatch):
    """Exercise the acceptance-only metadata write at the failed run's 2026-09 shape."""
    stamp = datetime(2026, 9, 28, 9, 23, 30, tzinfo=timezone.utc)

    class CurrentDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return stamp.astimezone(tz or timezone.utc)

    calls = []

    def fixture_fetch(**kwargs):
        month = kwargs["requested_month"]
        retrieved = kwargs["retrieved_at"]
        calls.append(month)
        year, month_number = (int(value) for value in month.split("-"))
        first = date(year, month_number, 1)
        next_month = date(year + (month_number == 12), 1 if month_number == 12 else month_number + 1, 1)
        observations = []
        day = first
        while day < next_month:
            if day.weekday() < 5 and (month != "2026-09" or day.day <= 28):
                observations.append(_observation(day.isoformat(), retrieved))
            day += timedelta(days=1)
        return _source_result(month, retrieved, observations)

    monkeypatch.setattr(production, "datetime", CurrentDateTime)
    monkeypatch.setattr(production, "fetch_twse_stock_day_month", fixture_fetch)
    monkeypatch.setenv("H3_LIVE_ACCEPTANCE_TELEMETRY", "YES")

    request = _request(lookback=20)
    outcome = production.production_operation_adapter(
        request,
        DispatchRuntimeContext(str(tmp_path), "execute-approved"),
    )

    assert outcome["schema_version"] == "unified_market_evidence_operation_result.v2"
    assert outcome["status"] == "succeeded"
    assert outcome["execution_request_id"] == request["execution_request_id"]
    assert outcome["execution_request_hash"] == request["execution_request_hash"]
    assert calls == ["2026-09", "2026-08"]
    telemetry = json.loads((tmp_path / "h3-live-transport-summary.json").read_text(encoding="utf-8"))
    assert telemetry["execution_timestamp"] == "2026-09-28T09:23:30Z"
    assert telemetry["requested_months"] == ["2026-09", "2026-08"]
    assert telemetry["network_request_count"] == 2
    assert telemetry["retry_count"] == 0
    assert telemetry["walker"]["status"] == "available"
    assert telemetry["walker"]["valid_lookback_count"] == 20
    assert telemetry["network_request_count"] <= 3


def test_h3_transport_failure_replay_returns_governed_source_failure_without_exception(tmp_path, monkeypatch):
    real_fetch = production.fetch_twse_stock_day_month
    calls = []

    def offline_transport_failure(*args, **kwargs):
        calls.append((args, kwargs))
        raise OSError("FOR_FORENSICS_NO_NETWORK")

    def offline_fetch(**kwargs):
        return real_fetch(**kwargs, http_get=offline_transport_failure)

    monkeypatch.setattr(production, "fetch_twse_stock_day_month", offline_fetch)
    outcome = production.production_operation_adapter(
        _request(lookback=20),
        DispatchRuntimeContext(str(tmp_path), "execute-approved"),
    )

    assert len(calls) == 1
    assert outcome["schema_version"] == "unified_market_evidence_operation_result.v2"
    assert outcome["status"] == "failed"
    assert outcome["error_code"] == "source_failed"
    primary = next(item for item in outcome["evidence_artifacts"] if item["artifact_role"] == "primary_evidence")
    evidence = json.loads((tmp_path / primary["relative_path"]).read_text(encoding="utf-8"))
    assert evidence["coverage_status"] == "source_failed"
    assert evidence["caveats"] == ["source_failed:transport_failure"]


def test_h3_binding_failure_replay_stays_binding_failed_v2(tmp_path, monkeypatch):
    def binding_failure(**kwargs):
        return TWSEStockDayResult(
            status="binding_failed",
            requested_month=kwargs["requested_month"],
            retrieved_at=kwargs["retrieved_at"],
            error_code="binding_failed:report_heading_target_or_month_mismatch",
        )

    monkeypatch.setattr(production, "fetch_twse_stock_day_month", binding_failure)
    outcome = production.production_operation_adapter(
        _request(lookback=20),
        DispatchRuntimeContext(str(tmp_path), "execute-approved"),
    )

    assert outcome["schema_version"] == "unified_market_evidence_operation_result.v2"
    assert outcome["status"] == "failed"
    assert outcome["error_code"] == "binding_failed"
    primary = next(item for item in outcome["evidence_artifacts"] if item["artifact_role"] == "primary_evidence")
    evidence = json.loads((tmp_path / primary["relative_path"]).read_text(encoding="utf-8"))
    assert evidence["coverage_status"] == "binding_failed"


def test_h3_unavailable_and_insufficient_remain_succeeded_v2_outcomes(tmp_path, monkeypatch):
    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 9, 28, 9, 23, 30, tzinfo=timezone.utc).astimezone(tz or timezone.utc)

    monkeypatch.setattr(production, "datetime", FixedDateTime)

    def empty_month(**kwargs):
        return _source_result(kwargs["requested_month"], kwargs["retrieved_at"], [])

    monkeypatch.setattr(production, "fetch_twse_stock_day_month", empty_month)
    unavailable_root = tmp_path / "unavailable"
    unavailable = production.production_operation_adapter(
        _request(lookback=20),
        DispatchRuntimeContext(str(unavailable_root), "execute-approved"),
    )
    assert unavailable["schema_version"] == "unified_market_evidence_operation_result.v2"
    assert unavailable["status"] == "succeeded"
    unavailable_primary = next(item for item in unavailable["evidence_artifacts"] if item["artifact_role"] == "primary_evidence")
    unavailable_evidence = json.loads((unavailable_root / unavailable_primary["relative_path"]).read_text(encoding="utf-8"))
    assert unavailable_evidence["coverage_status"] == "unavailable"

    def sparse_month(**kwargs):
        month = kwargs["requested_month"]
        retrieved = kwargs["retrieved_at"]
        row_date = {"2026-09": "2026-09-28", "2026-08": "2026-08-31", "2026-07": "2026-07-31"}.get(month)
        rows = [_observation(row_date, retrieved)] if row_date else []
        return _source_result(month, retrieved, rows)

    monkeypatch.setattr(production, "fetch_twse_stock_day_month", sparse_month)
    insufficient_root = tmp_path / "insufficient"
    insufficient = production.production_operation_adapter(
        _request(lookback=20),
        DispatchRuntimeContext(str(insufficient_root), "execute-approved"),
    )
    assert insufficient["schema_version"] == "unified_market_evidence_operation_result.v2"
    assert insufficient["status"] == "succeeded"
    insufficient_primary = next(item for item in insufficient["evidence_artifacts"] if item["artifact_role"] == "primary_evidence")
    insufficient_evidence = json.loads((insufficient_root / insufficient_primary["relative_path"]).read_text(encoding="utf-8"))
    assert insufficient_evidence["coverage_status"] == "insufficient"


def test_h3_operation_result_v2_schema_and_active_sidecar_contract(tmp_path, fake_month_source):
    request = _request(1)
    outcome = _dispatch(request, tmp_path)
    schema = json.loads((ROOT / "schemas/unified_market_evidence_operation_result.v2.schema.json").read_text(encoding="utf-8"))
    assert not list(Draft202012Validator(schema).iter_errors(outcome))
    assert outcome["execution_request_id"] == request["execution_request_id"]
    assert outcome["execution_request_hash"] == request["execution_request_hash"]


@pytest.mark.parametrize(
    ("mutation", "expected_coverage"),
    [
        ("wrong_target", "binding_failed"),
        ("requested_month", "source_failed"),
        ("invalid_close", "source_failed"),
        ("invalid_source_family", "source_failed"),
        ("invalid_source_contract", "source_failed"),
        ("retrieved_at_mismatch", "source_failed"),
        ("conflicting_duplicate", "source_failed"),
    ],
)
def test_h3_normalized_source_drift_fails_closed_with_truthful_classification(
    tmp_path, monkeypatch, mutation, expected_coverage
):
    monkeypatch.setattr(production, "datetime", FixedDateTime)
    stamp = "2025-03-10T08:00:00Z"

    def fetch(**kwargs):
        row = _observation("2025-03-07", stamp)
        rows = [row]
        requested_month = kwargs["requested_month"]
        if mutation == "wrong_target":
            row["canonical_target_id"] = "TWSE:2330"
        elif mutation == "requested_month":
            requested_month = "2025-02"
        elif mutation == "invalid_close":
            row["close"] = float("nan")
        elif mutation == "invalid_source_family":
            row["source_family"] = "UNEXPECTED_SOURCE"
        elif mutation == "invalid_source_contract":
            row["source_contract_id"] = "UNEXPECTED_CONTRACT"
        elif mutation == "retrieved_at_mismatch":
            row["retrieved_at"] = "2025-03-09T08:00:00Z"
        elif mutation == "conflicting_duplicate":
            rows.append({**row, "close": row["close"] + 1.0})
        return _source_result(requested_month, stamp, rows)

    monkeypatch.setattr(production, "fetch_twse_stock_day_month", fetch)
    outcome = _dispatch(_request(5), tmp_path)
    assert outcome["status"] == "failed"
    primary = next(item for item in outcome["evidence_artifacts"] if item["artifact_role"] == "primary_evidence")
    evidence = json.loads((tmp_path / primary["relative_path"]).read_text(encoding="utf-8"))
    assert evidence["coverage_status"] == expected_coverage
    assert evidence["coverage_status"] not in {"unavailable", "insufficient", "complete", "partial"}


@pytest.mark.parametrize(("source_status", "expected"), [("source_failed", "source_failed"), ("binding_failed", "binding_failed")])
def test_h3_source_and_binding_failures_are_not_relabelled_as_coverage(
    tmp_path, monkeypatch, source_status, expected
):
    stamp = "2025-03-10T08:00:00Z"
    monkeypatch.setattr(production, "datetime", FixedDateTime)
    monkeypatch.setattr(
        production,
        "fetch_twse_stock_day_month",
        lambda **kwargs: TWSEStockDayResult(
            status=source_status,
            requested_month=kwargs["requested_month"],
            retrieved_at=stamp,
            error_code=f"{source_status}:fixture",
        ),
    )
    outcome = _dispatch(_request(5), tmp_path)
    assert outcome["status"] == "failed"
    primary = next(item for item in outcome["evidence_artifacts"] if item["artifact_role"] == "primary_evidence")
    evidence = json.loads((tmp_path / primary["relative_path"]).read_text(encoding="utf-8"))
    assert evidence["coverage_status"] == expected

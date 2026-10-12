from __future__ import annotations

import copy
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

import scripts.m8r_06_03_production_adapter as production
from scripts.m8r_05c.citation_builder import _build_citation_id, build_citation_index
from scripts.m8r_05c.evidence_projector import project_phase_h_typed_evidence
from scripts.m8r_05c.lineage_resolver import LineageMap, OperationBinding
from scripts.m8r_05c.artifact_loader import load_projection_inputs
from scripts.m8r_05c.lineage_resolver import build_lineage_map
from scripts.m8r_05c.result_builder import build_result
from scripts.m8r_05c.audit_package_builder import build_audit_package
from scripts.m8r_05b_03.orchestrator import execute_controlled_plan
from scripts.m8r_05b_03.receipt import bundle_relative_path, receipt_relative_path
from server.services import unified_mode_b2
from tests.unit.test_phase_h_h3_activation_candidate_preview import _production_preview, _request as _v3_request
from scripts.m8r_05b_03.dispatch import (
    DispatchRuntimeContext,
    dispatch_prepared,
    prepare_dispatch,
)
from scripts.m8r_05b_03.registry import ExecutorMetadataRegistry
from scripts.m8r_06_02_mode_b1_preview import build_mode_b1_preview_package
from scripts.m8r_05a_f3.request_intake import validate_unified_market_evidence_request
from server.unified_mcp.tool_contracts import build_tool_specs
from tests.unit.test_phase_h_h3_activation_candidate_preview import OfflineSecurityMaster
from server.services.unified_contract_versions import PREFERRED_REQUEST_SCHEMA_VERSION, REQUEST_SCHEMA_PATHS
from server.services.unified_mode_a import validate_mode_a_request
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


def test_h3_primary_citation_matches_v3_artifact_lineage(tmp_path, fake_month_source):
    """The typed citation must name the governed artifact, not a source month."""
    request = _request(lookback=1)
    outcome = _dispatch(request, tmp_path)
    primary, sidecar = outcome["evidence_artifacts"]
    primary_obj = json.loads((tmp_path / primary["relative_path"]).read_text(encoding="utf-8"))
    sidecar_obj = json.loads((tmp_path / sidecar["relative_path"]).read_text(encoding="utf-8"))
    binding = OperationBinding(
        operation_id=request["operation_id"],
        capability_id="recent_performance",
        executor_id=EXECUTOR,
        canonical_target_id=TARGET,
        requested_data_need="recent_performance",
        market="TWSE",
        status="succeeded",
        error_code=None,
        evidence_artifacts=[primary, sidecar],
        artifact_objects={primary["relative_path"]: primary_obj, sidecar["relative_path"]: sidecar_obj},
    )
    lineage = LineageMap(bindings={TARGET: {"recent_performance": binding}})
    inventory = [
        {key: artifact[key] for key in ("relative_path", "sha256", "schema_version", "byte_size", "item_count", "evidence_contract")}
        for artifact in (primary, sidecar)
    ]
    citations = build_citation_index(
        lineage, {"artifact_inventory": inventory, "finalized_at": "2025-03-10T08:00:00Z"},
        "unified_market_evidence_result.v3",
    )
    primary_citation = _build_citation_id(request["operation_id"], primary["relative_path"])
    target_citations = citations.target_need_citations[f"{TARGET}::recent_performance"]
    assert primary_obj["citation_ids"] == [primary_citation]
    assert set(primary_obj["citation_ids"]).issubset(target_citations)
    assert citations.all_citations[primary_citation].artifact_reference == primary["relative_path"]
    assert citations.all_citations[primary_citation].normalized_evidence_hash == primary["sha256"]
    assert project_phase_h_typed_evidence(
        binding, target_citations, "recent_performance_evidence.v1"
    ) == primary_obj
    assert sidecar_obj["attempts"][0]["citation_ids"] == [primary_citation]
    assert all(row["citation_ids"] == ["synthetic:2025-03-07"] for row in primary_obj["observations"])


def test_h3_producer_artifacts_project_through_real_receipt_bundle_and_v3(tmp_path, monkeypatch, fake_month_source):
    """Offline producer -> governed execution -> verified loader -> V3 Result/Audit."""
    request = _v3_request("TWSE", "1423") | {"execution_mode": "execute"}
    package = _production_preview(request, "TWSE", "1423")
    preview, plan = package["preview"], package["orchestration_plan"]
    assert preview["status"] == "ready_for_confirmation"
    monkeypatch.setattr(unified_mode_b2, "CONTROL_ROOT", tmp_path)
    monkeypatch.setattr(unified_mode_b2, "build_mode_b1_preview", lambda _request: package)
    monkeypatch.setattr(unified_mode_b2, "_utc_now", lambda: FIXED_TIMESTAMP)
    ticket = unified_mode_b2.build_mode_b2_authorization({
        "request": request,
        "expected_preview_id": preview["internal_execution_reference"]["preview_id"],
        "expected_plan_id": plan["plan_id"],
        "expected_plan_hash": plan["plan_hash"],
        "confirm_authorization": True,
        "owner_review_reference": "offline-h3-citation-regression",
    })
    root = tmp_path / ticket["authorization_id"]
    control = root / "control"
    artifacts = {name: json.loads((control / f"{name}.json").read_text(encoding="utf-8"))
                 for name in ("plan", "authorization", "consumption_binding", "unused_consumption_state", "preflight")}
    timestamp = "2025-03-10T08:00:00Z"
    execution = execute_controlled_plan(
        artifacts["plan"], artifacts["authorization"], artifacts["consumption_binding"],
        supplied_consumption_state=artifacts["unused_consumption_state"],
        accepted_preflight=artifacts["preflight"], evaluation_timestamp=timestamp,
        claim_created_at=timestamp, finalized_at=timestamp,
        executor_registry_metadata=production.load_production_executor_metadata(),
        runtime_adapter_registry=production.build_production_runtime_adapter_registry(),
        output_root=str(root), mode="execute-approved", confirm_execution=True,
        operator_confirmation_reference="offline-h3-citation-regression", confirm_network_execution=True,
    )
    assert fake_month_source
    outcome = execution["dispatch_outcomes"][0]
    assert outcome["schema_version"] == "unified_market_evidence_operation_result.v2"
    assert outcome["status"] == "succeeded"
    primary = next(item for item in outcome["evidence_artifacts"] if item["artifact_role"] == "primary_evidence")
    evidence = json.loads((root / primary["relative_path"]).read_text(encoding="utf-8"))
    canonical = _build_citation_id(outcome["operation_id"], primary["relative_path"])
    assert evidence["citation_ids"] == [canonical]
    assert evidence["governed_end_observation"]["citation_ids"] == ["synthetic:2025-03-10"]
    assert any(row["citation_ids"] == ["synthetic:2025-02-28"] for row in evidence["observations"])
    f3_path = tmp_path / "f3-validation.json"
    f3_path.write_text(json.dumps(package["validation"]), encoding="utf-8")
    auth_id = ticket["authorization_id"]
    inputs = load_projection_inputs(
        request_path=str(control / "request.json"), f3_validation_path=str(f3_path),
        plan_path=str(control / "plan.json"), authorization_path=str(control / "authorization.json"),
        consumption_binding_path=str(control / "consumption_binding.json"),
        claim_path=str(root / execution["claim_relative_path"]),
        receipt_path=str(root / receipt_relative_path(auth_id)),
        bundle_path=str(root / bundle_relative_path(auth_id)), artifact_root=str(root),
        calculated_at=timestamp,
    )
    lineage = build_lineage_map(inputs)
    citations = build_citation_index(lineage, inputs.bundle, "unified_market_evidence_result.v3")
    assert canonical in citations.target_need_citations[f"{TARGET}::recent_performance"]
    assert citations.all_citations[canonical].artifact_reference == primary["relative_path"]
    assert citations.all_citations[canonical].normalized_evidence_hash == primary["sha256"]
    citation_lineage = next(item for item in citations.audit_entries if item.citation_id == canonical)
    assert citation_lineage.operation_id == outcome["operation_id"]
    assert citation_lineage.artifact_relative_path == primary["relative_path"]
    assert citation_lineage.artifact_hash == primary["sha256"]
    assert citation_lineage.canonical_target_id == TARGET
    assert citation_lineage.requested_data_need == "recent_performance"
    result = build_result(inputs, output_schema_version="unified_market_evidence_result.v3")
    audit = build_audit_package(
        result, inputs, citations, "ai_context/unified_market_evidence_result.v3.json",
        output_schema_version="unified_market_evidence_audit_package.v3",
    )
    assert result["schema_version"] == "unified_market_evidence_result.v3"
    assert audit["schema_version"] == "unified_market_evidence_audit_package.v3"
    assert result["targets"][0]["evidence"]["recent_performance"] == evidence
    assert set(evidence["citation_ids"]).issubset(citations.all_citations)


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


def _h3_roll_004_local_evidence_hashes() -> dict[str, str]:
    package = ROOT / "data/phase_h_h3_live_acceptance/20260929T021651Z-bb11ec10/control/umea-v1-3821b18dce3d1915813c"
    paths = {
        "primary": package / "evidence/phase_h/h3/umeop-op-v1-c62377892aaac73a9431.json",
        "governance": package / "evidence/phase_h/governance/umeop-op-v1-c62377892aaac73a9431.json",
        "telemetry": package / "h3-live-transport-summary.json",
        "receipt": package / "receipts/umea-v1-3821b18dce3d1915813c.execution-receipt.json",
        "bundle": package / "bundles/umea-v1-3821b18dce3d1915813c.evidence-bundle.json",
        "result_v3": package / "ai_context/unified_market_evidence_result.v3.json",
        "audit_v3": package / "audit/unified_market_evidence_audit_package.v3.json",
        "claim": package / "claims/umea-v1-3821b18dce3d1915813c.consumption-record.json",
    }
    if not all(path.is_file() for path in paths.values()):
        return {}
    return {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in paths.items()}


def test_h0h_roll_004_simulates_h3_deactivation_without_mutating_authority_or_evidence():
    catalog_path = ROOT / "docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json"
    routing_path = ROOT / "docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json"
    authority_files_before = {
        path: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (catalog_path, routing_path)
    }
    evidence_before = _h3_roll_004_local_evidence_hashes()
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    routing = json.loads(routing_path.read_text(encoding="utf-8"))

    cap_before = next(item for item in catalog["data_need_capabilities"] if item["capability_id"] == "recent_performance")
    route_before = next(item for item in routing["routes"] if item["capability_id"] == "recent_performance")
    records_before = routing["phase_h_source_authority"]["records"]
    active_before = {
        item["source_id"]
        for item in records_before
        if item["activation_state"] == "active" and item["runtime_executable"] is True
    }
    assert cap_before["support_status"] == "runtime_executable"
    assert cap_before["runtime_executable"] is True
    assert cap_before["phase_h_activation_state"] == "selected_route_active"
    assert route_before["supported_markets"] == ["TWSE"]
    assert route_before["routing_status"] == "resolved"
    assert route_before["runtime_executable"] is True
    assert route_before["selected_executor_id"] == EXECUTOR
    assert route_before["network_required"] is True
    assert route_before["batching_scope"] == "none"
    assert catalog["phase_h_contract"]["active_phase_h_source_count"] == 5
    assert routing["phase_h_source_authority"]["active_source_count"] == 5
    assert active_before == {"H1-TPEX-ATTENTION-OPENAPI", "H1-TPEX-DISPOSITION-OPENAPI", "H1-TPEX-CHANGED-TRADING-OPENAPI", "H3-TWSE-DEFAULT-BOUNDED", "H2-TWSE-EXRIGHT-PRE-OPENAPI"}
    assert len(build_tool_specs()) == 6
    live_candidate_preview = _production_preview(_v3_request("TWSE", "1423"), "TWSE", "1423")
    candidate_operation = live_candidate_preview["orchestration_plan"]["operations"][0]
    assert live_candidate_preview["validation"]["validation_status"] == "valid"
    assert live_candidate_preview["validation"]["capability_results"][0]["status"] == "runtime_executable"
    assert live_candidate_preview["preview"]["status"] == "ready_for_confirmation"
    assert candidate_operation["operation_status"] == "executable_pending_approval"
    assert candidate_operation["executor_id"] == EXECUTOR
    assert candidate_operation["network_required"] is True

    h1_route_before = copy.deepcopy(next(item for item in routing["routes"] if item["capability_id"] == "trading_status_context"))
    h1_source_before = copy.deepcopy(next(item for item in records_before if item["source_id"] == "H1-TPEX-ATTENTION-OPENAPI"))
    h2_routes_before = copy.deepcopy([item for item in routing["routes"] if item["capability_id"] == "corporate_action_context"])
    h2_records_before = copy.deepcopy([item for item in records_before if item["source_id"].startswith("H2-")])
    h2_caps_before = copy.deepcopy([item for item in catalog["data_need_capabilities"] if item["capability_id"] == "corporate_action_context"])
    tpex_h3_before = copy.deepcopy(next(item for item in route_before["source_authority_states"] if item["market"] == "TPEX"))
    assert sum(item["activation_state"] == "active" and item["runtime_executable"] is True for item in h2_records_before) == 1
    assert next(item for item in h2_records_before if item["source_id"] == "H2-TWSE-EXRIGHT-PRE-OPENAPI")["activation_state"] == "active"
    assert all(item["activation_state"] != "active" and item["runtime_executable"] is False for item in h2_records_before if item["source_id"] != "H2-TWSE-EXRIGHT-PRE-OPENAPI")
    assert tpex_h3_before["activation_state"] == "blocked"

    # Simulate rollback exclusively on independent in-memory copies.
    rollback_catalog = copy.deepcopy(catalog)
    rollback_routing = copy.deepcopy(routing)
    rollback_cap = next(item for item in rollback_catalog["data_need_capabilities"] if item["capability_id"] == "recent_performance")
    rollback_cap.update(
        support_status="contract_supported",
        runtime_executable=False,
        phase_h_activation_state="inactive",
    )
    rollback_catalog["phase_h_contract"]["active_phase_h_source_count"] = 4
    rollback_route = next(item for item in rollback_routing["routes"] if item["capability_id"] == "recent_performance")
    rollback_route.update(
        runtime_executable=False,
        selected_executor_id=None,
        routing_status="plan_only",
        network_required=False,
    )
    rollback_routing["phase_h_source_authority"]["active_source_count"] = 4
    h3_source = next(item for item in rollback_routing["phase_h_source_authority"]["records"] if item["source_id"] == "H3-TWSE-DEFAULT-BOUNDED")
    h3_source.update(activation_state="eligible", runtime_executable=False)
    # Candidate executor inventory and source metadata remain available.
    assert rollback_route["candidate_executor_ids"] == route_before["candidate_executor_ids"] == [EXECUTOR]
    assert rollback_route["source_compatibility_key"] == route_before["source_compatibility_key"]
    assert tpex_h3_before == next(item for item in rollback_route["source_authority_states"] if item["market"] == "TPEX")

    active_after = {
        item["source_id"]
        for item in rollback_routing["phase_h_source_authority"]["records"]
        if item["activation_state"] == "active" and item["runtime_executable"] is True
    }
    assert rollback_cap["support_status"] == "contract_supported"
    assert rollback_cap["runtime_executable"] is False
    assert rollback_cap["phase_h_activation_state"] == "inactive"
    assert rollback_route["runtime_executable"] is False
    assert rollback_route["selected_executor_id"] is None
    assert rollback_route["routing_status"] == "plan_only"
    assert rollback_catalog["phase_h_contract"]["active_phase_h_source_count"] == 4
    assert rollback_routing["phase_h_source_authority"]["active_source_count"] == 4
    assert active_after == {"H1-TPEX-ATTENTION-OPENAPI", "H1-TPEX-DISPOSITION-OPENAPI", "H1-TPEX-CHANGED-TRADING-OPENAPI", "H2-TWSE-EXRIGHT-PRE-OPENAPI"}
    assert h1_route_before == next(item for item in rollback_routing["routes"] if item["capability_id"] == "trading_status_context")
    assert h1_source_before == next(item for item in rollback_routing["phase_h_source_authority"]["records"] if item["source_id"] == "H1-TPEX-ATTENTION-OPENAPI")
    assert h2_routes_before == [item for item in rollback_routing["routes"] if item["capability_id"] == "corporate_action_context"]
    assert h2_records_before == [item for item in rollback_routing["phase_h_source_authority"]["records"] if item["source_id"].startswith("H2-")]
    assert h2_caps_before == [item for item in rollback_catalog["data_need_capabilities"] if item["capability_id"] == "corporate_action_context"]
    assert len(build_tool_specs()) == 6

    authorities = {
        "capability_catalog": rollback_catalog,
        "routing_matrix": rollback_routing,
        "handoff_contract": json.loads((ROOT / "docs/data_capabilities/m8r_05b_orchestration_handoff_contract.json").read_text(encoding="utf-8")),
        "executor_disposition": json.loads((ROOT / "docs/data_capabilities/m8r_05b_existing_orchestrator_disposition.json").read_text(encoding="utf-8")),
        "preview_schema": json.loads((ROOT / "schemas/unified_market_evidence_preview_response.v1.schema.json").read_text(encoding="utf-8")),
    }
    twse_request = _v3_request("TWSE", "1423")
    twse_security_master = OfflineSecurityMaster("TWSE", "1423")
    twse_validation = validate_unified_market_evidence_request(
        twse_request,
        security_master=twse_security_master,
        capability_catalog=rollback_catalog,
        request_schema=json.loads(REQUEST_SCHEMA_PATHS[PREFERRED_REQUEST_SCHEMA_VERSION].read_text(encoding="utf-8")),
    )
    twse_rollback_preview = build_mode_b1_preview_package(
        twse_request, twse_validation, twse_security_master,
        planning_timestamp="2026-09-29T00:00:00Z", authorities=authorities,
    )
    twse_plan = twse_rollback_preview["orchestration_plan"]
    assert twse_validation["validation_status"] == "valid"
    assert twse_validation["capability_results"][0]["status"] == "contract_supported"
    assert twse_rollback_preview["preview"]["status"] == "unsupported_capability"
    assert twse_rollback_preview["preview"]["bounds"]["estimated_network_calls"] == 0
    assert len(twse_plan["operations"]) == 1
    assert twse_plan["operations"][0]["operation_status"] == "plan_only_not_executable"
    assert twse_plan["operations"][0]["executor_id"] is None
    assert twse_plan["operations"][0]["network_required"] is False
    assert twse_rollback_preview["authorization_created"] is False
    assert twse_rollback_preview["network_executed"] is False

    tpex_request = _v3_request("TPEX", "6488")
    tpex_security_master = OfflineSecurityMaster("TPEX", "6488")
    tpex_validation = validate_unified_market_evidence_request(
        tpex_request,
        security_master=tpex_security_master,
        capability_catalog=rollback_catalog,
        request_schema=json.loads(REQUEST_SCHEMA_PATHS[PREFERRED_REQUEST_SCHEMA_VERSION].read_text(encoding="utf-8")),
    )
    tpex_preview = build_mode_b1_preview_package(
        tpex_request, tpex_validation, tpex_security_master,
        planning_timestamp="2026-09-29T00:00:00Z", authorities=authorities,
    )
    assert tpex_validation["validation_status"] == "valid"
    assert tpex_preview["preview"]["status"] != "ready_for_confirmation"
    assert tpex_preview["preview"]["bounds"]["estimated_network_calls"] == 0
    blocked = tpex_preview["orchestration_plan"]["blocked_operations"]
    assert len(blocked) == 1
    assert blocked[0]["capability_id"] == "recent_performance"
    assert blocked[0]["executor_id"] is None
    assert blocked[0]["executor_invocation_eligible"] is False
    assert "unsupported_market" in blocked[0]["blocking_reason_codes"]

    # H1 stays selected/executable under the same simulated rollback authority.
    h1_request = {
        "schema_version": PREFERRED_REQUEST_SCHEMA_VERSION,
        "request_id": "h0h-roll-004-h1-isolation",
        "execution_mode": "preview",
        "targets": [{"input": "6488", "market_hint": "TPEX", "resolution_requirement": "exact"}],
        "data_needs": [{"type": "trading_status_context", "priority": "required", "parameters": {}}],
    }
    h1_security_master = OfflineSecurityMaster("TPEX", "6488")
    h1_validation = validate_mode_a_request(h1_request, allow_fixture_snapshot=True)
    h1_preview = build_mode_b1_preview_package(
        h1_request, h1_validation, h1_security_master,
        planning_timestamp="2026-09-29T00:00:00Z", authorities=authorities,
    )
    h1_operation = h1_preview["orchestration_plan"]["operations"][0]
    assert h1_preview["preview"]["status"] == "ready_for_confirmation"
    assert h1_operation["operation_status"] == "executable_pending_approval"
    assert h1_operation["market"] == "TPEX"
    assert h1_operation["executor_id"] == "phase_h_h1_tpex_composite_executor"
    assert h1_operation["network_required"] is True
    assert h1_preview["authorization_created"] is False
    assert h1_preview["network_executed"] is False

    assert len(build_tool_specs()) == 6
    assert authority_files_before == {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in authority_files_before}
    assert evidence_before == _h3_roll_004_local_evidence_hashes()
    if evidence_before:
        assert evidence_before == {
            "primary": "e2e92c86d02a38fd1bafec249484e5142df464af2daae938c38125dd52e2a8eb",
            "governance": "5b5c69ad5d65233d4f72ce5071183b274c0b5367802dbeb1eecb81a19671d143",
            "telemetry": "2de9ccca53c76dc49d5c341220eb156f3c6b9d64d22f1fa19f9a22bc560243d7",
            "receipt": "86375dd7214874ff7119b480d87a3a3580a54c2b7ae7b47fdafdf1f102f9f7d8",
            "bundle": "cc34ddde3cc1b48b92c2b0052c169aef46f31e5317fe366ed0c7cbdcf7d0bd77",
            "result_v3": "7cd8ee5241ab775391f42e2094b6954cfffe9644e6e2b1ee77fe72d41ba94722",
            "audit_v3": "1cc487380befa76c4aad63165a1493628df923359af430e30ec708170fd5e8e1",
            "claim": evidence_before["claim"],
        }
        claim = json.loads((ROOT / "data/phase_h_h3_live_acceptance/20260929T021651Z-bb11ec10/control/umea-v1-3821b18dce3d1915813c/claims/umea-v1-3821b18dce3d1915813c.consumption-record.json").read_text(encoding="utf-8"))
        assert claim["state"] == "consumed_success"
        assert claim["attempt_count"] == 1

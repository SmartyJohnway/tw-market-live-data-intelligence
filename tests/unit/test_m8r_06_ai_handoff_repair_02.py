"""Focused no-network regressions for the Mode C human AI handoff repair."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import ValidationError, validate

from scripts.m8r_05c.errors import ProjectionError
from scripts.m8r_05c import evidence_projector
from scripts.m8r_05c.evidence_projector import LEGACY_PROJECTOR_VERSION, _project_envelope, _project_envelope_legacy, _project_official_eod
from scripts.m8r_05c.lineage_resolver import OperationBinding, build_lineage_map
from scripts.m8r_05c.markdown_renderer import render_result_markdown
from scripts.m8r_05c.models import ProjectionInputs
from scripts.m8r_05c.result_builder import build_result


def _binding(capability: str, market: str, target: str, record: dict) -> OperationBinding:
    return OperationBinding("op", capability, "adapter", target, capability, market, "succeeded", None,
        artifact_objects={"evidence/op.json": {"schema_version": "m8r_06_03_operation_evidence.v1", "source_family": "TWSE_OPENAPI" if market == "TWSE" else "TPEX_OPENAPI", "records": [record]}})


def _rich_current_record(symbol: str) -> dict:
    return {"source": "TWSE_MIS", "source_type": "official_browser_json_endpoint_candidate", "adapter_id": "adapter", "symbol": symbol, "display_symbol": symbol, "source_timestamp": "2026-08-12T03:17:00Z", "retrieved_at_utc": "2026-08-12T03:17:12Z", "delay_seconds": 12, "freshness_assessment": "candidate", "caveats": ["not_realtime_guaranteed"], "twse_mis_rich_facts": {"instrument_facts": {"instrument_kind_candidate": "security", "price_domain": "equity_price", "raw_c": symbol, "raw_name": "台積電"}, "market_mode_facts": {"market_mode_candidate": "regular_board"}, "session_state_candidate_facts": {"session_state_candidate": "regular"}, "price_facts": {"last_value": 2405, "previous_close": 2395, "open": 2405, "high": 2410, "low": 2390}, "limit_or_reference_facts": {"limit_up": 2630, "limit_down": 2160}, "displayed_depth_facts": {"applicable": True, "best_bid": 2405, "best_ask": 2410, "bid_prices": [2405,2400,2395,2390,2385], "ask_prices": [2410,2415,2420,2425,2430], "bid_quantities_raw": ["160"]*5, "ask_quantities_raw": ["1496"]*5}, "quality_facts": {"malformed_fields": [], "placeholder_fields": ["pz"], "ladder_mismatch_flags": [], "field_presence": {"pid": True, "m%": True}}, "raw_unknown_facts": {"raw_pid": "secret", "raw_hash": "secret"}}}


@pytest.mark.parametrize(("market", "target", "symbol"), [("TWSE", "TWSE:2330", "2330"), ("TPEX", "TPEX:5227", "5227")])
def test_current_observation_uses_controlled_standard_extended_and_excludes_file_only_fields(market, target, symbol):
    record = _rich_current_record(symbol)
    projected = _project_envelope(_binding("current_observation", market, target, record), [])
    rendered = render_result_markdown({"status": "full_success", "targets": [{"resolution": {"status": "resolved"}, "evidence": {"current_observation": {"status": projected.status, "observed_fields": projected.observed_fields, "caveats": projected.caveats}}}]})
    text = str(projected.observed_fields) + rendered
    assert "extended_displayed_depth_snapshot" in projected.observed_fields and "last_value" in text and "best_bid" in text
    assert all(flag in text for flag in ["displayed_snapshot_only", "not_full_order_book", "quantity_unit_unverified"])
    assert "twse_mis_rich_facts" not in text and "raw_pid" not in text and "field_presence" not in text and "raw_hash" not in text
    assert record["twse_mis_rich_facts"]["raw_unknown_facts"]["raw_pid"] == "secret"
    assert target == ("TWSE:2330" if market == "TWSE" else "TPEX:5227")


def test_blocked_m7b_projection_has_no_standard_or_extended_raw_fallback(monkeypatch):
    monkeypatch.setattr(evidence_projector, "promote_ai_safe_market_context_projection_for_controlled_context", lambda _candidate: {"safe_for_ai_context": False, "exposure_status": "blocked"})
    projected = _project_envelope(_binding("current_observation", "TPEX", "TPEX:5227", _rich_current_record("5227")), [])
    text = str(projected.observed_fields) + str(projected.caveats)
    assert projected.status == "missing"
    assert projected.observed_fields == {}
    assert "extended_displayed_depth_snapshot" not in text and "bid_prices" not in text and "twse_mis_rich_facts" not in text


def test_controlled_projection_selects_the_actual_twse_mis_rich_record():
    binding = _binding("current_observation", "TPEX", "TPEX:5227", _rich_current_record("5227"))
    binding.artifact_objects["evidence/op.json"]["records"].insert(0, {"source": "TPEX_OPENAPI", "symbol": "5227", "observed_fields": {"raw": "not-controlled"}})
    projected = _project_envelope(binding, [])
    assert projected.status == "available"
    assert projected.observed_fields["source_context"]["source"] == "TWSE_MIS"


def test_eod_is_available_with_unresolved_currentness_and_drift_is_caveated():
    stale_caveat = "unclassified rows are excluded from deterministic metrics and AI context by default"
    record = {"symbol": "5227", "market": "tpex_otc", "source_id": "TPEX_OPENAPI", "authority_level": "official_documented", "timing_class": "official_eod", "trade_date": "2026-08-11", "price": {"open": "34.00", "close": "34.45", "change": "0.45"}, "activity": {"trade_volume": 311506}, "caveats": [stale_caveat], "field_validation": {"instrument_classification": {"coverage_mode": "bounded_seed_only", "classification_status": "unclassified"}}}
    eod = _project_official_eod(_binding("official_eod_reference", "TPEX", "TPEX:5227", record), ["citation"])
    assert eod["status"] == "available" and eod["currentness_status"] == "calendar_status_unresolved"
    assert eod["price"]["close"] == "34.45" and "legacy_classifier_coverage_drift" in eod["caveats"]
    assert "canonical_identity_preserved_from_verified_execution_binding" in eod["caveats"]
    assert stale_caveat in record["caveats"] and stale_caveat not in eod["caveats"]
    markdown = render_result_markdown({"status": "full_success", "targets": [{"resolution": {"status": "resolved"}, "evidence": {"official_eod_reference": eod}}]})
    assert "34.45" in markdown and "日曆狀態未解析" in markdown
    assert stale_caveat not in markdown and "legacy_classifier_coverage_drift" in markdown


def _schema_result_with_eod(eod: dict) -> dict:
    return {"schema_version": "unified_market_evidence_result.v1", "result_id": "umeresult-v1-00000000000000000000", "result_hash": "0" * 64, "generated_at": "2026-07-20T12:00:00Z", "request_id": "req-001", "request_summary": {"execution_mode": "latest_published", "target_count": 1, "requested_data_needs": ["official_eod_reference"], "required_data_needs": ["official_eod_reference"], "optional_data_needs": []}, "status": "full_success", "targets": [{"client_target_reference": "target-1", "resolution": {"status": "resolved", "canonical_target_id": "TWSE:2330"}, "evidence": {"official_eod_reference": eod}, "coverage": {}, "caveats": [], "citations": []}], "audit_reference": {"audit_package_id": "umeap-v1-00000000000000000000", "schema_version": "unified_market_evidence_audit_package.v1", "relative_path": "audit/a.json"}}


def test_eod_schema_is_additive_but_not_empty_or_untyped():
    schema = json.loads((Path(__file__).parents[2] / "schemas" / "unified_market_evidence_result.v1.schema.json").read_text(encoding="utf-8"))
    legacy = {"currentness_status": "official_latest_completed_eod", "caveats": []}
    enriched = {"status": "available", "price": {"close": "34.45", "open": None}, "activity": {"trade_volume": 311506}, "caveats": []}
    validate(_schema_result_with_eod(legacy), schema)
    validate(_schema_result_with_eod(enriched), schema)
    with pytest.raises(ValidationError): validate(_schema_result_with_eod({}), schema)
    non_scalar = copy.deepcopy(enriched); non_scalar["price"]["close"] = {"raw": "34.45"}
    with pytest.raises(ValidationError): validate(_schema_result_with_eod(non_scalar), schema)
    unknown = copy.deepcopy(enriched); unknown["unexpected"] = True
    with pytest.raises(ValidationError): validate(_schema_result_with_eod(unknown), schema)


def test_eod_source_identity_mismatch_fails_closed_and_partial_display_is_one_based():
    record = {"symbol": "9999", "market": "tpex_otc", "source_id": "TPEX_OPENAPI", "price": {"close": "1"}}
    try:
        _project_official_eod(_binding("official_eod_reference", "TPEX", "TPEX:5227", record), [])
    except ProjectionError as exc:
        assert str(exc) == "official_eod_identity_mismatch"
    else:
        raise AssertionError("identity mismatch must fail closed")
    markdown = render_result_markdown({"status": "partially_failed", "partial_failures": [{"target_index": 1, "data_need": "current_observation", "reason": "missing"}], "targets": []})
    assert "目標 #2 [current_observation]" in markdown


def _plan_only_inputs() -> ProjectionInputs:
    root = Path(__file__).parents[2] / "tests" / "fixtures" / "m8r_05c"
    load = lambda name: json.loads((root / name).read_text(encoding="utf-8"))
    request, plan = load("request_single_target.json"), load("plan_single_target.json")
    request["data_needs"] = [{"type": "identity", "priority": "required"}, {"type": "recent_performance", "priority": "optional"}]
    plan["operations"].append({"operation_id": "plan-only-recent", "capability_id": "recent_performance", "executor_id": "", "canonical_target_ids": ["TW.2330"], "market": "TWSE", "operation_status": "plan_only_not_executable", "executor_invocation_eligible": False})
    return ProjectionInputs(request=request, f3_validation=load("f3_validation.json"), plan=plan, authorization=load("authorization.json"), consumption_binding=load("consumption_binding.json"), claim=load("claim.json"), receipt=load("receipt.json"), bundle=load("bundle.json"), artifact_root=str(root / "artifact_root"), calculated_at="2026-08-12T00:00:00Z", evidence_artifacts={"operations/op_identity/evidence.json": load("artifact_root/operations/op_identity/evidence.json")})


def test_plan_only_current_projection_is_explicit_without_weakening_missing_executable():
    inputs = _plan_only_inputs()
    lineage = build_lineage_map(inputs)
    plan_only = lineage.bindings["TW.2330"]["recent_performance"]
    assert plan_only.plan_operation_status == "plan_only_not_executable"
    assert plan_only.status == "plan_only_not_executed"
    result = build_result(inputs)
    evidence = result["targets"][0]["evidence"]["recent_performance"]
    metric = result["targets"][0]["derived_metrics"][0]
    markdown = render_result_markdown(result)
    assert result["status"] == "success_with_partial_coverage"
    assert evidence["status"] == "plan_only_not_executed"
    assert "operation_failed:unknown" not in evidence["caveats"]
    assert metric["status"] == "unavailable" and metric["invalid_reason"] == "recent_performance_plan_only_not_executed"
    assert "Plan-only（未執行）" in markdown and "no_execution_attempted" in markdown
    assert _project_envelope_legacy(plan_only, []).status == "failed"

    executable = copy.deepcopy(inputs)
    executable.plan["operations"][-1]["operation_status"] = "executable_pending_approval"
    missing = build_lineage_map(executable).bindings["TW.2330"]["recent_performance"]
    assert missing.status == "failed"
    assert _project_envelope(missing, []).caveats == ["operation_failed:unknown"]

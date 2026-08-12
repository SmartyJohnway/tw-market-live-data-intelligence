"""Focused no-network regressions for the Mode C human AI handoff repair."""
from __future__ import annotations

from scripts.m8r_05c.errors import ProjectionError
from scripts.m8r_05c.evidence_projector import _project_envelope, _project_official_eod
from scripts.m8r_05c.lineage_resolver import OperationBinding
from scripts.m8r_05c.markdown_renderer import render_result_markdown


def _binding(capability: str, market: str, target: str, record: dict) -> OperationBinding:
    return OperationBinding("op", capability, "adapter", target, capability, market, "succeeded", None,
        artifact_objects={"evidence/op.json": {"schema_version": "m8r_06_03_operation_evidence.v1", "source_family": "TWSE_OPENAPI" if market == "TWSE" else "TPEX_OPENAPI", "records": [record]}})


def test_current_observation_uses_controlled_standard_extended_and_excludes_file_only_fields():
    record = {"source": "TWSE_MIS", "source_type": "official_browser_json_endpoint_candidate", "adapter_id": "adapter", "symbol": "2330", "display_symbol": "2330", "source_timestamp": "2026-08-12T03:17:00Z", "retrieved_at_utc": "2026-08-12T03:17:12Z", "delay_seconds": 12, "freshness_assessment": "candidate", "caveats": ["not_realtime_guaranteed"], "twse_mis_rich_facts": {"instrument_facts": {"instrument_kind_candidate": "security", "price_domain": "equity_price", "raw_c": "2330", "raw_name": "台積電"}, "market_mode_facts": {"market_mode_candidate": "regular_board"}, "session_state_candidate_facts": {"session_state_candidate": "regular"}, "price_facts": {"last_value": 2405, "previous_close": 2395, "open": 2405, "high": 2410, "low": 2390}, "limit_or_reference_facts": {"limit_up": 2630, "limit_down": 2160}, "displayed_depth_facts": {"applicable": True, "best_bid": 2405, "best_ask": 2410, "bid_prices": [2405,2400,2395,2390,2385], "ask_prices": [2410,2415,2420,2425,2430], "bid_quantities_raw": ["160"]*5, "ask_quantities_raw": ["1496"]*5}, "quality_facts": {"malformed_fields": [], "placeholder_fields": ["pz"], "ladder_mismatch_flags": [], "field_presence": {"pid": True, "m%": True}}, "raw_unknown_facts": {"raw_pid": "secret", "raw_hash": "secret"}}}
    projected = _project_envelope(_binding("current_observation", "TWSE", "TWSE:2330", record), [])
    rendered = render_result_markdown({"status": "full_success", "targets": [{"resolution": {"status": "resolved"}, "evidence": {"current_observation": {"status": projected.status, "observed_fields": projected.observed_fields, "caveats": projected.caveats}}}]})
    text = str(projected.observed_fields) + rendered
    assert "extended_displayed_depth_snapshot" in projected.observed_fields and "last_value" in text and "best_bid" in text
    assert all(flag in text for flag in ["displayed_snapshot_only", "not_full_order_book", "quantity_unit_unverified"])
    assert "twse_mis_rich_facts" not in text and "raw_pid" not in text and "field_presence" not in text and "raw_hash" not in text
    assert record["twse_mis_rich_facts"]["raw_unknown_facts"]["raw_pid"] == "secret"


def test_eod_is_available_with_unresolved_currentness_and_drift_is_caveated():
    record = {"symbol": "5227", "market": "tpex_otc", "source_id": "TPEX_OPENAPI", "authority_level": "official_documented", "timing_class": "official_eod", "trade_date": "2026-08-11", "price": {"open": "34.00", "close": "34.45", "change": "0.45"}, "activity": {"trade_volume": 311506}, "field_validation": {"instrument_classification": {"coverage_mode": "bounded_seed_only", "classification_status": "unclassified"}}}
    eod = _project_official_eod(_binding("official_eod_reference", "TPEX", "TPEX:5227", record), ["citation"])
    assert eod["status"] == "available" and eod["currentness_status"] == "calendar_status_unresolved"
    assert eod["price"]["close"] == "34.45" and "classification_coverage_drift" in eod["caveats"]
    markdown = render_result_markdown({"status": "full_success", "targets": [{"resolution": {"status": "resolved"}, "evidence": {"official_eod_reference": eod}}]})
    assert "34.45" in markdown and "日曆狀態未解析" in markdown


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

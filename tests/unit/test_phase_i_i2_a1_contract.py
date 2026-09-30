"""Offline-only contract fixture checks; no market adapters or source calls."""
from __future__ import annotations

import json
from pathlib import Path
import sys

import jsonschema

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.validate_phase_i_i2_a1_contracts import (  # noqa: E402
    _valid_complete_fixture,
    decode_payload_fixture,
    normalize_selected_fixture,
    select_contract_fixture,
)


def _row(**overrides):
    row = {
        "Date": "20260929", "Contract": "TX", "ContractMonth(Week)": "202610",
        "Open": "48098", "High": "48194", "Low": "47630", "Last": "47767",
        "Change": "-358", "%": "-0.74%", "Volume": "43812", "SettlementPrice": "47781",
        "OpenInterest": "102023", "BestBid": "47753", "BestAsk": "47765",
        "TradingHalt": "-", "TradingSession": "一般",
    }
    row.update(overrides)
    return row


def _schema_validator():
    schema_path = ROOT / "schemas/index_futures_context_evidence.v1.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    return jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())


def test_a1_complete_schema_accepts_contract_shape_and_percent_scale():
    validator = _schema_validator()
    evidence = _valid_complete_fixture({})
    validator.validate(evidence)
    assert evidence["market_data"]["change_percent"] == -0.74
    assert evidence["unit_metadata"]["change_percent"] == "percent"


def test_only_regular_session_and_nearest_valid_standard_month_are_selected():
    rows = [
        _row(**{"ContractMonth(Week)": "202610", "TradingSession": "盤後"}),
        _row(**{"ContractMonth(Week)": "202611"}),
        _row(**{"ContractMonth(Week)": "202612"}),
        _row(**{"ContractMonth(Week)": "202610"}, Date="20260928"),
        _row(**{"ContractMonth(Week)": "202610/202611"}),
        _row(**{"ContractMonth(Week)": "2026W1"}),
        _row(**{"ContractMonth(Week)": "202613"}),
    ]
    status, selected = select_contract_fixture(rows)
    assert status == "selected"
    assert selected["ContractMonth(Week)"] == "202611"
    assert selected["TradingSession"] == "一般"
    assert selected["_selected_date"] == "20260929"
    assert select_contract_fixture([_row(**{"ContractMonth(Week)": "202613"})]) == ("unavailable", None)


def test_newest_valid_date_without_eligible_tx_does_not_fallback():
    status, selected = select_contract_fixture([
        _row(Date="20260928"),
        _row(Date="20260929", Contract="MTX"),
    ])
    assert (status, selected) == ("unavailable", None)


def test_no_valid_gregorian_compact_date_fails_source():
    status, selected = select_contract_fixture([_row(Date="1150929"), _row(Date="20260230")])
    assert (status, selected) == ("source_failed", None)


def test_duplicate_nearest_selected_binding_fails_closed():
    status, selected = select_contract_fixture([_row(), _row()])
    assert (status, selected) == ("binding_failed", None)


def test_percent_and_missing_markers_keep_frozen_semantics():
    status, normalized = normalize_selected_fixture(_row())
    assert status == "complete"
    assert normalized["market_data"]["change_percent"] == -0.74
    for marker in ("-", "NULL", ""):
        status, normalized = normalize_selected_fixture(_row(Volume=marker))
        assert status == "partial"
        assert normalized["market_data"]["volume"] is None
        assert "volume" in normalized["missing_fields"]
    assert normalize_selected_fixture(_row(Volume="not-an-integer"))[0] == "source_failed"
    assert normalize_selected_fixture(_row(Volume="-2"))[0] == "source_failed"
    malformed_keys = _row()
    malformed_keys.pop("Last")
    assert normalize_selected_fixture(malformed_keys)[0] == "source_failed"


def test_evidence_schema_accepts_explicit_partial_and_failure_without_fake_values():
    validator = _schema_validator()
    complete = _valid_complete_fixture({})
    partial = {**complete, "status": "partial", "missing_fields": ["open_interest"]}
    partial["market_data"] = dict(partial["market_data"])
    partial["market_data"].pop("open_interest")
    validator.validate(partial)
    assert partial["market_data"]
    assert partial["unit_metadata"]
    assert partial["missing_fields"]
    for status in ("unavailable", "source_failed", "binding_failed"):
        failure = {**complete, "status": status}
        for key in ("contract_period", "trade_date", "market_data", "unit_metadata"):
            failure.pop(key, None)
        if status == "source_failed":
            failure["transport"] = {**failure["transport"], "http_status": None, "content_type": None, "response_sha256": None, "get_count": 1}
        validator.validate(failure)
    transport_failure = {**complete, "status": "source_failed"}
    for key in ("contract_period", "trade_date", "market_data", "unit_metadata"):
        transport_failure.pop(key, None)
    transport_failure["transport"] = {**transport_failure["transport"], "http_status": 503, "content_type": None, "response_sha256": None, "error_code": "http_status_not_200"}
    validator.validate(transport_failure)
    bad_complete = {**complete, "market_data": {"open": 1}}
    assert not validator.is_valid(bad_complete)
    invalid_sentinel = {**complete, "status": "source_failed", "trade_date": "0001-01-01"}
    # ISO-format validation is syntactic; the failure fixture requires no date at all.
    for key in ("contract_period", "trade_date", "market_data", "unit_metadata"):
        invalid_sentinel.pop(key, None)
    validator.validate(invalid_sentinel)


def test_partial_evidence_requires_nonempty_observations_units_and_governed_missing_fields():
    validator = _schema_validator()
    complete = _valid_complete_fixture({})
    partial = {**complete, "status": "partial", "missing_fields": ["open_interest"]}
    partial["market_data"] = dict(partial["market_data"])
    partial["market_data"].pop("open_interest")
    validator.validate(partial)

    without_market_data = {**partial}
    without_market_data.pop("market_data")
    assert not validator.is_valid(without_market_data)

    without_unit_metadata = {**partial}
    without_unit_metadata.pop("unit_metadata")
    assert not validator.is_valid(without_unit_metadata)

    assert not validator.is_valid({**partial, "market_data": {}})
    assert not validator.is_valid({**partial, "unit_metadata": {}})
    assert not validator.is_valid({**partial, "missing_fields": ["not_a_governed_i2_observation"]})


def test_payload_byte_row_utf8_json_and_root_bounds_fail_closed():
    valid = json.dumps([_row()], ensure_ascii=False).encode("utf-8")
    assert decode_payload_fixture(valid)[0] == "available"
    assert decode_payload_fixture(b"\xff\xfe")[0] == "source_failed"
    assert decode_payload_fixture(b"{")[0] == "source_failed"
    assert decode_payload_fixture(b"{}")[0] == "source_failed"
    assert decode_payload_fixture(b" " * (2_097_152 + 1))[0] == "source_failed"
    too_many = json.dumps([{}] * 5001).encode("utf-8")
    assert decode_payload_fixture(too_many)[0] == "source_failed"


def test_i2_a1_keeps_tpex_and_runtime_route_unsupported_and_dormant():
    contract = json.loads((ROOT / "docs/governance/phase_i/PHASE_I_I2_TX_REGULAR_SESSION_SOURCE_EVIDENCE_CONTRACT_2026-09-30_FROZEN.json").read_text(encoding="utf-8"))
    catalog = json.loads((ROOT / "docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json").read_text(encoding="utf-8"))
    routing = json.loads((ROOT / "docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json").read_text(encoding="utf-8"))
    assert contract["target_association"]["tpex_supported"] is False
    assert contract["runtime_activation"]["i2_active_sources"] == 0
    assert contract["runtime_activation"]["i2_normal_production_routes"] == 0
    i2_cap = next(item for item in catalog.get("data_need_capabilities", []) if item.get("capability_id") == "index_futures_context")
    i2_route = next(item for item in routing.get("routes", []) if item.get("capability_id") == "index_futures_context")
    assert i2_cap["support_status"] == "contract_supported" and i2_cap["runtime_executable"] is False
    assert i2_route["routing_status"] == "plan_only" and i2_route["selected_executor_id"] is None

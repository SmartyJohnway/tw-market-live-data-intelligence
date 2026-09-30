"""Offline governance and fixture checks for frozen Phase I I2-A1.

This module is a contract validator/test oracle only. It is not imported by the
runtime and performs no network or production normalization work.
"""
from __future__ import annotations

from datetime import date
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = "docs/governance/phase_i/PHASE_I_I2_TX_REGULAR_SESSION_SOURCE_EVIDENCE_CONTRACT_2026-09-30_FROZEN.json"
A0_PATH = "docs/governance/phase_i/PHASE_I_I2_A0_TX_REGULAR_SESSION_GO_NO_GO_PREFLIGHT_2026-09-30.json"
EVIDENCE_SCHEMA_PATH = "schemas/index_futures_context_evidence.v1.schema.json"
MAX_BYTES = 2_097_152
MAX_ROWS = 5_000
MONTH_RE = re.compile(r"^[0-9]{6}$")
DATE_RE = re.compile(r"^[0-9]{8}$")


class I2A1ContractError(ValueError):
    pass


def _json(path: str) -> Any:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def parse_compact_date(value: Any) -> date | None:
    if not isinstance(value, str) or not DATE_RE.fullmatch(value):
        return None
    try:
        return date(int(value[:4]), int(value[4:6]), int(value[6:8]))
    except ValueError:
        return None


def select_contract_fixture(rows: list[dict[str, Any]]) -> tuple[str, dict[str, Any] | None]:
    """Test-only deterministic selector for frozen A1 examples."""
    valid = [(parse_compact_date(row.get("Date")), row) for row in rows]
    valid = [(parsed, row) for parsed, row in valid if parsed is not None]
    if not valid:
        return "source_failed", None
    latest = max(parsed for parsed, _ in valid)
    latest_text = latest.strftime("%Y%m%d")
    eligible: list[tuple[str, dict[str, Any]]] = []
    for parsed, row in valid:
        if parsed != latest or row.get("Contract") != "TX" or row.get("TradingSession") != "一般":
            continue
        period = row.get("ContractMonth(Week)")
        if not isinstance(period, str) or not MONTH_RE.fullmatch(period):
            continue
        if not 1 <= int(period[4:6]) <= 12:
            continue
        eligible.append((period, row))
    if not eligible:
        return "unavailable", None
    nearest = min(period for period, _ in eligible)
    bound = [row for period, row in eligible if period == nearest]
    if len(bound) != 1:
        return "binding_failed", None
    return "selected", {**bound[0], "_selected_date": latest_text}


def normalize_selected_fixture(row: dict[str, Any]) -> tuple[str, dict[str, Any] | None]:
    """Test-only field-contract oracle; never used to acquire or serve data."""
    required_keys = {"Date", "Contract", "ContractMonth(Week)", "Open", "High", "Low", "Last", "Change", "%", "Volume", "SettlementPrice", "OpenInterest", "BestBid", "BestAsk", "TradingHalt", "TradingSession"}
    if not required_keys <= set(row):
        return "source_failed", None
    numeric_map = {
        "Open": "open", "High": "high", "Low": "low", "Last": "last", "Change": "change_points",
        "%": "change_percent", "Volume": "volume", "SettlementPrice": "settlement_price", "OpenInterest": "open_interest",
        "BestBid": "best_bid", "BestAsk": "best_ask",
    }
    missing_markers = {"", "-", "NULL"}
    values: dict[str, Any] = {}
    missing: list[str] = []
    complete_fields = {"open", "high", "low", "last", "change_points", "change_percent", "volume", "settlement_price", "open_interest"}
    for source_key, target_key in numeric_map.items():
        raw = row[source_key]
        if not isinstance(raw, str):
            return "source_failed", None
        text = raw.strip() if isinstance(raw, str) else raw
        if text in missing_markers:
            values[target_key] = None
            if target_key in complete_fields:
                missing.append(target_key)
            continue
        if target_key == "change_percent" and isinstance(text, str) and text.endswith("%"):
            text = text[:-1]
        try:
            if target_key in {"volume", "open_interest"}:
                if isinstance(text, bool) or str(text).strip() != str(int(text)):
                    raise ValueError("non_integer_count")
                values[target_key] = int(text)
                if values[target_key] < 0:
                    raise ValueError("negative_count")
            else:
                number = float(text)
                if not __import__("math").isfinite(number):
                    raise ValueError("non_finite")
                values[target_key] = number
        except (TypeError, ValueError, OverflowError):
            return "source_failed", None
    return ("partial" if missing else "complete"), {"market_data": values, "missing_fields": missing}


def decode_payload_fixture(body: bytes) -> tuple[str, list[dict[str, Any]] | None]:
    """Test-only validation of the frozen in-memory payload bounds."""
    if len(body) > MAX_BYTES:
        return "source_failed", None
    try:
        decoded = json.loads(body.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return "source_failed", None
    if not isinstance(decoded, list) or len(decoded) > MAX_ROWS or any(not isinstance(row, dict) for row in decoded):
        return "source_failed", None
    return "available", decoded


def _valid_complete_fixture(schema: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "index_futures_context_evidence.v1",
        "status": "complete",
        "target_market": "TWSE",
        "venue": "TAIFEX",
        "product_code": "TX",
        "contract_period": "202610",
        "trade_date": "2026-09-29",
        "trading_session": "regular",
        "currentness_status": "unknown",
        "retrieved_at": "2026-09-30T00:00:00Z",
        "market_data": {
            "open": 48098, "high": 48194, "low": 47630, "last": 47767,
            "change_points": -358, "change_percent": -0.74, "volume": 43812,
            "settlement_price": 47781, "open_interest": 102023,
            "best_bid": 47753, "best_ask": 47765,
        },
        "unit_metadata": {
            "open": "index_point", "high": "index_point", "low": "index_point",
            "last": "index_point", "change_points": "index_point",
            "change_percent": "percent", "volume": "contract_count",
            "settlement_price": "index_point", "open_interest": "contract_count",
            "best_bid": "index_point", "best_ask": "index_point",
        },
        "alignment_status": "not_comparable",
        "source": {
            "source_id": "I2-TAIFEX-DAILYMARKETREPORTFUT-OPENAPI",
            "source_family": "TAIFEX_DAILY_MARKET_REPORT_FUT",
            "source_contract_id": "TAIFEX_DAILY_MARKET_REPORT_FUT_OPENAPI_V1",
            "endpoint": "https://openapi.taifex.com.tw/v1/DailyMarketReportFut",
            "authority": "official_taifex_oas_open_data", "dataset_id": "11319", "attribution_required": True,
        },
        "transport": {
            "http_status": 200, "content_type": "application/octet-stream", "response_byte_count": 813057,
            "response_sha256": "7a35adfc030aba52378dcc5e68a1bcfd90082d4a065b3fff891a365e9fa9370b",
            "retrieved_at": "2026-09-30T00:00:00Z", "get_count": 1, "retry_count": 0,
            "raw_payload_persisted": False,
        },
        "citation_ids": ["fixture-citation"],
        "caveats": ["Descriptive official-session context; not a trading signal."],
    }


def validate_a1_contract() -> None:
    contract = _json(CONTRACT_PATH)
    a0 = _json(A0_PATH)
    schema = _json(EVIDENCE_SCHEMA_PATH)
    contract_sha = hashlib.sha256((ROOT / CONTRACT_PATH).read_bytes()).hexdigest()
    companion = (ROOT / "docs/governance/phase_i/Phase_I_I2_TX_Regular_Session_Source_Evidence_Contract_2026-09-30_FROZEN.md").read_text(encoding="utf-8")
    if f"JSON SHA-256: `{contract_sha}`" not in companion:
        raise I2A1ContractError("markdown_companion_json_hash_mismatch")
    if (a0.get("owner_authority_ref"), a0.get("recorded_under_a1_authority_ref")) != (
        "USER_CHAT_2026-09-30_PHASE_I_I2_A0_TX_REGULAR_SESSION_GO_NO_GO_PREFLIGHT",
        "USER_CHAT_2026-09-30_PHASE_I_I2_A1_TX_REGULAR_SESSION_SOURCE_EVIDENCE_CONTRACT_FREEZE",
    ):
        raise I2A1ContractError("a0_execution_and_recording_authorities_not_separated")
    if (contract.get("status"), contract.get("gate"), contract.get("capability_id")) != ("FROZEN_PASS", "I2-A1", "index_futures_context"):
        raise I2A1ContractError("a1_identity_or_status_invalid")
    if contract["authority_boundary"].get("a2_implementation_authorized") is not False:
        raise I2A1ContractError("a2_must_remain_unauthorized")
    if contract["source_authority"].get("source_family") != "TAIFEX_DAILY_MARKET_REPORT_FUT" or contract["source_authority"].get("source_contract_id") != "TAIFEX_DAILY_MARKET_REPORT_FUT_OPENAPI_V1":
        raise I2A1ContractError("source_authority_mismatch")
    if contract["source_authority"]["government_open_data"].get("dataset_id") != "11319" or contract["source_authority"]["government_open_data"].get("attribution_required") is not True:
        raise I2A1ContractError("government_dataset_attribution_missing")
    if contract["product_scope"].get("source_trading_session") != "一般" or contract["series_selector"].get("standard_month_fullmatch_regex") != "^[0-9]{6}$":
        raise I2A1ContractError("regular_session_or_series_selector_drift")
    t = contract["transport"]
    if (t.get("maximum_unique_gets_per_governed_execution"), t.get("automatic_retry_count"), t.get("timeout_seconds"), t.get("maximum_response_bytes"), t.get("maximum_root_rows"), t.get("raw_payload_persistence")) != (1, 0, 30, MAX_BYTES, MAX_ROWS, "forbidden"):
        raise I2A1ContractError("transport_bounds_drift")
    if contract["target_association"].get("eligible_market") != "TWSE" or contract["target_association"].get("eligible_instrument_family") != "company_share" or contract["target_association"].get("eligible_instrument_type") != "common_share":
        raise I2A1ContractError("target_association_drift")
    excluded = set(contract["product_scope"].get("excluded", []))
    required_exclusions = {"after_hours_盤後", "weekly_series", "calendar_spreads", "options", "put_call_ratio", "institutional_positioning", "large_trader_positioning", "MTX", "TMF", "single_stock_futures", "historical_lookup", "historical_backfill", "rolling_futures_calculations", "continuous_contract_synthesis", "futures_basis_or_premium_discount", "trading_signals", "bullish_or_bearish_labels"}
    if not required_exclusions <= excluded:
        raise I2A1ContractError("product_scope_exclusions_incomplete")
    fields = contract["source_row_contract"]["fields"]
    if fields["%"]["example_normalized"] != -0.74 or fields["%"]["unit"] != "percent" or fields["%"]["fraction_conversion"] is not False:
        raise I2A1ContractError("percent_scale_semantics_drift")
    if contract["evidence_contract"]["currentness_status"] != "unknown" or contract["timing_and_alignment"]["equal_dates_mean_simultaneous_observations"] is not False:
        raise I2A1ContractError("timing_or_alignment_guard_drift")
    if contract["runtime_activation"].get("i2_normal_production_routes") != 0 or contract["runtime_activation"].get("i2_active_sources") != 0 or contract["runtime_activation"].get("current_i1_active_sources") != 3 or contract["runtime_activation"].get("mcp_tool_count") != 6:
        raise I2A1ContractError("runtime_dormancy_or_i1_count_drift")
    if (a0["status"], a0["source"]["response_sha256"], a0["source"]["response_bytes"], a0["source"]["root_row_count"], a0["source"]["unique_source_dates"], a0["selection_observation"]["selected"]["ContractMonth(Week)"], a0["selection_observation"]["eligible_tx_regular_standard_month_candidates"]) != ("PASS_GO", "7a35adfc030aba52378dcc5e68a1bcfd90082d4a065b3fff891a365e9fa9370b", 813057, 2156, ["20260929"], "202610", ["202610", "202611", "202612", "202703", "202706", "202709"]):
        raise I2A1ContractError("a0_accepted_observation_drift")
    expected_selected = {"Date": "20260929", "Contract": "TX", "ContractMonth(Week)": "202610", "TradingSession": "一般", "Open": "48098", "High": "48194", "Low": "47630", "Last": "47767", "Change": "-358", "%": "-0.74%", "Volume": "43812", "SettlementPrice": "47781", "OpenInterest": "102023", "BestBid": "47753", "BestAsk": "47765"}
    if a0["selection_observation"]["selected"] != expected_selected or a0["source"].get("http_status") != 200 or a0["source"].get("content_type") != "application/octet-stream" or a0["source"].get("trading_sessions_observed") != ["一般", "盤後"] or a0["source"].get("required_source_keys_missing") != []:
        raise I2A1ContractError("a0_selected_row_or_transport_drift")
    if a0["source"].get("get_count") != 1 or a0["source"].get("retry_count") != 0 or a0["source"].get("raw_response_committed") is not False or a0.get("market_network_calls_in_this_a1_tranche") != 0:
        raise I2A1ContractError("a0_or_a1_network_boundary_drift")

    catalog = _json("docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json")
    routing = _json("docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json")
    source_authority = _json("docs/data_capabilities/phase_i_i1_source_authority.v1.json")
    registry = _json("config/m8r_06_03_executor_registry_metadata.json")
    if any(item.get("capability_id") == "index_futures_context" for item in catalog.get("data_need_capabilities", [])):
        raise I2A1ContractError("i2_capability_placeholder_unexpected")
    if any(item.get("capability_id") == "index_futures_context" for item in routing.get("routes", [])):
        raise I2A1ContractError("i2_route_must_remain_absent")
    if any(item.get("capability_id") == "index_futures_context" for item in registry.get("executors", [])):
        raise I2A1ContractError("i2_executor_must_remain_absent")
    expected_i1 = {"I1-TWSE-FMTQIK-OPENAPI", "I1-TWSE-BREADTH-TWTAZU-OPENAPI", "I1-TPEX-MAINBOARD-HIGHLIGHT-OPENAPI"}
    active_i1 = {item.get("source_id") for item in source_authority.get("records", []) if item.get("activation_state") == "active" and item.get("runtime_executable") is True}
    if source_authority.get("active_source_count") != 3 or active_i1 != expected_i1:
        raise I2A1ContractError("i1_active_source_truth_changed")
    if any(item.get("capability_id") in {"taifex_market_state", "institutional_positioning_context"} for item in catalog.get("data_need_capabilities", [])):
        raise I2A1ContractError("i3_scope_unexpectedly_added")
    sys.path.insert(0, str(ROOT))
    from server.unified_mcp.tool_contracts import build_tool_contract_snapshot
    if len(build_tool_contract_snapshot().tools) != 6:
        raise I2A1ContractError("mcp_tool_count_changed")
    jsonschema.Draft202012Validator.check_schema(schema)
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    complete = _valid_complete_fixture(schema)
    validator.validate(complete)
    failure = dict(complete)
    for status in ("unavailable", "source_failed", "binding_failed"):
        item = {**failure, "status": status}
        for key in ("contract_period", "trade_date", "market_data", "unit_metadata"):
            item.pop(key, None)
        validator.validate(item)
    oversize_failure = {**failure, "status": "source_failed"}
    oversize_failure["transport"] = {**oversize_failure["transport"], "response_byte_count": MAX_BYTES + 1, "http_status": 200, "content_type": "application/octet-stream"}
    validator.validate(oversize_failure)
    invalid_complete = {**complete, "market_data": {"open": 1}}
    if validator.is_valid(invalid_complete):
        raise I2A1ContractError("complete_without_governed_fields_accepted")
    partial = {**complete, "status": "partial", "missing_fields": ["open_interest"]}
    partial["market_data"] = {key: value for key, value in complete["market_data"].items() if key != "open_interest"}
    validator.validate(partial)
    for field in ("market_data", "unit_metadata"):
        invalid_partial = {**partial}
        invalid_partial.pop(field)
        if validator.is_valid(invalid_partial):
            raise I2A1ContractError(f"partial_without_{field}_accepted")
        invalid_partial = {**partial, field: {}}
        if validator.is_valid(invalid_partial):
            raise I2A1ContractError(f"partial_with_empty_{field}_accepted")
    invalid_partial = {**partial, "missing_fields": ["invented_market_metric"]}
    if validator.is_valid(invalid_partial):
        raise I2A1ContractError("partial_with_ungoverned_missing_field_accepted")
    print("Phase I I2-A1 source/evidence contract: PASS (offline, dormant, no source calls)")


if __name__ == "__main__":
    validate_a1_contract()

"""Pure adapter from M8C-01 TAIFEX MIS observations to M8 builder observations.

The adapter is intentionally fail-closed: malformed or incomplete runtime
observations are converted to metadata-only contexts, never defaulted into a
market-valued futures/options snapshot.
"""
from __future__ import annotations

import re
from decimal import Decimal
from typing import Any

SCHEMA_VERSION = "m8c_taifex_mis_context_adapter.v1"
MONTHLY_YYYYMM_RE = re.compile(r"^\d{6}$")
VALID_CURRENTNESS = {
    "active_session_fresh_liveish",
    "active_session_aging_liveish",
    "active_session_stale_liveish",
    "preopen",
    "indicative",
    "halted",
    "noncontinuous_phase",
    "closed_session_latest_completed",
    "special_closure_latest_completed",
    "closed_session_historical",
    "market_phase_unresolved",
    "session_alignment_unresolved",
    "source_timestamp_unresolved",
    "transport_completed_without_valid_snapshot",
    "no_accepted_mode_1",
}
OMITTED_FIELDS = [
    "numeric_qid_keys",
    "trueValues",
    "raw_mode_1_dictionary",
    "raw_rest_records",
    "raw_payload",
    "full_option_chain",
    "raw_qid_map",
    "competing_top_of_book_families",
    "cookies",
    "session_ids",
]


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    return [value]


def _append_unique(items: list[Any], value: Any) -> None:
    if value and value not in items:
        items.append(value)


def _json_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {k: _json_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_value(v) for v in value]
    return value


def _provenance_source(prov: Any) -> Any:
    if isinstance(prov, dict):
        return prov.get("source")
    return None


def _contract_identity(obs: dict) -> dict:
    return {
        "requested_product_id": obs.get("requested_product_id"),
        "mis_cid": obs.get("mis_cid"),
        "runtime_symbol_id": obs.get("runtime_symbol_id"),
        "contract_month_or_week": obs.get("contract_month_or_week"),
        "strike_price": obs.get("strike_price"),
        "option_type": obs.get("option_type"),
        "session": obs.get("session"),
    }


def _source_time(obs: dict) -> dict:
    return {
        "source_timestamp": obs.get("source_timestamp_asia_taipei"),
        "cdate_raw": obs.get("raw_CDate"),
        "ctime_raw": obs.get("raw_CTime"),
    }


def _accepted_mode_1_present(obs: dict) -> bool:
    provenance = obs.get("field_provenance") or {}
    return any(_provenance_source(provenance.get(key)) == "sockjs_mode_1" for key in ("last_price", "reference_price", "total_volume"))


def validate_taifex_mis_runtime_observation(observation: dict) -> dict:
    """Validate one normalized M8C-01 observation for value projection eligibility."""
    obs = dict(observation or {})
    errors: list[str] = []
    source_id = obs.get("source_id", "TAIFEX_MIS")
    if source_id != "TAIFEX_MIS":
        errors.append("source_id_not_taifex_mis")
    instrument = obs.get("instrument_type")
    if instrument not in {"future", "option"}:
        errors.append("unsupported_or_missing_instrument_type")
    if obs.get("session") != "regular":
        errors.append("session_not_regular")
    month = obs.get("contract_month_or_week")
    if not isinstance(month, str) or not MONTHLY_YYYYMM_RE.match(month):
        errors.append("contract_month_or_week_not_monthly_yyyymm")
    symbol = obs.get("runtime_symbol_id")
    suffix = "-F" if instrument == "future" else "-O" if instrument == "option" else None
    if not isinstance(symbol, str) or not suffix or not symbol.endswith(suffix):
        errors.append("runtime_symbol_suffix_mismatch")
    for field in ("requested_product_id", "mis_cid", "runtime_symbol_id", "contract_month_or_week"):
        if not obs.get(field):
            errors.append(f"missing_{field}")
    if instrument == "option" and (obs.get("strike_price") in (None, "") or obs.get("option_type") not in {"C", "P"}):
        errors.append("incomplete_option_identity")
    if obs.get("raw_payload_retained") is not False:
        errors.append("raw_payload_retained_not_false")
    currentness = obs.get("currentness") or {}
    overall = currentness.get("overall_ai_currentness")
    if overall not in VALID_CURRENTNESS:
        errors.append("unknown_currentness_status")
    accepted_mode_1 = _accepted_mode_1_present(obs)
    if not accepted_mode_1:
        errors.append("accepted_mode_1_provenance_missing")
    return {
        "schema_version": "m8c_taifex_mis_adapter_validation.v1",
        "valid": not errors,
        "errors": errors,
        "accepted_mode_1_present": accepted_mode_1,
        "currentness_status": overall,
    }


def _metadata_safe_fields(obs: dict) -> dict:
    return {
        "contract_identity": _contract_identity(obs),
        "source_time": _source_time(obs),
        "source_status_code": obs.get("source_status_code"),
        "currentness": obs.get("currentness"),
    }


def _valued_safe_fields(obs: dict) -> dict:
    cands = dict(obs.get("normalized_field_candidates") or {})
    canon_status = cands.get("canonicalization_status") or "top_of_book_field_family_unresolved"
    top = {
        "best_bid": _json_value(cands.get("best_bid")) if canon_status == "candidate_families_agree" else None,
        "best_ask": _json_value(cands.get("best_ask")) if canon_status == "candidate_families_agree" else None,
        "best_bid_size": _json_value(cands.get("best_bid_size")) if canon_status == "candidate_families_agree" else None,
        "best_ask_size": _json_value(cands.get("best_ask_size")) if canon_status == "candidate_families_agree" else None,
        "canonicalization_status": canon_status,
    }
    prov = obs.get("field_provenance") or {}
    fields = _metadata_safe_fields(obs)
    fields.update(
        {
            "price": {"last": _json_value(cands.get("last_price")), "reference": _json_value(cands.get("reference_price"))},
            "activity": {"total_volume": _json_value(cands.get("total_volume"))},
            "top_of_book": top,
            "field_provenance": {
                "last": _provenance_source(prov.get("last_price")),
                "reference": _provenance_source(prov.get("reference_price")),
                "total_volume": _provenance_source(prov.get("total_volume")),
            },
        }
    )
    return fields


def adapt_taifex_mis_observation(observation: dict) -> dict:
    obs = dict(observation or {})
    validation = validate_taifex_mis_runtime_observation(obs)
    inst = obs.get("instrument_type")
    context_type = None
    builder_inst = inst
    if inst == "future":
        context_type = "official_derivatives_futures_liveish_snapshot"
        builder_inst = "futures"
    elif inst == "option":
        context_type = "official_derivatives_options_liveish_snapshot"
        builder_inst = "options"
    safe_fields = _valued_safe_fields(obs) if validation["valid"] else _metadata_safe_fields(obs)
    caveats = _as_list(obs.get("caveats"))
    for caveat in [
        "regular session only",
        "monthly YYYYMM contracts only",
        "mode=1 initial state only",
        "no delta merge",
        "no reconnect",
        "no raw payload",
        "no full option chain",
        "directional interpretation forbidden",
    ]:
        _append_unique(caveats, caveat)
    if not validation["valid"]:
        _append_unique(caveats, "TAIFEX MIS observation failed strict adapter validation; market values withheld")
    return {
        "source_id": "TAIFEX_MIS",
        "source_family": "TAIFEX_MIS",
        "authority_level": "official_undocumented",
        "timing_class": "liveish_intraday_snapshot",
        "market": "taifex",
        "symbol": obs.get("runtime_symbol_id") or obs.get("symbol"),
        "instrument_type": builder_inst,
        "context_type": context_type,
        "source_timestamp": obs.get("source_timestamp_asia_taipei"),
        "retrieved_at_utc": obs.get("retrieved_at_utc"),
        "session": obs.get("session"),
        "currentness": obs.get("currentness"),
        "safe_fields": safe_fields,
        "omitted_fields": OMITTED_FIELDS,
        "caveats": list(dict.fromkeys(caveats)),
        "provenance": {"adapter_schema_version": SCHEMA_VERSION, "runtime_source": "M8C-01 TAIFEX MIS bounded runtime", "raw_payload_retained": False},
        "adapter_validation": validation,
        "observation_valid": validation["valid"],
        "accepted_mode_1_present": validation["accepted_mode_1_present"],
        "withhold_market_values_from_conversation": not validation["valid"],
    }


def _failure_observation(selector_result: dict, execution_result: dict, reason: str) -> dict:
    selector = selector_result.get("selector") if isinstance(selector_result, dict) else None
    symbol = selector_result.get("runtime_symbol_id") if isinstance(selector_result, dict) else None
    currentness = {
        "overall_ai_currentness": "transport_completed_without_valid_snapshot",
        "transport_state": execution_result.get("status"),
        "source_timestamp_state": "unresolved",
        "retrieved_at_freshness_ignored_for_upgrade": True,
    }
    return {
        "source_id": "TAIFEX_MIS",
        "source_family": "TAIFEX_MIS",
        "authority_level": "official_undocumented",
        "timing_class": "liveish_intraday_snapshot",
        "market": "taifex",
        "symbol": symbol or selector,
        "instrument_type": None,
        "context_type": None,
        "source_timestamp": None,
        "retrieved_at_utc": None,
        "session": "regular",
        "currentness": currentness,
        "safe_fields": {
            "contract_identity": {"runtime_symbol_id": symbol, "selector": selector, "session": "regular"},
            "source_time": {"source_timestamp": None, "cdate_raw": None, "ctime_raw": None},
            "source_status_code": None,
            "currentness": currentness,
        },
        "omitted_fields": OMITTED_FIELDS,
        "caveats": [reason, "metadata-only failed/missing TAIFEX MIS selector; no market values exposed"],
        "provenance": {"adapter_schema_version": SCHEMA_VERSION, "runtime_source": "M8C-01 TAIFEX MIS bounded runtime", "raw_payload_retained": False},
        "adapter_validation": {"schema_version": "m8c_taifex_mis_adapter_validation.v1", "valid": False, "errors": [reason], "accepted_mode_1_present": False, "currentness_status": "transport_completed_without_valid_snapshot"},
        "observation_valid": False,
        "accepted_mode_1_present": False,
        "source_unavailable": True,
        "source_unavailable_reason": reason,
        "withhold_market_values_from_conversation": True,
    }


def build_taifex_mis_m8_observations(execution_result_or_observations: Any) -> list[dict]:
    if not isinstance(execution_result_or_observations, dict):
        return [adapt_taifex_mis_observation(o) for o in (execution_result_or_observations or []) if isinstance(o, dict)]
    execution_result = execution_result_or_observations
    output = [adapt_taifex_mis_observation(o) for o in execution_result.get("observations", []) if isinstance(o, dict)]
    observed_symbols = {obs.get("symbol") for obs in output if obs.get("symbol")}
    for result in execution_result.get("selector_results", []) or []:
        if not isinstance(result, dict):
            continue
        symbol = result.get("runtime_symbol_id")
        if result.get("status") == "ok" or (symbol and symbol in observed_symbols):
            continue
        output.append(_failure_observation(result, execution_result, f"selector_result_{result.get('status') or 'missing'}"))
    for symbol in (execution_result.get("transport_summary") or {}).get("missing_symbols", []) or []:
        if symbol not in observed_symbols:
            output.append(_failure_observation({"runtime_symbol_id": symbol, "status": "missing_initial_state"}, execution_result, "transport_missing_symbol"))
    return output
